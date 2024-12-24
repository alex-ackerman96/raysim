from dataclasses import dataclass

@dataclass
class Material:
    n = None
    k = None
    epsilon1 = None
    epsilon2 = None
    alpha = None
    abbe = None
    dispersion = None
    groupindex = None
    gvd = None
    d = None

    mfg = None
    source = None