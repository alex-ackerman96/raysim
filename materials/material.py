import json

class Material:

    def __init__(self, filepath, material):
        
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