from elements.surfaces import SphericalSurface
from elements.surfaces import AsphericSurface
from elements.lens import Lens
from rays.ray import Ray

# import numpy as np
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D

# # Assuming you have already defined Ray, SphericalSurface, and Lens classes

# def plot_lens_and_ray(lens, ray, ax_range=150):
#     fig = plt.figure(figsize=(12, 8))
#     ax = fig.add_subplot(111, projection='3d')
    
#     # Plot the lens surfaces
#     for surface in lens.surfaces:
#         u = np.linspace(0, 2 * np.pi, 100)
#         v = np.linspace(0, np.pi, 100)
#         x = surface.radius * np.outer(np.cos(u), np.sin(v)) + surface.center[0]
#         y = surface.radius * np.outer(np.sin(u), np.sin(v)) + surface.center[1]
#         z = surface.radius * np.outer(np.ones(np.size(u)), np.cos(v)) + surface.center[2]
#         ax.plot_surface(x, y, z, alpha=0.2)

#     # Trace and plot the ray
#     points = [ray.origin]
#     current_ray = ray
#     for surface in lens.surfaces:
#         intersection, _ = surface.intersect(current_ray)
#         if intersection is not None:
#             points.append(intersection)
#             current_ray = lens.trace(current_ray)
#             if current_ray is None:
#                 break
    
#     if current_ray:
#         # Extend the final ray
#         points.append(current_ray.origin + current_ray.direction * ax_range)
    
#     points = np.array(points)
#     ax.plot(points[:, 0], points[:, 1], points[:, 2], 'r-', linewidth=2)

#     # Set plot limits and labels
#     ax.set_xlim(-ax_range/2, ax_range/2)
#     ax.set_ylim(-ax_range/2, ax_range/2)
#     ax.set_zlim(-ax_range, ax_range)
#     ax.set_xlabel('X')
#     ax.set_ylabel('Y')
#     ax.set_zlabel('Z')
#     ax.set_title('Ray Tracing through Lens')

#     plt.show()

# # Create surfaces
# surface1 = SphericalSurface([0, 0, 0], 100, 1.0, 1.5, 30)  # Air to glass
# surface2 = SphericalSurface([0, 0, 5], -150, 1.5, 1.0, 30)  # Glass to air

# # Create a lens
# lens = Lens([surface1, surface2])

# # Create a ray parallel to the axis
# input_ray = Ray([0, 10, -100], [0, 0, 1])

# # Plot the lens and ray
# plot_lens_and_ray(lens, input_ray)

# # Trace the ray through the lens
# output_ray = lens.trace(input_ray)

# # Estimate focal length
# focal_length = lens.focal_length()
# print(f"Estimated focal length: {focal_length}")

import numpy as np
import matplotlib.pyplot as plt
from elements.surfaces import SphericalSurface
from elements.lens import Lens
from rays.ray import Ray

# Create surfaces
surface1 = SphericalSurface([0, 0, -45], 50, 1.0, 1.5, 30)  # Air to glass
surface2 = SphericalSurface([0, 0, 45], -50, 1.5, 1.0, 30)  # Glass to air

# Create a lens
lens = Lens([surface1, surface2], thicknesses=[5])

# Create a ray parallel to the axis
input_ray = Ray([0, 10, -100], [0, 0, 1])

# Trace the ray through the lens
output_ray = lens.trace(input_ray)

# Plot the 2D cross-section
plt.figure(figsize=(12, 6))

# Plot input ray
z_in = np.linspace(-100, 0, 100)
y_in = input_ray.origin[1] + input_ray.direction[1] * (z_in - input_ray.origin[2]) / input_ray.direction[2]
# plt.plot(z_in, y_in, 'r--', label='Input Ray')

# Plot output ray
z_out = np.linspace(5, 100, 100)
y_out = output_ray.origin[1] + output_ray.direction[1] * (z_out - output_ray.origin[2]) / output_ray.direction[2]
# plt.plot(z_out, y_out, 'r-', label='Output Ray')

# Plot lens surfaces
for surface in lens.surfaces:
    z = surface.center[2]
    y = np.linspace(-surface.diameter/2, surface.diameter/2, 100)
    x = np.sqrt(surface.radius**2 - y**2) * np.sign(surface.radius) + z
    plt.plot(x, y, 'b-', alpha=0.5)
    # plt.plot([z, z], [-surface.diameter/2, surface.diameter/2], 'b-', alpha=0.5)

plt.xlim(-110, 110)  # Z-axis range (ray propagation direction)
plt.ylim(-20, 20)    # Y-axis range (cross-section height)
plt.xlabel('Z-axis (mm)')
plt.ylabel('Y-axis (mm)')
plt.title('2D Cross-Section of Ray through Lens')
plt.legend()
plt.grid(True)
plt.gca().set_aspect('equal', adjustable='box')
plt.show()

# Calculate and print focal length
if hasattr(lens, 'focal_length'):
    focal_length = lens.focal_length()
    print(f"Estimated focal length: {focal_length:.2f} mm")
else:
    print("Focal length calculation not available for this lens.")

