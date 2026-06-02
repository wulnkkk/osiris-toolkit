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
| `__init__.py` | `VisEngine` unified entry |

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
