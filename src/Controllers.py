"""
Library of available swarm controllers

Each controller is defined by single function to be passed to the controller thread
that takes the state and returns a velocity setpoint as result.

ExampleController:

    def __init__(self):
        self.ref = [0 0 0]

    def compute(self, state):
        output = {}
        for uri in state:
            x_error = self.ref[0] - state[uri][0]
            y_error = self.ref[1] - state[uri][1]
            z_error = self.ref[2] - state[uri][2]
            output[uri] = (x_error, y_error, z_error)

        return output

"""
import numpy as np
from copy import deepcopy as copy
import math
from Formation import Formation

from CFUtil import CFUtil
import PyUtil


class FlockingController:
    # TODO Make this whole thing thread safe, multiple holes in implementation

    def __init__(self, ref=(0, 0, 1), k=1, weight=(1, 0, 0.1, 0.05)):
        """
        Weighed swarm controller balancing relative positions and velocities of drones
        :param ref: List of swarm center reference point (x, y, z)
        :param k: Overall controller gain
        :param weight: List of weighted gains. (pos_ref, vel_ref, pos_rel, vel_rel)
        """
        #weight = weight/np.linalg.norm(weight)
        self.r_ref = k*weight[0]
        self.rdot_ref = k*weight[1]
        self.r_rel = k*weight[2]
        self.rdot_rel = k*weight[3]

        self.angle_cap = 15 * math.pi / 180
        self.angle_k = 0.2
        self.angle_k = 0  # Nullifies rejection calculations

        self.distance_offset = 0
        self.distance_minimum = 0.01

        self.ref = np.array(ref)
        self.output = {}

        self._ignore_list = []

    def compute(self, state):
        """
        Compute control signal based on supplied swarm state. Stores output in self.output
        :param state: dict{URI: dict{kalman.stateX: x, ..., kalman.statePZ: vz}}
        :return: Control signal, dict{URI: np.array[u_vx, u_vy, u_vz]}
        """

        uris = list(state.keys())
        # Convert individual state information from dict to numpy vector
        state = CFUtil.state_dict_to_numpy_matrix(state)
        count = len(uris)

        #state[CFUtil.URI1][1] = state[CFUtil.URI1][1] - 0.3

        # Set initial outputs to 0
        output = {}
        for uri in uris:
            output[uri] = np.zeros(3)

        # Loop all active drones
        for i in range(count):
            uri = uris[i]
            error_ref = self.ref[0:3] - state[uri][0:3]
            output[uri] = output[uri] + error_ref*self.r_ref

            # Loop unseen drones for relative avoidance
            for j in range(i+1, count):

                uri2 = uris[j]
                _sum = np.zeros(3)

                error_rel = state[uri][:] - state[uri2][:]
                error_position = error_rel[0:3]
                error_velocity = -error_rel[3:6]

                distance = np.linalg.norm(error_position)
                if distance < self.distance_minimum:  # Fail safe for tiny distances (crashes)
                    distance = self.distance_minimum

                # Relative positions and velocities
                # if uri is CFUtil.URI1 or uri2 is CFUtil.URI1:
                #     sum_pos = error_position * self.r_rel
                # else:
                #     sum_pos = error_position * self.r_rel

                sum_pos = error_position * self.r_rel / (distance - self.distance_offset)
                sum_vel = error_velocity * self.rdot_rel

                # "Shadowing" protection
                angle, rej_1, rej_2 = PyUtil.compute_rejections(state[uri][0:3] - self.ref, state[uri2][0:3] - self.ref)
                angle_cap = self.angle_cap
                angle_k = self.angle_k
                if angle < angle_cap:
                    angle_ratio = (angle_cap - angle)/angle_cap
                    angle_ampl = angle_k*min([1, angle_ratio/(distance - self.distance_offset)])
                    rej_1 = rej_1 * angle_ampl
                    rej_2 = rej_2 * angle_ampl
                else:
                    rej_1 = rej_1 * 0
                    rej_2 = rej_2 * 0

                # Sum all components
                _sum = _sum + sum_pos + sum_vel
                _sum = _sum / (distance - self.distance_offset)

                output[uri] = output[uri] + _sum + rej_1
                output[uri2] = output[uri2] - _sum + rej_2

        self.output = output
        return output

    def get_u(self):
        return copy(self.output)

    def get_u_list(self):
        """
        Retrieves references in nested lists. Required for swarm.parallel and swarm.sequence
        :return: dict{uri: [[vx, vy, vz]]}
        """
        # TODO Move into get_u?
        u = self.get_u()
        for uri in u:
            u[uri] = [u[uri]]

        for uri in self._ignore_list:
            if uri in u:
                u[uri].append(True)

        return u

    def set_ref(self, new_ref):
        """
        Update swarm center reference to new_ref
        :param new_ref: list[x, y, z]
        :return:
        """
        self.ref = np.array(new_ref)

    def get_ref(self):
        """
        For logging purposes
        :return:
        """
        return {'flock': list(self.ref)}

    def reset(self):
        pass

    def add_ignore(self, uri):
        """
        Adds drone uri to the ignore list
        :param uri: list[uri]
        """
        if isinstance(uri, list):
            for i in uri:
                if i not in self._ignore_list:
                    self._ignore_list.append(i)
        else:
            if uri not in self._ignore_list:
                self._ignore_list.append(uri)

    def remove_ignore(self, uri):
        """
        Removes drone uris from the ignore list
        :param uri: list[uri]
        """
        if isinstance(uri, list):
            for i in uri:
                if i in self._ignore_list:
                    self._ignore_list.remove(i)
        else:
            if uri in self._ignore_list:
                self._ignore_list.remove(uri)


class DistanceController:

    def __init__(self, ref=(0, 0, 1), period_ms=50):
        self.kp = 1.2
        self.ki = 0
        self.kd = 0.1
        self.kp_swarm = 0.5

        self.h = period_ms/1000
        self.k_disturb = 0.1

        self.dist = 0.5     # defined distance between each drone.
        self.ref = np.array(ref)
        self.output = {}

        self.integ = 0
        self.deriv = 0
        self.swarm_e = 0
        self.prev_swarm_e = 0

        self.adj = None
        self._ignore_list = []

        self.k1 = -0.3
        self.k2 = 0.9
        self.k3 = 0

    # Generate the adjacency matrix, defining the swarm formation
    def _calc_adjacency(self, uris, count):

        """Generate formation
        :Option: Parameter to set formation:
        0: Tetrahedron
        1: Circle
        2: Line
        """

        # Remove ignored drone from uris list
        # for uri in uris:
        #     if uri in self._ignore_list:
        #         uris.remove(uri)

        formation_list = Formation.gen_formation(dist=self.dist, drone_count=count, option=0)

        formation = {}
        for i in range(count):
            uri = uris[i]
            formation[uri] = formation_list[i]

        self.adj = np.zeros((count, count))

        # Create adjacency matrix, defining the distance between each drone
        for i in range(count):
            uri1 = uris[i]
            for j in range(count):
                uri2 = uris[j]
                self.adj[i][j] = math.sqrt((formation[uri1][0] - formation[uri2][0]) ** 2 +
                                           (formation[uri1][1] - formation[uri2][1]) ** 2 +
                                           (formation[uri1][2] - formation[uri2][2]) ** 2)

    def _update_params(self, states, uris, count):

        swarm_pos = np.zeros(3)

        # Remove detached drone from swarm calculation
        # for uri in uris:
        #     if uri in self._ignore_list:
        #         uris.remove(uri)

        # Center position of swarm
        for i in range(count):
            uri = uris[i]
            swarm_pos = swarm_pos + states[uri][0:3]/count

        # Swarm position error
        self.swarm_e = self.ref - swarm_pos
        # Update integral part
        self.integ = self.integ + self.ki*self.h*self.swarm_e
        # Update derivative part
        self.deriv = (self.swarm_e-self.prev_swarm_e)*self.kd/self.h

    def compute(self, states):
        uris = list(states.keys())

        # Save number of drones of the actual swarm, not including disturbances.
        count = self.get_drone_count(states)
        uris_disturbance = list(set(self._ignore_list))

        # Create numpy matrices out of the state dictionaries
        states = CFUtil.state_dict_to_numpy_matrix(states)

        # Initialize velocity vector
        pdot = {}
        for uri in uris:
            pdot[uri] = np.zeros(3)

        # Save active drones separately
        uris_active = list(set(uris) - set(self._ignore_list))

        # Calculate adjacency matrix if empty or if drone count changes.
        if self.adj is None or count != len(self.adj):
            self._calc_adjacency(copy(uris_active), count)

        self._update_params(states, copy(uris_active), count)

        # Loop over uris and states to generate velocity vector
        for i in range(count):
            uri1 = uris_active[i]

            for j in range(i+1, count):
                uri2 = uris_active[j]
                # Normalize distance vector, initialize at 5 cm to avoid dividing by zero
                pos_norm = max(np.linalg.norm(states[uri1][0:3]-states[uri2][0:3]), 0.05)

                # Precalculate
                pos_norm2 = (pos_norm-self.adj[i][j])/pos_norm
                _sum = (states[uri1][0:3] - states[uri2][0:3])*pos_norm2*self.kp_swarm

                pdot[uri1][0:3] = pdot[uri1][0:3] - _sum
                pdot[uri2][0:3] = pdot[uri2][0:3] + _sum

            # Control signal from trajectory ref
            pdot[uri1][0:3] = pdot[uri1][0:3] + self.kp * self.swarm_e + self.integ + self.deriv

            # Disturbance/detached drone contribution
            for k in range(len(uris_disturbance)):
                uri3 = uris_disturbance[k]

                # Calculate distance between drone and disturbance, get direction on where to go
                disturbance_dist = states[uri1][0:3] - states[uri3][0:3]
                direction, magn = self.calculate_disturbance(disturbance_dist)

                pdot[uri1][0:3] = pdot[uri1][0:3] + self.k_disturb*magn*direction

        self.prev_swarm_e = self.swarm_e
        self.output = pdot

        return pdot

    def calculate_disturbance(self, disturbance_dist):
        """
        Calculates the impact the disturbance has on each drone, following a non-linear curve with cut-off
        :param disturbance_dist: Array containing distance vector between drone and disturbance
        :return: direction, magn: direction for drone to take, magn of direction
        """
        distance = np.linalg.norm(disturbance_dist)

        # Set distance to 5 cm to avoid dividing by zero
        if distance < 0.05:
            distance = 0.05
        direction = disturbance_dist/distance

        magn = max(0, self.k1*distance + self.k2/distance + self.k3)

        return direction, magn

    def get_drone_count(self, states):
        """
        Returns the number of drones in the actual swarm, not counting disconnected/disturbance drones
        :param states:
        :return:
        """
        return len(list(states.keys())) - len(self._ignore_list)

    def get_u(self):
        return copy(self.output)

    def get_u_list(self):
        """
        Retrieves references in nested lists. Required for swarm.parallel and swarm.sequence
        :return: dict{uri: [[vx, vy, vz]]}
        """
        # TODO Move into get_u?
        u = self.get_u()
        for uri in u:
            u[uri] = [u[uri]]

        for uri in self._ignore_list:
            if uri in u:
                u[uri].append(True)

        return u

    def set_ref(self, new_ref):
        self.ref = np.array(new_ref)

    def get_ref(self):
        """
        For logging purposes
        :return:
        """
        return {'flock': list(self.ref)}

    def reset(self):
        self.integ = 0
        self.deriv = 0
        self.swarm_e = 0
        self.prev_swarm_e = 0

    def add_ignore(self, uri):
        """
        Adds drone uri to the ignore list
        :param uri: list[uri]
        """
        if isinstance(uri, list):
            for i in uri:
                if i not in self._ignore_list:
                    self._ignore_list.append(i)
        else:
            if uri not in self._ignore_list:
                self._ignore_list.append(uri)

    def remove_ignore(self, uri):
        """
        Removes drone uris from the ignore list
        :param uri: list[uri]
        """
        if isinstance(uri, list):
            for i in uri:
                if i in self._ignore_list:
                    self._ignore_list.remove(i)
        else:
            if uri in self._ignore_list:
                self._ignore_list.remove(uri)


