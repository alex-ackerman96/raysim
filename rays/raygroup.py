import numpy as np

class RayPlaneMap:
    "Array of rays in plane normal to optical axis at location z along optical axis, with ray parameters (x, y, theta_x, theta_y, wavelength) where theta_x and theta_y are angles with respect to the optical axis in x and y directions respectively."
    def __init__(self, rays, z : float = 0):
        self.location = z

class RayGroup:
    def __init__(self, origin, direction, wavelength : float = 550):
        self.wavelength = wavelength
        self.origin = np.array(origin)
        self.direction = np.array(direction) / np.linalg.norm(direction)

    def propagate(self, distance):
        self.origin += distance * self.direction
