---
audience: [human, agent]
role: user
topic: simulation
kind: guide
tasks: ["load simulation", "list diagnostics", "read data", "inspect metadata"]
api: ["Simulation", "list_fields", "list_iterations", "get_field", "get_density", "get_phasespace", "info_field"]
cli: ["sim info", "sim list"]
updated: 2026-06-04
---

# Simulation Browsing

Load, explore, and read data from OSIRIS simulation output directories.

## Construction

```python
from osiris_toolkit.sim import Simulation

# Basic — auto-discovers MS/, HIST/, TIMINGS/
sim = Simulation("/data/Au")

# With custom output root (useful when simulation data is read-only)
sim = Simulation("/data/Au", output_root="/results/figures/Au")
```

`Simulation` accepts the directory that contains the `MS/` subdirectory
(not `MS/` itself). The path is converted to absolute immediately.
It also accepts an optional `config` parameter for per-simulation
`OsirisConfig` overrides.

## Path properties

```python
sim.path         # Absolute path to the simulation directory
sim.output_root  # Root for generated outputs (default: {path}/figures/)
sim.output_dir("k_space")  # Create and return {output_root}/k_space/
sim.run_info     # Parsed contents of the run-info file
sim.detected_format  # "zdf", "hdf5", "mixed", or "unknown"
```

## Listing available data

```python
sim.list_fields()              # ['e1', 'e2', 'e3', 'b1', 'b2', 'b3']
sim.list_species()             # ['electrons', 'Au']
sim.list_iterations("e1")      # [0, 50, 100, ...]
sim.list_iterations("e1", step=5)  # every 5th iteration

sim.list_phasespaces()         # [('x1x2', 'electrons'), ...]
sim.list_tracks()              # ['test_electrons']
sim.list_history()             # ['energy-history']
sim.list_timings()             # ['timing_0000.txt', ...]
sim.list_raw_species()         # species with RAW particle dumps
```

## Reading data

### Fields (EMF)

```python
grid = sim.get_field("e1", iteration=100)
# Returns GridData with .data (ndarray), .axes, .iteration, .time, .label

grid = sim.get_field("e1", iteration=100, report_type="savg")
# Read with a report modifier (e.g. time-averaged "savg" data)
```

### Density

```python
grid = sim.get_density("electrons", "charge", iteration=100)
```

### Phasespace

```python
ps = sim.get_phasespace("x1x2", "electrons", iteration=100)
# Returns PhasespaceData with .data, .axes, .iteration, .time, .deposited_quantity
```

### Cell-average / u-dist / ionization

```python
grid = sim.get_cell_avg("electrons", "ene", iteration=100)
grid = sim.get_udist("electrons", "uflx", iteration=100)
grid = sim.get_ion("electrons", "charge", iteration=100)
```

### Raw particles

```python
raw = sim.get_raw("electrons", iteration=100)
# Returns ParticleData with .data (dict of ndarrays), .nparts, .iteration, .time
```

### Tracks

```python
td = sim.get_tracks("test_electrons")
# Returns TrackData with .tracks, .quants, .niter
```

### History / Timings

```python
hist = sim.get_history("energy-history")
# Returns HistoryData with parsed columns

timing = sim.get_timings("timing_0000.txt")
# Returns TimingsData with profiling data
```

### Charge conservation / Wall

```python
cc = sim.get_chargecons(iteration=100)
wall = sim.get_wall("right", iteration=100)
```

## Reading metadata only (no data arrays)

Use `info_*()` methods for fast metadata inspection without loading data:

```python
fi = sim.info_field("e1", iteration=100)
# FieldInfo: quantity, iteration, time, label, units, ndim, shape, axes

pi = sim.info_raw("electrons", iteration=100)
# ParticleInfo: species, iteration, time, nparts, quants

ti = sim.info_tracks("test_electrons")
# TrackInfo: name, label, ntracks, ndump, niter, quants
```

## CLI

```bash
# Print simulation summary
osiris-toolkit sim info /data/Au

# JSON output (suitable for scripts)
osiris-toolkit sim info /data/Au --output json

# List fields with iteration ranges
osiris-toolkit sim list /data/Au --kind EMF

# List other diagnostic kinds
osiris-toolkit sim list /data/Au --kind DENSITY
osiris-toolkit sim list /data/Au --kind PHASESPACE
osiris-toolkit sim list /data/Au --kind TRACKS
osiris-toolkit sim list /data/Au --kind HISTORY
```

## API Reference

| Method | Returns | Description |
|---|---|---|
| `list_fields()` | `list[str]` | Available field quantities |
| `list_species()` | `list[str]` | Species names across all diagnostics |
| `list_iterations(qty, *, step)` | `list[int]` | Iteration numbers for a field |
| `list_phasespaces()` | `list[tuple[str,str]]` | (ps_name, species) pairs |
| `list_tracks()` | `list[str]` | Track diagnostic names |
| `list_history()` | `list[str]` | History file names |
| `list_timings()` | `list[str]` | TIMINGS file names |
| `list_raw_species()` | `list[str]` | Species with RAW data |
| `get_field(qty, iter)` | `GridData` | Field data (EMF) |
| `get_density(sp, qty, iter)` | `GridData` | Species density |
| `get_phasespace(ps, sp, iter)` | `PhasespaceData` | Phasespace distribution |
| `get_raw(sp, iter)` | `ParticleData` | Raw particle dump |
| `get_tracks(name)` | `TrackData` | Track trajectories |
| `get_history(name)` | `HistoryData` | History text data |
| `get_timings(name)` | `TimingsData` | Profiling data |
| `get_cell_avg(sp, qty, iter)` | `GridData` | Cell-averaged quantities |
| `get_udist(sp, qty, iter)` | `GridData` | u-distribution |
| `get_ion(sp, qty, iter)` | `GridData` | Ionization diagnostic |
| `get_chargecons(iter)` | `GridData` | Charge conservation |
| `get_wall(name, iter)` | `GridData` | Wall diagnostic |
| `info_field(qty, iter)` | `FieldInfo` | Field metadata only |
| `info_raw(sp, iter)` | `ParticleInfo` | Particle metadata only |
| `info_tracks(name)` | `TrackInfo` | Track metadata only |
