from elements.lenses import CircularLens

from materials.material import Material

# lens1 = CircularLens(origin = [0, 0, 0], diameter = 50, axialthickness = 5, surfaces = ["convex-spherical", "convex-spherical"], materials=["BK7", "BK7"])

nbk7 = Material(filepath = "library/glass.json", material = "N-BK7")
print(nbk7.abbe)