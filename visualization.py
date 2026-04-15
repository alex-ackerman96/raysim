from matplotlib import pyplot as plt
import numpy as np
from typing import Union, List
from dataclasses import dataclass
from elements.surfaces import Surface
# from elements.lenses import Lens
from rays.ray import Ray, RayGroup

def wavelength_nm_to_rgb(wl):
    """
    Approximate sRGB triple (0–1) for wavelength l in nm, valid ~400–700 nm.
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
    else:  # 645–1000 nm
        r = 1.0 - (wl - 645.0) / (1000.0 - 645.0)
        g = 0.0
        b = 0.0

    # Intensity factor near vision limits
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
    Class for visualizing ray paths and lens surfaces in a 2D cross-sectional plot, or ray distributions in a plane normal to the optical axis.
    """
    def __init__(self, rays: Union[Ray, RayGroup], elements: Union[Lens, list], *args, **kwargs):
        self.rays = rays
        self.paths = rays.ray_paths
        self.elements = elements
        self.lenses = self.elements # if elements is a list of lenses, otherwise wrap in a list
        self.max_r = None
        self.colors = "wavelength" 

    def set_focalpoint_visible(self, visible=True):
        # Placeholder for toggling focal point visibility in the plot
        pass

    def set_principal_planes_visible(self, visible=True):
        # Placeholder for toggling principal plane visibility in the plot
        pass

    def set_ray_paths_visible(self, visible=True):
        # Placeholder for toggling ray path visibility in the plot
        pass

    def set_ray_colors(self, color_map='wavelength'):
        # Placeholder for setting ray colors based on a color map (e.g., wavelength)
        pass

    def plot_cross_section(self):
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
        S, N, _ = self.paths.shape
        colors = ['#4dbf6b']

        for i in range(N):
            p = self.paths[:, i, :]  # (S, 3) – sequence of points for ray i
            # you may have NaNs for rays that stopped early; mask them
            mask = ~np.isnan(p[:, 0])
            if not np.any(mask):
                continue
            z = p[mask, 2]
            y = p[mask, 1]
            if self.colors == 'wavelength' and self.rays.wavelengths is not None:
                wl = self.rays.wavelengths[i]
                color = wavelength_nm_to_rgb(wl)
            else:
                color = colors[i % len(colors)]
            ax.plot(z, y, color=color, lw=0.8, alpha=0.9)

        # ---- draw surfaces ----
        all_surfaces = [s for lens in self.lenses for s in lens.surfaces]
        if self.max_r is None:
            self.max_r = max(s.diameter for s in all_surfaces) / 2.0

        n = 4000
        # r = np.linspace(0, max_r, n)
        for lens in self.lenses:
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
        ax.set_ylim(-1.25*self.max_r, 1.25*self.max_r)
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('Z')
        ax.set_ylabel('Radius / Y')
        ax.set_title('Vectorized Ray Propagation with Tracer')
        plt.tight_layout()
        return fig, ax
   
    def show(self):
        plt.show()

class NormalPlaneMap:
    """
    Class for visualizing ray distributions in a plane normal to the optical axis.
    """
    def __init__(self, rays: RayGroup, z: float = 0, x_extents: tuple = (-2, 2), y_extents: tuple = (-2, 2), render_type: str = "points", reference_axis: str = "main"):
        self.rays = rays
        self.ray_wavelengths = rays.wavelengths if rays.wavelengths is not None else np.full(len(rays), 550.0)  # default to green if no wavelengths
        self.location = z
        self.xmin = x_extents[0]
        self.xmax = x_extents[1]
        self.ymin = y_extents[0]
        self.ymax = y_extents[1]
        self.render_type = render_type # "points" for scatter plot, "heatmap" for density plot
        self.reference_axis = reference_axis # name of optical axis which plane is normal to; "main" is the default optical axis

    def xy_at_z(self, update_paths=True, require_forward=True, atol=1e-12):
        """
        Interpolate x,y for each ray at plane z using traced path vertices in self.ray_paths.

        self.ray_paths is assumed to have shape (S, N, 3), where:
            S = number of path vertices per ray
            N = number of rays

        For each ray:
        - If one segment crosses z, interpolate within that segment.
        - If the path already contains a vertex at z, use that point.
        - If the path does not reach z, extend the final segment to z and optionally
        overwrite the final stored point with the extrapolated point.

        Parameters
        ----------
        z : float
            Target z-plane.
        update_paths : bool, default True
            If True, overwrite the last point of rays that must be extended to reach z.
        require_forward : bool, default True
            If True, only allow interpolation/extrapolation in the forward direction of the
            segment (segment parameter u >= 0). This is usually what you want.
        atol : float, default 1e-12
            Tolerance for detecting dz == 0 or exact z matches.

        Returns
        -------
        xy : (N, 2) ndarray
            Interpolated [x, y] for each ray at z. Invalid rays are NaN.
        points : (N, 3) ndarray
            Full interpolated/extrapolated [x, y, z] points.
        found_mask : (N,) bool
            True where a valid point at z was found or extrapolated.
        """
        if self.rays.ray_paths is None:
                raise ValueError("RayGroup has no ray_paths defined. Run tracing first.")

        paths = np.asarray(self.rays.ray_paths, dtype=float)
        if paths.ndim != 3 or paths.shape[2] != 3:
            raise ValueError("ray_paths must have shape (S, N, 3)")

        z = self.location
        S, N, _ = paths.shape

        out_pts = np.full((N, 3), np.nan, dtype=float)
        found = np.zeros(N, dtype=bool)

        for i in range(N):
            p = paths[:, i, :]  # (S,3)
            valid_rows = ~np.isnan(p).any(axis=1)
            p = p[valid_rows]

            if len(p) == 0:
                continue

            z_vals = p[:, 2]
            exact = np.where(np.isclose(z_vals, z, atol=atol))[0]
            if exact.size > 0:
                out_pts[i] = p[exact[0]]
                found[i] = True
                continue

            crossed = False
            for j in range(len(p) - 1):
                p0 = p[j]
                p1 = p[j + 1]
                z0 = p0[2]
                z1 = p1[2]
                dz = z1 - z0

                if np.isclose(dz, 0.0, atol=atol):
                    continue

                if (z - z0) * (z - z1) <= 0:
                    u = (z - z0) / dz
                    if require_forward and u < -atol:
                        continue
                    pt = p0 + u * (p1 - p0)
                    pt[2] = z
                    out_pts[i] = pt
                    found[i] = True
                    crossed = True
                    break

            if crossed:
                continue

            if len(p) >= 2:
                p0 = p[-2]
                p1 = p[-1]
                dz = p1[2] - p0[2]

                if not np.isclose(dz, 0.0, atol=atol):
                    u = (z - p0[2]) / dz
                    if (not require_forward) or (u >= 1.0 - atol):
                        pt = p0 + u * (p1 - p0)
                        pt[2] = z
                        out_pts[i] = pt
                        found[i] = True

                        if update_paths:
                            # overwrite final valid stored point in the RayGroup's paths
                            valid_idx = np.where(valid_rows)[0]
                            self.rays.ray_paths[valid_idx[-1], i, :] = pt

            elif len(p) == 1:
                continue

        print(out_pts[:, :2])
        print(found)

        self.xy = out_pts[:, :2]

    def plot(self):
        # Placeholder for plotting logic
        x = self.xy[:, 0]
        y = self.xy[:, 1]

        plt.figure()
        colors = [wavelength_nm_to_rgb(wl) for wl in self.ray_wavelengths]
        plt.scatter(x, y, marker='.', s=10, c=colors)
        plt.xlabel("x")
        plt.ylabel("y")
        # plt.gca().set_aspect('equal', adjustable='box')  # optional, equal scaling
        plt.show()

    def histogram(self, bins=10):
        # Placeholder for histogram logic
        x = self.xy[:, 0]
        y = self.xy[:, 1]

        plt.figure()
        plt.hist2d(x, y, bins=bins, cmap='viridis', range=[[self.xmin, self.xmax], [self.ymin, self.ymax]])
        plt.xlabel("x")
        plt.ylabel("y")
        plt.colorbar(label='Count in bin')
        plt.show()

if __name__ == "__main__":
    print(wavelength_nm_to_rgb(400))  # Should be violet