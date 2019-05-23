import unittest
import time

from PyUtil import Periodic


class MyTestCase(unittest.TestCase):

    def test_second_cycles(self):
        start = time.time()
        for cycle in Periodic(duration=5, period=1):
            cur_time = time.time() - start
            print('Cycle ' + str(cycle) + ' starting after ' + str(cur_time) + ' seconds.')

    def test_half_second_cycles(self):
        start = time.time()
        for cycle in Periodic(duration=5, period=0.5):
            cur_time = time.time() - start

    def test_100Hz_cycles(self):
        start = time.time()
        for cycle in Periodic(duration=5, period=0.01):
            cur_time = time.time() - start
            print('Cycle ' + str(cycle) + ' starting after ' + str(cur_time) + ' seconds.')

    def test_sleep_in_cycle(self):
        start = time.time()
        for cycle in Periodic(duration=5, period=1):
            cur_time = time.time() - start
            print('Cycle ' + str(cycle) + ' starting after ' + str(cur_time) + ' seconds.')
            time.sleep(0.7)

    def test_cycle_delayed_by_sleep(self):
        start = time.time()
        for cycle in Periodic(duration=5, period=0.5):
            cur_time = time.time() - start
            print('Cycle ' + str(cycle) + ' starting after ' + str(cur_time) + ' seconds.')
            if cycle % 2:
                time.sleep(0.7)


if __name__ == '__main__':
    unittest.main()
