import numpy as np
from scipy.optimize import root_scalar

class Surface:
    def __init__(self, center, radius, n1, n2, diameter):
        pass

class SphericalSurface:
    def __init__(self, center, radius, n1, n2, diameter):
        self.center = np.array(center)
        self.radius = radius
        self.n1 = n1  # Refractive index before surface
        self.n2 = n2  # Refractive index after surface
        self.diameter = diameter  # Fixed diameter of the lens surface

    @property
    def vertex(self):
        return self.center

    def intersect(self, ray):
        oc = ray.origin - self.center
        a = np.dot(ray.direction, ray.direction)
        b = 2.0 * np.dot(oc, ray.direction)
        c = np.dot(oc, oc) - self.radius**2
        discriminant = b**2 - 4*a*c
        
        if discriminant < 0:
            return None, None  # No intersection
        
        t = (-b - np.sqrt(discriminant)) / (2.0*a)
        if t < 0:
            t = (-b + np.sqrt(discriminant)) / (2.0*a)
        
        if t < 0:
            return None, None  # Intersection behind the ray origin
        
        intersection = ray.origin + t * ray.direction
        
        # Check if the intersection is within the lens diameter
        radial_distance = np.linalg.norm(intersection[:2] - self.center[:2])
        if radial_distance > self.diameter / 2:
            return None, None
        
        normal = (intersection - self.center) / self.radius
        return intersection, normal

class AsphericSurface:
    def __init__(self, vertex, radius, conic, aspheric_coeffs, n1, n2, diameter):
        self.vertex = np.array(vertex)
        self.radius = radius
        self.conic = conic
        self.aspheric_coeffs = aspheric_coeffs
        self.n1 = n1
        self.n2 = n2
        self.diameter = diameter  # Fixed diameter of the lens surface

    def sag(self, r):
        c = 1 / self.radius
        z = (c * r**2) / (1 + np.sqrt(1 - (1 + self.conic) * c**2 * r**2))
        for i, a in enumerate(self.aspheric_coeffs):
            z += a * r**(2*(i+2))
        return z

    def intersect(self, ray):
        def f(t):
            p = ray.origin + t * ray.direction
            r = np.sqrt(np.sum((p[:2] - self.vertex[:2])**2))
            return p[2] - self.vertex[2] - self.sag(r)

        result = root_scalar(f, bracket=[0, 100], method='brentq')
        if not result.converged:
            return None, None

        t = result.root
        intersection = ray.origin + t * ray.direction
        
        # Check if the intersection is within the lens diameter
        radial_distance = np.linalg.norm(intersection[:2] - self.vertex[:2])
        if radial_distance > self.diameter / 2:
            return None, None
        
        r = np.sqrt(np.sum((intersection[:2] - self.vertex[:2])**2))
        
        # Compute normal numerically
        epsilon = 1e-6
        dr = np.array([epsilon, 0, self.sag(r+epsilon) - self.sag(r)])
        dtheta = np.array([0, epsilon, self.sag(r) - self.sag(np.sqrt(r**2 - epsilon**2))])
        normal = np.cross(dr, dtheta)
        normal /= np.linalg.norm(normal)

        return intersection, normal
