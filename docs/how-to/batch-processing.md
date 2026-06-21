---
audience: [human, agent]
role: user
topic: batch
kind: guide
tasks: ["batch process simulation", "dry-run preview", "parallel batch"]
api: ["process_simulation", "PostProcessor.batch", "BatchResult", "ProgressEvent"]
cli: ["vis batch", "vis batch --dry-run", "vis batch --progress"]
updated: 2026-06-04
---

# Batch Processing

Process all iterations of a simulation in one command: field plots, k-space
spectra, density distributions, and scattering analysis.

## Quick example

```python
from osiris_toolkit.vis.batch import process_simulation

result = process_simulation("/data/Au", "Au")
print(f"Generated {len(result.files)} files in {result.elapsed:.0f}s")
print(f"Errors: {result.errors}")
```

## What it generates

`process_simulation()` creates the following directory structure under
`{output_root}/{sim_name}/`:

```
fields/       # Field component images: e1_000100.png, e2_000100.png, ...
k_space/      # FFT k-space images: kspace_e1_000100.png, ...
density/      # Species density images: density_electrons_000100.png, ...
scattering/   # Scattering fraction plots: scattering_e1.png, ...
```

## Parameters

| Parameter         | Type                        | Default      | Description |
|------------------|-----------------------------|--------------|-------------|
| `sim_path`        | `str` or `Path`             | *(required)* | Path to simulation directory |
| `sim_name`        | `str`                       | *(required)* | Human-readable name for output subdirectory |
| `output_root`     | `str` or `Path` or `None`   | `None`       | Root output dir (default: sim's `output_root`) |
| `x_unit`          | `str`                       | `"um"`       | X-axis spatial unit |
| `y_unit`          | `str`                       | `"um"`       | Y-axis spatial unit |
| `time_unit`       | `str`                       | `"ps"`       | Time unit in titles |
| `max_workers`     | `int` or `None`             | `None`       | Parallel workers (None = sequential) |
| `overwrite`       | `bool`                      | `False`      | Overwrite existing files |
| `progress_callback`| `Callable[[ProgressEvent]]` | `None`       | Per-iteration callback |

## BatchResult

```python
@dataclass
class BatchResult:
    sim_name: str       # Human-readable simulation name
    files: list[Path]   # All generated output file paths
    elapsed: float      # Total wall-clock time (seconds)
    errors: list[str]   # Non-fatal error messages
```

## Progress tracking

```python
from osiris_toolkit.vis.batch import process_simulation, ProgressEvent

def on_progress(event: ProgressEvent) -> None:
    print(f"  iter={event.iteration} ({event.elapsed:.1f}s, ETA {event.eta:.0f}s)")

result = process_simulation("/data/Au", "Au", progress_callback=on_progress)
```

## Using PostProcessor

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.postproc import PostProcessor

sim = Simulation("/data/Au")
pp = PostProcessor(sim)
pp.batch(sim_name="Au", max_workers=8)
```

## Custom output root

```python
# Write to a central figures directory instead of in-place
result = process_simulation("/data/Au", "Au", output_root="/results/figures")
# Output goes to /results/figures/Au/fields/, etc.
```

## Parallel execution

Set `max_workers` to enable parallel processing:

```python
result = process_simulation("/data/Au", "Au", max_workers=8)
```

Internally uses `ProcessPoolExecutor` with `spawn` context. BLAS threads are
limited to 1 per worker to prevent thread contention. See the
[parallel execution guide](parallel-execution.md) for details on SLURM and MPI
support.

## CLI

```bash
# Preview what would be generated (no processing)
osiris-toolkit vis batch --dry-run /data/Au Au

# Process with progress bar
osiris-toolkit vis batch --progress /data/Au Au

# Process with 8 parallel workers
osiris-toolkit vis batch -j 8 --progress /data/Au Au

# Custom output directory
osiris-toolkit vis batch -o /results/figures --progress /data/Au Au

# Multiple simulations in one command
osiris-toolkit vis batch --progress /data/Au Au /data/Au0 Au0
```

## API Reference

| Symbol | Description |
|---|---|
| `process_simulation(sim_path, sim_name, ...)` | Run all visualization pipelines on one simulation |
| `BatchResult` | Returned result dataclass |
| `ProgressEvent` | Emitted per-iteration progress dataclass |
| `PostProcessor.batch(sim_name, ...)` | Convenience method via PostProcessor |
