import sys
import time
import numpy as np
import math


def printf(formatting, *args):
    sys.stdout.write(formatting % args)


class Periodic(object):

    def __init__(self, duration, period):
        """
        Iterable object for easier periodic time management
        :param duration: Total duration of run in seconds
        :param period: Cycle period in seconds
        """
        self.duration = duration
        self.period = period
        self.starttime = time.time()

    def __iter__(self):
        self._cycle = 0
        return self

    def __next__(self):
        """
        Sleeps until next action is due
        :return: current cycle count
        """
        run_time = time.time() - self.starttime
        if run_time + self.period > self.duration:
            raise StopIteration
        else:
            sleep_time = self.period * self._cycle - run_time
            self._cycle = self._cycle + 1
            if sleep_time > 0:
                time.sleep(sleep_time)
            return int(self._cycle)


def compute_rejections(A, B):
    angle = 0
    rej_A = np.array([0, 0, 0])
    rej_B = np.array([0, 0, 0])
    if not np.array_equal(A, B):
        dAB = np.dot(A, B)
        dBB = np.dot(B, B)

        len_A = np.linalg.norm(A)
        len_B = np.linalg.norm(B)

        rej_A = A - dAB / dBB * B
        rej_A = rej_A / np.linalg.norm(rej_A)
        rej_B = -1 * rej_A

        angle = max(0.01, math.acos(dAB / (len_A * len_B)))

    return angle, rej_A, rej_B
