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
    def __init__(self, rays: Union[Ray, list[Ray]] = None):
        self.ray_origins = None      # (N,3)
        self.ray_directions = None   # (N,3)
        self.ray_paths = None        # (S,N,3), filled by Tracer
        self.wavelengths = None       # (N,)
        self._rays = None            # optional: keep original Ray objects

        if rays is not None:
            self.add_rays(rays)

    def add_rays(self, rays: Union[Ray, list[Ray]]):
        if isinstance(rays, Ray):
            rays = [rays]
        elif not isinstance(rays, list):
            raise TypeError("rays must be Ray or list[Ray]")

        if len(rays) == 0:
            raise ValueError("RayGroup must contain at least one Ray")

        origins = np.vstack([r.origin for r in rays])
        directions = np.vstack([r.direction for r in rays])

        self.ray_origins = origins
        self.ray_directions = directions
        self.wavelengths = np.array([r.wavelength for r in rays], dtype=float)
        self._rays = rays

    def propagate(self, distance):
        self.ray_origins += distance * self.ray_directions

    def set_state(self, origins, directions):
        origins = np.asarray(origins, dtype=float).reshape(-1, 3)
        directions = np.asarray(directions, dtype=float).reshape(-1, 3)

        if origins.shape != directions.shape:
            raise ValueError("origins and directions must have the same shape (N, 3)")

        mags = np.linalg.norm(directions, axis=1)
        if np.any(mags == 0):
            raise ValueError("direction vectors cannot contain zeros")

        self.ray_origins = origins
        self.ray_directions = directions / mags[:, None]

        self.i = self.ray_directions[:, 0]
        self.j = self.ray_directions[:, 1]
        self.k = self.ray_directions[:, 2]

class IdealAngularSource3D(RayGroup):
    def __init__( self, origin, num_rays=1000, wavelength=550.0, angle = 30):
        rays = []
        for _ in range(num_rays):
            theta_x = np.random.uniform(-angle/2, angle/2)
            theta_y = np.random.uniform(-angle/2, angle/2)
            ray = Ray(origin=origin, direction=[theta_x, theta_y], wavelength=wavelength)
            rays.append(ray)
        super().__init__(rays)

class IdealLambertianSource3D(RayGroup):
    def __init__(self, origin, num_rays=1000, wavelength=550.0,
                 distribution='random'):

        if distribution not in ['random', 'deterministic']:
            raise ValueError("distribution must be 'random' or 'deterministic'")

        rays = []

        # 3D Lambertian / cosine-weighted hemisphere sampling
        #
        # PDF over solid angle:
        # p(omega) = cos(theta) / pi
        #
        # In spherical coordinates:
        # phi   = 2*pi*v
        # theta = arcsin(sqrt(u))
        #
        # where u,v are uniform on [0,1].

        if distribution == 'random':
            u = np.random.uniform(0.0, 1.0, size=num_rays)
            v = np.random.uniform(0.0, 1.0, size=num_rays)
        else:
            # Deterministic smooth sampling:
            # evenly spaced quantiles in theta-distribution,
            # evenly spaced azimuth samples
            u = (np.arange(num_rays) + 0.5) / num_rays
            golden_ratio_conjugate = (np.sqrt(5.0) - 1.0) / 2.0
            v = (np.arange(num_rays) * golden_ratio_conjugate) % 1.0

        theta = np.arcsin(np.sqrt(u))      # polar angle from +z normal
        phi = 2.0 * np.pi * v              # azimuth angle

        # Convert to Cartesian direction cosines
        dx = np.sin(theta) * np.cos(phi)
        dy = np.sin(theta) * np.sin(phi)
        dz = np.cos(theta)

        # Convert to projected angular representation relative to +z
        theta_x = np.degrees(np.arctan2(dx, dz))
        theta_y = np.degrees(np.arctan2(dy, dz))

        for tx, ty in zip(theta_x, theta_y):
            ray = Ray(
                origin=origin,
                direction=[tx, ty],
                wavelength=wavelength
            )
            rays.append(ray)

        super().__init__(rays)

class TruncatedLambertianSource3D(RayGroup):
    def __init__(self, origin, num_rays=1000, wavelength=550.0, distribution='random', half_angle_deg=30.0):

        if distribution not in ['random', 'deterministic']:
            raise ValueError("distribution must be 'random' or 'deterministic'")

        if not (0.0 < half_angle_deg <= 90.0):
            raise ValueError("half_angle_deg must be in the range (0, 90]")

        rays = []

        theta_max = np.radians(half_angle_deg)
        sin_theta_max = np.sin(theta_max)

        # Truncated 3D Lambertian / cosine-weighted cone sampling
        #
        # Full hemisphere PDF over solid angle:
        #   p(omega) = cos(theta) / pi
        #
        # Restricted to cone 0 <= theta <= theta_max:
        #   p(theta, phi) ∝ cos(theta) sin(theta)
        #
        # CDF in theta:
        #   F(theta) = sin^2(theta) / sin^2(theta_max)
        #
        # Inverse CDF:
        #   theta = arcsin( sin(theta_max) * sqrt(u) )
        #
        # phi remains uniform on [0, 2*pi)

        if distribution == 'random':
            u = np.random.uniform(0.0, 1.0, size=num_rays)
            v = np.random.uniform(0.0, 1.0, size=num_rays)
        else:
            u = (np.arange(num_rays) + 0.5) / num_rays
            golden_ratio_conjugate = (np.sqrt(5.0) - 1.0) / 2.0
            v = (np.arange(num_rays) * golden_ratio_conjugate) % 1.0

        theta = np.arcsin(sin_theta_max * np.sqrt(u))
        phi = 2.0 * np.pi * v

        # Cartesian direction cosines, cone centered on +z
        dx = np.sin(theta) * np.cos(phi)
        dy = np.sin(theta) * np.sin(phi)
        dz = np.cos(theta)

        # Convert to your projected angular representation
        theta_x = np.degrees(np.arctan2(dx, dz))
        theta_y = np.degrees(np.arctan2(dy, dz))

        for tx, ty in zip(theta_x, theta_y):
            ray = Ray(
                origin=origin,
                direction=[tx, ty],
                wavelength=wavelength
            )
            rays.append(ray)

        super().__init__(rays)

class AngularSource2D(RayGroup):
    def __init__(self, origin, num_rays=1000, wavelength=550.0, distribution='random', plane='xz'):

        if plane not in ['xz', 'yz']:
            raise ValueError("plane must be 'xz' or 'yz'")

        if distribution not in ['random', 'uniform']:
            raise ValueError("distribution must be 'random' or 'uniform'")

        rays = []

        if distribution == 'random':
            theta = np.random.uniform(0, 1, num_rays)
        elif distribution == 'uniform':
            theta = np.linspace(-90.0, 90.0, num_rays)

        if plane == 'xz':
            for theta_x in theta:
                ray = Ray(origin=origin, direction=[theta_x, 0.0], wavelength=wavelength)
                rays.append(ray)

        elif plane == 'yz':
            for theta_y in theta:
                ray = Ray(origin=origin, direction=[0.0, theta_y], wavelength=wavelength)
                rays.append(ray)

        super().__init__(rays)

import numpy as np

class IdealLambertianSource2D(RayGroup):
    def __init__(self, origin, num_rays=1000, wavelength=550.0, distribution='random', plane='xz'):

        if plane not in ['xz', 'yz']:
            raise ValueError("plane must be 'xz' or 'yz'")

        if distribution not in ['random', 'deterministic']:
            raise ValueError("distribution must be 'random' or 'deterministic'")

        rays = []

        # 2D Lambertian angular PDF:
        # p(theta) = cos(theta) / 2,  theta in [-pi/2, pi/2]
        #
        # CDF:
        # F(theta) = (sin(theta) + 1) / 2
        #
        # Inverse CDF:
        # theta = arcsin(2u - 1)

        if distribution == 'random':
            # Monte Carlo Lambertian sampling
            u = np.random.uniform(0.0, 1.0, size=num_rays)
        else:
            # Smooth deterministic Lambertian sampling:
            # evenly spaced quantiles in cumulative probability
            u = (np.arange(num_rays) + 0.5) / num_rays

        theta = np.degrees(np.arcsin(2.0 * u - 1.0))

        # Optional: sort for cleaner fan plotting
        theta = np.sort(theta)

        if plane == 'xz':
            for theta_x in theta:
                ray = Ray(
                    origin=origin,
                    direction=[theta_x, 0.0],
                    wavelength=wavelength
                )
                rays.append(ray)

        else:  # plane == 'yz'
            for theta_y in theta:
                ray = Ray(
                    origin=origin,
                    direction=[0.0, theta_y],
                    wavelength=wavelength
                )
                rays.append(ray)

        super().__init__(rays)

class TruncatedLambertianSource2D(RayGroup):
    def __init__(self, origin, num_rays=1000, wavelength=550.0,
                 distribution='random', plane='xz', half_angle_deg=30.0):

        if plane not in ['xz', 'yz']:
            raise ValueError("plane must be 'xz' or 'yz'")

        if distribution not in ['random', 'deterministic']:
            raise ValueError("distribution must be 'random' or 'deterministic'")

        if not (0.0 < half_angle_deg <= 90.0):
            raise ValueError("half_angle_deg must be in the range (0, 90]")

        theta_max = np.radians(half_angle_deg)
        sin_theta_max = np.sin(theta_max)

        rays = []

        # 2D truncated Lambertian angular PDF:
        # p(theta) = cos(theta) / (2 sin(theta_max)),
        # theta in [-theta_max, +theta_max]
        #
        # CDF:
        # F(theta) = (sin(theta) + sin(theta_max)) / (2 sin(theta_max))
        #
        # Inverse CDF:
        # theta = arcsin((2u - 1) * sin(theta_max))

        if distribution == 'random':
            u = np.random.uniform(0.0, 1.0, size=num_rays)
        else:
            # Smooth deterministic quantile sampling
            u = (np.arange(num_rays) + 0.5) / num_rays

        theta = np.degrees(np.arcsin((2.0 * u - 1.0) * sin_theta_max))

        theta = np.sort(theta)

        if plane == 'xz':
            for theta_x in theta:
                ray = Ray(
                    origin=origin,
                    direction=[theta_x, 0.0],
                    wavelength=wavelength
                )
                rays.append(ray)

        else:  # plane == 'yz'
            for theta_y in theta:
                ray = Ray(
                    origin=origin,
                    direction=[0.0, theta_y],
                    wavelength=wavelength
                )
                rays.append(ray)

        super().__init__(rays)

class ExtendedLambertianSource(RayGroup):
    pass

class IdealHomogenousBeam(RayGroup):
    pass

class IdealGaussianBeam(RayGroup):
    pass


if __name__ == "__main__":
    r1 = Ray(origin=[0, 0, 0], direction=[45, 45])
    print(r1.get_angles())