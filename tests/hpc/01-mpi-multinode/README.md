# Test 01: MPI Multi-Node Parallel

Validates MPI rank detection, iteration splitting, and multi-node parallel
analysis/visualisation using mpi4py.

## Requirements

- At least 2 compute nodes
- Intel MPI or OpenMPI module available
- mpi4py installed in the Conda environment

## How to Run

1. Replace `<conda_env>`, `<PROJECT_ROOT>`, `<SIM_DATA_DIR>`, `<partition>`, `<mpi_module>`
   in the submit script.
2. Submit:

```bash
# Intel MPI
sbatch submit_intelmpi.sh

# Or OpenMPI
sbatch submit_openmpi.sh
```

3. Check output: `cat slurm-*.out`

## Expected Output

```
[INFO] MPI rank=0, world_size=4
[INFO] Rank 0 iterations: [0, 40, 80, 120, 160]
[INFO] Rank 1 iterations: [10, 50, 90, 130, 170]
...
[PASS] 1.1 MPI distribution: all ranks detected
[PASS] 1.2 Iteration split: no overlap, no gaps
[PASS] 1.3 Multi-node analysis: 200/200 results collected
[PASS] 1.4 Multi-node visualisation: 150 files generated
[TOTAL] 4/4 passed
```
