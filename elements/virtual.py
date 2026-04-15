import numpy as np
from rays.ray import RayGroup

class NormalPlaneMap:
    """
    plane normal to a specified optical axis (default "main") at a given z location, with specified x and y extents for plotting. Interpolates ray paths to find x,y coordinates at the plane.
    """
    def __init__(self, rays: RayGroup, z: float = 0, x_extents: tuple = (-50, 50), y_extents: tuple = (-50, 50), reference_axis: str = "main"):
        self.rays = rays
        self.ray_wavelengths = rays.wavelengths if rays.wavelengths is not None else np.full(len(rays), 550.0)  # default to green if no wavelengths
        self.location = z
        self.xmin = x_extents[0]
        self.xmax = x_extents[1]
        self.ymin = y_extents[0]
        self.ymax = y_extents[1]
        self.reference_axis = reference_axis # name of optical axis which plane is normal to; "main" is the default optical axis
    
    def get_points(self):
        xy = self._xy_at_z()

    def _xy_at_z(self, update_paths=True, require_forward=True, atol=1e-12):
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

            # Drop invalid rows if any were stored as NaN
            valid_rows = ~np.isnan(p).any(axis=1)
            p = p[valid_rows]

            if len(p) == 0:
                continue

            # 1) Exact vertex match
            z_vals = p[:, 2]
            exact = np.where(np.isclose(z_vals, z, atol=atol))[0]
            if exact.size > 0:
                out_pts[i] = p[exact[0]]
                found[i] = True
                continue

            # 2) Search for segment crossing
            crossed = False
            for j in range(len(p) - 1):
                p0 = p[j]
                p1 = p[j + 1]
                z0 = p0[2]
                z1 = p1[2]
                dz = z1 - z0

                if np.isclose(dz, 0.0, atol=atol):
                    continue

                # Does target z lie on this segment?
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

            # 3) Path does not reach z: extend final segment
            if len(p) >= 2:
                p0 = p[-2]
                p1 = p[-1]
                dz = p1[2] - p0[2]

                if not np.isclose(dz, 0.0, atol=atol):
                    u = (z - p0[2]) / dz

                    # Require the target to be beyond the final point in the same direction
                    # as the last segment, not "behind" it.
                    if (not require_forward) or (u >= 1.0 - atol):
                        pt = p0 + u * (p1 - p0)
                        pt[2] = z
                        out_pts[i] = pt
                        found[i] = True

                        if update_paths:
                            # overwrite final valid stored point in the master array
                            valid_idx = np.where(valid_rows)[0]
                            self.ray_paths[valid_idx[-1], i, :] = pt

            elif len(p) == 1:
                # Cannot extrapolate from only one point
                continue
        print(out_pts[:, :2])
        print(found)

        self.xy = out_pts[:, :2]