---
audience: [human, agent]
topic: modules
kind: reference
module: _models
updated: 2026-06-04
---

# _models — Foundation Data Model (v0.14.0)

All diagnostic data container classes used across the entire toolkit. Lives in the
foundation layer (alongside `exceptions.py`), below `io/`, `compute/`, `sim/`, etc.

Previously these classes were in `sim/diagnostics.py` (middle layer), causing reverse
dependencies from `io/` and `compute/` (bottom layer). `sim/diagnostics.py` is now a
backward-compatible re-export shim.

## Classes

### Field / GridData

Grid-based diagnostic data with operator overloading and physical slicing.
`GridData` is an alias for backward compatibility.

```python
from osiris_toolkit._models import Field

f = Field(data=np.arange(100.0).reshape(10, 10), axes=axes, iteration=50, time=15.0)

# Arithmetic
energy = (f1 ** 2 + f2 ** 2) * 0.5

# Physical slicing
roi = f[50:150, 30:120]
center = f[:, 64.5]  # interpolated

# Serialization
f.to_npz("field.npz")
f.to_csv("field.csv")
f.to_vtk("field")     # requires pyevtk
```

### GridAxis

Axis descriptor with coordinate conversion:

```python
ax = GridAxis(name="x1", min=0.0, max=10.0, npoints=101)
ax.value_to_index(5.0)     # 5.0 → 50.0 (fractional index)
ax.index_to_value(50)      # grid index → 5.0
```

### ParticleData

Per-particle diagnostic data with filter and serialization:

```python
raw = sim.get_raw("electrons", iteration=50)
hot = raw.filter("ene > 100")
hot.to_npz("hot_electrons.npz")
```

### Other Classes

| Class | Purpose |
|-------|---------|
| `PhasespaceData` | Phasespace diagnostic (2D histogram) |
| `TrackData` | Particle track diagnostic (list of per-track arrays) |
| `HistoryData` | Time-series history from text files |
| `TimingsData` | Timing profiles from TIMINGS/ text files |
| `FieldInfo` | Lightweight field metadata (no data loaded) |
| `ParticleInfo` | Lightweight particle metadata |
| `TrackInfo` | Lightweight track metadata |

## Import Paths

```python
# Direct (recommended for new code)
from osiris_toolkit._models import Field, ParticleData

# Via shim (backward compatible)
from osiris_toolkit.sim.diagnostics import Field  # still works

# Via public API
from osiris_toolkit import Field  # works through top-level __init__.py
```
