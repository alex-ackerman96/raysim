import numpy as np
import matplotlib.pyplot as plt
from elements.surfaces import AsphericSurface, PlanarSurface, SphericalSurface
from rays.ray import RayGroup, Ray, IdealLambertianSource3D, IdealLambertianSource2D, TruncatedLambertianSource2D
from dataclasses import dataclass
from typing import List

@dataclass
class Lens:
    surfaces: List  # ordered list of surfaces, front to back

    def load_from_file(self, filename):
        # Placeholder for loading lens data from a file (e.g., JSON, CSV)
        pass  


class Tracer:

    def __init__(self, t_max=200.0, bracket_samples=256, refine_iters=10, eps=1e-6):
        self.t_max = float(t_max)
        self.bracket_samples = int(bracket_samples)
        self.refine_iters = int(refine_iters)
        self.eps = float(eps)
    # ----------------- adapters: objects -> arrays -----------------

    def _from_ray(self, ray: Ray):
        origins = ray.origin.reshape(1, 3)
        directions = ray.direction.reshape(1, 3)
        return origins, directions

    def _from_raygroup(self, group: RayGroup):
        if group.ray_origins is None or group.ray_directions is None:
            raise ValueError("RayGroup has no origins/directions set")
        origins = np.asarray(group.ray_origins, dtype=float).reshape(-1, 3)
        directions = np.asarray(group.ray_directions, dtype=float).reshape(-1, 3)
        return origins, directions
    
        # ----------------- adapters: arrays -> objects -----------------

    def _update_ray_from_arrays(self, ray: Ray, paths, final_origins, final_dirs):
        """
        paths: (S, 1, 3), final_origins: (1,3), final_dirs: (1,3)
        """
        # update origin/direction
        ray.set_state(final_origins[0], final_dirs[0])
        # rebuild path from paths (S,1,3)
        ray.path = [paths[s, 0, :].copy() for s in range(paths.shape[0])]

    def _update_raygroup_from_arrays(self, group: RayGroup, paths, final_origins, final_dirs):
        """
        paths: (S, N, 3), final_origins: (N,3), final_dirs: (N,3)
        """
        group.ray_origins = final_origins
        group.ray_directions = final_dirs
        group.ray_paths = paths  # store full history at group level

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

    def bracket_roots(self, surface, origins, directions,
                    base_pad=5.0,
                    samples_per_pass=128,
                    max_expansions=10,
                    growth=1.8,
                    near_zero_tol=1e-7,
                    debug=False):
        N = origins.shape[0]
        z_v = float(surface.vertex[2])

        hit_mask = np.zeros(N, dtype=bool)
        a = np.full(N, np.nan, dtype=float)
        b = np.full(N, np.nan, dtype=float)

        oz = origins[:, 2]
        dz = directions[:, 2]

        valid = np.abs(dz) > 1e-12
        t_plane = np.full(N, np.nan, dtype=float)
        t_plane[valid] = (z_v - oz[valid]) / dz[valid]
        valid &= (t_plane >= 0.0)

        for i in np.where(valid)[0]:
            d_i = directions[i]
            o_i = origins[i:i+1]
            d_i2 = directions[i:i+1]

            cosz = abs(d_i[2])
            pad = base_pad / max(cosz, 0.1)

            found = False
            best_a = np.nan
            best_b = np.nan
            best_t = np.nan
            best_absF = np.inf

            for _ in range(max_expansions):
                left = max(0.0, t_plane[i] - pad)
                right = t_plane[i] + pad
                t_grid = np.linspace(left, right, samples_per_pass)

                F_vals = np.array([self.F(surface, o_i, d_i2, t)[0] for t in t_grid], dtype=float)

                finite = np.isfinite(F_vals)
                if np.count_nonzero(finite) < 2:
                    pad *= growth
                    continue

                t_valid = t_grid[finite]
                f_valid = F_vals[finite]
                absf = np.abs(f_valid)

                jmin = np.argmin(absf)
                if absf[jmin] < best_absF:
                    best_absF = absf[jmin]
                    best_t = t_valid[jmin]

                zero_idx = np.where(absf < near_zero_tol)[0]
                if zero_idx.size > 0:
                    j = zero_idx[0]
                    j0 = max(j - 1, 0)
                    j1 = min(j + 1, len(t_valid) - 1)
                    best_a = t_valid[j0]
                    best_b = t_valid[j1]
                    found = True
                    break

                sign_prod = np.sign(f_valid[:-1]) * np.sign(f_valid[1:])
                crosses = np.where(sign_prod <= 0)[0]
                for j in crosses:
                    t_mid = 0.5 * (t_valid[j] + t_valid[j + 1])
                    p_mid = o_i[0] + t_mid * d_i2[0]
                    xy = p_mid[:2] - surface.vertex[:2]
                    r_mid = np.linalg.norm(xy)
                    if r_mid <= surface.diameter / 2.0:
                        best_a = t_valid[j]
                        best_b = t_valid[j + 1]
                        found = True
                        break

                if found:
                    break

                pad *= growth

            if (not found) and np.isfinite(best_t) and best_absF < near_zero_tol:
                best_a = max(0.0, best_t - 1e-3)
                best_b = best_t + 1e-3
                found = True

            if found:
                hit_mask[i] = True
                a[i] = best_a
                b[i] = best_b
            elif debug:
                print(f"[bracket miss] ray={i}, t_plane={t_plane[i]:.6f}, best_absF={best_absF:.3e}")

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
        eps0 = self.eps
        x = hit_points[:, 0] - surface.vertex[0]
        y = hit_points[:, 1] - surface.vertex[1]
        r = np.sqrt(x**2 + y**2)

        eps = np.maximum(eps0, 1e-3 * np.maximum(r, 1.0))

        r_xp = np.sqrt((x + eps)**2 + y**2)
        r_xm = np.sqrt((x - eps)**2 + y**2)
        sag_xp = surface.sag(r_xp)
        sag_xm = surface.sag(r_xm)
        dsag_dx = (sag_xp - sag_xm) / (2 * eps)

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

    def trace_group(self, lenses, origins, directions, output_z=None):
        # normalize input
        origins = np.asarray(origins, dtype=float).reshape(-1, 3).copy()
        directions = np.asarray(directions, dtype=float).reshape(-1, 3).copy()

        mags = np.linalg.norm(directions, axis=1)
        if np.any(mags == 0):
            raise ValueError("direction vectors cannot be zero")
        directions = directions / mags[:, None]

        N = origins.shape[0]
        surfaces = [s for lens in lenses for s in lens.surfaces]

        if output_z is None:
            # default output plane a little beyond last surface vertex
            output_z = max(s.vertex[2] for s in surfaces) + 20.0

        # all rays start active
        active = np.ones(N, dtype=bool)
        path_list = [origins.copy()]

        # march through each surface
        for surface in surfaces:
            if not np.any(active):
                break

            active_idx = np.where(active)[0]
            o_act = origins[active]
            d_act = directions[active]

            hit_mask_local, t_hit, hit_points, normals = self.intersect_surface_group(
                surface, o_act, d_act
            )
            ##########################################################################################################3
            # DEBUG: intersection stats
            print(
                f"Surface at z={surface.vertex[2]:.3f}: "
                f"{np.sum(hit_mask_local)} hits out of {o_act.shape[0]} active rays"
            )

            # --- deactivate misses at this surface ---
            miss_idx_global = active_idx[~hit_mask_local]
            active[miss_idx_global] = False

            # --- process hits ---
            if np.any(hit_mask_local):
                hit_idx_global = active_idx[hit_mask_local]

                # update positions at the surface
                origins[hit_idx_global] = hit_points[hit_mask_local]

                # compute refracted directions at this surface
                new_dirs, tir = self.refract_group(
                    d_act[hit_mask_local],
                    normals[hit_mask_local],
                    surface.n1,
                    surface.n2
                )
                ############################################################################################################
                # DEBUG: how many actually refract?
                old_dirs = d_act[hit_mask_local]
                delta = np.linalg.norm(new_dirs - old_dirs, axis=1)
                print(
                    f"    refract_group: {np.sum(delta > 1e-6)} changed, "
                    f"{np.sum(delta <= 1e-6)} unchanged, "
                    f"{np.sum(tir)} TIR"
                )

                # keep only non-TIR, finite directions
                valid_refract = (~tir) & (~np.isnan(new_dirs).any(axis=1))

                # update directions for valid refracted rays
                refr_idx_global = hit_idx_global[valid_refract]
                directions[refr_idx_global] = new_dirs[valid_refract]

                # deactivate TIR / invalid rays
                tir_idx_global = hit_idx_global[~valid_refract]
                active[tir_idx_global] = False

            # record state after this surface
            path_list.append(origins.copy())

        # --- final propagation for all remaining active rays to output_z ---
        z0 = origins[:, 2]
        dz = directions[:, 2]

        final_points = origins.copy()
        valid = np.abs(dz) > 1e-12
        t_out = np.full(N, np.nan, dtype=float)
        t_out[valid] = (output_z - z0[valid]) / dz[valid]

        forward = valid & (t_out >= 0.0)
        final_points[forward] = origins[forward] + t_out[forward, None] * directions[forward]

        path_list.append(final_points.copy())
        origins = final_points

        paths = np.stack(path_list, axis=0)
        return paths, origins, directions
    

    def trace(self, lenses, rays, output_z=None):
        """
        Generic entry point: accepts a single Ray, a list[Ray], or a RayGroup.

        Returns:
            paths, final_origins, final_directions
        """
        if isinstance(rays, Ray):
            origins, directions = self._from_ray(rays)
            paths, final_origins, final_dirs = self.trace_group(
                lenses, origins, directions, output_z=output_z
            )
            self._update_ray_from_arrays(rays, paths, final_origins, final_dirs)
            return paths, final_origins, final_dirs

        if isinstance(rays, RayGroup):
            origins, directions = self._from_raygroup(rays)
            paths, final_origins, final_dirs = self.trace_group(
                lenses, origins, directions, output_z=output_z
            )
            self._update_raygroup_from_arrays(rays, paths, final_origins, final_dirs)
            return paths, final_origins, final_dirs

        if isinstance(rays, (list, tuple)) and all(isinstance(r, Ray) for r in rays):
            origins = np.vstack([r.origin for r in rays])
            directions = np.vstack([r.direction for r in rays])
            paths, final_origins, final_dirs = self.trace_group(
                lenses, origins, directions, output_z=output_z
            )

            S, N, _ = paths.shape
            for i, ray in enumerate(rays):
                ray.set_state(final_origins[i], final_dirs[i])
                ray.path = [paths[s, i, :].copy() for s in range(S)]

            return paths, final_origins, final_dirs

        raise TypeError("rays must be Ray, RayGroup, or list[Ray]")
    
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

    # ---- draw rays using paths ----
    S, N, _ = paths.shape
    colors = ['#4dbf6b']

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

    # ---- draw surfaces ----
    all_surfaces = [s for lens in lenses for s in lens.surfaces]
    if max_r is None:
        max_r = max(s.diameter for s in all_surfaces) / 2.0

    n = 4000
    # r = np.linspace(0, max_r, n)
    for lens in lenses:
        surf_zprofiles = []
        for surface in lens.surfaces:
            r = np.linspace(0, surface.diameter/2, n)
            z = np.array([surface.sag(ri) for ri in r]) + surface.vertex[2]
            surf_zprofiles.append(z)
            ax.plot(z,  r, lw=0.5, color='black', alpha=0.9)
            ax.plot(z, -r, lw=0.5, color='black', alpha=0.9)

        # fill glass between surfaces in this lens
        for i in range(1, len(lens.surfaces)):
            z_prev = surf_zprofiles[i - 1]
            z_curr = surf_zprofiles[i]
            ax.fill_betweenx( r, z_prev, z_curr, color='lightblue', alpha=0.8)
            ax.fill_betweenx(-r, z_prev, z_curr, color='lightblue', alpha=0.8)
    ax.set_xlim(0, None)
    ax.set_ylim(-1.25*max_r, 1.25*max_r)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel('Z')
    ax.set_ylabel('Radius / Y')
    ax.set_title('Vectorized Ray Propagation with Tracer')
    plt.tight_layout()
    return fig, ax


if __name__ == '__main__':

    lens1 = Lens(surfaces=[
        AsphericSurface(vertex=[0, 0, 90], radius=30, conic=-1.1, aspheric_coeffs=[0.15e-6, -0.15e-8, -1e-11], n1=1.0, n2=1.5, diameter=50.0),
        # SphericalSurface(center=[0, 0, 90], radius=60,  n1=1.0, n2=1.5, diameter=50.0),
        SphericalSurface(center=[0, 0, 105], radius=-100, n1=1.5, n2=1.0, diameter=50.0),
    ])

    # Singlet lens 2
    lens2 = Lens(surfaces=[
        SphericalSurface(center=[0, 0, 120], radius=40,  n1=1.0, n2=1.5, diameter=45.0),
        SphericalSurface(center=[0, 0, 140], radius=-40, n1=1.5, n2=1.3, diameter=45.0),
        SphericalSurface(center=[0, 0, 145], radius=-120, n1=1.3, n2=1.0, diameter=45.0),
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

    # g = RayGroup(rays)   # after you implement this
    g = TruncatedLambertianSource2D(origin=[0, 0, 0], num_rays=50, wavelength=500, distribution='deterministic', plane='yz', half_angle_deg=90)
    tracer = Tracer(t_max=400.0, bracket_samples=1024, refine_iters=15, eps=1e-6)

    i = 10  # ray index you want to inspect

    origin_i = g.ray_origins[i]
    direction_i = g.ray_directions[i]


    single_ray = Ray(origin=origin_i, direction=direction_i, wavelength=600)
    single_group = RayGroup(single_ray)

    paths_i, final_origins_i, final_dirs_i = tracer.trace([lens1, lens2], single_group, output_z=200.0)


    paths, final_origins, final_dirs = tracer.trace([lens1, lens2], g, output_z=200.0)

    i0 = i  # for example, replace with one of the visually "straight" rays
    print("PATH for ray", i0)
    print(paths[:, i0, :])

    # And check whether it was ever considered a hit at each surface:
    orig0 = g.ray_origins
    dir0 = g.ray_directions

    # Re-run a single-surface check on the asphere only
    orig = orig0[[i0]]
    dir_ = dir0[[i0]]
    hit_mask, t_hit, hit_points, normals = tracer.intersect_surface_group(
        lens1.surfaces[0], orig, dir_
    )
    print("hit_mask on S1 for ray", i0, ":", hit_mask)
    print("hit_points S1 for ray", i0, ":", hit_points)
    
    # ---- plot result ----
    fig, ax = plot_lens_and_rays([lens1, lens2], paths, max_r=None)
    # print(paths)
    plt.show()