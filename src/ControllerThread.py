from threading import Thread
import time


class ControllerThread(Thread):

    def __init__(self, swarm, controller_func=None, period_ms=20):
        """
        Calls function on swarm at specified intervals when running.
        :param swarm: AsyncSwarm object to retrieve state from
        :param controller_func: Controller function to execute, passes swarm state as parameter
        :param period_ms: Period at which to call function, in milliseconds
        """
        Thread.__init__(self)
        self._swarm = swarm
        self._controller_func = controller_func
        self._period_ms = period_ms
        self.running = True
        self.starttime = None

    def run(self):
        self.starttime = time.time()
        while self.running and self._controller_func is not None:
            state = self._swarm.get_state()
            self._controller_func(state)

            # Sleep until next call interval happens
            current_time = time.time()
            d_time = (current_time - self.starttime)
            sleeptime = (self._period_ms - ((d_time * 1000.0) % self._period_ms)) / 1000.0
            time.sleep(sleeptime)

    def stop(self):
        self.running = False
        try:
            self.join()
        except RuntimeError as e:
            print('Attempted join on unstarted ControllerThread')
