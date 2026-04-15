import numpy as np
from elements.surfaces import AsphericSurface
from rays.ray import IdealLambertianSource2D
from tracer import Tracer, Lens

lens1 = Lens(surfaces=[AsphericSurface(vertex=[0, 0, 90], radius=30, conic=-1.1, aspheric_coeffs=[0.15e-6, -0.15e-8, -1e-11], n1=1.0, n2=1.5, diameter=40.0)])


g = IdealLambertianSource2D(origin=[0,0,0], num_rays=100, wavelength=500,
                             distribution='deterministic', plane='yz')
tracer = Tracer(t_max=400.0, bracket_samples=1024, refine_iters=15, eps=1e-6)

origins_launch = np.array(g.ray_origins, dtype=float).copy()
dirs_launch    = np.array(g.ray_directions, dtype=float).copy()

surf = lens1.surfaces[0]
i = 10
o = origins_launch[[i]]
d = dirs_launch[[i]]

print(f"ray 10 origin:    {o[0]}")
print(f"ray 10 direction: {d[0]}")
print(f"surface vertex:   {surf.vertex}")
print(f"surface radius:   {surf.radius}")
print(f"surface diameter: {surf.diameter}")
print(f"sag(0) = {surf.sag(0.0)}")
print(f"sag(10) = {surf.sag(10.0)}")
print(f"sag(20) = {surf.sag(20.0)}")

t_grid = np.linspace(0.0, 400.0, 5000)
F_vals = np.array([tracer.F(surf, o, d, t)[0] for t in t_grid])

finite = np.isfinite(F_vals)
print(f"\nfinite samples: {finite.sum()} / {len(t_grid)}")
print(f"F min = {np.nanmin(F_vals):.6f}")
print(f"F max = {np.nanmax(F_vals):.6f}")
print(f"min|F| = {np.nanmin(np.abs(F_vals)):.6f}  at t = {t_grid[np.nanargmin(np.abs(F_vals))]:.4f}")

sign_changes = np.where(np.sign(F_vals[:-1]) != np.sign(F_vals[1:]))[0]
print(f"sign changes at t indices: {sign_changes}")
if sign_changes.size > 0:
    for idx in sign_changes:
        print(f"  t = [{t_grid[idx]:.4f}, {t_grid[idx+1]:.4f}]  F = [{F_vals[idx]:.6f}, {F_vals[idx+1]:.6f}]")