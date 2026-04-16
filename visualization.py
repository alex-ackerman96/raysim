from matplotlib import pyplot as plt
import numpy as _np_cpu
from backend import np, BACKEND, to_cpu
from typing import Union, List
from dataclasses import dataclass
from elements.surfaces import Surface
from rays.ray import Ray, RayGroup


def wavelength_nm_to_rgb(wl):
    """
    Approximate sRGB triple (0-1) for wavelength l in nm, valid ~380-780 nm.
    Outside this range returns (0,0,0).
    """
    wl = float(wl)
    if wl < 380 or wl > 780:
        return (0.0, 0.0, 0.0)

    if 380 <= wl < 440:
        r = -(wl - 440.0) / (440.0 - 380.0)
        g = 0.0
        b = 1.0
    elif 440 <= wl < 490:
        r = 0.0
        g = (wl - 440.0) / (490.0 - 440.0)
        b = 1.0
    elif 490 <= wl < 510:
        r = 0.0
        g = 1.0
        b = -(wl - 510.0) / (510.0 - 490.0)
    elif 510 <= wl < 580:
        r = (wl - 510.0) / (580.0 - 510.0)
        g = 1.0
        b = 0.0
    elif 580 <= wl < 645:
        r = 1.0
        g = -(wl - 645.0) / (645.0 - 580.0)
        b = 0.0
    else:  # 645-780 nm
        r = 1.0 - (wl - 645.0) / (1000.0 - 645.0)
        g = 0.0
        b = 0.0

    if 380 <= wl < 420:
        factor = 0.3 + 0.7 * (wl - 380.0) / (420.0 - 380.0)
    elif 420 <= wl <= 700:
        factor = 1.0
    elif 700 < wl <= 780:
        factor = 0.3 + 0.7 * (780.0 - wl) / (780.0 - 700.0)
    else:
        factor = 0.0

    gamma = 0.8

    def correct(c):
        if c <= 0.0:
            return 0.0
        return (c * factor) ** gamma

    return (correct(r), correct(g), correct(b))


@dataclass
class Lens:
    surfaces: List  # ordered list of surfaces, front to back


class Plotter:
    """
    Visualize ray paths and lens surfaces in a 2D cross-sectional plot.
    """
    def __init__(self, rays: Union[Ray, RayGroup], elements: Union[Lens, list], *args, **kwargs):
        self.rays     = rays
        # Convert paths to CPU once at construction — matplotlib always needs CPU arrays
        self.paths    = to_cpu(rays.ray_paths)
        self.elements = elements
        self.lenses   = self.elements
        self.max_r    = None
        self.colors   = "wavelength"

    def set_focalpoint_visible(self, visible=True):
        pass

    def set_principal_planes_visible(self, visible=True):
        pass

    def set_ray_paths_visible(self, visible=True):
        pass

    def set_ray_colors(self, color_map='wavelength'):
        pass

    def plot_cross_section(self):
        """
        Plot 2D cross-section of ray paths through lens system.
        paths shape: (S, N, 3)
        """
        fig, ax = plt.subplots(figsize=(10, 7))

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

        # paths is already CPU NumPy (converted in __init__)
        S, N, _ = self.paths.shape
        fallback_colors = ['#4dbf6b']

        wavelengths_cpu = to_cpu(self.rays.wavelengths) if self.rays.wavelengths is not None else None

        for i in range(N):
            p    = self.paths[:, i, :]              # (S, 3) CPU
            mask = ~_np_cpu.isnan(p[:, 0])
            if not mask.any():
                continue
            z = p[mask, 2]
            y = p[mask, 1]
            if self.colors == 'wavelength' and wavelengths_cpu is not None:
                wl    = float(wavelengths_cpu[i])
                color = wavelength_nm_to_rgb(wl)
            else:
                color = fallback_colors[i % len(fallback_colors)]
            ax.plot(z, y, color=color, lw=0.8, alpha=0.5)

        # ---- draw surfaces ----
        all_surfaces = [s for lens in self.lenses for s in lens.surfaces]
        if self.max_r is None:
            self.max_r = max(s.diameter for s in all_surfaces) / 2.0

        n_pts = 4000

        for lens in self.lenses:
            surf_zprofiles = []
            r_max_prev     = None
            z_edge_prev    = None

            for surface in lens.surfaces:
                r_arr = _np_cpu.linspace(0, surface.diameter / 2, n_pts)
                # sag may return CuPy array — convert to CPU
                sag_vals = to_cpu(surface.sag(r_arr)) if BACKEND == 'cupy' else surface.sag(r_arr)
                z_arr    = _np_cpu.asarray(sag_vals) + float(surface.vertex[2])
                surf_zprofiles.append(z_arr)

                ax.plot( z_arr,  r_arr, lw=0.5, color='black', alpha=0.9)
                ax.plot( z_arr, -r_arr, lw=0.5, color='black', alpha=0.9)

                # connect edge of this surface to edge of previous surface (lens rim)
                if r_max_prev is not None:
                    ax.plot([z_edge_prev, z_arr[-1]], [ r_max_prev,  r_arr[-1]], lw=0.5, color='black', alpha=0.9)
                    ax.plot([z_edge_prev, z_arr[-1]], [-r_max_prev, -r_arr[-1]], lw=0.5, color='black', alpha=0.9)

                r_max_prev  = float(r_arr[-1])
                z_edge_prev = float(z_arr[-1])

            # fill glass between surfaces in this lens
            for i in range(1, len(lens.surfaces)):
                z_prev = surf_zprofiles[i - 1]
                z_curr = surf_zprofiles[i]
                r_fill = _np_cpu.linspace(0, lens.surfaces[i].diameter / 2, n_pts)
                ax.fill_betweenx( r_fill, z_prev, z_curr, color='lightblue', alpha=0.8)
                ax.fill_betweenx(-r_fill, z_prev, z_curr, color='lightblue', alpha=0.8)

        ax.set_xlim(0, None)
        ax.set_ylim(-1.25 * self.max_r, 1.25 * self.max_r)
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('Z')
        ax.set_ylabel('Radius / Y')
        ax.set_title('Ray Propagation Cross-Section')
        plt.tight_layout()
        return fig, ax

    def show(self):
        plt.show()


class NormalPlaneMap:
    """
    Visualize ray distributions in a plane normal to the optical axis.
    """
    def __init__(self, rays: RayGroup, z: float = 0,
                 x_extents: tuple = (-5, 5), y_extents: tuple = (-5, 5),
                 render_type: str = "points", reference_axis: str = "main"):
        self.rays            = rays
        self.ray_wavelengths = to_cpu(rays.wavelengths) if rays.wavelengths is not None \
                               else _np_cpu.full(len(rays), 550.0)
        self.location        = z
        self.xmin            = x_extents[0]
        self.xmax            = x_extents[1]
        self.ymin            = y_extents[0]
        self.ymax            = y_extents[1]
        self.render_type     = render_type
        self.reference_axis  = reference_axis
        self.xy              = None   # set by xy_at_z()

    def xy_at_z(self, update_paths=True, require_forward=True, atol=1e-12):
        """
        Interpolate x,y for each ray at plane z using traced path vertices.
        ray_paths shape: (S, N, 3)
        """
        if self.rays.ray_paths is None:
            raise ValueError("RayGroup has no ray_paths defined. Run tracing first.")

        # Pull to CPU once for the serial interpolation loop
        paths = _np_cpu.asarray(to_cpu(self.rays.ray_paths), dtype=float)
        if paths.ndim != 3 or paths.shape[2] != 3:
            raise ValueError("ray_paths must have shape (S, N, 3)")

        z    = float(self.location)
        S, N, _ = paths.shape

        out_pts = _np_cpu.full((N, 3), _np_cpu.nan, dtype=float)
        found   = _np_cpu.zeros(N, dtype=bool)

        for i in range(N):
            p           = paths[:, i, :]                        # (S, 3)
            valid_rows  = ~_np_cpu.isnan(p).any(axis=1)
            p_valid     = p[valid_rows]

            if len(p_valid) == 0:
                continue

            z_vals = p_valid[:, 2]

            # Check for exact match
            exact = _np_cpu.where(_np_cpu.isclose(z_vals, z, atol=atol))[0]
            if exact.size > 0:
                out_pts[i] = p_valid[exact[0]]
                found[i]   = True
                continue

            # Search for bracketing segment
            crossed = False
            for j in range(len(p_valid) - 1):
                p0, p1 = p_valid[j], p_valid[j + 1]
                z0, z1 = p0[2], p1[2]
                dz     = z1 - z0

                if _np_cpu.isclose(dz, 0.0, atol=atol):
                    continue

                if (z - z0) * (z - z1) <= 0:
                    u = (z - z0) / dz
                    if require_forward and u < -atol:
                        continue
                    pt    = p0 + u * (p1 - p0)
                    pt[2] = z
                    out_pts[i] = pt
                    found[i]   = True
                    crossed    = True
                    break

            if crossed:
                continue

            # Extrapolate from final segment
            if len(p_valid) >= 2:
                p0, p1 = p_valid[-2], p_valid[-1]
                dz     = p1[2] - p0[2]
                if not _np_cpu.isclose(dz, 0.0, atol=atol):
                    u = (z - p0[2]) / dz
                    if (not require_forward) or (u >= 1.0 - atol):
                        pt    = p0 + u * (p1 - p0)
                        pt[2] = z
                        out_pts[i] = pt
                        found[i]   = True

                        if update_paths:
                            valid_idx = _np_cpu.where(valid_rows)[0]
                            pt_gpu = np.asarray(pt)
                            self.rays.ray_paths[int(valid_idx[-1]), i, :] = pt_gpu

        # print(out_pts[:, :2])
        # print(found)

        # Store as CPU NumPy — all plotting methods expect CPU
        self.xy = out_pts[:, :2]

    def plot(self):
        """Scatter plot of ray hit positions at the normal plane."""
        if self.xy is None:
            raise ValueError("Call xy_at_z() before plot()")

        x      = self.xy[:, 0]   # already CPU from xy_at_z
        y      = self.xy[:, 1]
        colors = [wavelength_nm_to_rgb(float(wl)) for wl in self.ray_wavelengths]

        plt.figure()
        plt.scatter(x, y, marker='.', s=10, c=colors)
        plt.xlabel("x")
        plt.ylabel("y")
        plt.show()

    def histogram(self, bins=10):
        """2D histogram of ray hit positions at the normal plane."""
        if self.xy is None:
            raise ValueError("Call xy_at_z() before histogram()")

        x = self.xy[:, 0]   # already CPU from xy_at_z
        y = self.xy[:, 1]

        plt.figure()
        plt.hist2d(x, y, bins=bins, cmap='viridis',
                   range=[[self.xmin, self.xmax], [self.ymin, self.ymax]])
        plt.xlabel("x")
        plt.ylabel("y")
        plt.colorbar(label='Count in bin')
        plt.show()


if __name__ == "__main__":
    print(wavelength_nm_to_rgb(400))
    print(wavelength_nm_to_rgb(550))
    print(wavelength_nm_to_rgb(700))
