from CFUtil import CFUtil
from PyUtil import Periodic
import numpy as np
import math


class Sequences:
    TAKE_OFF_FOLLOW_CONTROLLER = 0
    TAKE_OFF_HOVER = 1
    TAKE_OFF_CONTROLLER_SEQ = 2
    TAKE_OFF_MERGE = 3
    SINGLE_TAKE_OFF_STEPS = 4
    Y_STEP = 5
    TEST_IGNORE = 6
    TEST_IGNORE_2 = 7
    ROBOT_LAB_1 = 8
    ROBOT_LAB_2 = 9

    """REPORT SEQUENCES"""
    TAKE_OFF_STANDARD = -2
    LAND_UNSAFE = -1

    HOVER = 101         # 1, 3, 5 drones

    STEP_Z_POS = 102    # 1, 3 drones
    STEP_Z_NEG = 103    # 1, 3 drones
    STEP_Y = 104        # 1, 3 drones

    RAMP_Z_POS = 105    # 1, 3 drones
    RAMP_Z_NEG = 106    # 1, 3 drones
    RAMP_Y = 107        # 1, 3 drones

    MERGE_1_1_C = 108   # 2 drones
    MERGE_1_1_1 = 109   # 2 drones
    MERGE_1_3_C = 110   # 4 drones
    MERGE_1_3_3 = 111   # 4 drones
    MERGE_1_3_1 = 112   # 4 drones

    LEAVE_HOVER = 113   # 4 drones
    LEAVE_RAMP = 114    # 4 drones

    REAL = {
        'Take off': TAKE_OFF_STANDARD,
        'Land unsafe': LAND_UNSAFE,
        'Hover': HOVER,
        'Merge 1 to 3': MERGE_1_3_C,
        'Z step': STEP_Z_POS
    }

    # Collapse?
    # Scatter?

    def __init__(self, period_ms=20):
        """
        Initialize sequencer, standard period is 20ms
        :param period_ms:
        """
        # Sanity check, make sure no colliding constants
        self.get_statics()

        self.period_s = period_ms/1000

    @staticmethod
    def get_statics():
        statics = [getattr(Sequences, attr) for attr in dir(Sequences) if not attr.startswith("__")]
        seen = []
        collisions = []
        for attr in statics:
            if attr in seen:
                collisions.append(attr)
                print('!!!COLLIDING SEQUENCE IDS: ' + attr + '!!!')
            else:
                seen.append(attr)
        return seen, collisions

    def run(self, swarm, controller, sequence, log=None):
        """
        Run sequence with id
        :param swarm: AsyncSwarm object containing swarm attributes
        :param controller: Swarm controller to follow/update
        :param sequence: ID of sequence to follow, keys available in Sequences class
        :param log: LogManager to add custom logs to
        :return:
        """

        if sequence == Sequences.TAKE_OFF_FOLLOW_CONTROLLER:
            # Lift off
            swarm.parallel(func=CFUtil.take_off)
            controller.reset()

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0, 0.5))
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

            # Stop all motors ("crash" from previous setpoint)
            swarm.parallel(CFUtil.send_stop_signal)

        elif sequence == Sequences.TAKE_OFF_HOVER:
            # Lift off
            swarm.parallel(func=CFUtil.take_off)
            controller.reset()

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

            state = swarm.get_state()
            swarm.parallel(CFUtil.land, args_dict=CFUtil.get_land_dict(state=state))

        elif sequence == Sequences.TAKE_OFF_CONTROLLER_SEQ:
            # Lift off
            swarm.parallel(func=CFUtil.take_off)
            controller.reset()

            controller.set_ref(new_ref=(0, 0, 1.2))
            for cycle in Periodic(duration=4, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, -0.5, 0.8))
            for cycle in Periodic(duration=2, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0.5, 0, 1.5))
            for cycle in Periodic(duration=2, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0, 1.2))
            for cycle in Periodic(duration=2, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, -0.5, 0.8))
            for cycle in Periodic(duration=2, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0.5, 0, 1.5))
            for cycle in Periodic(duration=2, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=2, period=self.period_s):
                swarm.follow_controller(controller)

            # Prepare for landing
            controller.set_ref(new_ref=(0, 0, 0.5))
            for cycle in Periodic(duration=4, period=self.period_s):
                swarm.follow_controller(controller)

            state = swarm.get_state()
            swarm.parallel(CFUtil.land, args_dict=CFUtil.get_land_dict(state=state))

        elif sequence == Sequences.TAKE_OFF_MERGE:
            # Lift off
            swarm.parallel(func=CFUtil.take_off)
            controller.reset()

            positions = CFUtil.POS_HOVER

            # Get uri of first 2 drones in swarm
            state = swarm.get_state()
            drone_list = list(state.items())
            uri1 = drone_list[0][0]
            uri2 = drone_list[1][0]

            # Move setpoints to right side to avoid collision
            if state[uri1][CFUtil.KEY_Y] > state[uri2][CFUtil.KEY_Y]:
                positions[uri1] = [(0, 1, 1, 0)]
                positions[uri2] = [(0, -1, 1, 0)]
            else:
                positions[uri1] = [(0, -1, 1, 0)]
                positions[uri2] = [(0, 1, 1, 0)]

            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.parallel(CFUtil.set_abs_pos, args_dict=positions)

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0, 0.1))
            for cycle in Periodic(duration=3, period=self.period_s):
                swarm.follow_controller(controller)

            # Stop all motors ("crash" from previous setpoint)
            swarm.parallel(CFUtil.send_stop_signal)

        elif sequence == Sequences.SINGLE_TAKE_OFF_STEPS:
            swarm.parallel(func=CFUtil.take_off)
            controller.reset()

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(1, 0, 1))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 1, 1))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0, 1.5))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0, 0.1))
            for cycle in Periodic(duration=3, period=self.period_s):
                swarm.follow_controller(controller)

        elif sequence == Sequences.Y_STEP:
            # Lift off
            swarm.parallel(func=CFUtil.take_off)
            controller.reset()

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=4, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0.5, 1))
            for cycle in Periodic(duration=4, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=4, period=self.period_s):
                swarm.follow_controller(controller)

            controller.set_ref(new_ref=(0, 0, 0.5))
            for cycle in Periodic(duration=3, period=self.period_s):
                swarm.follow_controller(controller)

            # Stop all motors ("crash" from previous setpoint)
            swarm.parallel(CFUtil.send_stop_signal)

        elif sequence == Sequences.TEST_IGNORE:

            start_1 = (0, 0, 1)
            start_2 = (0.2, 0, 1)
            end_2 = (-0.5, 0, 1)
            merge_pos = (0, 0, 1)

            uri1 = swarm.get_uris()[0]
            scf1 = swarm.get_cfs()[uri1]
            ignore_list = [uri1]
            controller.add_ignore(ignore_list)

            controller.set_ref(start_2)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=start_1)

            # controller.set_ref(end_2)
            # for cycle in Periodic(duration=5, period=self.period_s):
            #     swarm.follow_controller(controller)
            #     CFUtil.set_abs_pos(scf=scf1, pos=start_1)

            controller.remove_ignore(ignore_list)

            # controller.set_ref(merge_pos)
            # for cycle in Periodic(duration=10, period=self.period_s):
                # swarm.follow_controller(controller)


            # hover_pos = (0, 0, 1)
            #
            # swarm_start = (0, -1, 1)
            # swarm_end = (0, 1, 1)
            #
            # # Lift off
            # swarm.parallel(func=CFUtil.take_off)
            # controller.reset()
            #
            # uri1 = swarm.get_uris()[0]
            # scf1 = swarm.get_cfs()[uri1]
            # ignore_list = [uri1]
            #
            # controller.set_ref(new_ref=(0, 0, 1))
            # for cycle in Periodic(duration=5, period=self.period_s):
            #     swarm.follow_controller(controller)
            #
            # controller.add_ignore(ignore_list)
            #
            # controller.set_ref(new_ref=swarm_start)
            #
            # for cycle in Periodic(duration=3, period=self.period_s):
            #     swarm.follow_controller(controller)
            #     CFUtil.set_abs_pos(scf=scf1, pos=hover_pos)
            #
            # dur = 3
            # for cycle in Periodic(duration=dur, period=self.period_s):
            #     t = cycle * self.period_s
            #     p0 = np.array(swarm_start)
            #     p1 = np.array(swarm_end)
            #     pos = np.add(p0, np.subtract(p1, p0) * t / dur)
            #     controller.set_ref(new_ref=list(pos))
            #     swarm.follow_controller(controller)
            #     CFUtil.set_abs_pos(scf=scf1, pos=hover_pos)
            #
            # for cycle in Periodic(duration=3, period=self.period_s):
            #     swarm.follow_controller(controller)
            #     CFUtil.set_abs_pos(scf=scf1, pos=hover_pos)
            #
            # controller.remove_ignore(ignore_list)
            #
            # controller.set_ref(new_ref=(0, 0, 0.5))
            # for cycle in Periodic(duration=5, period=self.period_s):
            #     swarm.follow_controller(controller)
            #
            # state = swarm.get_state()
            # swarm.parallel(CFUtil.land, args_dict=CFUtil.get_land_dict(state=state))

        elif sequence == Sequences.TEST_IGNORE_2:
            hover_pos = (0, 0, 1)

            drone_start = (0, -1, 1)
            drone_end = (0, 1, 1)

            # Lift off
            # swarm.parallel(func=CFUtil.take_off)
            controller.reset()

            uri1 = swarm.get_uris()[0]
            scf1 = swarm.get_cfs()[uri1]
            ignore_list = [uri1]

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

            controller.add_ignore(ignore_list)

            controller.set_ref(new_ref=hover_pos)

            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=drone_start)

            dur = 3
            for cycle in Periodic(duration=dur, period=self.period_s):
                t = cycle*self.period_s
                p0 = np.array(drone_start)
                p1 = np.array(drone_end)
                pos = np.add(drone_start, np.subtract(drone_end, drone_start)*t/dur)
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=tuple(pos))

            for cycle in Periodic(duration=3, period=self.period_s):
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=drone_end)

            controller.remove_ignore(ignore_list)

            controller.set_ref(new_ref=(0, 0, 0.5))
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

            # state = swarm.get_state()
            # swarm.parallel(CFUtil.land, args_dict=CFUtil.get_land_dict(state=state))

        # Useful standards here
        # Take off and land
        # More space to read

        elif sequence == Sequences.TAKE_OFF_STANDARD:
            # Lift off
            swarm.parallel(func=CFUtil.take_off)
            controller.reset()
            controller.set_ref(new_ref=(0, 0, 1))

        elif sequence == Sequences.LAND_UNSAFE:
            # Descend and turn off
            state = swarm.get_state()
            swarm.parallel(CFUtil.land, args_dict=CFUtil.get_land_dict(state=state))

        # ALL CASES MENTIONED IN REPORT START HERE
        # Naming should be consistent with report

        elif sequence == Sequences.ROBOT_LAB_1:
            #for cycle in Periodic(duration=5, period=self.period_s):
            #    swarm.parallel(CFUtil.set_abs_pos, args_dict=CFUtil.POS_HOVER)

            z_pos = 1.3

            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller=controller)

            controller.set_ref(new_ref=(-0.7, -0.7, z_pos))
            for cycle in Periodic(duration=3, period=self.period_s):
                swarm.follow_controller(controller=controller)

            controller.set_ref(new_ref=(0.7, -0.7, z_pos))
            for cycle in Periodic(duration=3, period=self.period_s):
                swarm.follow_controller(controller=controller)

            controller.set_ref(new_ref=(0.7, 0.7, z_pos))
            for cycle in Periodic(duration=3, period=self.period_s):
                swarm.follow_controller(controller=controller)

            controller.set_ref(new_ref=(-0.7, 0.7, z_pos))
            for cycle in Periodic(duration=3, period=self.period_s):
                swarm.follow_controller(controller=controller)

            controller.set_ref(new_ref=(0, 0, 1))
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller=controller)

        elif sequence == Sequences.ROBOT_LAB_2:
            #for cycle in Periodic(duration=5, period=self.period_s):
            #    swarm.parallel(CFUtil.set_abs_pos, args_dict=CFUtil.POS_HOVER)
            z_pos_0 = 1.3
            dur = 6
            scale_x = 0.7
            scale_y = 1.2
            scale_z = 0.3

            controller.set_ref(new_ref=(0, 0, z_pos_0))
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller=controller)

            for cycle in Periodic(duration=dur, period=self.period_s):
                angle = cycle*self.period_s/dur * 2*math.pi
                x_pos = math.cos(angle)*scale_x
                y_pos = math.sin(angle)*scale_y
                z_pos = z_pos_0 + math.sin(2*angle)*scale_z
                controller.set_ref(new_ref=(x_pos, y_pos, z_pos))
                swarm.follow_controller(controller=controller)

            controller.set_ref(new_ref=(0, 0, z_pos_0))
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller=controller)

        elif sequence == Sequences.HOVER:
            #for cycle in Periodic(duration=5, period=self.period_s):
            #    swarm.parallel(CFUtil.set_abs_pos, args_dict=CFUtil.POS_HOVER)
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller=controller)

        elif sequence == Sequences.STEP_Z_POS:
            controller.set_ref((0, 0, 0.5))
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller=controller)
            controller.set_ref((0, 0, 1.5))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller=controller)

        elif sequence == Sequences.STEP_Z_NEG:
            controller.set_ref((0, 0, 1.5))
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller=controller)
            controller.set_ref((0, 0, 0.5))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller=controller)

        elif sequence == Sequences.STEP_Y:
            controller.set_ref((0, 0, 1))
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller=controller)
            controller.set_ref((0, 1, 1))
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller=controller)

        elif sequence == Sequences.RAMP_Z_POS:
            start = (0, 0, 0.5)
            end = (0, 0, 1.5)

            controller.set_ref(new_ref=start)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

            dur = 2
            for cycle in Periodic(duration=dur, period=self.period_s):
                t = cycle*self.period_s
                pos = np.add(start, np.subtract(end, start)*t/dur)
                controller.set_ref(pos)
                swarm.follow_controller(controller)

            controller.set_ref(end)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

        elif sequence == Sequences.RAMP_Z_NEG:
            start = (0, 0, 1.5)
            end = (0, 0, 0.5)

            controller.set_ref(new_ref=start)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

            dur = 2
            for cycle in Periodic(duration=dur, period=self.period_s):
                t = cycle*self.period_s
                pos = np.add(start, np.subtract(end, start)*t/dur)
                controller.set_ref(pos)
                swarm.follow_controller(controller)

            controller.set_ref(end)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

        elif sequence == Sequences.RAMP_Y:
            start = (0, 0, 1)
            end = (0, 1, 1)

            controller.set_ref(new_ref=start)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

            dur = 2
            for cycle in Periodic(duration=dur, period=self.period_s):
                t = cycle*self.period_s
                pos = np.add(start, np.subtract(end, start)*t/dur)
                controller.set_ref(pos)
                swarm.follow_controller(controller)

            controller.set_ref(end)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

        elif sequence == Sequences.MERGE_1_1_C:
            start_1 = (0, -1, 1)
            start_2 = (0, 1, 1)
            merge_pos = (0, 0, 1)

            uri1 = swarm.get_uris()[0]
            scf1 = swarm.get_cfs()[uri1]
            ignore_list = [uri1]
            controller.add_ignore(ignore_list)

            controller.set_ref(start_2)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=start_1)

            controller.remove_ignore(ignore_list)

            controller.set_ref(merge_pos)
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

        elif sequence == Sequences.MERGE_1_1_1:
            start_1 = (0, 0, 1)
            start_2 = (0, 1, 1)
            merge_pos = (0, 0, 1)

            uri1 = swarm.get_uris()[0]
            scf1 = swarm.get_cfs()[uri1]
            ignore_list = [uri1]
            controller.add_ignore(ignore_list)

            controller.set_ref(start_2)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=start_1)

            controller.remove_ignore(ignore_list)

            controller.set_ref(merge_pos)
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

        elif sequence == Sequences.MERGE_1_3_C:
            start_1 = (0, -1, 1.3)
            start_2 = (0, 1, 1.3)
            merge_pos = (0, 0, 1.3)

            uri1 = swarm.get_uris()[0]
            scf1 = swarm.get_cfs()[uri1]
            ignore_list = [uri1]
            controller.add_ignore(ignore_list)

            controller.set_ref(start_2)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=start_1)

            controller.remove_ignore(ignore_list)

            controller.set_ref(merge_pos)
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

        elif sequence == Sequences.MERGE_1_3_3:
            start_1 = (0, -1, 1)
            start_2 = (0, 0, 1)
            merge_pos = (0, 0, 1)

            uri1 = swarm.get_uris()[0]
            scf1 = swarm.get_cfs()[uri1]
            ignore_list = [uri1]
            controller.add_ignore(ignore_list)

            controller.set_ref(start_2)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=start_1)

            controller.remove_ignore(ignore_list)

            controller.set_ref(merge_pos)
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

        elif sequence == Sequences.MERGE_1_3_1:
            start_1 = (0, 0, 1)
            start_2 = (0, 1, 1)
            merge_pos = (0, 0, 1)

            uri1 = swarm.get_uris()[0]
            scf1 = swarm.get_cfs()[uri1]
            ignore_list = [uri1]
            controller.add_ignore(ignore_list)

            controller.set_ref(start_2)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=start_1)

            controller.remove_ignore(ignore_list)

            controller.set_ref(merge_pos)
            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)

        elif sequence == Sequences.LEAVE_HOVER:
            hover_pos = (-0.5, 0, 1)
            branch_pos = (1, 0, 1)

            uri1 = swarm.get_uris()[0]
            scf1 = swarm.get_cfs()[uri1]
            ignore_list = [uri1]

            controller.set_ref(new_ref=hover_pos)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

            controller.add_ignore(ignore_list)

            for cycle in Periodic(duration=10, period=self.period_s):
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=branch_pos)

            controller.remove_ignore(ignore_list)

        elif sequence == Sequences.LEAVE_RAMP:
            start = (0, -1, 1)
            end = (0, 1, 1)
            branch_pos = (1, 0, 1)

            uri1 = swarm.get_uris()[0]
            scf1 = swarm.get_cfs()[uri1]
            ignore_list = [uri1]

            controller.set_ref(new_ref=start)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)

            dur = 2
            for cycle in Periodic(duration=dur/2, period=self.period_s):
                t = cycle * self.period_s
                pos = np.add(start, np.subtract(end, start) * t / dur)
                controller.set_ref(pos)
                swarm.follow_controller(controller)

            controller.add_ignore(ignore_list)

            for cycle in Periodic(duration=dur/2, period=self.period_s):
                t = cycle * self.period_s
                pos = np.add(start, np.subtract(end, start) * (dur/2 + t) / dur)
                controller.set_ref(pos)
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=branch_pos)

            controller.set_ref(end)
            for cycle in Periodic(duration=5, period=self.period_s):
                swarm.follow_controller(controller)
                CFUtil.set_abs_pos(scf=scf1, pos=branch_pos)

            controller.remove_ignore(ignore_list)



