import numpy as np
from elements.surfaces import SphericalSurface
from elements.surfaces import AsphericSurface
from elements.lens import Lens
from rays.ray import Ray

class TracingEngine:
    surfaces = []
    lenses = []
    def __init__(self):
        pass

    def add_surface(self, surface):
        self.surfaces.append(surface)