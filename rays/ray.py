import numpy as np

class Ray:
    def __init__(self, origin, direction, wavelength : float = 550):
        self.wavelength = wavelength
        self.origin = np.array(origin)
        self.direction = np.array(direction) / np.linalg.norm(direction)

    def propagate(self, distance):
        self.origin += distance * self.direction
