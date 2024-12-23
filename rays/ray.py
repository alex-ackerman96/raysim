import numpy as np

class Ray:
    def __init__(self, origin, direction):
        self.origin = np.array(origin)
        self.direction = np.array(direction) / np.linalg.norm(direction)

    def propagate(self, distance):
        self.origin += distance * self.direction
