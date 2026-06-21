---
audience: [human, agent]
role: developer
topic: modules
kind: reference
module: parallel
updated: 2026-06-04
---

# parallel — Cluster-Aware Parallel Execution

Parallel data processing that scales from a personal laptop to HPC clusters. Each module
(`analysis`, `vis`) provides its own parallel functions with dedicated worker processes.

## Architecture

```
parallel/
├── __init__.py        Public API: detect_available_workers, split_iterations, etc.
└── _cluster.py        Resource detection (SLURM/PBS/MPI), BLAS thread control, iteration partitioning

analysis/
└── parallel.py        field_energy_all(), describe_all() — fan-out across iterations

vis/
├── parallel.py        batch_process_parallel() — fan-out plot tasks across processes
└── batch.py           process_simulation() delegates to parallel when max_workers > 0
```

## Scheduling Model

Three-layer scheduling, detected and applied automatically:

```
1. MPI (mpi4py)        → rank/world_size → split_iterations()
2. SLURM job array     → task_id/count   → split_iterations()
3. ProcessPoolExecutor → local multi-core fan-out
```

Each layer is optional and composable. MPI or job arrays shard iterations across nodes;
ProcessPoolExecutor handles intra-node CPU parallelism.

## Cluster Utilities

`parallel._cluster` provides shared detection and partitioning functions:

| Function | Role |
|----------|------|
| `detect_available_workers()` | SLURM_CPUS_PER_TASK > OMP_NUM_THREADS > `os.cpu_count()` |
| `limit_blas_threads(n=1)` | Sets OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS to prevent BLAS thread inflation |
| `detect_job_array()` | Reads SLURM_ARRAY_TASK_ID / PBS_ARRAYID environment variables |
| `detect_mpi_rank()` | Tries `import mpi4py`, checks `MPI.COMM_WORLD` size |
| `split_iterations(its, rank, n)` | Evenly distributes iterations via `iterations[rank::n]` |

## Usage

### Parallel Analysis

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.analysis.parallel import field_energy_all, describe_all

sim = Simulation("/data/sim")

# Compute total field energy for all iterations (auto-detect worker count)
results = field_energy_all(sim, "e1")
# [{"iteration": 0, "time": 0.0, "energy": 1.23e6}, ...]

# Compute describe() stats for specific iterations with 8 workers
stats = describe_all(sim, "e1", iterations=[0, 10, 20], max_workers=8)
```

### Parallel Visualization

```python
from osiris_toolkit.vis.batch import process_simulation

# Sequential (backward compatible)
process_simulation("/data/sim", "MyRun", output_root="./output")

# Parallel — auto-detect workers
process_simulation("/data/sim", "MyRun", output_root="./output", max_workers=None)

# Parallel — explicit 8 workers
process_simulation("/data/sim", "MyRun", output_root="./output", max_workers=8)
```

### CLI

```bash
# Local workstation — auto-detect core count
osiris-toolkit vis batch -o ./output /data/sim MySim -j auto

# Local workstation — explicit 8 workers
osiris-toolkit vis batch -o ./output /data/sim MySim -j 8

# HPC single node (SLURM auto-detected)
#SBATCH --cpus-per-task=64
osiris-toolkit vis batch -o /scratch/out /data/sim MySim

# HPC job array — each task processes 1/10 of iterations
#SBATCH --array=0-9
osiris-toolkit vis batch -o /scratch/out /data/sim MySim
```

### Worker Functions

Each module provides module-level worker functions (required for Windows `spawn` compatibility).
Workers receive `sim_path: str` (not a `Simulation` object) to avoid cross-process pickling.
Each worker constructs its own `Simulation` instance (~100 ms), calls `limit_blas_threads(1)`,
performs the computation, and returns a picklable result.

## Cross-Platform Compatibility

| Concern | Resolution |
|---------|-----------|
| Windows spawn | All workers are module-level functions |
| BLAS thread inflation | `limit_blas_threads(1)` at top of every worker |
| matplotlib subprocess | Agg backend; each worker creates/destroys its own figure |
| pickle safety | All worker arguments are primitives (`str`, `int`, `float`) |
| MPI optional | `detect_mpi_rank()` returns `None` if mpi4py not installed |
| File write conflicts | Unique paths per `(quantity, iteration)` pair |

## Key Design Decisions

- **Module-level parallelism**: each module owns its parallel implementation rather than
  routing through a shared Task abstraction. Avoids unnecessary indirection for
  embarrassingly parallel workloads.
- **Zero new dependencies**: stdlib `concurrent.futures.ProcessPoolExecutor` and
  `multiprocessing`. mpi4py is optional, detected at runtime.
- **Backward compatible**: `max_workers=None` (default) preserves existing sequential
  behavior. All plot functions accept both `sim_path` (old) and `sim` (new) parameters.
- **`load_sim()` reuse**: `vis/common.py::load_sim()` accepts an optional `sim=` keyword
  argument to reuse an already-constructed `Simulation` object, eliminating redundant
  directory discoveries in batch processing.
