import json
import pandas as pd
import numpy as np

class Material:

    def __init__(self):
        
        self.n = np.empty(shape=(0,2), dtype=float)             # Wavelength (um) and real refractive index n
        self.k = np.empty(shape=(0,2), dtype=float)             # Wavelength (um) and imaginary refractive index k
        self.dielectric_const_1 = None                          
        self.dielectric_const_2 = None
        self.absorption = None
        self.abbe_number = None
        self.chromatic_dispersion = None
        self.group_index = None
        self.gvd = None
        self.d = None

    def import_from_json(self, filepath, material):
        
        self.filepath = filepath
        self.material = material

        with open(filepath, 'r') as file:
            data = json.load(file)

        self.n = data[material]['n']
        self.k = data[material]['k']
        self.epsilon1 = data[material]['relpermativity1']
        self.epsilon2 = data[material]['relpermativity2']
        self.alpha = data[material]['alpha']
        self.abbe = data[material]['abbe']
        self.dispersion = data[material]['dispersion']
        self.groupindex = data[material]['groupindex']
        self.gvd = data[material]['gvd']
        self.d = data[material]['d']

        self.mfg = data[material]['mfg']
        self.source = data[material]['source']