# Test 04: Large-Scale Data Parallel Processing

Tests parallel analysis and batch visualisation throughput on real simulation
output (10-100 GB scale). Measures scaling efficiency across worker counts.

## Requirements

- One compute node with ≥16 CPUs for scaling tests
- Existing OSIRIS simulation output (multiple iterations, ideally 100+)

## How to Run

1. Replace placeholders in both submit scripts.
2. Submit both (can run concurrently):

```bash
sbatch submit_analysis.sh
sbatch submit_batch_vis.sh
```

3. The scripts run the same test with different `--mode` flags:
   - `analysis`: runs `field_energy_all()` with 1/2/4/8 workers, measures speedup
   - `vis`: runs `batch_process_parallel()`, counts output files

## Expected Output (analysis mode)

```
[INFO] Mode: analysis, Iterations: 150, Workers: 1
  Time: 45.2 s,  Memory peak: 320.5 MB
[INFO] Mode: analysis, Iterations: 150, Workers: 2
  Time: 28.1 s,  Memory peak: 380.2 MB,  Speedup: 1.61x
[INFO] Mode: analysis, Iterations: 150, Workers: 4
  Time: 15.3 s,  Memory peak: 510.8 MB,  Speedup: 2.95x
[INFO] Mode: analysis, Iterations: 150, Workers: 8
  Time: 9.8 s,   Memory peak: 890.1 MB,  Speedup: 4.61x
[PASS] 4.1 field_energy_all: 150 iterations
[PASS] 4.3 Scalability: speedup > 1.5x at 4 workers
```

## Expected Output (vis mode)

```
[INFO] Mode: vis
[INFO] Available fields: ['e1', 'e2', 'e3', 'b1', 'b2', 'b3']
[INFO] Available species: ['electrons', 'Au']
[INFO] Iterations: 50
[INFO] Generating plots with 8 workers...
[PASS] 4.2 Batch visualisation: 450 files generated
```
