from tkinter import *
import tkinter.ttk as ttk
import random

from cflib.crazyflie import State as CFStates

from CFUtil import CFUtil


class GUI:

    def __init__(self):
        self.root = Tk()
        frame = Frame(self.root)
        frame.pack()

        self.test_status = CFStates.DISCONNECTED
        button_row = Frame(frame)
        btn_test = Button(button_row, text="TEST GUI", command=self.test)
        btn_test.pack(side='left')
        button_row.pack(side='top')

        self.status_container = Frame(frame)
        self.status_container.pack(side='left')
        self.status_frames = {}

        uris = CFUtil.URIS_DEFAULT
        for index, uri in enumerate(uris):
            status_frame = CFStatusFrame(self.status_container, uri)
            status_frame.pack(fill='x', padx=2)
            self.status_frames[uri] = status_frame

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        self.root.destroy()

    def connect_all(self):
        pass

    def test(self):
        self.test_status = (self.test_status + 1) % CFStates.SETUP_FINISHED
        state_dict = {}
        for uri in self.status_frames:
            state_dict[uri] = {}
            state_dict[uri][CFStatusFrame.KEY_CONNECTION] = self.test_status
            state_dict[uri][CFStatusFrame.KEY_BATTERY] = 0
        self.update_states(state_dict)

    def update_states(self, states):
        """
        Update frame to present specified state of drone
        :param state: dict containing uri keyed state information
        """
        for uri in states:
            if uri in self.status_frames:
                self.status_frames[uri].update_state(states[uri])


    # def scan(self):
    #     self.controller.scan()
    #     if self.controller.is_available():
    #         self.btn_connect.config(state=NORMAL)
    #     else:
    #         self.btn_connect.config(state=DISABLED)
    #
    # def connect(self):
    #     if self.controller.is_available():
    #         self.controller.connect()


class CFStatusFrame(Frame):
    KEY_CONNECTION = 0
    KEY_BATTERY = 1

    def __init__(self, parent, uri):
        Frame.__init__(self, parent)

        line = Frame(self, height=1, bg="black")
        line.pack(fill='x')

        frame_top = Frame(self)
        frame_top.pack(fill='x')

        self.label = Label(frame_top, text=('Drone ' + uri[-1:]), anchor="w")
        self.label.pack(side="left")

        self.status = Label(frame_top, anchor='e')
        self.status.pack(side="right")
        self.update_connection_status(CFStates.DISCONNECTED)

        self.address = Label(self, text=uri, anchor="w")
        self.address.pack(fill='x')

        self.battery_var = DoubleVar()
        self.battery_var.set(0)
        self.battery_bar = ttk.Progressbar(self, orient=HORIZONTAL, length=200, mode="determinate", variable=self.battery_var)
        self.battery_bar.pack(side="left", fill='x')

    def update_connection_status(self, status):
        if status is CFStates.DISCONNECTED:
            self.status.config(text='Disconnected', bg='red')
        elif status is CFStates.INITIALIZED:
            self.status.config(text='Connecting...', bg='yellow')
        elif status is CFStates.CONNECTED or status is CFStates.SETUP_FINISHED:
            self.status.config(text='Connected', bg='green')

    def update_state(self, state):
        """
        Update frame to present specified state of drone
        :param state: dict containing uri keyed state information
        """
        if self.KEY_CONNECTION in state:
            self.update_connection_status(state[self.KEY_CONNECTION])
        if self.KEY_BATTERY in state:
            self.battery_var.set(random.randint(0, 100))

if __name__ == "__main__":
    gui = GUI()
