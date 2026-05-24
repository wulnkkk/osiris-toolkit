# sim — Simulation Data Access Layer

Directory discovery and typed access to OSIRIS simulation output. Traverses the `MS/` directory tree,
catalogs all diagnostic files, and provides typed read methods that return `GridData`, `ParticleData`,
`PhasespaceData`, etc.

## Architecture

```
Simulation(path)
    │
    ├── _discover()          Walk MS/, HIST/, TIMINGS/
    │   ├── MS/FLD/      →   _fields
    │   ├── MS/DENSITY/  →   _density
    │   ├── MS/PHA/      →   _phasespace
    │   ├── MS/RAW/      →   _raw
    │   ├── MS/TRACKS/   →   _tracks
    │   └── ...
    │
    ├── list_*()             List available data
    └── get_*()              Read with typed return
            │
            └── io._reader   Stateless ZDF functions
```

**Files:**

| File | Role |
|------|------|
| `simulation.py` | `Simulation` class: directory discovery, 11 typed accessors, history parser |
| `diagnostics.py` | Data containers: `GridData`, `GridAxis`, `ParticleData`, `PhasespaceData`, `TrackData`, `HistoryData` |
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

Then add the corresponding `_discover_*()` method and `get_*()` accessor to `Simulation`.
