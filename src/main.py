import cflib.crtp
import logging
from AsyncSwarm import AsyncSwarm
from LogManager import LogManager
from Controllers import FlockingController
from Controllers import DistanceController
from ControllerThread import ControllerThread
from CFUtil import CFUtil
from PyUtil import Periodic
from Sequences import Sequences

if __name__ == '__main__':
    # Set logging level to DEBUG
    logging.basicConfig(level=logging.ERROR)
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    # Log manager initialization
    log = LogManager()

    # Initialize swarm
    active_indices = (0, 2, 3, 4)
    swarm = AsyncSwarm(uri_indices=active_indices, log=log)
    swarm.start()

    # Start controller and controller thread

    for cycle in Periodic(duration=1, period=0.1):
        pass

    period_ms = 50
    period_s = period_ms/1000

    controller = FlockingController(ref=(0, 0, 1))
    #controller = DistanceController(ref=(0, 0, 1), period_ms=period_ms)
    controller_thread = ControllerThread(swarm=swarm, controller_func=controller.compute, period_ms=period_ms)
    controller_thread.start()

    # Add relevant log calls
    log.add_caller(name='state', call=swarm.get_state, period_ms=10)
    log.add_caller(name='control', call=controller.get_u, period_ms=10)
    log.add_caller(name='ref', call=controller.get_ref, period_ms=10)

    # param_log = log.add_caller(name='params', call=None, period_ms=None, start=False)
    # param_log.push_data()

    seq = Sequences(period_ms=period_ms)
    # seq.run(swarm=swarm, controller=controller, sequence=seq.TAKE_OFF_CONTROLLER_SEQ)
    seq.run(swarm=swarm, controller=controller, sequence=seq.TAKE_OFF_STANDARD)
    seq.run(swarm=swarm, controller=controller, sequence=seq.MERGE_1_3_C)
    seq.run(swarm=swarm, controller=controller, sequence=seq.LAND_UNSAFE)

    swarm.stop()
    controller_thread.stop()
    log.stop()
    log.write_mat()
