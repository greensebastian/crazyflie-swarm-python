import time
from functools import partial
from threading import Thread
import numpy as np
from copy import deepcopy as copy
import math

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.crazyflie.commander import Commander
from cflib.crtp.crtpstack import CRTPPacket
from cflib.crazyflie import Crazyflie


class CFUtil:

    KEY_X = 'kalman.stateX'
    KEY_Y = 'kalman.stateY'
    KEY_Z = 'kalman.stateZ'
    KEY_DX = 'kalman.statePX'
    KEY_DY = 'kalman.statePY'
    KEY_DZ = 'kalman.statePZ'

    RW_CACHE = "./cache"

    # Drone URIs, set manually through client
    URI1 = 'radio://0/120/2M/E7E7E7E701'
    URI2 = 'radio://0/120/2M/E7E7E7E702'
    URI3 = 'radio://0/120/2M/E7E7E7E703'
    URI4 = 'radio://0/120/2M/E7E7E7E704'
    URI5 = 'radio://0/120/2M/E7E7E7E705'

    # List of URIs
    URIS_DEFAULT = (
        URI1,
        URI2,
        URI3,
        URI4,
        URI5
    )

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
    POS_HOVER = {
        URI1: [[0, 0, 1, 0]],
        URI2: [[0.5, 0, 1, 0]],
        URI3: [[0, 0.5, 1, 0]],
        URI4: [[-0.5, 0, 1, 0]],
        URI5: [[0, -0.5, 1, 0]]
    }

    POS_LAND = {
        URI1: [[0, 0, 0, 0]],
        URI2: [[0.5, 0, 0, 0]],
        URI3: [[0, 0.5, 0, 0]],
        URI4: [[-0.5, 0, 0, 0]],
        URI5: [[0, -0.5, 0, 0]]
    }

    @staticmethod
    def state_dict_to_numpy_matrix(state):
        """
        Changes dict{uri: dict{key: value}} to dict{uri: numpy[x, y ... dy, dz]}
        :param state: dictionary of dictionaries containing state information
        :returns: dictionary of arrays containing x-y-z-dx-dy-dz
        """
        state = copy(state)
        for uri in state:
            state[uri] = np.array([state[uri][CFUtil.KEY_X],
                                   state[uri][CFUtil.KEY_Y],
                                   state[uri][CFUtil.KEY_Z],
                                   state[uri][CFUtil.KEY_DX],
                                   state[uri][CFUtil.KEY_DY],
                                   state[uri][CFUtil.KEY_DZ]])
        return state

    @staticmethod
    def default_log_config(sample_time_ms=10):
        config = LogConfig(name='Kalman Position and Velocity', period_in_ms=sample_time_ms)
        config.add_variable(CFUtil.KEY_X, 'float')
        config.add_variable(CFUtil.KEY_Y, 'float')
        config.add_variable(CFUtil.KEY_Z, 'float')
        config.add_variable(CFUtil.KEY_DX, 'float')
        config.add_variable(CFUtil.KEY_DY, 'float')
        config.add_variable(CFUtil.KEY_DZ, 'float')
        return config

    @staticmethod
    def start_default_log_config(callback, scf, sample_time=50):
        log_config = CFUtil.default_log_config(sample_time_ms=sample_time)
        log_config.data_received_cb.add_callback(partial(callback, scf.cf.link_uri))
        scf.cf.log.add_config(log_config)
        log_config.start()
        while log_config._started is False:
            time.sleep(0.1)
        print('Logger started for ' + scf.cf.link_uri + ', sleep 0.5 seconds for stability.')
        time.sleep(0.5)

    @staticmethod
    def wait_for_position_estimator(scf):
        print('Waiting for estimator to find position...')

        log_config = LogConfig(name='Kalman Variance', period_in_ms=500)
        log_config.add_variable('kalman.varPX', 'float')
        log_config.add_variable('kalman.varPY', 'float')
        log_config.add_variable('kalman.varPZ', 'float')

        var_y_history = [1000] * 10
        var_x_history = [1000] * 10
        var_z_history = [1000] * 10

        threshold = 0.001

        with SyncLogger(scf, log_config) as logger:
            for log_entry in logger:
                data = log_entry[1]

                var_x_history.append(data['kalman.varPX'])
                var_x_history.pop(0)
                var_y_history.append(data['kalman.varPY'])
                var_y_history.pop(0)
                var_z_history.append(data['kalman.varPZ'])
                var_z_history.pop(0)

                min_x = min(var_x_history)
                max_x = max(var_x_history)
                min_y = min(var_y_history)
                max_y = max(var_y_history)
                min_z = min(var_z_history)
                max_z = max(var_z_history)

                # print("{} {} {}".
                #       format(max_x - min_x, max_y - min_y, max_z - min_z))

                if (max_x - min_x) < threshold and (
                        max_y - min_y) < threshold and (
                        max_z - min_z) < threshold:
                    break

    @staticmethod
    def wait_for_param_download(scf):
        while not scf.cf.param.is_updated:
            time.sleep(0.5)
        print('Parameters downloaded for', scf.cf.link_uri)

    @staticmethod
    def reset_estimator(scf):
        cf = scf.cf
        cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        cf.param.set_value('kalman.resetEstimation', '0')

        CFUtil.wait_for_position_estimator(cf)

    @staticmethod
    def set_abs_pos(scf, pos):
        if len(pos) < 4:
            pos = pos + (0,)
        cf = scf.cf
        mc = Commander(cf)
        mc.send_position_setpoint(pos[0], pos[1], pos[2], pos[3])

    @staticmethod
    def set_abs_pos_blocking(scf, pos, duration=5):
        cf = scf.cf
        hover_time = duration
        sleep_time = 0.2
        length = int(hover_time / sleep_time)

        mc = Commander(cf)

        for i in range(length):
            mc.send_position_setpoint(pos[0], pos[1], pos[2], pos[3])
            time.sleep(sleep_time)

    @staticmethod
    def set_world_vel(scf, vel):
        cf = scf.cf
        mc = Commander(cf)
        mc.send_velocity_world_setpoint(vel[0], vel[1], vel[2], vel[3])

    @staticmethod
    def set_world_vel_no_yaw(scf, vel, ignore=False):
        """
        Send velocity setpoint to drone and set desired yaw to 0
        :param scf: SyncCrazyflie to send setpoint to
        :param vel: Desired velocity as list [vx, vy, vz]
        :param ignore: True if statement setpoint should be ignored, useful for swarm functions
        :return:
        """
        if ignore:
            return
        cf = scf.cf
        mc = Commander(cf)
        mc.send_velocity_world_setpoint(vel[0], vel[1], vel[2], 0)

    @staticmethod
    def set_world_vel_blocking(scf, vel, duration=5):
        cf = scf.cf
        hover_time = duration
        sleep_time = 0.2
        length = int(hover_time / sleep_time)
        mc = Commander(cf)

        for i in range(length):
            mc.send_velocity_world_setpoint(vel[0], vel[1], vel[2], vel[3])
            time.sleep(sleep_time)

    @staticmethod
    def take_off(scf, position=(0, 0, 1, 0)):
        cf = scf.cf
        take_off_time = 1.0
        sleep_time = 0.1
        steps = int(take_off_time / sleep_time)
        vz = position[2] / take_off_time

        for i in range(steps):
            cf.commander.send_velocity_world_setpoint(0, 0, vz, 0)
            time.sleep(sleep_time)

    @staticmethod
    def take_off_raw(scf, position=(0, 0, 1, 0)):
        cf = scf.cf
        take_off_time = 1.0
        sleep_time = 0.1
        steps = int(take_off_time / sleep_time)
        thrust = 40000

        for i in range(steps):
            cf.commander.send_setpoint(roll=0, pitch=0, yaw=0, thrust=thrust)
            time.sleep(sleep_time)

    @staticmethod
    def get_land_dict(state):
        args_dict = {}
        state = CFUtil.state_dict_to_numpy_matrix(state)
        for uri in state:
            args_dict[uri] = CFUtil.POS_LAND[uri]
            args_dict[uri].append(list(state[uri]))
        return args_dict

    @staticmethod
    def land(scf, position, current_position=None):
        if current_position is None:
            return

        cf = scf.cf
        landing_time = 2.0
        sleep_time = 0.1
        steps = int(landing_time / sleep_time)
        vz = position[2]-current_position[2] / landing_time

        print(vz)

        for i in range(steps):
            cf.commander.send_velocity_world_setpoint(0, 0, vz, 0)
            time.sleep(sleep_time)

        CFUtil.send_stop_signal(scf)

    @staticmethod
    def ext_open_link_cf(scf, timeout=0, retries=5):
        cf = scf.cf
        tries = 0
        while tries < retries and cf.is_connected() is not True:
            tries = tries + 1
            print('Connection attempt ' + str(tries) + ' for ' + scf._link_uri)
            thread = Thread(target=partial(cf.open_link, scf._link_uri))
            thread.start()
            if timeout > 0:
                timestep = 0.1
                steps = timeout/timestep
                for i in range(int(steps)):
                    time.sleep(timestep)
                    if cf.is_connected():
                        break
            else:
                thread.join()

            if cf.is_connected():
                scf._is_link_open = True
                return
            else:
                try:
                    CFUtil.reset_logging(scf)
                    cf.close_link()
                except Exception as e:
                    print(e)

                cf = Crazyflie(rw_cache=CFUtil.RW_CACHE)
                scf.cf = cf
                scf._is_link_open = False
                print('Connection attempt failed...')

    @staticmethod
    def send_stop_signal(scf):
        cf = scf.cf
        mc = Commander(cf)
        mc.send_stop_setpoint()
        time.sleep(0.1)

    @staticmethod
    def stop_all_logging(scf):
        print('Stopping all loggers for: ' + scf.cf.link_uri)
        for index, log in enumerate(scf.cf.log.log_blocks):
            log.stop()
            log.delete()

    @staticmethod
    def reset_logging(scf):
        """Reset onboard logging for this Crazyflie"""
        print('Resetting onboard log settings for: ' + scf.cf.link_uri)
        CHAN_SETTINGS = 1
        CMD_RESET_LOGGING = 5
        if scf.cf.link is not None:
            pk = CRTPPacket()
            pk.set_header(5, CHAN_SETTINGS)
            pk.data = (CMD_RESET_LOGGING,)
            scf.cf.send_packet(pk)

    @staticmethod
    def wave_testing(scf, amp, time, freq, dimension):
        """
        Method for testing velocity controller system response at varying frequencies
        :param scf: Drone instance
        :return:
        """
        omega = 2*math.pi*freq
        x = 0
        y = 0
        z = 0
        if "x" in dimension:
            x = x + amp*math.sin(omega*time)
        if "y" in dimension:
            y = y + amp*math.sin(omega*time)
        if "z" in dimension:
            z = z + amp*math.sin(omega*time)
        #scf.cf.commander.send_velocity_world_setpoint(vx=x, vy=y, vz=z, yawrate=0)
        return x, y, z

    @staticmethod
    def generate_drone(name, pos=(0, 0, 1), vel=(0, 0, 0)):
        return {name: {CFUtil.KEY_X: pos[0], CFUtil.KEY_Y: pos[1], CFUtil.KEY_Z: pos[2],
                       CFUtil.KEY_DX: vel[0], CFUtil.KEY_DY: vel[1], CFUtil.KEY_DZ: vel[2]}}
