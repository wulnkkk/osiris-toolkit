---
audience: [human, agent]
role: developer
topic: modules
kind: reference
module: sim
updated: 2026-06-04
---

# sim — Simulation Data Access Layer

Directory discovery and typed access to OSIRIS simulation output. Traverses the `MS/` directory tree,
catalogs all diagnostic files, and provides typed read methods that return `Field`/`GridData`, `ParticleData`,
`PhasespaceData`, etc.

## Architecture (v0.14.0)

`Simulation` is built from a core class + two mixins:

```
Simulation(_DataAccessors, _InfoAccessors)
    │
    ├── simulation.py   (382 lines)   Core: __init__, _discover*, to_dict/from_dict, properties
    ├── _accessors.py   (560 lines)   _DataAccessors mixin: all get_* / list_* / _read_* methods
    ├── _info.py        (112 lines)   _InfoAccessors mixin: info_field / info_raw / info_tracks
    └── _parse.py       (126 lines)   Filename parsing, report suffix detection, history/timings parsers
```

Data model classes live in `_models.py` (foundation layer), re-exported through
`diagnostics.py` (backward-compatible shim).

**Files:**

| File | Role |
|------|------|
| `simulation.py` | `Simulation` class: directory discovery, configuration, serialization |
| `_accessors.py` | `_DataAccessors` mixin: all typed data accessors (`get_*`, `list_*`, `_read_*`) |
| `_info.py` | `_InfoAccessors` mixin: metadata-only reads (`info_field`, `info_raw`, `info_tracks`) |
| `_parse.py` | Filename/quantity parsing, report suffix detection, history/timings text parsers |
| `diagnostics.py` | Re-export shim → `osiris_toolkit._models` (backward compatibility) |
| `catalog.py` | Declarative `DiagKind` table: 12 diagnostic types with directory patterns, data classes, quantity lists |

## Diagnostic Types

| Kind | Pattern | Data Class | Per-species |
|------|---------|------------|-------------|
| EMF | `MS/FLD/` | `GridData` | No |
| CHARGE_CONS | `MS/CHARGECONS/` | `GridData` | No |
| DENSITY | `MS/DENSITY/{sp}/` | `GridData` | Yes |
| CELL_AVG | `MS/CELL_AVG/{sp}/` | `GridData` | Yes |
| UDIST | `MS/UDIST/{sp}/` | `GridData` | Yes |
| PHASESPACE | `MS/PHA/{ps}/{sp}/` | `PhasespaceData` | Yes |
| RAW | `MS/RAW/{sp}/` | `ParticleData` | Yes |
| TRACKS | `MS/TRACKS/` | `TrackData` | No |
| CURRENT | `MS/CURRENT/` | `GridData` | No |
| ION | `MS/ION/{sp}/` | `GridData` | Yes |
| WALL | `MS/FLD_WALL_*/{name}/` | `GridData` | No |
| HISTORY | `HIST/` | `HistoryData` | No |

## Data Model

### Field (v0.7.0)

`Field` is the primary grid data container, replacing `GridData` (preserved as an alias). Supports
element-wise operators and physical-coordinate slicing:

```python
from osiris_toolkit import Field, GridData  # GridData == Field

# Operator overloading (element-wise on .data)
f1 = sim.get_field("e1", iteration=100)
f2 = sim.get_field("e2", iteration=100)
energy = (f1 ** 2 + f2 ** 2) * 0.5    # returns new Field
diff = f1 - f2                          # Field - Field
scaled = f1 * 3.0                       # scalar multiplication

# Properties
print(f1.ndim)     # number of dimensions
print(f1.shape)    # data shape
print(f1.mean())   # scalar mean
print(f1.mean(axis=0))  # per-column mean (returns array)

# Physical slicing
roi = f1[50:150, 30:120]   # slice by grid indices → new Field with updated axes
center = f1[:, 64]          # scalar index → reduced-dimension Field
```

### GridAxis (v0.7.0)

`GridAxis` now carries `npoints` and coordinate conversion methods:

```python
ax = grid.axes[0]
idx = ax.value_to_index(5.0)     # 5.0 physical → fractional grid index
coord = ax.index_to_value(50)    # grid index → physical coordinate
print(ax.npoints)                # number of grid points along this axis
```

## Usage

```python
from osiris_toolkit.sim import Simulation

sim = Simulation("/path/to/output")

# Discovery
print(sim.list_fields())      # ['e1', 'e2', 'e3', 'b1', ...]
print(sim.list_species())     # ['electrons', 'protons']
print(sim.run_info)           # {'nprocs': '128', 'algorithm': 'standard', ...}

# Read field
e1 = sim.get_field("e1", iteration=100)
print(e1.data.shape)          # (nx, ny)
print(e1.time)                # 30.0

# Metadata-only read (no data loading — fast)
info = sim.info_field("e1", iteration=100)
print(info.shape, info.units, info.axes[0].npoints)

# Report modifier filtering
e1_savg = sim.get_field("e1", iteration=100, report_type="savg")
sim.list_iterations("e1", report_type=None)  # plain only (default)

# Read density
rho = sim.get_density("electrons", "charge", iteration=100)

# Read phasespace
ps = sim.get_phasespace("p1p2", "electrons", iteration=100)

# Read raw particles
raw = sim.get_raw("electrons", iteration=100)
print(raw.data.keys())        # dict_keys(['x1', 'x2', 'p1', 'p2', 'p3', 'q'])

# Read tracks
tracks = sim.get_tracks("track-electrons")
```

## Metadata-Only Accessors (v0.7.0)

Lightweight methods that read ZDF metadata without loading data arrays:

```python
info = sim.info_field("e1", iteration=100)   # → FieldInfo
info = sim.info_raw("electrons", iteration=0) # → ParticleInfo
info = sim.info_tracks("track-electrons")     # → TrackInfo
```

| Return Type | Fields |
|-------------|--------|
| `FieldInfo` | quantity, iteration, time, label, units, ndim, shape, axes, report_type |
| `ParticleInfo` | species, iteration, time, label, nparts, quants |
| `TrackInfo` | name, label, ntracks, ndump, niter, quants |

## Report Modifier Support (v0.7.0)

OSIRIS report modifiers (`savg`, `senv`, `line`, `slice`, `tavg`) are detected from ZDF filenames
during discovery and stored in `_FieldEntry.report_type`. All grid-based accessors accept an
optional `report_type` filter:

```python
# Get spatial average version
e1_savg = sim.get_field("e1", iteration=100, report_type="savg")

# When report_type=None (default), returns only plain (no-modifier) entries
e1 = sim.get_field("e1", iteration=100)  # report_type="" only

# List iterations filtered by modifier
sim.list_iterations("e1")                       # plain only
sim.list_iterations("e1", report_type="savg")   # savg only
```

## Adding a New Diagnostic Type

Add an entry to `catalog.py` in `OSIRIS_DIAGNOSTICS`:

```python
"NEW_TYPE": DiagKind(
    name="NEW_TYPE",
    dir_pattern="MS/NEW/{species}",
    data_class=GridData,
    is_per_species=True,
    quantities=["quant1", "quant2"],
    unit_category="density",
),
```

Then add the corresponding `_discover_*()` method to `Simulation` (in `simulation.py`) and
`get_*()` accessor to `_DataAccessors` (in `_accessors.py`).

## Format Transparency (v0.12.0)

`Simulation` automatically discovers and reads both ZDF (`.zdf`) and HDF5 (`.h5`) files.
No configuration needed — file extension determines the reader:

```python
sim = Simulation("/path/to/output")   # works for ZDF, HDF5, or mixed directories
field = sim.get_field("e1", iteration=50)  # auto-dispatched
```

## Lightweight Serialization (v0.13.0)

`Simulation` supports lightweight serialization for passing references between
sub-tasks (e.g., AI agent workflows):

```python
state = sim.to_dict()                  # {"path": "/output/dir"}
sim2 = Simulation.from_dict(state)     # rebuilds catalog from disk
```

Only the path is serialized — cached catalog data is cheaply rebuilt on load.

## Configuration (v0.10.0)

`Simulation` accepts an optional `OsirisConfig` parameter. When not provided, a snapshot of the global singleton is used:

```python
from osiris_toolkit.config import OsirisConfig
from osiris_toolkit.sim import Simulation

# Inherit from global config
sim = Simulation("/path/to/output")
print(sim.config.x_unit)  # "um" (global default)

# Per-simulation override
custom = OsirisConfig().copy_with(output_root="/other/figures", x_unit="nm")
sim = Simulation("/path/to/output", config=custom)
print(sim.output_root)  # Path("/other/figures")
```

`output_root` cascade: explicit `output_root` kwarg > `sim.config.output_root` > `{sim_path}/figures/`.
