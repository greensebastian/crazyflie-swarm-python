from threading import Thread
import queue
import time

from Sequences import Sequences


class SwarmThread(Thread):

    def __init__(self, swarm, controller, period_ms=20):
        """
        Calls function on swarm at specified intervals when running.
        :param swarm: AsyncSwarm object to retrieve state from
        :param controller: Controller function to execute, passes swarm state as parameter
        :param period_ms: Period at which to call function, in milliseconds
        """
        Thread.__init__(self)
        self.queue = queue.Queue(maxsize=15)

        self.paused = False

        self.swarm = swarm
        self.controller = controller
        self._period_ms = period_ms
        self._seq = Sequences(period_ms=self._period_ms)

        self.running = True
        self.starttime = None

    def run(self):
        self.starttime = time.time()
        while self.running:
            if not self.paused:
                if not self.queue.empty():
                    msg = None
                    try:
                        msg = self.queue.get_nowait()
                        self._seq.run(swarm=self.swarm, controller=self.controller, sequence=msg['seq'])
                    except queue.Empty:
                        print('Error, get called on empty queue in SwarmThread.')
                else:
                    self.swarm.follow_controller(self.controller)

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
            print('Attempted join on unstarted SwarmThread')

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
