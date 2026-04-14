import numpy as np
import matplotlib.pyplot as plt
from elements.surfaces import AsphericSurface, PlanarSurface, SphericalSurface
from rays.ray import RayGroup, Ray
from dataclasses import dataclass
from typing import List

@dataclass
class Lens:
    surfaces: List  # ordered list of surfaces, front to back

    def load_from_file(self, filename):
        # Placeholder for loading lens data from a file (e.g., JSON, CSV)
        pass  

class Tracer:
    """
    Vectorized ray tracer for sequential optical surfaces.

    - Operates on ray groups: origins (N, 3), directions (N, 3).
    - Uses coarse bracketing + fixed-iteration bisection per surface.
    - Computes sagged-surface intersections, aperture clipping, and refraction.
    - Returns full per-step paths for all rays.
    """

    def __init__(self, t_max=200.0, bracket_samples=256, refine_iters=10, eps=1e-6):
        self.t_max = float(t_max)
        self.bracket_samples = int(bracket_samples)
        self.refine_iters = int(refine_iters)
        self.eps = float(eps)

    # ---------- core implicit surface function ----------

    def F(self, surface, origins, directions, t):
        """
        Implicit surface function F(p) = z - z_v - sag(r).
        origins, directions: (N, 3)
        t: scalar or array broadcastable to (N,)
        returns: (N,) values of F at p = origin + t * direction
        """
        t = np.asarray(t, dtype=float)
        p = origins + t[..., None] * directions         # (N, 3)
        xy = p[..., :2] - surface.vertex[:2]            # (N, 2)
        r = np.linalg.norm(xy, axis=-1)                 # (N,)
        return p[..., 2] - surface.vertex[2] - surface.sag(r)

    # ---------- bracketing ----------

    def bracket_roots(self, surface, origins, directions):
        """
        Coarse bracket search along each ray to find [a,b] where F changes sign.
        origins, directions: (N, 3)
        returns:
            hit_mask: (N,) bool, True where a sign change exists
            a, b: (N,) floats, bracket endpoints (NaN where no hit)
        """
        N = origins.shape[0]
        t_grid = np.linspace(0.0, self.t_max, self.bracket_samples)   # (S,)
        S = t_grid.size

        # Evaluate F at each t for all rays: shape (S, N)
        F_vals = np.empty((S, N), dtype=float)
        for s, t in enumerate(t_grid):
            F_vals[s] = self.F(surface, origins, directions, t)

        # sign changes along t: shape (S-1, N)
        sign_prod = np.sign(F_vals[:-1]) * np.sign(F_vals[1:])
        crosses = sign_prod <= 0   # True where there's a sign change

        # For each ray, pick first index where crossing occurs
        hit_mask = crosses.any(axis=0)                  # (N,)
        idx_lo = np.where(hit_mask, crosses.argmax(axis=0), -1)  # (N,)

        a = np.full(N, np.nan, dtype=float)
        b = np.full(N, np.nan, dtype=float)
        valid = idx_lo >= 0
        a[valid] = t_grid[idx_lo[valid]]
        b[valid] = t_grid[idx_lo[valid] + 1]

        return hit_mask, a, b

    # ---------- refinement ----------

    def refine_root(self, surface, origins, directions, a, b, hit_mask):
        """
        Fixed-iteration bisection refinement on [a,b] for each ray that has a bracket.
        a, b: (N,)
        hit_mask: (N,) bool
        returns: t_hit: (N,) with NaN where no hit
        """
        t_lo = a.copy()
        t_hi = b.copy()

        for _ in range(self.refine_iters):
            t_mid = 0.5 * (t_lo + t_hi)
            f_lo = self.F(surface, origins, directions, t_lo)
            f_mid = self.F(surface, origins, directions, t_mid)

            # Decide which half to keep: if f_lo * f_mid <= 0, root is in [lo, mid]
            same_sign = f_lo * f_mid > 0
            t_lo = np.where(same_sign, t_mid, t_lo)
            t_hi = np.where(same_sign, t_hi, t_mid)

        t_hit = 0.5 * (t_lo + t_hi)
        t_hit[~hit_mask] = np.nan
        return t_hit

    # ---------- normals ----------

    def surface_normal(self, surface, hit_points):
        """
        Finite-difference normal for sagged surface at hit_points.
        hit_points: (M, 3)
        returns: normals: (M, 3)
        """
        eps = self.eps
        x = hit_points[:, 0] - surface.vertex[0]
        y = hit_points[:, 1] - surface.vertex[1]

        # x-perturbation
        r_xp = np.sqrt((x + eps)**2 + y**2)
        r_xm = np.sqrt((x - eps)**2 + y**2)
        sag_xp = surface.sag(r_xp)
        sag_xm = surface.sag(r_xm)
        dsag_dx = (sag_xp - sag_xm) / (2 * eps)

        # y-perturbation
        r_yp = np.sqrt(x**2 + (y + eps)**2)
        r_ym = np.sqrt(x**2 + (y - eps)**2)
        sag_yp = surface.sag(r_yp)
        sag_ym = surface.sag(r_ym)
        dsag_dy = (sag_yp - sag_ym) / (2 * eps)

        normals = np.stack([-dsag_dx, -dsag_dy, np.ones_like(dsag_dx)], axis=1)
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        return normals

    def orient_normals(self, normals, directions):
        """
        Ensure normals point against incoming directions.
        normals, directions: (M,3)
        returns: (M,3)
        """
        dot = np.einsum('ij,ij->i', normals, directions)
        flip = dot > 0
        normals[flip] *= -1.0
        return normals

    # ---------- refraction (group) ----------

    def refract_group(self, directions, normals, n1, n2):
        """
        Vectorized Snell's law for a group of rays at one surface interface.
        directions, normals: (M,3), assumed normalized
        n1, n2: scalars
        returns: refracted_directions: (M,3), with NaN rows where TIR occurs
        """
        d = directions
        n = normals
        cos_i = -np.einsum('ij,ij->i', n, d)      # (M,)
        eta = n1 / n2
        k = 1.0 - eta**2 * (1.0 - cos_i**2)       # (M,)
        refracted = np.empty_like(d)
        # total internal reflection mask
        tir = k < 0.0
        # safe sqrt
        sqrt_k = np.sqrt(np.where(k > 0.0, k, 0.0))

        # eta * d + (eta * cos_i - sqrt(k)) * n
        refracted = eta * d + (eta * cos_i - sqrt_k)[:, None] * n

        # normalize where valid
        mag = np.linalg.norm(refracted, axis=1)
        valid = ~tir & (mag > 0)
        refracted[valid] /= mag[valid][:, None]
        refracted[~valid] = np.nan

        return refracted, tir

    # ---------- one surface for a group ----------

    def intersect_surface_group(self, surface, origins, directions):
        """
        Compute intersections of many rays with one surface.
        origins, directions: (N,3)
        returns:
            hit_mask: (N,) bool, True where ray hits within aperture
            t_hit: (N,) float, NaN where no hit
            hit_points: (N,3) float, NaN rows where no hit
            normals: (N,3) float, NaN rows where no hit
        """
        N = origins.shape[0]

        # 1. bracket
        root_mask, a, b = self.bracket_roots(surface, origins, directions)
        if not root_mask.any():
            # no sign change for any ray
            return np.zeros(N, dtype=bool), np.full(N, np.nan), np.full((N,3), np.nan), np.full((N,3), np.nan)

        # 2. refine
        t_hit = self.refine_root(surface, origins, directions, a, b, root_mask)  # (N,)

        # 3. hit points
        hit_points = origins + t_hit[:, None] * directions                      # (N,3)

        # 4. aperture check
        xy = hit_points[:, :2] - surface.vertex[:2]
        r = np.linalg.norm(xy, axis=1)
        aperture_mask = r <= (surface.diameter / 2.0)
        hit_mask = root_mask & aperture_mask

        # 5. normals only where hit
        normals = np.full((N, 3), np.nan, dtype=float)
        if hit_mask.any():
            hp = hit_points[hit_mask]
            n = self.surface_normal(surface, hp)
            n = self.orient_normals(n, directions[hit_mask])
            normals[hit_mask] = n

        # set invalid hits to NaN
        t_hit[~hit_mask] = np.nan
        hit_points[~hit_mask] = np.nan

        return hit_mask, t_hit, hit_points, normals

    # ---------- high-level trace ----------

    def trace_group(self, lenses, origins, directions, refracted_length=300.0):
        """
        Trace a group of rays through an ordered list of Lens objects.

        lenses: list of Lens, each with .surfaces (front-to-back).
        origins, directions: (N,3) initial ray positions and unit directions.

        returns:
            paths: (S, N, 3) array of ray positions at each step (including start)
            final_origins: (N,3)
            final_directions: (N,3)
        """
        origins = np.asarray(origins, dtype=float).reshape(-1, 3)
        directions = np.asarray(directions, dtype=float).reshape(-1, 3)

        N = origins.shape[0]
        # normalize directions
        mags = np.linalg.norm(directions, axis=1)
        if np.any(mags == 0):
            raise ValueError("direction vectors cannot be zero")
        directions = directions / mags[:, None]

        # collect surfaces in order
        surfaces = [s for lens in lenses for s in lens.surfaces]

        # path history: list of (N,3)
        path_list = [origins.copy()]

        for surface in surfaces:
            hit_mask, t_hit, hit_points, normals = self.intersect_surface_group(surface, origins, directions)

            if not hit_mask.any():
                # no ray hits this surface, propagate all rays forward and stop
                origins = origins + refracted_length * directions
                path_list.append(origins.copy())
                break

            # update origins for hit rays to their hit points
            origins[hit_mask] = hit_points[hit_mask]

            # refract only hit rays
            new_dirs, tir = self.refract_group(directions[hit_mask], normals[hit_mask], surface.n1, surface.n2)

            # mark TIR rays as having no new direction; here we just leave them as NaN
            # you could alternatively reflect them or stop them
            directions[hit_mask] = new_dirs

            path_list.append(origins.copy())

        paths = np.stack(path_list, axis=0)  # (S, N, 3)
        return paths, origins, directions
    
import numpy as np
import matplotlib.pyplot as plt

# assume these are imported from your codebase
from elements.surfaces import SphericalSurface
from dataclasses import dataclass
from typing import List

@dataclass
class Lens:
    surfaces: List  # ordered list of surfaces, front to back

# ---- Tracer class goes here (exactly as in previous answer) ----
# from tracer import Tracer  # if you put it in its own module


def plot_lens_and_rays(lenses, paths, max_r=None):
    """
    lenses: list[Lens]
    paths: (S, N, 3) array from Tracer.trace_group
    """
    fig, ax = plt.subplots(figsize=(10, 7))

    # background / grid styling (similar to your existing code)
    DARK_BG = '#0a0b0c'
    LIGHT_BG = '#ffffff'
    AXIS_COL = '#000000'
    GRID_COL = "#cccccc"

    fig.patch.set_facecolor(LIGHT_BG)
    ax.set_facecolor(LIGHT_BG)
    ax.grid(color=GRID_COL, linewidth=0.4, zorder=0)
    for spine in ax.spines.values():
        spine.set_color(GRID_COL)
    ax.tick_params(axis='x', colors=GRID_COL)
    ax.tick_params(axis='y', colors=GRID_COL)
    ax.axhline(0, color=AXIS_COL, lw=0.5, alpha=0.35, zorder=1)

    # ---- draw surfaces ----
    all_surfaces = [s for lens in lenses for s in lens.surfaces]
    if max_r is None:
        max_r = max(s.diameter for s in all_surfaces) / 2.0

    n = 400
    r = np.linspace(0, max_r, n)
    for lens in lenses:
        surf_zprofiles = []
        for surface in lens.surfaces:
            z = np.array([surface.sag(ri) for ri in r]) + surface.vertex[2]
            surf_zprofiles.append(z)
            ax.plot(z,  r, lw=0.5, color='black', alpha=0.9)
            ax.plot(z, -r, lw=0.5, color='black', alpha=0.9)

        # fill glass between surfaces in this lens
        for i in range(1, len(lens.surfaces)):
            z_prev = surf_zprofiles[i - 1]
            z_curr = surf_zprofiles[i]
            ax.fill_betweenx( r, z_prev, z_curr, color='lightblue', alpha=0.3)
            ax.fill_betweenx(-r, z_prev, z_curr, color='lightblue', alpha=0.3)

    # ---- draw rays using paths ----
    S, N, _ = paths.shape
    colors = ['#4dbf6b', '#ff6b6b', '#4d96ff', '#ffaa00', '#aa66cc', '#ff4444']

    for i in range(N):
        p = paths[:, i, :]  # (S, 3) – sequence of points for ray i
        # you may have NaNs for rays that stopped early; mask them
        mask = ~np.isnan(p[:, 0])
        if not np.any(mask):
            continue
        z = p[mask, 2]
        y = p[mask, 1]
        color = colors[i % len(colors)]
        ax.plot(z, y, color=color, lw=0.8, alpha=0.9)

    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel('Z')
    ax.set_ylabel('Radius / Y')
    ax.set_title('Vectorized Ray Propagation with Tracer')
    plt.tight_layout()
    return fig, ax


if __name__ == '__main__':
    # ---- build lenses as in your engine.py ----
    lens1 = Lens(surfaces=[
        SphericalSurface(center=[0, 0, 40], radius=60,  n1=1.0, n2=1.5, diameter=50.0),
        SphericalSurface(center=[0, 0, 55], radius=-60, n1=1.5, n2=1.0, diameter=50.0),
    ])

    lens2 = Lens(surfaces=[
        SphericalSurface(center=[0, 0, 80], radius=40,  n1=1.0, n2=1.5, diameter=40.0),
        SphericalSurface(center=[0, 0, 97], radius=-40, n1=1.5, n2=1.8, diameter=40.0),
        SphericalSurface(center=[0, 0, 100], radius=-120, n1=1.8, n2=1.0, diameter=40.0),
    ])

    lenses = [lens1, lens2]

    # ---- initial rays (matching your existing setup) ----
    origins = np.array([
        [0,   0, 0],
        [0,   0, 0],
        [0,   0, 0],
        [0,   5, 0],
        [0,   5, 0],
        [0,   5, 0],
        [0,  -5, 0],
        [0,  -5, 0],
        [0,  -5, 0],
        [0,  15, 0],
        [0,  15, 0],
        [0,  15, 0],
    ], dtype=float)

    directions = np.array([
        [0,  0.3, 1],
        [0,  0.0, 1],
        [0, -0.3, 1],
        [0,  0.3, 1],
        [0,  0.0, 1],
        [0, -0.3, 1],
        [0,  0.3, 1],
        [0,  0.0, 1],
        [0, -0.3, 1],
        [0,  0.3, 1],
        [0,  0.0, 1],
        [0, -0.3, 1],
    ], dtype=float)

    # ---- trace with Tracer ----
    tracer = Tracer(t_max=200.0, bracket_samples=256, refine_iters=10, eps=1e-6)
    paths, final_origins, final_dirs = tracer.trace_group(lenses, origins, directions)

    # ---- plot result ----
    fig, ax = plot_lens_and_rays(lenses, paths, max_r=None)
    print(paths)
    plt.show()