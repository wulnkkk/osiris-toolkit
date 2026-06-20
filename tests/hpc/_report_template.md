# HPC Cluster Test Report

> YYYY-MM-DD | HPC Test

## Environment

- Cluster name:
- SLURM version:
- MPI implementation & version:
- Conda environment:
- Project path:
- Data path:

---

## Test 1: MPI Multi-Node Parallel

- Execution time:
- Submit script: `submit_intelmpi.sh` / `submit_openmpi.sh`
- Number of nodes:
- Processes per node:

| # | Test Item | Result | Key Metric | Notes |
|---|-----------|--------|------------|-------|
| 1.1 | Single-node MPI distribution | | | |
| 1.2 | Multi-node iteration split | | | |
| 1.3 | Multi-node analysis parallel | | | |
| 1.4 | Multi-node visualization parallel | | | |

### Issues


---

## Test 2: SLURM Environment Integration

- Execution time:
- Submit script:
- Job array ID range:

| # | Test Item | Result | Key Metric | Notes |
|---|-----------|--------|------------|-------|
| 2.1 | CPU auto-detection | | | |
| 2.2 | Job array detection | | | |
| 2.3 | Job array iteration split | | | |
| 2.4 | BLAS thread limiting | | | |

### Issues


---

## Test 3: Resource Prediction Calibration

- Execution time:
- Number of simulations used:
- Simulation directory list:

| # | Test Item | Result | Key Metric | Notes |
|---|-----------|--------|------------|-------|
| 3.1 | Parameter extraction accuracy | | | |
| 3.2 | Memory prediction error | | | |
| 3.3 | Time prediction error | | | |
| 3.4 | Disk prediction error | | | |
| 3.5 | Coefficient calibration suggestion | | | |

### Calibration Suggestions

| Parameter | Current Default | Suggested Value |
|-----------|----------------|-----------------|
| efficiency | 0.15 | |
| io_bandwidth_gbs | 1.0 | |

### Issues


---

## Test 4: Large-Scale Data Parallel Processing

- Execution time:
- Data size:
- Maximum iterations:

| # | Test Item | Result | Key Metric | Notes |
|---|-----------|--------|------------|-------|
| 4.1 | Full-iteration field_energy | | | |
| 4.2 | Batch visualization | | | |
| 4.3 | Scalability test | | | |
| 4.4 | Large dataset read | | | |

### Performance Data

| Mode | Workers | Time(s) | Speedup | Peak Memory(MB) |
|------|---------|---------|---------|-----------------|
| analysis | 1 | | 1.0x | |
| analysis | 2 | | | |
| analysis | 4 | | | |
| analysis | 8 | | | |
| vis | 1 | | 1.0x | |
| vis | 4 | | | |
| vis | 8 | | | |

### Issues


---

## Test 5: Pipeline End-to-End

- Execution time:
- YAML config:

| # | Test Item | Result | Key Metric | Notes |
|---|-----------|--------|------------|-------|
| 5.1 | YAML → full pipeline | | | |
| 5.2 | Cluster path compatibility | | | |
| 5.3 | Missing environment modules | | | |

### Issues


---

## Summary

| Test Area | Pass/Fail | Test Cases Passed |
|-----------|-----------|-------------------|
| 01 MPI multi-node | | |
| 02 SLURM environment | | |
| 03 Resource calibration | | |
| 04 Large-scale data | | |
| 05 Pipeline E2E | | |

## Conclusion
