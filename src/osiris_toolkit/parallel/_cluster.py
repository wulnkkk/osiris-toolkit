"""Cluster-aware resource detection and iteration partitioning."""

import os


def detect_available_workers() -> int:
    """Return max worker count for current environment.

    Priority: SLURM_CPUS_PER_TASK > OMP_NUM_THREADS > os.cpu_count()
    """
    for var in ("SLURM_CPUS_PER_TASK", "OMP_NUM_THREADS"):
        val = os.environ.get(var)
        if val and val.isdigit():
            return int(val)
    return os.cpu_count() or 4


def limit_blas_threads(n: int = 1) -> None:
    """Call at start of every worker process to prevent BLAS thread inflation.

    Without this, N workers x M BLAS threads per worker = NxM threads
    competing for N physical cores.
    """
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[var] = str(n)


def detect_job_array() -> tuple[int, int] | None:
    """Detect SLURM/PBS job array environment.

    Returns
    -------
    (task_id, task_count) or None
    """
    for id_var, count_var in (
        ("SLURM_ARRAY_TASK_ID", "SLURM_ARRAY_TASK_COUNT"),
        ("PBS_ARRAYID", "PBS_ARRAY_INDEX"),
    ):
        tid = os.environ.get(id_var)
        tcnt = os.environ.get(count_var)
        if tid is not None and tcnt is not None:
            return int(tid), int(tcnt)
    return None


def detect_mpi_rank() -> tuple[int, int] | None:
    """Detect mpi4py environment.

    Returns
    -------
    (rank, world_size) or None
        None if mpi4py is not installed or not launched with mpirun.
    """
    try:
        from mpi4py import MPI

        comm = MPI.COMM_WORLD
        if comm.Get_size() > 1:
            return comm.Get_rank(), comm.Get_size()
    except ImportError:
        pass
    return None


def split_iterations(
    iterations: list[int],
    rank: int,
    world_size: int,
) -> list[int]:
    """Evenly split iteration list for current rank.

    Example:
        iterations=[0,10,20,30,40,50], rank=1, world_size=3 → [20,30]
    """
    return iterations[rank::world_size]
