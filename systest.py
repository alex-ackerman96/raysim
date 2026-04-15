from tracer import Tracer
from visualization import NormalPlaneMap
from rays.ray import Ray, RayGroup, IdealLambertianSource3D
from elements.surfaces import AsphericSurface, PlanarSurface, SphericalSurface
from dataclasses import dataclass
from typing import List

@dataclass
class Lens:
    surfaces: List  # ordered list of surfaces, front to back

    def load_from_file(self, filename):
        # Placeholder for loading lens data from a file (e.g., JSON, CSV)
        pass  

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
    Ray(origin=[-15, -15, 0], direction=[0,  0.3, 1]),
    Ray(origin=[-15, -15, 0], direction=[0,  0.0, 1]),
    Ray(origin=[-15, -15, 0], direction=[0, -0.3, 1]),
]

# g = RayGroup(rays)   # after you implement this
g = IdealLambertianSource3D(origin=[0, 0, 0], num_rays=10000, wavelength=500)
tracer = Tracer()
paths, final_origins, final_dirs = tracer.trace([lens1, lens2], g)

plane_map = NormalPlaneMap(rays=g, z=70)
plane_map.xy_at_z()
plane_map.plot()