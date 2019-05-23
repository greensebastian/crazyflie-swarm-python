import unittest
import random
import time
from Controllers import FlockingController
from AsyncSwarm import AsyncSwarm
from CFUtil import CFUtil
import numpy as np


def generate_drone(name, pos=(0, 0, 1), vel=(0, 0, 0)):
    return {name: {CFUtil.KEY_X: pos[0], CFUtil.KEY_Y: pos[1], CFUtil.KEY_Z: pos[2],
                   CFUtil.KEY_DX: vel[0], CFUtil.KEY_DY: vel[1], CFUtil.KEY_DZ: vel[2]}}


class TestFlockingController(unittest.TestCase):
    def setUp(self):
        self.swarm = AsyncSwarm((0, 1, 2, 3, 4))
        self.ctr = FlockingController((0, 0, 1))

    def tearDown(self):
        pass

    def test_single_drone(self):
        state = {}
        name = 'd1'
        #state.update(generate_drone(name, pos=(-1.1175, 0.1494, 0.2618)))
        state.update(generate_drone(name, pos=(1, 0, 1)))
        test = self.ctr.compute(state)
        print(test)

    def test_z_line(self):
        state = {}
        for i in range(5):
            name = 'd' + str(i)
            state.update(generate_drone(name, pos=(0, 0, i/2)))
        test = self.ctr.compute(state)
        print(test)

    def test_x_line(self):
        state = {}
        for i in range(5):
            name = 'd' + str(i)
            state.update(generate_drone(name, pos=((i-2)/2, -0.5, 1)))
        test = self.ctr.compute(state)

    def test_runtime(self):
        state = {}
        for i in range(100):
            name = 'd' + str(i)
            state.update(generate_drone(name, pos=(random.random(), random.random(), 1 + random.random())))

        t0 = time.time()
        test = self.ctr.compute(state)
        t1 = time.time()
        print('Runtime: ' + str((t1-t0)*1000) + ' ms.')

    def test_relative_velocity(self):
        state = {}
        state.update(generate_drone('d1', pos=(0, -1, 1)))
        state.update(generate_drone('d2', pos=(0, -1.5, 1), vel=(0, 0.5, 0)))
        state.update(generate_drone('d3', pos=(0, 0, 1)))
        test = self.ctr.compute(state)
        print(test)

    def test_ignore_list(self):
        uris = self.swarm.get_uris()
        uri = uris[0]
        self.ctr.add_ignore(uri)
        self.assertTrue(uri in self.ctr._ignore_list)

    def test_land_generator(self):
        state = {}
        state.update(generate_drone(CFUtil.URI1, pos=(0, -1, 1)))
        state.update(generate_drone(CFUtil.URI2, pos=(0, -1.5, 1), vel=(0, 0.5, 0)))
        state.update(generate_drone(CFUtil.URI3, pos=(0, 0, 1)))
        test = CFUtil.get_land_dict(state=state)
        print(test)


if __name__ == '__main__':
    unittest.main()
