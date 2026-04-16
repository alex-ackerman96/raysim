import os
# Point CuPy to the CUDA bin directory so it finds nvrtc.dll
cuda_bin = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin"
os.add_dll_directory(cuda_bin)
os.environ["CUDA_PATH"] = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2"

from backend import np, BACKEND
import cupy as cp
from tracer import Tracer
from visualization import NormalPlaneMap, Plotter
from rays.ray import Ray, RayGroup, IdealLambertianSource3D, TruncatedLambertianSource3D, TruncatedLambertianSource2D
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
        AsphericSurface(vertex=[0, 0, 90], radius=30, conic=-1.1, aspheric_coeffs=[0.35e-6, -0.35e-8, -1e-11], n1=1.0, n2=1.5, diameter=50.0),
        # SphericalSurface(center=[0, 0, 40], radius=60,  n1=1.0, n2=1.5, diameter=50.0),
        SphericalSurface(center=[0, 0, 105], radius=-80, n1=1.5, n2=1.0, diameter=50.0),
    ])

# Singlet lens 2
lens2 = Lens(surfaces=[
    SphericalSurface(center=[0, 0, 110], radius=60,  n1=1.0, n2=1.5, diameter=40.0),
    SphericalSurface(center=[0, 0, 122], radius=-30, n1=1.5, n2=1.3, diameter=40.0),
    SphericalSurface(center=[0, 0, 123], radius=-40, n1=1.3, n2=1.0, diameter=40.0),
])


# rays = [
#     Ray(origin=[0,   0, 0], direction=[0,  0.3, 1]),
#     Ray(origin=[0,   0, 0], direction=[0,  0.0, 1]),
#     Ray(origin=[0,   0, 0], direction=[0, -0.3, 1]),
#     Ray(origin=[0,   5, 0], direction=[0,  0.3, 1]),
#     Ray(origin=[0,   5, 0], direction=[0,  0.0, 1]),
#     Ray(origin=[0,   5, 0], direction=[0, -0.3, 1]),
#     Ray(origin=[0,  -5, 0], direction=[0,  0.3, 1]),
#     Ray(origin=[0,  -5, 0], direction=[0,  0.0, 1]),
#     Ray(origin=[0,  -5, 0], direction=[0, -0.3, 1]),
#     Ray(origin=[0,  15, 0], direction=[0,  0.3, 1]),
#     Ray(origin=[0,  15, 0], direction=[0,  0.0, 1]),
#     Ray(origin=[0,  15, 0], direction=[0, -0.3, 1]),
#     Ray(origin=[-15, -15, 0], direction=[0,  0.3, 1]),
#     Ray(origin=[-15, -15, 0], direction=[0,  0.0, 1]),
#     Ray(origin=[-15, -15, 0], direction=[0, -0.3, 1]),
# ]

# g = RayGroup(rays)   # after you implement this
print("Backend:", BACKEND)
print("CuPy available:", cp.is_available())
print("GPU count:", cp.cuda.runtime.getDeviceCount())
print("Device:", cp.cuda.Device().use())
g = TruncatedLambertianSource3D(origin=[0, 0, 0], num_rays=300000, wavelength=470, distribution='random', half_angle_deg=12)
tracer = Tracer()
paths, final_origins, final_dirs = tracer.trace([lens1, lens2], g)

plane_map = NormalPlaneMap(rays=g, z=135)
plane_map.xy_at_z()
# plane_map.plot()
plane_map.histogram(bins=100)

# p = Plotter(rays=g, elements=[lens1, lens2])
#     # ---- plot result ----
# fig, ax = p.plot_cross_section()
# p.show()