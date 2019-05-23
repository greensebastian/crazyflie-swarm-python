from tkinter import *
import tkinter.ttk as ttk
import random

from cflib.crazyflie import State as CFStates

from CFUtil import CFUtil
from Sequences import Sequences


class GUI:
    COLOR_BG = 'white'
    COLOR_FG = 'black'

    def __init__(self):
        self.root = Tk()
        self.root.title('Crazyflie Swarm Manager 9000')
        self.root.tk_setPalette(background=self.COLOR_BG, foreground=self.COLOR_FG)

        frame_left = Frame(self.root)
        frame_left.pack(side='left')

        self.test_status = CFStates.DISCONNECTED
        button_row = Frame(frame_left)
        btn_test = Button(button_row, text="TEST GUI", command=self.test)
        btn_test.pack(side='left')
        btn_test = Button(button_row, text="Select all", command=self.select_all)
        btn_test.pack(side='left')
        button_row.pack(side='top')

        self.status_container = Frame(frame_left)
        self.status_container.pack(side='left')
        self.status_frames = {}

        uris = CFUtil.URIS_DEFAULT
        for index, uri in enumerate(uris):
            status_frame = CFStatusFrame(self.status_container, uri, index)
            status_frame.pack(fill='x', padx=3, pady=3)
            self.status_frames[uri] = status_frame

        frame_middle = Frame(self.root)
        frame_middle.pack(side='left', fill=BOTH)

        btn = Button(frame_middle, text="STOP", command=self.stop_all, font=(0, 25), background='red', foreground='white', padx=10, pady=10)
        btn.pack(side='top')

        connection_commands = Frame(frame_middle)
        connection_commands.pack(side='top')
        btn = Button(connection_commands, text="Connect", command=self.connect, font=(0, 16))
        btn.pack(side='left')

        btn = Button(connection_commands, text="Disconnect", command=self.disconnect, font=(0, 16))
        btn.pack(side='left')

        flight_commands = Frame(frame_middle)
        flight_commands.pack(side='top')
        btn = Button(flight_commands, text="Take off", command=self.take_off)
        btn.pack(side='left')

        btn = Button(flight_commands, text="Land unsafe", command=self.land_unsafe)
        btn.pack(side='left')

        btn = Button(flight_commands, text="Start sequence", command=self.start_sequence)
        btn.pack(side='left')

        #TODO sequence picker
        self.sequence_picker = Listbox(frame_middle, font=(0, 16), selectmode=BROWSE)
        self.sequence_picker.pack(side='top', fill=BOTH, expand=1)

        self.sequences = Sequences.REAL
        for seq_name in self.sequences:
            self.sequence_picker.insert(END, seq_name)
            self.sequence_picker.insert(END, seq_name)
            self.sequence_picker.insert(END, seq_name)

        frame_right = Frame(self.root)
        frame_right.pack(side='left')

        frame_limits = Frame(frame_right)
        frame_limits.pack(side='top')

        lbl = Label(frame_limits, text='Max')
        lbl.grid(row=1, column=0)
        lbl = Label(frame_limits, text='Min')
        lbl.grid(row=2, column=0)

        self.limits = [[-1.0, 1.0], [-1.0, 1.0], [0.0, 1.5]]
        self.limit_vars = []
        for low, high in self.limits:
            self.limit_vars.append((StringVar(value=str(low)), StringVar(value=str(high))))
        for i, axes in enumerate(('X', 'Y', 'Z')):
            label = Label(frame_limits, text=axes)
            label.grid(row=0, column=i+1)
            limit_high = Entry(frame_limits, textvariable=self.limit_vars[i][1], width=5)
            limit_low = Entry(frame_limits, textvariable=self.limit_vars[i][0], width=5)
            limit_high.grid(row=1, column=i+1)
            limit_low.grid(row=2, column=i+1)

        btn = Button(frame_limits, text="Set", command=self.set_limits)
        btn.grid(row=3, column=0, columnspan=2, sticky=N+W+S+E)
        btn = Button(frame_limits, text="Reset", command=self.reset_limits)
        btn.grid(row=3, column=2, columnspan=2, sticky=N+W+S+E)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def set_limits(self):
        for i, value in enumerate(self.limit_vars):
            low = float(value[0].get())
            if -5 < low < 1:
                self.limits[i][0] = low

            high = float(value[1].get())
            if -1 < high < 5:
                self.limits[i][1] = high

        self.reset_limits()

    def reset_limits(self):
        for i, value in enumerate(self.limit_vars):
            self.limit_vars[i][0].set(str(self.limits[i][0]))
            self.limit_vars[i][1].set(str(self.limits[i][1]))

    def on_close(self):
        self.root.destroy()

    def connect(self):
        #TODO
        pass

    def disconnect(self):
        #TODO
        pass

    def stop_all(self):
        #TODO Send stop commands, disconnect
        pass

    def take_off(self):
        #TODO
        pass

    def land_unsafe(self):
        #TODO
        pass

    def start_sequence(self):
        #TODO
        pass

    def test(self):
        self.test_status = (self.test_status + 1) % CFStates.SETUP_FINISHED
        state_dict = {}
        for uri in self.status_frames:
            state_dict[uri] = {}
            state_dict[uri][CFStatusFrame.KEY_CONNECTION] = self.test_status
            state_dict[uri][CFStatusFrame.KEY_BATTERY] = 0
        self.update_states(state_dict)
        print('Selected: ' + str(self.get_selected()))

    def select_all(self):
        for uri in self.status_frames:
            if not self.status_frames[uri].selected:
                self.status_frames[uri].click_handler()

    def update_states(self, states):
        """
        Update frame to present specified state of drone
        :param states: dict containing uri keyed state information
        """
        for uri in states:
            if uri in self.status_frames:
                self.status_frames[uri].update_state(states[uri])

    def get_selected(self):
        selected_uris = []
        for uri in self.status_frames:
            if self.status_frames[uri].selected:
                selected_uris.append(uri)
        return selected_uris

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

    def __init__(self, parent, uri, index):
        Frame.__init__(self, parent, highlightthickness=5)

        self.uri = uri
        self.index = index
        self.selected = False

        line = Frame(self, height=1, bg="black", bd=2)
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

        bind_tree(widget=self, event="<Button-1>", callback=self.click_handler)

    def click_handler(self, event=None):
        print('Clicked: ' + self.uri)
        self.selected = not self.selected
        if self.selected:
            self.config(highlightbackground="#317ef9")
        else:
            self.config(highlightbackground=GUI.COLOR_BG)

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


def bind_tree(widget, event, callback, add=''):
    """Binds an event to a widget and all its descendants."""
    widget.bind(event, callback, add)
    for child in widget.children.values():
        bind_tree(child, event, callback)


if __name__ == "__main__":
    gui = GUI()
