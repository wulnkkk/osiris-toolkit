# Test 03: Resource Prediction Calibration

Compares osiris-toolkit resource estimates against actual SLURM job metrics
from completed OSIRIS simulations to calibrate formula coefficients.

## Requirements

- At least 3 completed OSIRIS simulation directories, each containing:
  - Input deck file (`.in`)
  - SLURM output log (`slurm-*.out`) or `sacct` accessible
  - Simulation output on disk
- Single node, no MPI needed

## How to Run

1. Replace `<conda_env>`, `<PROJECT_ROOT>`, `<partition>` in `submit.sh`.
2. Edit `test_estimate.py` and fill in `SIM_DIRS` with paths to your completed
   simulation directories.
3. Submit:

```bash
sbatch submit.sh
```

## Collecting Actual Values

The script will print estimated values. For each simulation directory,
manually collect the actual values and enter them into the comparison:

```bash
# Actual wall time (seconds)
sacct -j <JOBID> --format=ElapsedRaw -n -P

# Actual memory (MB)
sacct -j <JOBID> --format=MaxRSS -n -P

# Actual disk (GB)
du -sh <sim_output_dir>/

# Actual node count
sacct -j <JOBID> --format=NNodes -n -P
```

## Expected Output

```
[INFO] Sim 1: /path/to/sim1
  Estimated memory: 45.2 GB/node,  Wall time: 12.3 h,  Disk: 320.5 GB
  Actual:   memory=38.1 GB, wall=14.5 h, disk=305.2 GB
  Deviation: memory=-15.7%, wall=+17.9%, disk=-4.8%

[SUMMARY] Calibration Recommendations:
  efficiency:  0.15 → 0.18 (based on avg runtime deviation)
  io_bandwidth_gbs: 1.0 → 0.85 (based on avg disk deviation)
```
