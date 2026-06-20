"""Parallel analysis — fan out per-iteration computations across processes.

All worker functions are module-level (required for Windows spawn).
Results are always sorted by iteration before return.
"""

import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from osiris_toolkit.parallel._cluster import (
    detect_available_workers,
    detect_job_array,
    detect_mpi_rank,
    limit_blas_threads,
    split_iterations,
)
from osiris_toolkit.sim import Simulation

# ── Worker functions (module-level, pickle-safe) ──────────────────────


def _worker_field_energy(
    sim: Simulation,
    iteration: int,
    quantity: str,
) -> dict:
    """Worker: compute total field energy for one iteration."""
    limit_blas_threads(1)
    grid = sim.get_field(quantity, iteration)
    if grid is None:
        return {"iteration": iteration, "time": -1.0, "energy": float("nan")}
    return {
        "iteration": iteration,
        "time": grid.time,
        "energy": float((grid.data**2).sum()),
    }


def _worker_describe(
    sim: Simulation,
    iteration: int,
    quantity: str,
) -> dict:
    """Worker: compute describe() statistics for one iteration."""
    limit_blas_threads(1)
    import numpy as np

    grid = sim.get_field(quantity, iteration)
    if grid is None:
        return {"iteration": iteration, "error": "no data"}
    return {
        "iteration": iteration,
        "time": grid.time,
        "mean": float(np.mean(grid.data)),
        "std": float(np.std(grid.data)),
        "min": float(np.min(grid.data)),
        "max": float(np.max(grid.data)),
        "rms": float(np.sqrt(np.mean(grid.data**2))),
    }


# ── Internal fan-out ──────────────────────────────────────────────────


def _run_analysis_parallel(
    sim: Simulation,
    iterations: list[int],
    worker_fn,
    worker_kwargs: dict,
    max_workers: int | None,
) -> list[dict]:
    """Fan out *worker_fn* across *iterations*, collect sorted results."""
    mpi = detect_mpi_rank()
    if mpi:
        my_iters = split_iterations(iterations, *mpi)
    else:
        arr = detect_job_array()
        my_iters = split_iterations(iterations, *arr) if arr else iterations

    if max_workers is None:
        max_workers = detect_available_workers()
    ctx = multiprocessing.get_context("spawn")

    with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as ex:
        futures = [ex.submit(worker_fn, sim, it, **worker_kwargs) for it in my_iters]
        results = [f.result() for f in futures]

    results.sort(key=lambda r: r.get("iteration", 0))
    return results


# ── Public API ─────────────────────────────────────────────────────────


def field_energy_all(
    sim: Simulation,
    quantity: str,
    max_workers: int | None = None,
) -> list[dict]:
    """Compute total field energy for all iterations in parallel.

    Parameters
    ----------
    sim : Simulation
        Loaded simulation object.
    quantity : str
        Field component name (e.g. ``'e1'``).
    max_workers : int or None
        Number of worker processes.  If None, auto-detected from SLURM
        or CPU count.

    Returns
    -------
    list[dict]
        Sorted by iteration.  Each dict has keys ``"iteration"``,
        ``"time"``, ``"energy"``.
    """
    iterations = sim.list_iterations(quantity)
    return _run_analysis_parallel(
        sim,
        iterations,
        _worker_field_energy,
        {"quantity": quantity},
        max_workers,
    )


def describe_all(
    sim: Simulation,
    quantity: str,
    iterations: list[int] | None = None,
    max_workers: int | None = None,
) -> list[dict]:
    """Compute describe() statistics for multiple iterations in parallel.

    Parameters
    ----------
    sim : Simulation
        Loaded simulation object.
    quantity : str
        Field component name.
    iterations : list of int or None
        Iteration numbers to process.  If None, all available iterations.
    max_workers : int or None
        Number of worker processes.

    Returns
    -------
    list[dict]
        Sorted by iteration.  Each dict has keys ``"iteration"``,
        ``"time"``, ``"mean"``, ``"std"``, ``"min"``, ``"max"``, ``"rms"``.
    """
    if iterations is None:
        iterations = sim.list_iterations(quantity)
    return _run_analysis_parallel(
        sim,
        iterations,
        _worker_describe,
        {"quantity": quantity},
        max_workers,
    )
