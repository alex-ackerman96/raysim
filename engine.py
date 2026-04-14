import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
from elements.surfaces import AsphericSurface, PlanarSurface, SphericalSurface
from rays.ray import RayGroup, Ray

DARK_BG    = '#0a0b0c'
LIGHT_BG   = '#ffffff'
AXIS_COL   = '#ffffff'
GRID_COL   = "#383a3d"
LABEL_COL  = '#aaaaaa'

from dataclasses import dataclass
from typing import List

@dataclass
class Lens:
    surfaces: List  # ordered list of surfaces, front to back

    def load_from_file(self, filename):
        # Placeholder for loading lens data from a file (e.g., JSON, CSV)
        pass  


def ray_surface_intersection(surface, ray, t_max=200.0):
    """
    Find where a ray intersects an optical surface and compute the surface normal at that point.

    The surface is defined implicitly as:
        F(p) = p.z - vertex.z - sag(r) = 0
    where r is the radial distance from the optical axis at the surface vertex,
    and sag(r) is the surface's sag function (height along z as a function of radius).

    Returns (t_hit, normal) where t_hit is the ray parameter at the intersection,
    or (None, None) if no valid intersection is found within the aperture.
    """

    def f(t):
        # Evaluate the implicit surface equation at ray parameter t.
        # Ray point: p = origin + t * direction
        # r = radial distance from the surface's optical axis (x and y components only)
        # Returns 0 when the ray point lies exactly on the surface.
        p = ray.origin + t * ray.direction
        r = np.sqrt(np.sum((p[:2] - surface.vertex[:2])**2))
        return p[2] - surface.vertex[2] - surface.sag(r)

    # --- Step 1: Bracket search ---
    # Sample f(t) at 1000 evenly spaced points along the ray.
    # Look for sign changes in consecutive samples, which indicate a root (surface crossing).
    grid = np.linspace(0, t_max, 1000)
    vals = np.array([f(t) for t in grid])
    idx = np.where(np.sign(vals[:-1]) * np.sign(vals[1:]) <= 0)[0]
    if len(idx) == 0:
        # No sign change found — ray never crosses the surface within t_max
        return None, None, None

    # --- Step 2: Root refinement with Brent's method ---
    # Use the first sign-change interval [a, b] as the bracket.
    # Brent's method gives a fast, robust, high-precision root.
    a, b = grid[idx[0]], grid[idx[0] + 1]
    res = optimize.root_scalar(f, bracket=[a, b], method='brentq')
    if not res.converged:
        return None, None, None

    t_hit = res.root
    hit = ray.origin + t_hit * ray.direction  # 3D intersection point on the surface

    # --- Step 3: Aperture check ---
    # Reject intersections outside the physical lens aperture (diameter/2 radius).
    # The sag function is mathematically defined for all r, but the lens only
    # exists within its clear aperture — rays outside it should pass unobstructed.
    r_hit = np.sqrt((hit[0] - surface.vertex[0])**2 + (hit[1] - surface.vertex[1])**2)
    if r_hit > surface.diameter / 2:
        return None, None, None

    # --- Step 4: Surface normal via finite differences ---
    # The surface is z = vertex_z + sag(r), so it can be written as:
    #     G(x, y, z) = z - vertex_z - sag(r) = 0
    # The gradient of G gives the surface normal: ∇G = (-∂sag/∂x, -∂sag/∂y, 1)
    #
    # Since sag depends on r = sqrt(x² + y²), by chain rule:
    #     ∂sag/∂x = (dsag/dr) * (x / r)
    # We approximate this with central finite differences.
    eps = 1e-6

    # ∂sag/∂x: vary x by ±eps, compute sag, take central difference
    dr = (
        surface.sag(np.sqrt((hit[0] - surface.vertex[0] + eps)**2 + (hit[1] - surface.vertex[1])**2))
        - surface.sag(np.sqrt((hit[0] - surface.vertex[0] - eps)**2 + (hit[1] - surface.vertex[1])**2))
    ) / (2 * eps)

    # ∂sag/∂y: vary y by ±eps
    dz = (
        surface.sag(np.sqrt((hit[0] - surface.vertex[0])**2 + (hit[1] - surface.vertex[1] + eps)**2))
        - surface.sag(np.sqrt((hit[0] - surface.vertex[0])**2 + (hit[1] - surface.vertex[1] - eps)**2))
    ) / (2 * eps)

    # Unnormalized normal: ∇G = (-∂sag/∂x, -∂sag/∂y, 1)
    normal = np.array([-dr, -dz, 1.0], dtype=float)
    normal /= np.linalg.norm(normal)  # normalize to unit vector

    # --- Step 5: Normal orientation ---
    # Ensure the normal points against the incoming ray (into the hemisphere the ray comes from).
    # If the dot product with ray direction is positive, they point the same way — flip the normal.
    if np.dot(normal, ray.direction) > 0:
        normal = -normal

    print("Hit at:", hit[0], hit[1], hit[2])
    ray.add_hit(hit)

    return t_hit, normal, hit


def refract(direction, normal, n1, n2):
    d = direction / np.linalg.norm(direction)
    n = normal / np.linalg.norm(normal)
    cos_i = -np.dot(n, d)
    eta = n1 / n2
    k = 1 - eta**2 * (1 - cos_i**2)
    if k < 0:
        return None
    return eta * d + (eta * cos_i - np.sqrt(k)) * n


def plot_aspheric_surface_with_refract(lenses, rays, max_r=None, n=500, ray_length=200, refracted_length=200):
    # Flatten all surfaces for ray tracing
    all_surfaces = [s for lens in lenses for s in lens.surfaces]

    if max_r is None:
        max_r = all_surfaces[0].diameter / 2

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(LIGHT_BG)
    ax.set_facecolor(LIGHT_BG)
    ax.grid(color=GRID_COL, linewidth=0.4, zorder=0)
    for spine in ax.spines.values():
        spine.set_color(GRID_COL)
    ax.tick_params(axis='x', colors=GRID_COL)
    ax.tick_params(axis='y', colors=GRID_COL)
    ax.axhline(0, color=AXIS_COL, lw=0.5, alpha=0.35, zorder=1)
    colors = ['#4dbf6b', '#ff6b6b', '#4d96ff', '#ffaa00', '#aa66cc', '#ff4444']

    # --- Draw each lens independently ---
    for lens in lenses:
        r = np.linspace(0, max_r, n)
        surf_zprofiles = []

        for surface in lens.surfaces:
            z = np.array([surface.sag(ri) for ri in r]) + surface.vertex[2]
            surf_zprofiles.append(z)
            ax.plot(z,  r, lw=0.5, color='black', alpha=0.9)
            ax.plot(z, -r, lw=0.5, color='black', alpha=0.9)

        # Shade material and draw rim lines only between adjacent surfaces within this lens
        for i in range(1, len(lens.surfaces)):
            z_prev = surf_zprofiles[i - 1]
            z_curr = surf_zprofiles[i]

            ax.fill_betweenx( r, z_prev, z_curr, color='lightblue', alpha=0.3)
            ax.fill_betweenx(-r, z_prev, z_curr, color='lightblue', alpha=0.3)

            # Rim line connecting the two surface edges at max_r
            ax.plot([z_prev[-1], z_curr[-1]], [ max_r,  max_r], 'k-', lw=0.5)
            ax.plot([z_prev[-1], z_curr[-1]], [-max_r, -max_r], 'k-', lw=0.5)

    # --- Ray tracing (unchanged, uses flattened all_surfaces) ---
    T = 0.95
    R = 0.05

    for ray_idx, ray in enumerate(rays):
        color = colors[0]
        current_intensity = 1.0
        current_ray = ray
        completed = True

        for surface in all_surfaces:
            t_hit, normal, hit = ray_surface_intersection(surface, current_ray, t_max=ray_length)

            if t_hit is None:
                t1 = np.linspace(0, ray_length, 200)
                pts1 = current_ray.origin[None, :] + t1[:, None] * current_ray.direction[None, :]
                ax.plot(pts1[:, 2], pts1[:, 1], color=color, lw=0.8, alpha=current_intensity * 0.8)

                # endpoint of this free-space segment
                end_point = current_ray.origin + ray_length * current_ray.direction
                current_ray.set_state(end_point, current_ray.direction)
                current_ray.add_hit(end_point)

                completed = False
                break

            t1 = np.linspace(0, t_hit, 200)
            pts1 = current_ray.origin[None, :] + t1[:, None] * current_ray.direction[None, :]
            ax.plot(pts1[:, 2], pts1[:, 1], color=color, lw=0.8, alpha=current_intensity * T * 0.8)

            current_ray.add_hit(hit)

            reflect_dir = current_ray.direction*1e-6 - 2 * np.dot(current_ray.direction, normal) * normal
            reflect_ray = Ray(hit, reflect_dir, wavelength=current_ray.wavelength)
            t_refl = np.linspace(0, refracted_length * 0.7, 150)
            pts_refl = reflect_ray.origin[None, :] + t_refl[:, None] * reflect_ray.direction[None, :]
            ax.plot(pts_refl[:, 2], pts_refl[:, 1], color=color, lw=0.6,
                    alpha=current_intensity * R * 0.6, linestyle='--')

            refr_dir = refract(current_ray.direction, normal, surface.n1, surface.n2)
            if refr_dir is None:
                completed = False
                break

            current_ray.set_state(hit + 1e-6 * refr_dir, refr_dir)
            current_intensity *= T

        if completed:
            t2 = np.linspace(0, refracted_length, 200)
            pts2 = current_ray.origin[None, :] + t2[:, None] * current_ray.direction[None, :]
            ax.plot(pts2[:, 2], pts2[:, 1], color=color, lw=0.8, alpha=current_intensity * 0.8)

        print(len(current_ray.path))
        print("Ray path:")
        for i, p in enumerate(current_ray.path):
            print(f"  {i}: {p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}")
    return fig, ax



# if __name__ == '__main__':
#     # s1 = AsphericSurface(vertex=[0, 0, 10], radius=15.871, conic=-1.57, aspheric_coeffs=[2.86468e-05, -2.31409e-08], n1=1.0, n2=1.5, diameter=25.0)
#     # s1 = AsphericSurface(vertex=[0, 0, 40], radius=20, conic=-1.2, aspheric_coeffs=[1.5e-6, -3.5e-8, -2e-11], n1=1.0, n2=1.5, diameter=50.0)
#     s1 = SphericalSurface(center=[0, 0, 40], radius=60, n1=1.0, n2=1.5, diameter=50.0)
#     # s2 = PlanarSurface(center=[0, 0, 20], normal=[0,0,1], n1=1.5, n2=1.0, diameter=40.0)
#     s2 = SphericalSurface(center=[0, 0, 55], radius=-60, n1=1.5, n2=1.0, diameter=50.0)
#     # r = Ray(origin=[0, 0, 0], direction=[0, 0.5, 1])
#     r1 = Ray(origin=[0, 0, 0], direction=[0, 0.3, 1])
#     r2 = Ray(origin=[0, 0, 0], direction=[0, 0, 1])
#     r3 = Ray(origin=[0, 0, 0], direction=[0, -0.3, 1])
#     r4 = Ray(origin=[0, 5, 0], direction=[0, 0.3, 1])
#     r5 = Ray(origin=[0, 5, 0], direction=[0, 0, 1])
#     r6 = Ray(origin=[0, 5, 0], direction=[0, -0.3, 1])
#     r7 = Ray(origin=[0, -5, 0], direction=[0, 0.3, 1])
#     r8 = Ray(origin=[0, -5, 0], direction=[0, 0, 1])
#     r9 = Ray(origin=[0, -5, 0], direction=[0, -0.3, 1])
#     r10 = Ray(origin=[0, 15, 0], direction=[0, 0.3, 1])
#     r11 = Ray(origin=[0, 15, 0], direction=[0, 0, 1])
#     r12 = Ray(origin=[0, 15, 0], direction=[0, -0.3, 1])    
#     fig, ax = plot_aspheric_surface_with_refract([s1, s2],[r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12])
#     plt.show()

if __name__ == '__main__':
    # Singlet lens 1
    lens1 = Lens(surfaces=[
        SphericalSurface(center=[0, 0, 40], radius=60,  n1=1.0, n2=1.5, diameter=50.0),
        SphericalSurface(center=[0, 0, 55], radius=-60, n1=1.5, n2=1.0, diameter=50.0),
    ])

    # Singlet lens 2
    lens2 = Lens(surfaces=[
        SphericalSurface(center=[0, 0, 80], radius=40,  n1=1.0, n2=1.5, diameter=40.0),
        SphericalSurface(center=[0, 0, 97], radius=-40, n1=1.5, n2=1.8, diameter=40.0),
        SphericalSurface(center=[0, 0, 100], radius=-120, n1=1.8, n2=1.0, diameter=40.0),
    ])

    # Example doublet lens 3 (3 surfaces: air | glass1 | glass2 | air)
    # lens3 = Lens(surfaces=[
    #     SphericalSurface(center=[0, 0, 200], radius=30,   n1=1.0,  n2=1.5,  diameter=30.0),
    #     SphericalSurface(center=[0, 0, 210], radius=-25,  n1=1.5,  n2=1.62, diameter=30.0),
    #     SphericalSurface(center=[0, 0, 218], radius=-60,  n1=1.62, n2=1.0,  diameter=30.0),
    # ])

    rays = [
        Ray(origin=[0,   0, 0], direction=[0,  0.3, 1]),
        Ray(origin=[0,   0, 0], direction=[0,  0.0, 1]),
        Ray(origin=[0,   0, 0], direction=[0, -0.3, 1]),
        Ray(origin=[0,   5, 0], direction=[0,  0.3, 1]),
        Ray(origin=[0,   5, 0], direction=[0,  0.0, 1]),
        Ray(origin=[0,   5, 0], direction=[0, -0.3, 1]),
        Ray(origin=[0,  -5, 0], direction=[0,  0.3, 1]),
        Ray(origin=[0,  -5, 0], direction=[0,  0.0, 1]),
        Ray(origin=[0,  -5, 0], direction=[0, -0.3, 1]),
        Ray(origin=[0,  15, 0], direction=[0,  0.3, 1]),
        Ray(origin=[0,  15, 0], direction=[0,  0.0, 1]),
        Ray(origin=[0,  15, 0], direction=[0, -0.3, 1]),
    ]

    group = RayGroup(rays)

    fig, ax = plot_aspheric_surface_with_refract(
        [lens1, lens2], rays, refracted_length=300
    )
    plt.show()