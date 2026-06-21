---
audience: [human, agent]
role: user
topic: parallel
kind: guide
tasks: ["parallel batch", "SLURM detection", "MPI sharding", "memory tuning"]
api: ["batch_process_parallel", "detect_available_workers", "detect_job_array", "detect_mpi_rank", "limit_blas_threads", "split_iterations"]
cli: ["vis batch -j"]
updated: 2026-06-04
---

# Parallel Execution

Run batch visualization across multiple CPU cores or cluster nodes.

## Quick start

```bash
# Auto-detect worker count from environment
osiris-toolkit vis batch /data/Au Au

# Explicit worker count
osiris-toolkit vis batch -j 8 /data/Au Au
```

```python
from osiris_toolkit.vis.batch import process_simulation

process_simulation("/data/Au", "Au", max_workers=8)
```

## Worker detection

The number of workers is determined by this priority chain:

1. `--max-workers` / `-j` CLI flag (explicit override)
2. `SLURM_CPUS_PER_TASK` environment variable
3. `OMP_NUM_THREADS` environment variable
4. `os.cpu_count()` (fallback to 4 if unavailable)

```python
from osiris_toolkit.parallel._cluster import detect_available_workers

n = detect_available_workers()
print(f"Using {n} workers")
```

## Architecture

Parallel processing uses `concurrent.futures.ProcessPoolExecutor` with the
`spawn` multiprocessing context. Each worker:

1. Creates its own `Simulation` instance (pickle-serialized from parent)
2. Sets `matplotlib.use("Agg")` (no GUI)
3. Limits BLAS threads to 1 via `limit_blas_threads(1)`
4. Reads data, renders a single figure, saves PNG, and closes

File writes target deterministic paths (e.g. `fields/e1_000100.png`), so no
file locking is needed.

## BLAS thread control

Without BLAS thread limiting, N workers x M BLAS threads = NxM threads
competing for N physical cores. `limit_blas_threads(1)` sets:

- `OMP_NUM_THREADS`
- `MKL_NUM_THREADS`
- `OPENBLAS_NUM_THREADS`
- `NUMEXPR_NUM_THREADS`

to 1 in each worker process.

## SLURM job arrays

When running under SLURM or PBS job arrays, iterations are automatically
partitioned across tasks:

```python
from osiris_toolkit.parallel._cluster import detect_job_array, split_iterations

arr = detect_job_array()
if arr:
    task_id, task_count = arr
    my_iters = split_iterations(iterations, task_id, task_count)
    print(f"Task {task_id}/{task_count}: {len(my_iters)} iterations")
```

Job array detection checks `SLURM_ARRAY_TASK_ID` / `SLURM_ARRAY_TASK_COUNT`
and `PBS_ARRAYID` / `PBS_ARRAY_INDEX`.

## MPI support

When launched with `mpirun` and `mpi4py` is installed, iterations are
partitioned by MPI rank:

```python
from osiris_toolkit.parallel._cluster import detect_mpi_rank, split_iterations

mpi = detect_mpi_rank()
if mpi:
    rank, world_size = mpi
    my_iters = split_iterations(iterations, rank, world_size)
    print(f"Rank {rank}/{world_size}: {len(my_iters)} iterations")
```

MPI sharding takes priority over SLURM job array sharding.

## Memory considerations

- **Peak memory per worker**: ~200-500 MB (matplotlib + numpy + data array)
- **Recommendation**: `max_workers` should not exceed `physical_cores - 1`
- **For large grids** (>4000x4000): reduce workers or set `OMP_NUM_THREADS=1` globally
- **Output disk space**: approximate with `vis batch --dry-run` first

```bash
# Preview disk usage before processing
osiris-toolkit vis batch --dry-run /data/Au Au
```

## Scattering analysis note

Scattering analysis has a cross-iteration dependency (iterates over all
time steps to compute scattered vs total field energy). It always runs
sequentially after all parallel workers finish, regardless of `max_workers`.

## API Reference

| Function | Description |
|---|---|
| `batch_process_parallel(sim_path, sim_name, ...)` | Parallel version of process_simulation |
| `detect_available_workers()` | Return max worker count for current environment |
| `detect_job_array()` | Detect SLURM/PBS job array, return `(task_id, task_count)` |
| `detect_mpi_rank()` | Detect mpi4py, return `(rank, world_size)` |
| `limit_blas_threads(n)` | Set BLAS environment variables to n |
| `split_iterations(iters, rank, world_size)` | Evenly split iteration list for current rank |
