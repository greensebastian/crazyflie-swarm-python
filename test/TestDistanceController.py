import unittest
import copy
import time
import random
import AsyncSwarm
from CFUtil import CFUtil
from Controllers import DistanceController
#from examples.DistanceController import DistanceController


"""Define states for testing; all 6 states for every drone"""
TEST_CASE = {'d1': {CFUtil.KEY_X: 0, CFUtil.KEY_Y: 0, CFUtil.KEY_Z: 1,
                    CFUtil.KEY_DX: 0, CFUtil.KEY_DY: 0, CFUtil.KEY_DZ: 0},
             'd2': {CFUtil.KEY_X: 1, CFUtil.KEY_Y: 0, CFUtil.KEY_Z: 1,
                    CFUtil.KEY_DX: 0, CFUtil.KEY_DY: 0, CFUtil.KEY_DZ: 0},
             'd3': {CFUtil.KEY_X: -1, CFUtil.KEY_Y: 0, CFUtil.KEY_Z: 1,
                    CFUtil.KEY_DX: 0, CFUtil.KEY_DY: 0, CFUtil.KEY_DZ: 0}
             }

REF = (0, 0, 1)
URI = (0, 1)


def generate_drone(name, pos=(0, 0, 1), vel=(0, 0, 0)):
    return {name: {CFUtil.KEY_X: pos[0], CFUtil.KEY_Y: pos[1], CFUtil.KEY_Z: pos[2],
                   CFUtil.KEY_DX: vel[0], CFUtil.KEY_DY: vel[1], CFUtil.KEY_DZ: vel[2]}}


class TestDistanceController(unittest.TestCase):

    def setUp(self):
        self.swarm = AsyncSwarm.AsyncSwarm(URI)
        self.ctr = DistanceController(REF)

    def tearDown(self):
        pass

    def test_single_drone(self):
        state = {}
        name = 'd1'
        state.update(generate_drone(name, pos=(0, 0, 0)))

        vel_ref = self.ctr.compute(state)

        #print('Vel_ref = ')
        #print(vel_ref)

    def test_x(self):
        state = {}
        for i in range(3):
            name = 'd' + str(i)
            state.update(generate_drone(name, pos=(i/2, 0, 1)))

        test = self.ctr.compute(state)

        print(test)

    def test_y(self):
        state = {}
        for i in range(3):
            name = 'd' + str(i)
            state.update(generate_drone(name, pos=(0, i, 1)))

        test = self.ctr.compute(state)
        print(test)

    def test_z(self):
        state = {}
        for i in range(4):
            name = 'd' + str(i)
            state.update(generate_drone(name, pos=(0, 0, i/2)))

        test = self.ctr.compute(state)
        print(test)

    def test_runtime(self):
        state = {}
        for i in range(5):
            name = 'd1' + str(i)
            state.update(generate_drone(name, pos=(random.random(), random.random(), 1 + random.random())))

        t0 = time.time()
        test = self.ctr.compute(state)
        dur = time.time() - t0

        print('Runtime: ' + str(dur*1000) + 'ms.')


if __name__ == '__main__':
    unittest.main()