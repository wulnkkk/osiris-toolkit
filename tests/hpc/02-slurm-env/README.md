# Test 02: SLURM Environment Variable Integration

Validates that osiris-toolkit correctly detects SLURM environment variables
for CPU count, job arrays, and thread limiting.

## Requirements

- SLURM cluster (single node is sufficient)
- No MPI needed

## How to Run

1. Replace `<conda_env>`, `<PROJECT_ROOT>`, `<SIM_DATA_DIR>`, `<partition>`
   in `submit_array.sh`.
2. Submit:

```bash
sbatch submit_array.sh
```

This launches a 4-task job array (`--array=0-3`). Each array task runs the
test independently.

3. Check output: `cat slurm-*.out`

## Expected Output (per array task)

```
[INFO] SLURM_ARRAY_TASK_ID=2, SLURM_ARRAY_TASK_COUNT=4
[INFO] SLURM_CPUS_PER_TASK=8
[INFO] detect_available_workers()=8
[PASS] 2.1 CPU detection: workers=8 matches SLURM_CPUS_PER_TASK=8
[PASS] 2.2 Job array detection: task 2/4
[PASS] 2.3 Job array iteration split: no overlap between tasks
[PASS] 2.4 BLAS thread limiting: OMP_NUM_THREADS=1
[TOTAL] 4/4 passed
```
