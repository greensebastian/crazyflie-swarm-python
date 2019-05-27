from CFUtil import CFUtil
from PyUtil import printf

from functools import partial
import copy
import time

import cflib.crtp
from cflib.crazyflie.swarm import Swarm
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie import State as CFStates

# List of URIs, comment the one you do not want to fly
uris_default = CFUtil.URIS_DEFAULT

'''
The Crazyflies should be positioned in a "cross" formation according to the image below for the positions to work.
They are all spaced 0.5 m apart meaning the total distance between drone 2 and drone 4 is 1 m.

Ex: drone 2 should be started on the ground 0.5 meters from drone 1 along the positive x-axis

    2             

3   1   5           x
                    ^
    4               |
                    |
            y <-----
'''

# Base positioning for take off and hovering [x, y, z, yaw]
pos_hover = CFUtil.POS_HOVER


class CfFactory:

    # Generate SyncCrazyflies with loggers according to base swarm setup
    def __init__(self, ro_cache=None, rw_cache=None):
        self.ro_cache = ro_cache
        self.rw_cache = rw_cache

    # Construct individual Crazyflie
    def construct(self, uri):
        cf = Crazyflie(ro_cache=self.ro_cache, rw_cache=self.rw_cache)
        return SyncCrazyflie(uri, cf)


class AsyncSwarm(Swarm):
    """
    Swarm wrapper for communicating with crazyflies. Contains functions for sending commands sequentially
    or in parallel.

    Swarm wide operations are sent through either one of the following functions:
        self.sequential(func, args_dict)
        self.parallel(func, args_dict)

    The first argument of the function that is passed in will be a
    SyncCrazyflie instance connected to the Crazyflie to operate on.
    A list of optional parameters (per Crazyflie) may follow defined by
    the args_dict. The dictionary is keyed on URI.

    Example:
    def my_function(scf, optional_param0, optional_param1)
        ...

    args_dict = {
        URI0: [optional_param0_cf0, optional_param1_cf0],
        URI1: [optional_param0_cf1, optional_param1_cf1],
        ...
    }

    self.sequential(my_function, args_dict)
    """

    def __init__(self, uri_indices, log=None, GUI_callback = None):
        uris = []
        for i in uri_indices:
            uris.append(uris_default[i])

        cflib.crtp.init_drivers(enable_debug_driver=False)

        self.GUI_callback = GUI_callback

        self._factory = CfFactory(rw_cache=CFUtil.RW_CACHE)
        super(AsyncSwarm, self).__init__(uris, self._factory)

        self.state = {}
        self.last_seen = {}
        for uri in uris:
            self.state[uri] = [None] * 6
            self.last_seen[uri] = [0, time.time()]

        self.log = log
        self.cb_log = None
        if log is not None:
            self.init_logging()

    def init_logging(self):
        self.cb_log = self.log.add_caller(name='callbacks', call=None, period_ms=None, start=False)

    def start(self, status_callback=None):
        """
        Open communication with all drones and wait for system to stabilize.
        """
        if self._is_open:
            print('Error, attempted connection on already open links')
            return
        starttime = time.time()
        self.open_links_sequence(status_callback)
        printf('Links opened after: %d seconds\n', int(time.time()-starttime))
        print('Starting all loggers...')
        self.parallel(partial(CFUtil.start_default_log_config, self.log_callback))
        printf('All logs initiated after: %d seconds\n', int(time.time() - starttime))

    def stop(self):
        self.close_links()
        status = {}
        for uri in CFUtil.URIS_DEFAULT:
            status[uri] = {CFUtil.KEY_CONNECTION: CFStates.DISCONNECTED, CFUtil.KEY_BATTERY: 0}
        print('Disconnected')
        self.GUI_update(status)

    def open_links_sequence(self, status_callback=None):
        """
        Open links to all individuals in the swarm
        """
        if self._is_open:
            print('Error, attempted connection on already open links')
            return
        try:
            self.sequential(self.connect_and_param)
            self.sequential(CFUtil.reset_estimator)
            self._is_open = True
        except Exception as e:
            print(e)
            self.close_links()
            raise e

    def connect_and_param(self, scf):
        """
        Open link to specified drone and wait for parameters to download.
        Calls external function that resets logging and tries again if first attempt unsuccessful.
        """
        uri = scf._link_uri
        self.GUI_update({uri: {CFUtil.KEY_CONNECTION: CFStates.INITIALIZED}})
        time.sleep(1)
        try:
            CFUtil.ext_open_link_cf(scf, timeout=3, retries=2)
        except AttributeError as e:
            print('Attribute Error caught: ' + ' '.join(e.args))
            self.GUI_update({uri: {CFUtil.KEY_CONNECTION: CFStates.DISCONNECTED}})
            return
        except Exception as e:
            print('Aborting connection')
            self.GUI_update({uri: {CFUtil.KEY_CONNECTION: CFStates.DISCONNECTED}})
            return
        CFUtil.wait_for_param_download(scf)
        CFUtil.stop_all_logging(scf)
        self.GUI_update({uri: {CFUtil.KEY_CONNECTION: CFStates.CONNECTED}})

    def add_drone(self, uri):
        # TODO fix all this...
        if uri in self._cfs:
            return
        scf = self._factory.construct(uri)
        self._cfs[uri] = scf
        self.state[uri] = [None] * 6
        self.last_seen[uri] = [0, time.time()]
        if self._is_open:
            self.connect_and_param(scf)

    def take_off_and_hover(self):
        """
        Uses predefined positions as listed above, be careful when starting
        :return:
        """
        print('Taking off...')
        self.parallel(CFUtil.take_off, args_dict=pos_hover)
        self.parallel(CFUtil.set_abs_pos_blocking, args_dict=pos_hover)

    def follow_controller(self, controller):
        """
        Retrieve velocity setpoints from controller and send to drones. Uses controllers get_u_list() function.
        :param controller: Object with get_u_list function as defined in Controllers file
        :param ignore_list: List of URIs to ignore. Any URI in list will not receive setpoint
        :return:
        """
        # TODO Change to function parameter instead of controller reference
        u = controller.get_u_list()

        self.parallel(CFUtil.set_world_vel_no_yaw, args_dict=u)

    def log_callback(self, uri, timestamp, data, logconf):
        """Callback from the log API when data arrives"""
        self.state[uri] = data
        self.last_seen[uri] = [timestamp, time.time()]
        if self.cb_log is not None:
            self.cb_log.push_data(copy.copy(self.last_seen))

    def get_state(self):
        """
        Get state of swarm as dictionary of dictionary containing [x, y, z, vx, vy, vz]
        ex: x = state[URI1]['kalman.stateX']
        """
        return copy.copy(self.state)

    def get_state_list(self):
        """
        Get state of swarm as list of dictionaries containing [x, y, z, vx, vy, vz]
        ex: x = state[0]['kalman.stateX']
        """
        return list(self.get_state().values())

    def get_relative_order(self):
        """
        Get relative positioning of all drones in swarm
        :return: 3 element list containing list of active uris sorted by ascending position in x/y/z direction
        """

        uris = list(self.state.keys())

        output = []
        output.append(sorted(uris, key=lambda uri: self.state[uri][CFUtil.KEY_X]))
        output.append(sorted(uris, key=lambda uri: self.state[uri][CFUtil.KEY_Y]))
        output.append(sorted(uris, key=lambda uri: self.state[uri][CFUtil.KEY_Z]))

        return output

    def get_uris(self):
        """
        Get list of active uris
        :return: list containing all active uris
        """
        return list(self._cfs.keys())

    def get_cfs(self):
        """
        Dict of drones
        :return: Dict of uris and drones
        """
        return self._cfs

    def GUI_update(self, state):
        """
        Push information to attached GUI
        :param state:
        :return:
        """
        if self.GUI_callback is not None:
            self.GUI_callback(state)
