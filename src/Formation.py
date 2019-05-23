import math
import numpy as np


class Formation:

    @staticmethod
    def gen_formation(dist=0.5, drone_count=0, option=0):

        if option == 0:
            tetrahedron = [(0, 0, 0),
                           (dist, 0, 0),
                           (dist/2, dist, 0),
                           (dist/2, dist/2, dist),
                           (dist/2, dist/2, -dist)]

            return tetrahedron
        elif option == 1:
            angle = 2*math.pi/drone_count

            circle = [(0, 0, 0),
                      (math.cos(angle), math.sin(angle), 0),
                      (math.cos(2*angle), math.sin(2*angle), 0),
                      (math.cos(3*angle), math.sin(3*angle), 0),
                      (math.cos(4*angle), math.sin(4*angle), 0)]
            return circle

        elif option == 2:

            line = [(0, 0, 0),
                    (dist, 0, 0),
                    (2*dist, 0, 0),
                    (3*dist, 0, 0),
                    (4*dist, 0, 0)]
            return line
