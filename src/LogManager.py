import time
import threading
from functools import partial
import scipy.io
import numpy as np


class LogManager:

    def __init__(self):
        """
        Manages multiple logging threads and creates .mat files for Matlab imports
        """
        self.callers = {}

    def add_caller(self, name, call, period_ms, start=True):
        """
        Add function to call at regular interval
        :param name: Unique reference for file creation
        :param call: Function to retrieve log data from, should return dict{obj_key: dict{param1: value, param2_ value}}
        :param period_ms: Call period
        :param start: Start log or not
        :return: Created Log object
        """
        log = Log(name, call, period_ms, start)
        self.callers[name] = log
        return log

    def stop(self):
        for caller in self.callers:
            self.callers[caller].stop()

    def write_mat(self):
        """
        Write all logged data to .mat file in ./output folder using predefined names. Appends date and time.
        :return:
        """
        call_time = time.localtime()
        time_string = time.strftime("%Y-%m-%d_T%H%M%S")
        data = {}
        for caller in self.callers:
            data.update(self.callers[caller].get_data())

        filename = 'log_' + time_string
        scipy.io.savemat('output/' + filename, mdict=data)


class Log:

    def __init__(self, name, call, period_ms, start):
        """
        Create and start periodic log gathering. Function will be used as retrieval point.
        :param name: Log name
        :param call: Function to be used for data collection. Should return dict containing dict/list
        :param period_ms:
        :param start:
        """
        self.name = name
        self.starttime = time.time()
        self.period_ms = period_ms
        self.data = []
        self.timestamps = []
        self.thread = threading.Thread(name=name, target=partial(self.run, call))

        if call is not None:
            self.running = start
            if start:
                self.thread.start()
        else:
            self.running = False

    def run(self, call):
        while self.running and self.period_ms is not 0:
            self.data.append(call())
            current_time = time.time()
            d_time = (current_time - self.starttime)
            self.timestamps.append(d_time)
            sleeptime = (self.period_ms - ((d_time*1000.0) % self.period_ms))/1000.0
            time.sleep(sleeptime)

    def stop(self):
        self.running = False
        try:
            self.thread.join()
        except RuntimeError as e:
            print('Attempted join on unstarted Log')

    def push_data(self, data):
        self.data.append(data)
        self.timestamps.append(time.time() - self.starttime)

    def get_data(self):
        """
        Retrieve all collected data
        :return: dict containing timestamps[], starttime[] and numpy matrices for each object logged.
        numpy matrices are of size A-B where A is the number of parameters and B is the number of data points.
        """
        # TODO keep individual variable names
        data = {'timestamps' + '_' + self.name: self.timestamps, 'starttime' + '_' + self.name: self.starttime}

        n_points = len(self.data)
        n_objects = len(self.data[1].items())
        testing = next(iter(self.data[1].items()))
        n_params = len(testing[1])

        arrays = {}
        for obj, params in self.data[0].items():
            obj = self.generate_name(obj)
            arrays[obj] = np.zeros((n_params, n_points))
        for index, point in enumerate(self.data):
            for obj, params in point.items():
                obj = self.generate_name(obj)
                if type(params) is dict:
                    arrays[obj][:, index] = list(params.values())
                else:
                    arrays[obj][:, index] = list(params)
        data.update(arrays)

        return data

    def generate_name(self, key):
        if 'radio' in key:
            key = 'd' + key[-2:]

        return key + '_' + self.name
