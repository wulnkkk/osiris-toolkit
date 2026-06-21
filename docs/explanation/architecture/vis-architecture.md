---
audience: [human, agent]
role: [user, developer]
topic: architecture
kind: explanation
updated: 2026-06-21
---

# Visualization Architecture

## PostVisHub Namespace Pattern

The visualization layer uses a "hub" with namespace sub-objects:

```python
from osiris_toolkit.vis import PostVisHub

hub = PostVisHub(sim, system=unit_system)
hub.plot_field("e1", iteration=50)            # field plots (direct)
hub.plot_density("electrons", iter=50)        # density plots (direct)
hub.plot_k_space("e1", iter=50)                # k-space plots (direct)
hub.plot_phasespace("electrons", iter=50)      # phase space plots (direct)

hub.field.plot("e1", iter=50)                  # field via namespace
hub.energy.timeline(results)                   # energy via namespace
hub.raw.scatter("electrons", iter=50)           # RAW particles via namespace
hub.raw.momentum("electrons", iter=50)
hub.tracks.plot()                              # particle tracks via namespace

# Scattering is a standalone plot function (not namespaced)
from osiris_toolkit.vis.scattering import plot_scattering_fraction
```

Each namespace (`field`, `energy`, `raw`, `tracks`) exposes methods scoped to
its diagnostic type. Direct methods (`plot_field`, `plot_density`, etc.)
are convenience wrappers that accept `sim` + `system` directly.

## Standardized Plot Function Signatures

All plot functions in `vis/` follow a consistent signature pattern:

```python
def plot_field(
    data,                    # QuantifiedGrid or GridData
    *,
    system: UnitSystem | None = None,
    comp: str = "e1",
    iteration: int | None = None,
    x_unit: str | None = None,
    y_unit: str | None = None,
    clim: tuple[float, float] | None = None,
    cmap: str = "RdBu_r",
    output: str | Path | None = None,
    show: bool = True,
    **kwargs,
) -> Figure:
```

Key conventions:
- `system` parameter: always `UnitSystem | None`, defaults to `None` (strict fallback).
- Unit parameters: `x_unit`, `y_unit`, `k_unit` control axis labeling via `UnitSystem`.
- `clim`: color limits in data units.
- `output`: path to save figure, `None` means display only.
- `show`: whether to call `plt.show()`.
- All plot functions return `matplotlib.figure.Figure`.

## Converter -> System Migration

The old `VisEngine` class (removed in v0.14.0) used `UnitConverter` directly. The new `PostVisHub` uses `UnitSystem` via the `QuantifiedGrid`/`QuantifiedSpectrum` facades.

| Pre-v0.14.0 | v0.14.0+ |
|---|---|
| `VisEngine(sim, converter=conv)` | `PostVisHub(sim, system=unit_system)` |
| `engine.plot_field("e1", 50)` | `hub.field.plot("e1", iteration=50)` |
| `engine.plot_k_space("e1", 50)` | `hub.kspace.plot("e1", iteration=50)` |
| Manual unit strings passed per call | Unit strings resolved from `UnitSystem` |

## Module Organization

```
vis/
  __init__.py         # PostVisHub + public API exports
  _quantified.py      # QuantifiedGrid, QuantifiedSpectrum facades
  field.py            # plot_field
  density.py          # plot_density
  kspace.py           # plot_k_space
  phasespace.py       # plot_phasespace
  energy.py           # plot_energy
  energy_summary.py   # plot_energy_summary
  tracks.py           # plot_tracks
  scattering.py       # plot_scattering
  raw.py              # plot_raw (low-level, no Quantified wrapper)
  comparison.py       # compare_two (side-by-side)
  composite.py        # composite plots (multi-panel)
  animation.py        # animation generation
  batch.py            # batch processing
  colormap.py         # colormap utilities
  common.py           # shared helpers (axis labels, saving)
  parallel.py         # parallel rendering
```

Each plot module exposes one or more `plot_*` functions. The `PostVisHub` in `__init__.py` provides the namespace-based convenience interface.
