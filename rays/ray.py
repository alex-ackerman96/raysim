import numpy as np
import warnings
from typing import Union

class Ray:
    def __init__(self, origin, direction=None, point=None, wavelength: float = 550.0):
        self.origin = np.empty(3, dtype=float)
        self.direction = np.empty(3, dtype=float)
        self.path = []
        self.wavelength = None

        # --- origin ---
        try:
            origin = np.asarray(origin, dtype=float).reshape(-1)
        except Exception:
            raise TypeError("origin value(s) cannot be cast as type float")

        if origin.shape != (3,):
            raise TypeError("origin must contain exactly 3 coordinates [x, y, z]")

        self.origin = origin
        self.path.append(origin.copy())

        # --- point overrides direction ---
        if point is not None:
            try:
                point = np.asarray(point, dtype=float).reshape(-1)
            except Exception:
                raise TypeError("point value(s) cannot be cast as type float")

            if point.shape != (3,):
                raise TypeError("invalid point provided: point must contain 3 coordinates [x, y, z]")

            if direction is not None:
                warnings.warn("point coordinates provided, direction will be overridden")

            direction = point - origin

        # --- direction required if point not used ---
        if direction is None:
            raise TypeError(
                "direction must be provided unless point is given"
            )

        try:
            direction = np.asarray(direction, dtype=float).reshape(-1)
        except Exception:
            raise TypeError("direction value(s) cannot be cast as type float")

        # --- direction from [theta_x, theta_y] in degrees ---
        if direction.shape == (2,):
            theta_x = np.radians(direction[0])
            theta_y = np.radians(direction[1])

            tx = np.tan(theta_x)
            ty = np.tan(theta_y)

            vec = np.array([tx, ty, 1.0], dtype=float)
            mag = np.linalg.norm(vec)
            if mag == 0:
                raise ValueError("invalid angular direction: resulting vector has zero magnitude")

            self.direction = vec / mag

        # --- direction from [x, y, z] components ---
        elif direction.shape == (3,):
            mag = np.linalg.norm(direction)
            if mag == 0:
                raise ValueError("direction vector cannot be zero")

            self.direction = direction / mag

        else:
            raise TypeError(
                "direction must have length 2 or 3, representing "
                "[theta_x, theta_y] or [x, y, z] respectively"
            )

        self.i, self.j, self.k = self.direction

        # --- wavelength ---
        try:
            self.wavelength = float(wavelength)
        except Exception:
            raise TypeError("wavelength cannot be cast as type float")

    def propagate(self, distance):
        self.origin += distance * self.direction

    def set_state(self, origin, direction):
        origin = np.asarray(origin, dtype=float).reshape(3)
        direction = np.asarray(direction, dtype=float).reshape(3)
        mag = np.linalg.norm(direction)
        if mag == 0:
            raise ValueError("direction vector cannot be zero")
        self.origin = origin
        self.direction = direction / mag
        self.i, self.j, self.k = self.direction

    def add_hit(self, hit):
        hit = np.asarray(hit, dtype=float)
        if hit.shape != (3,):
            raise ValueError("hit must be a 3-vector [x, y, z]")
        print(f"Adding hit at {hit} to ray path")
        self.path.append(hit.copy())

    def get_angles(self, units : str = "deg"):
        theta_x = np.arctan(self.direction[0]/self.direction[2])
        theta_y = np.arctan(self.direction[1]/self.direction[2])
        if units.lower() == "deg":
            theta_x = np.degrees(theta_x)
            theta_y = np.degrees(theta_y)
            
        return np.array([theta_x, theta_y])

class RayGroup:
    def __init__(self, rays : Union[Ray, list[Ray]]):
        self.ray_origins = None
        self.ray_directions = None
        self.ray_paths = None

    def add_rays(self, rays : Union[Ray, list[Ray]]):
        pass

    def propagate(self, distance):
        self.ray_origins += distance * self.ray_directions

class IdealLambertianSource(RayGroup):
    pass

class ExtendedLambertianSource(RayGroup):
    pass

class IdealHomogenousBeam(RayGroup):
    pass

class IdealGaussianBeam(RayGroup):
    pass

class RayPlaneMap:
    """
    Array of rays in plane normal to optical axis at location z along optical axis,
    with ray parameters (x, y, theta_x, theta_y, wavelength) where theta_x and theta_y
    are angles with respect to the optical axis in x and y directions respectively.

     """
    def __init__(self, rays : Union[Ray, list[Ray], RayGroup], z : float = 0):
        self.location = z

    def get_stokes_parameters(self):
        pass

if __name__ == "__main__":
    r1 = Ray(origin=[0, 0, 0], direction=[45, 45])
    print(r1.get_angles())