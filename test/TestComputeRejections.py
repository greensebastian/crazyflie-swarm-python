from unittest import TestCase
import numpy as np
from CFUtil import CFUtil
import PyUtil


class TestComputeRejections(TestCase):
    def test_compute_cross(self):
        ref = np.array([0, 0, 1])
        state = {}

        name1 = 'd1'
        state.update(CFUtil.generate_drone(name1, pos=(2, 0.1, 1)))

        name2 = 'd2'
        state.update(CFUtil.generate_drone(name2, pos=(1, 0, 1)))

        state = CFUtil.state_dict_to_numpy_matrix(state)

        # "Shadowing" protection
        angle, rej_1, rej_2 = PyUtil.compute_rejections(state[name1][0:3] - ref, state[name2][0:3] - ref)

        print('Angle: ' + str(angle))
        print('Rejection 1: ' + str(rej_1))
        print('Rejection 2: ' + str(rej_2))
