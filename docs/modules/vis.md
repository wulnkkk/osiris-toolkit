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
    └── .batch()                    → batch.py
```

**Files:**

| File | Role |
|------|------|
| `common.py` | `load_sim()`, `safe_log_norm()`, `save_or_show()` |
| `field.py` | `plot_field()`, `plot_all_fields()` — 2D colormap |
| `density.py` | `plot_density()` — log/linear, `plasma` colormap |
| `phasespace.py` | `plot_phasespace()` — momentum-space distribution |
| `kspace.py` | `compute_k_space()`, `plot_k_space()` — FFT spectrum with white-fade colormap |
| `scattering.py` | `analyze_scattering()`, `plot_scattering_fraction()` — k-region energy analysis |
| `composite.py` | `plot_composite()` — multi-panel overview |
| `batch.py` | `process_simulation()` — batch all plots for all iterations |
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

# Batch process all diagnostics
vis.batch("run01", x_unit="um", time_unit="ps")
```

## Key Design Decisions

- **No default paths**: `load_sim()` requires an explicit path. No hardcoded data directories.
- **Unit-aware**: when a `UnitConverter` is available (via bound deck), axis labels automatically
  show physical units (e.g., `x [um]` instead of `x [c/omega_p]`).
- **Agent-friendly**: `vis.plot("EMF", quantity="e1", iteration=50)` works for programmatic use.
- **Batch delegates**: `batch.py` calls the other modules' public functions rather than reimplementing
  plotting logic inline (unlike the original `batch_process.py`).
