import os
# import numpy as np
from backend import np, BACKEND
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from elements.surfaces import AsphericSurface, PlanarSurface, SphericalSurface
from rays.ray import RayGroup, Ray, IdealLambertianSource3D, IdealLambertianSource2D, TruncatedLambertianSource2D
from tracer import Tracer, Lens

def _trace_chunk(args):
    """
    Worker function: trace one chunk of rays through lenses.
    Returns (chunk_paths, chunk_final_origins, chunk_final_dirs)
    """
    tracer_kwargs, lenses, origins_chunk, directions_chunk, output_z = args
    # Re-instantiate Tracer inside the worker (required for process-based pools)
    tracer = Tracer(**tracer_kwargs)
    paths, final_origins, final_dirs = tracer.trace_group(
        lenses, origins_chunk, directions_chunk, output_z=output_z
    )
    return paths, final_origins, final_dirs


def parallel_trace(
    tracer: Tracer,
    lenses,
    ray_group: RayGroup,
    output_z=None,
    num_workers=None,
    backend='thread',   # 'thread' or 'process'
):
    """
    Trace a RayGroup in parallel across multiple CPU cores.

    Parameters
    ----------
    backend : 'thread' (preferred for NumPy-heavy code) or 'process'
    num_workers : number of parallel workers; defaults to cpu_count

    Returns
    -------
    merged_group : RayGroup with all rays merged
    paths : (S, N, 3) full path array
    """
    if num_workers is None:
        num_workers = os.cpu_count()

    origins    = np.asarray(ray_group.ray_origins,    dtype=float)
    directions = np.asarray(ray_group.ray_directions, dtype=float)
    N = origins.shape[0]

    # ---- split rays into equal chunks, one per worker ----
    chunk_size = max(1, N // num_workers)
    chunks = []
    for start in range(0, N, chunk_size):
        end = min(start + chunk_size, N)
        chunks.append((origins[start:end], directions[start:end]))

    # tracer config dict for re-instantiation inside worker processes
    tracer_kwargs = dict(
        t_max          = tracer.t_max,
        bracket_samples= tracer.bracket_samples,
        refine_iters   = tracer.refine_iters,
        eps            = tracer.eps,
    )

    # ---- choose executor ----
    Executor = ThreadPoolExecutor if backend == 'thread' else ProcessPoolExecutor

    args_list = [
        (tracer_kwargs, lenses, o_chunk, d_chunk, output_z)
        for (o_chunk, d_chunk) in chunks
    ]

    results = [None] * len(chunks)
    with Executor(max_workers=num_workers) as executor:
        future_map = {
            executor.submit(_trace_chunk, args): i
            for i, args in enumerate(args_list)
        }
        for future in as_completed(future_map):
            i = future_map[future]
            results[i] = future.result()

    # ---- merge results ----
    # paths has shape (S, N_chunk, 3) per worker; S may differ if lenses vary, but
    # here all workers see the same lenses so S is constant
    all_paths       = np.concatenate([r[0] for r in results], axis=1)  # (S, N, 3)
    all_origins     = np.concatenate([r[1] for r in results], axis=0)  # (N, 3)
    all_directions  = np.concatenate([r[2] for r in results], axis=0)  # (N, 3)

    # ---- build merged RayGroup ----
    merged_rays = []
    for i in range(N):
        ray = Ray(
            origin    = all_origins[i],
            direction = all_directions[i],
            wavelength= ray_group._rays[i].wavelength
        )
        merged_rays.append(ray)

    merged_group = RayGroup(merged_rays)
    merged_group.ray_origins    = all_origins
    merged_group.ray_directions = all_directions
    merged_group.ray_paths      = all_paths

    return merged_group, all_paths, all_origins, all_directions

if __name__ == "__main__":
    tracer   = Tracer(t_max=200, bracket_samples=256, refine_iters=10, eps=1e-6)
    source   = IdealLambertianSource3D(origin=[0, 0, 0], num_rays=10000)
    lens = Lens(surfaces=[
        AsphericSurface(vertex=[0, 0, 90], radius=30, conic=-1.1, aspheric_coeffs=[0.35e-6, -0.35e-8, -1e-11], n1=1.0, n2=1.5, diameter=50.0),
        SphericalSurface(center=[0, 0, 105], radius=-80, n1=1.5, n2=1.0, diameter=50.0),
    ])

    merged_group, paths, final_o, final_d = parallel_trace(
        tracer,
        lenses=[lens],
        ray_group=source,
        output_z=200.0,
        num_workers=80,
        backend='thread',   # threads are enough since Tracer is NumPy-heavy
    )