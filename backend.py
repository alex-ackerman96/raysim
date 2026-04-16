# backend.py
import os
import numpy as _np_cpu  # always import CPU NumPy as _np_cpu, regardless of backend choice

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

def to_cpu(arr):
    """Move any array to CPU NumPy — no-op if already NumPy."""
    if hasattr(arr, 'get'):
        return arr.get()
    return _np_cpu.asarray(arr)