import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
from elements import surfaces
from rays.ray import Ray

class RTEngine:

    def __init__(self):
        pass

    def ray_surface_intersection(self, surface, ray : Ray, t_max=200.0):
        
        def f(t):
            p = ray.origin + t * ray.direction
            r = np.sqrt(np.sum((p[:2] - surface.vertex[:2])**2))
            return p[2] - surface.vertex[2] - surface.sag(r)

        grid = np.linspace(0, t_max, 1000)
        vals = np.array([f(t) for t in grid])
        idx = np.where(np.sign(vals[:-1]) * np.sign(vals[1:]) <= 0)[0]
        if len(idx) == 0:
            return None, None

        a, b = grid[idx[0]], grid[idx[0] + 1]
        res = optimize.root_scalar(f, bracket=[a, b], method='brentq')
        if not res.converged:
            return None, None

        t_hit = res.root
        hit = ray.origin + t_hit * ray.direction

        eps = 1e-6
        dr = (
            surface.sag(np.sqrt((hit[0] - surface.vertex[0] + eps)**2 + (hit[1] - surface.vertex[1])**2))
            - surface.sag(np.sqrt((hit[0] - surface.vertex[0] - eps)**2 + (hit[1] - surface.vertex[1])**2))
        ) / (2 * eps)
        dz = (
            surface.sag(np.sqrt((hit[0] - surface.vertex[0])**2 + (hit[1] - surface.vertex[1] + eps)**2))
            - surface.sag(np.sqrt((hit[0] - surface.vertex[0])**2 + (hit[1] - surface.vertex[1] - eps)**2))
        ) / (2 * eps)

        normal = np.array([-dr, -dz, 1.0], dtype=float)
        normal /= np.linalg.norm(normal)
        if np.dot(normal, ray.direction) > 0:
            normal = -normal

        return t_hit, normal