import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
from elements.surfaces import AsphericSurface
from rays.ray import Ray


# class Ray:
#     def __init__(self, origin, direction):
#         self.origin = np.array(origin, dtype=float)
#         self.direction = np.array(direction, dtype=float)
#         self.direction = self.direction / np.linalg.norm(self.direction)

# 
# def ray_surface_intersection_distance(surface, ray, t_max=200.0):
#     def f(t):
#         p = ray.origin + t * ray.direction
#         r = np.sqrt(np.sum((p[:2] - surface.vertex[:2])**2))
#         return p[2] - surface.vertex[2] - surface.sag(r)

#     grid = np.linspace(0, t_max, 1000)
#     vals = np.array([f(t) for t in grid])
#     sign_changes = np.where(np.sign(vals[:-1]) * np.sign(vals[1:]) <= 0)[0]

#     if len(sign_changes) == 0:
#         return None

#     i = sign_changes[0]
#     a, b = grid[i], grid[i + 1]
#     result = optimize.root_scalar(f, bracket=[a, b], method='brentq')
#     return result.root if result.converged else None


# def plot_aspheric_surface_with_ray(surface, ray, max_r=None, n=500, ray_length=60):
#     if max_r is None:
#         max_r = surface.diameter / 2

#     r = np.linspace(0, max_r, n)
#     z = np.array([surface.sag(ri) for ri in r]) + surface.vertex[2]

#     t_hit = ray_surface_intersection_distance(surface, ray, t_max=ray_length)
#     t_end = ray_length if t_hit is None else t_hit

#     t = np.linspace(0, t_end, 200)
#     pts = ray.origin[None, :] + t[:, None] * ray.direction[None, :]
#     x = pts[:, 2]
#     y = pts[:, 1]

#     fig, ax = plt.subplots(figsize=(7, 5))
#     ax.plot(z, r, lw=1.5, color='black')
#     ax.plot(z, -r, lw=1.5, color='black')
#     ax.plot(x, y, color='red', lw=1.5, label='Ray')
#     ax.scatter([ray.origin[2]], [ray.origin[1]], color='red', s=20)

#     if t_hit is not None:
#         hit = ray.origin + t_hit * ray.direction
#         ax.scatter([hit[2]], [hit[1]], color='blue', s=25, label='Intersection')

#     ax.set_aspect('equal', adjustable='box')
#     ax.set_xlabel('Z')
#     ax.set_ylabel('Radius / Y')
#     ax.set_title('Aspheric Surface Profile with Ray to Intersection')
#     ax.grid(True, alpha=0.3)
#     ax.legend()
#     return fig, ax

def ray_surface_intersection(surface, ray, t_max=200.0):
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


def refract(direction, normal, n1, n2):
    d = direction / np.linalg.norm(direction)
    n = normal / np.linalg.norm(normal)
    cos_i = -np.dot(n, d)
    eta = n1 / n2
    k = 1 - eta**2 * (1 - cos_i**2)
    if k < 0:
        return None
    return eta * d + (eta * cos_i - np.sqrt(k)) * n


def plot_aspheric_surface_with_refract(surface, ray, max_r=None, n=500, ray_length=60, refracted_length=60):
    if max_r is None:
        max_r = surface.diameter / 2

    r = np.linspace(0, max_r, n)
    z = np.array([surface.sag(ri) for ri in r]) + surface.vertex[2]

    t_hit, normal = ray_surface_intersection(surface, ray, t_max=ray_length)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(z, r, lw=1, color='black')
    ax.plot(z, -r, lw=1, color='black')

    t1_end = ray_length if t_hit is None else t_hit
    t1 = np.linspace(0, t1_end, 200)
    pts1 = ray.origin[None, :] + t1[:, None] * ray.direction[None, :]
    ax.plot(pts1[:, 2], pts1[:, 1], color="#4dbf6b", lw=0.5, label='Incident ray')
    # ax.scatter([ray.origin[2]], [ray.origin[1]], color='red', s=20)

    if t_hit is not None:
        hit = ray.origin + t_hit * ray.direction
        # ax.scatter([hit[2]], [hit[1]], color='blue', s=25, label='Intersection')

        refr_dir = refract(ray.direction, normal, surface.n1, surface.n2)
        if refr_dir is not None:
            refr_ray = Ray(hit + 1e-6 * refr_dir, refr_dir, wavelength=ray.wavelength)
            t2 = np.linspace(0, refracted_length, 200)
            pts2 = refr_ray.origin[None, :] + t2[:, None] * refr_ray.direction[None, :]
            ax.plot(pts2[:, 2], pts2[:, 1], color="#4dbf6b", lw=0.5, label='Refracted ray')
        else:
            ax.text(hit[2], hit[1], ' TIR', color='orange')

    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel('Z')
    ax.set_ylabel('Radius / Y')
    ax.set_title('Aspheric Surface with Refraction')
    ax.grid(True, alpha=0.3)
    ax.legend()
    return fig, ax

if __name__ == '__main__':
    # s = AsphericSurface(vertex=[0, 0, 10], radius=15.871, conic=--1.57, aspheric_coeffs=[2.86468e-05, -2.31409e-08], n1=1.0, n2=1.5, diameter=25.0)
    s = AsphericSurface(vertex=[0, 0, 10], radius=20, conic=-1.2, aspheric_coeffs=[1.5e-6, -3.5e-8, -2e-11], n1=1.0, n2=1.5, diameter=40.0)
    r = Ray(origin=[0, 0, 0], direction=[0, 0.5, 1])
    r = Ray(origin=[0, 0, 0], direction=[0, 0.5, 1])
    fig, ax = plot_aspheric_surface_with_refract(s, r)
    plt.show()