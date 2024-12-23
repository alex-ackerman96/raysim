import numpy as np

class Lens:
    def __init__(self, surfaces, thicknesses=None):
        """
        Initialize a Lens object.
        
        Parameters:
        surfaces (list): A list of Surface objects (SphericalSurface or AsphericSurface)
                         in the order that a ray would encounter them.
        thicknesses (list): A list of distances (thicknesses) between consecutive surfaces.
                            The length should be len(surfaces) - 1. Default is None.
        """
        self.surfaces = surfaces
        if thicknesses is None:
            self.thicknesses = [0] * (len(surfaces) - 1)  # Default to zero if not provided
        else:
            self.thicknesses = thicknesses

    def trace(self, ray):
        """
        Trace a ray through all surfaces of the lens.
        
        Parameters:
        ray (Ray): The input ray to be traced through the lens.
        
        Returns:
        Ray: The output ray after passing through all surfaces, or None if the ray doesn't make it through.
        """
        current_ray = ray
        for i, surface in enumerate(self.surfaces):
            # Find intersection with current surface
            intersection, normal = surface.intersect(current_ray)
            
            if intersection is None:
                return None  # Ray missed the surface or had total internal reflection
            
            # Move the ray to the intersection point
            current_ray.origin = intersection
            
            # Refract the ray
            n1, n2 = surface.n1, surface.n2
            refracted_direction = self.refract(current_ray.direction, normal, n1, n2)
            
            if refracted_direction is None:
                return None  # Total internal reflection
            
            current_ray.direction = refracted_direction
            
            # Propagate the ray to the next surface if it's not the last one
            if i < len(self.surfaces) - 1:
                current_ray.propagate(self.thicknesses[i])

        return current_ray

    @staticmethod
    def refract(incident, normal, n1, n2):
        """
        Apply Snell's law to refract a ray.
        
        Parameters:
        incident (np.array): The incident ray direction.
        normal (np.array): The surface normal at the point of incidence.
        n1 (float): Refractive index of the medium the ray is coming from.
        n2 (float): Refractive index of the medium the ray is entering.
        
        Returns:
        np.array: The refracted ray direction, or None if total internal reflection occurs.
        """
        cos_theta1 = -np.dot(normal, incident)
        sin_theta1 = np.sqrt(1 - cos_theta1**2)
        sin_theta2 = n1 / n2 * sin_theta1
        
        if sin_theta2 > 1:
            return None  # Total internal reflection
        
        cos_theta2 = np.sqrt(1 - sin_theta2**2)
        return n1 / n2 * incident + (n1 / n2 * cos_theta1 - cos_theta2) * normal

    def focal_length(self, num_rays=100, z_start=-1000):
        """
        Estimate the focal length of the lens.
        
        Parameters:
        num_rays (int): Number of parallel rays to use for estimation.
        z_start (float): Starting z-coordinate for the parallel rays.
        
        Returns:
        float: Estimated focal length, or None if unable to estimate.
        """
        rays = []
        for _ in range(num_rays):
            x = np.random.uniform(-1, 1)
            y = np.random.uniform(-1, 1)
            ray = Ray([x, y, z_start], [0, 0, 1])
            output_ray = self.trace(ray)
            if output_ray is not None:
                rays.append(output_ray)

        if not rays:
            return None  # Unable to estimate focal length

        # Find where rays converge (approximately)
        z_intersects = []
        for i, ray1 in enumerate(rays):
            for ray2 in rays[i+1:]:
                a = ray1.direction[0:2]
                b = ray2.direction[0:2]
                c = ray2.origin[0:2] - ray1.origin[0:2]
                
                if np.cross(a, b) != 0:  # Check if rays are not parallel
                    t = np.cross(c, b) / np.cross(a, b)
                    intersection = ray1.origin + t * ray1.direction
                    z_intersects.append(intersection[2])

        if z_intersects:
            focal_point_z = np.mean(z_intersects)
            return focal_point_z - self.surfaces[0].vertex[2]  # Assuming first surface is at z=0
        else:
            return None  # Unable to estimate focal length
