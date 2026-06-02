# HPC Cluster Test Suite

Tests for osiris-toolkit features that require a real supercomputing cluster
environment (SLURM, MPI, job arrays).

## Prerequisites

- SLURM cluster with at least 2 compute nodes (test 01 needs multi-node)
- Intel MPI and/or OpenMPI module available
- Existing OSIRIS simulation output (10-100 GB scale) accessible from compute nodes
- Conda environment with osiris-toolkit and mpi4py installed

## Quick Environment Check

Before running any tests, verify the environment on a login node:

```bash
source activate <conda_env>
cd <PROJECT_ROOT>
python -c "
from osiris_toolkit.parallel import detect_mpi_rank, detect_job_array, detect_available_workers
print('MPI rank:', detect_mpi_rank())
print('Job array:', detect_job_array())
print('Workers:', detect_available_workers())
"
```

Expected output on a login node (no MPI, no job array):
```
MPI rank: None
Job array: None
Workers: <N>  (some CPU count)
```

## Variables to Replace

All scripts use `<>` angle-bracket placeholders. Replace these before submitting:

| Placeholder | Meaning | Example |
|-------------|---------|---------|
| `<conda_env>` | Conda environment name | `osiris-env` |
| `<PROJECT_ROOT>` | Absolute path to osiris-toolkit/ | `/home/user/osiris-toolkit` |
| `<SIM_DATA_DIR>` | Path to existing OSIRIS simulation output | `/scratch/sim-output/my-run/` |
| `<partition>` | SLURM partition name | `compute` |
| `<mpi_module>` | MPI module to load | `mpi/intelmpi/2021.1` |
| `<slurm_user>` | SLURM user account name | `your_username` |

## Execution Order

```
01-mpi-multinode  ──┐
                    ├── Run FIRST (infrastructure validation)
02-slurm-env      ──┘
                    │
03-resource-calibration ──┐
04-large-data-scale     ──┤ Run SECOND (can run in parallel)
05-pipeline-e2e         ──┘
```

01 and 02 must pass before proceeding — they validate MPI and SLURM integration.

## How to Run

```bash
# Navigate to a test area
cd tests/hpc/01-mpi-multinode/

# Replace placeholders in submit script, then:
sbatch submit_intelmpi.sh

# Monitor
squeue -u $USER

# Check results
cat slurm-*.out
cat slurm-*.err

# After all tests complete, fill in the report template
cp _report_template.md docs/devlog/notes/YYYY-MM-DD-test-hpc-cluster.md
```

## Report Template

After each test area completes, fill in the corresponding section of `_report_template.md`.
When all five areas are done, save the completed report to
`docs/devlog/notes/YYYY-MM-DD-test-hpc-cluster.md`.
