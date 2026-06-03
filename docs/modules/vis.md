# vis — Visualization

Plotting routines for all OSIRIS diagnostic types. Each module handles one diagnostic kind.
No hardcoded paths — data comes from a `Simulation` object.

## Architecture

```
VisEngine(sim, converter)
    ├── .plot(kind, **kwargs)     Generic agent-friendly interface
    ├── .plot_field()               → field.py
    ├── .plot_density()             → density.py
    ├── .plot_phasespace()          → phasespace.py
    ├── .plot_k_space()             → kspace.py
    ├── .plot_composite()           → composite.py
    └── .batch()                    → batch.py (sequential) / parallel.py (parallel)
```

**Files:**

| File | Role |
|------|------|
| `common.py` | `load_sim()`, `safe_log_norm()`, `save_or_show()` |
| `field.py` | `plot_field()`, `plot_all_fields()` — 2D colormap + 1D line plots |
| `density.py` | `plot_density()` — log/linear, `plasma` colormap + 1D support |
| `phasespace.py` | `plot_phasespace()` — momentum-space distribution |
| `kspace.py` | `compute_k_space()`, `plot_k_space()` — FFT spectrum with white-fade colormap |
| `scattering.py` | `analyze_scattering()`, `plot_scattering_fraction()` — k-region energy analysis |
| `composite.py` | `plot_composite()` — multi-panel overview |
| `batch.py` | `process_simulation()` — batch all plots for all iterations (sequential) |
| `parallel.py` | `batch_process_parallel()` — parallel batch via ProcessPoolExecutor |
| `colormap.py` | `symmetrical_colormap()`, `register_cmaps()` — symmetric diverging colormaps (v0.8.0) |
| `energy_summary.py` | `plot_energy_timeseries()`, `plot_spectrum_colormap()`, `plot_poynting_vector()` (v0.8.0) |
| `comparison.py` | `plot_difference()`, `plot_overlay()` — field comparison plots (v0.8.0) |
| `animation.py` | `animate_field()` — GIF/MP4 time-evolution animation (v0.8.0) |
| `raw.py` | `plot_raw_scatter()`, `plot_raw_momentum()`, `plot_raw_phasespace()`, `plot_raw_energy_spectrum()` — RAW particle visualization (v0.9.0) |
| `tracks.py` | `plot_tracks_orbit()`, `plot_tracks_energy()`, `plot_tracks_field()` — TRACKS trajectory visualization (v0.9.0) |
| `__init__.py` | `PostVisHub` unified entry with `.raw`, `.tracks`, `.field`, `.energy` namespaces |

## Usage

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis import VisEngine, plot_field

sim = Simulation("/path/to/output")
vis = VisEngine(sim)

# Single plot
vis.plot("EMF", quantity="e1", iteration=50, x_unit="um", output="e1.png")
vis.plot_density("electrons", iteration=50, quantity="charge")
vis.plot_phasespace("p1p2", "electrons", iteration=50, p_unit="MeV/c")
vis.plot_k_space("e1", iteration=50)

# Composite view
vis.plot_composite(iteration=100)

# Sequential batch
vis.batch("run01", output_root="./output")

# Parallel batch — 8 workers
vis.batch("run01", output_root="./output", max_workers=8)
```

### Direct function calls

Plot functions accept either a `sim_path` string (creates a new `Simulation`) or a pre-built
`sim` object (reuses it, avoiding redundant directory discovery):

```python
# Old style — still works
plot_field("e1", 50, sim_path="/path/to/output", output="e1.png")

# New style — reuse Simulation (more efficient in loops)
sim = Simulation("/path/to/output")
plot_field("e1", 50, sim=sim, converter=uc, output="e1.png")
plot_field("e2", 50, sim=sim, converter=uc, output="e2.png")
```

### CLI

```bash
# Single plot
osiris-toolkit vis plot /path/to/output/ --kind EMF --quantity e1 --iteration 50

# Sequential batch
osiris-toolkit vis batch -o ./output /data/sim MySim

# Parallel batch (auto-detect workers)
osiris-toolkit vis batch -o ./output -j auto /data/sim MySim

# Parallel batch (explicit 8 workers)
osiris-toolkit vis batch -o ./output -j 8 /data/sim MySim
```

## Key Design Decisions

- **No default paths**: `load_sim()` requires an explicit path. No hardcoded data directories.
- **Simulation reuse**: all plot functions accept an optional `sim=` keyword argument to reuse
  an already-constructed `Simulation` object, eliminating redundant directory discoveries in
  batch processing.
- **Unit-aware**: when a `UnitConverter` is available, axis labels automatically show physical
  units (e.g., `x [um]` instead of `x [c/omega_p]`).
- **Agent-friendly**: `vis.plot("EMF", quantity="e1", iteration=50)` works for programmatic use.
- **Parallel-ready**: `process_simulation()` accepts `max_workers`; when > 0, delegates to the
  parallel implementation. Workers are module-level functions (Windows `spawn` compatible).

## 1D Data Rendering (v0.7.0)

`plot_field()` and `plot_density()` detect 1-D data (e.g., lineouts, slab-averaged diagnostics)
and render a line plot via `ax.plot()` instead of `ax.imshow()`:

```python
# 1D simulation output → automatic line plot
plot_field("e1", iteration=0, sim=sim)
```

## Overwrite Protection (v0.7.0)

All plot functions accept `overwrite=False` (default). When `False`, `save_or_show()` raises
`FileExistsError` if the output file already exists:

```python
plot_field("e1", 0, sim=sim, output="out.png")            # raises if exists
plot_field("e1", 0, sim=sim, output="out.png", overwrite=True)  # overwrites
```

CLI: `--overwrite` flag on `vis plot` and `vis batch`.

## Logging (v0.7.0)

Library code uses Python's `logging` module. Output goes to `stderr`.
CLI verbose/quiet flags control the level:

```bash
osiris-toolkit --verbose vis batch ...   # DEBUG
osiris-toolkit --quiet vis batch ...     # ERROR only
osiris-toolkit vis batch ...             # WARNING (default)
```

## Parallel Performance (v0.7.0)

`batch_process_parallel()` now creates the `Simulation` once in the parent process and
picles it to workers, eliminating redundant directory discovery per worker.

## Field Float-Index Bilinear Interpolation (v0.8.0)

`Field.__getitem__` supports float indices for bilinear interpolation:

```python
field = sim.get_field("e1", 44100)
val = field[2000.5, 1800.3]      # float → bilinear at cell center
line = field[:, 1800.5]            # mixed slice + float → 1D Field
```

## Comparison & Overlay Plots (v0.8.0)

```python
from osiris_toolkit.vis.comparison import plot_difference, plot_overlay

plot_difference("e1", iter_a=0, iter_b=44100, sim=sim)
plot_overlay(["e1", "b3"], iteration=44100, sim=sim, alpha=0.5)
```

## Animation (v0.8.0)

```python
from osiris_toolkit.vis.animation import animate_field

animate_field("e1", sim=sim, output="evolution.gif", fps=10)
```

## Symmetric Colormaps (v0.8.0)

```python
from osiris_toolkit.vis.colormap import symmetrical_colormap, register_cmaps

register_cmaps()
plot_field("e1", 0, sim=sim, cmap="EField")
plot_field("b3", 0, sim=sim, cmap="BField")
```

## RAW Particle Visualization (v0.9.0)

```python
from osiris_toolkit.vis.raw import (
    plot_raw_scatter, plot_raw_momentum,
    plot_raw_phasespace, plot_raw_energy_spectrum,
)

raw = sim.get_raw("electrons", 50)
plot_raw_scatter(raw, "x1", "x2", color_by="ene")
plot_raw_momentum(raw, bins=80)
plot_raw_phasespace(raw, "x1", "p1", color_by="ene")
plot_raw_energy_spectrum(raw, bins=100)
```

All functions accept `color_by`, `cmap`, `alpha`, `marker_size` for tuning.

## TRACKS Trajectory Visualization (v0.9.0)

```python
from osiris_toolkit.vis.tracks import (
    plot_tracks_orbit, plot_tracks_energy, plot_tracks_field,
)

td = sim.get_tracks("track_electrons")
plot_tracks_orbit(td, "x1-x2")
plot_tracks_energy(td, per_track=True)
plot_tracks_field(td, "E1", vs="time")
```

`highlight_tracks` parameter allows emphasizing specific trajectories.

## PostVisHub Namespace Access (v0.9.0)

```python
pp = PostProcessor(sim)
pp.vis.raw.scatter("electrons", 50, x_axis="x1", y_axis="x2")
pp.vis.tracks.orbit("track_electrons", proj="x1-x2")
```

## OsirisConfig Integration (v0.10.0)

`save_or_show()` reads `overwrite` from `OsirisConfig` when not explicitly passed:

```python
from osiris_toolkit.config import OsirisConfig

OsirisConfig.get().overwrite = True
# All subsequent plots overwrite existing files by default
```

`process_simulation()` returns a `BatchResult` with file list and errors:

```python
from osiris_toolkit.vis.batch import process_simulation, BatchResult, ProgressEvent

def on_progress(event: ProgressEvent):
    print(f"{event.iteration}/{event.total}")

result: BatchResult = process_simulation("/data/sim", "run01", progress_callback=on_progress)
print(f"Generated {len(result.files)} files")
```
