# backend.py
import os

# Check env var first, then default to numpy
_BACKEND = os.environ.get("RAYSIM_BACKEND", "numpy").lower()

if _BACKEND == "cupy":
    try:
        import cupy as np
        import cupy as cp
    except ImportError:
        import warnings
        warnings.warn("CuPy not available, falling back to NumPy.")
        import numpy as np
        import numpy as cp
else:
    import numpy as np
    import numpy as cp

BACKEND = _BACKEND