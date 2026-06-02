# Test 05: Pipeline End-to-End

Validates that the `Pipeline.from_yaml()` → `run()` workflow functions correctly
on the cluster (network filesystem paths, minimal environment).

## Requirements

- Existing OSIRIS simulation output directory with input deck
- Single node, no MPI needed

## How to Run

1. Replace `<conda_env>`, `<PROJECT_ROOT>`, `<partition>`
   in `submit.sh`.
2. Edit `pipeline_test.yaml` and replace `<SIM_DIR>` with the simulation
   directory path.
3. Submit:

```bash
sbatch submit.sh
```

## YAML Pipeline

The pipeline runs three steps:
1. `deck_parse` — parse the input deck
2. `sim_load` — open the simulation output directory
3. `analyze` — run analysis on available fields

Visualisation is excluded from this test to keep it fast.

## Expected Output

```
[INFO] Pipeline loaded: 3 steps
[PASS] 5.1 Pipeline execution: 3/3 steps succeeded
[PASS] 5.2 Path resolution: /home/... resolves correctly
[PASS] 5.3 Minimal environment: no hidden system dependencies
[TOTAL] 3/3 passed
```
