---
audience: [agent]
role: user
topic: agent
kind: skill
updated: 2026-06-20
---

# Agent Skill — osiris-toolkit Operation Manual

## Overview

osiris-toolkit is a Python CLI and library for post-processing OSIRIS PIC simulation data. It handles input deck parsing, ZDF binary file I/O, unit conversion, numerical analysis, and visualization.

## CLI Quick Reference

| Command | Purpose |
|---------|---------|
| `osiris-toolkit --help` | List all command groups |
| `osiris-toolkit --version` | Print version |
| `osiris-toolkit -v ...` | Verbose mode (DEBUG logging) |
| `osiris-toolkit -q ...` | Quiet mode (ERROR only) |

### deck

| Command | Purpose |
|---------|---------|
| `osiris-toolkit deck parse <FILE>` | Parse input deck to JSON or Python dict |
| `osiris-toolkit deck parse <FILE> -o json` | JSON output (default) |
| `osiris-toolkit deck parse <FILE> -o python` | Python repr output |
| `osiris-toolkit deck lint <FILE>` | Validate and print issues |
| `osiris-toolkit deck validate <FILE>` | Validate, exit non-zero on errors |
| `osiris-toolkit deck estimate <FILE>` | Estimate memory/runtime/disk from deck |
| `osiris-toolkit deck estimate <FILE> -c 64 -e 0.2` | With cores-per-node and efficiency |

### sim

| Command | Purpose |
|---------|---------|
| `osiris-toolkit sim info <DIR>` | Summary of all diagnostics in output dir |
| `osiris-toolkit sim info <DIR> -o json` | Machine-readable JSON output |
| `osiris-toolkit sim list <DIR> -k EMF` | List fields and their iteration ranges |
| `osiris-toolkit sim list <DIR> -k DENSITY` | List available species |
| `osiris-toolkit sim list <DIR> -k PHASESPACE` | List phasespace/species pairs |
| `osiris-toolkit sim list <DIR> -k TRACKS` | List track names |
| `osiris-toolkit sim list <DIR> -k HISTORY` | List history file names |

### vis

| Command | Purpose |
|---------|---------|
| `osiris-toolkit vis plot <DIR> -k EMF -q e1 -i 50` | Plot field e1 at iteration 50 |
| `osiris-toolkit vis plot <DIR> -k KSPACE -q e1 -i 50 --k-unit k0` | K-space plot with k0 units |
| `osiris-toolkit vis plot <DIR> -k KSPACE ... --omega0-norm 10.0` | Override laser frequency |
| `osiris-toolkit vis plot <DIR> ... --clim -4,2 --log-scale` | Color range + log scale |
| `osiris-toolkit vis plot <DIR> ... -o output.png --overwrite` | Specify output path |
| `osiris-toolkit vis batch <PATH> <NAME> [<PATH2> <NAME2> ...]` | Batch process simulations |
| `osiris-toolkit vis batch ... --dry-run` | Preview batch without processing |
| `osiris-toolkit vis batch ... -j 8 --progress` | Parallel with progress bar |
| `osiris-toolkit vis batch ... -o /output/root` | Custom output root directory |

### analyze

| Command | Purpose |
|---------|---------|
| `osiris-toolkit analyze describe <DIR> -q e1 -i 50` | Stats (mean, std, min, max, rms) |

### run

| Command | Purpose |
|---------|---------|
| `osiris-toolkit run <workflow.yaml>` | Execute a YAML workflow pipeline |

### sync

| Command | Purpose |
|---------|---------|
| `osiris-toolkit sync extract --osiris-path <PATH>` | Extract definitions from Fortran source |

## Python API Entry Points

### Top-Level Objects

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units.converter import UnitSystem
from osiris_toolkit.units.params import SimulationParams
from osiris_toolkit.postproc import PostProcessor
from osiris_toolkit.vis import PostVisHub
from osiris_toolkit.analysis import PostAnalysisHub
from osiris_toolkit.deck import parse_deck_file, lint_deck_file
```

### Typical Workflow

```python
# 1. Load simulation
sim = Simulation("/path/to/sim/output")

# 2. Parse input deck (optional, needed for physical units)
from osiris_toolkit.deck import parse_deck_file
deck = parse_deck_file("/path/to/input.txt")
params = SimulationParams.from_deck(deck)
system = UnitSystem(params)

# 3. Unified post-processing
pp = PostProcessor(sim, system=system)

# 4a. Visualization
pp.vis.field.plot("e1", iteration=50, x_unit="um")
pp.vis.plot_k_space("e1", iteration=50, k_unit="k0")

# 4b. Analysis
result = pp.analyze.emf.field_energy("e1", iteration=50)
print(result.total_energy)

# 4c. Batch
pp.batch(sim_name="my_run", x_unit="um", time_unit="ps")
```

### Simulation Data Access

```python
# List available data
sim.list_fields()          # -> ["e1", "e2", "e3", "b1", "b2", "b3"]
sim.list_iterations("e1")  # -> [0, 10, 20, ...]
sim.list_species()         # -> ["electrons", "ions"]

# Read data
grid = sim.get_field("e1", iteration=50)   # -> GridData
particles = sim.get_raw("electrons", 50)   # -> ParticleData
tracks = sim.get_tracks("tracks_name")      # -> TrackData
```

### Direct Plot Function Calls

```python
from osiris_toolkit.vis import plot_field, plot_k_space, plot_density
from osiris_toolkit.vis import plot_energy_timeline, plot_phasespace

plot_field(sim=sim, system=system, quantity="e1", iteration=50, output="out.png")
plot_k_space(sim=sim, system=system, quantity="e1", iteration=50, k_unit="k0")
plot_density(sim=sim, system=system, species="electrons", iteration=50)
```

## Decision Tree for Common User Intents

```
User says: "plot field"
  -> Does user specify iteration?
    No  -> sim.list_iterations("e1"), suggest range
    Yes -> vis plot -k EMF -q <quantity> -i <iteration>

User says: "k-space" / "FFT"
  -> Need 2-D field data? Check sim.list_fields()
  -> vis plot -k KSPACE -q e1 -i <iter> --k-unit k0
  -> Advanced: omega0_norm override, clim, white_low -> Python API

User says: "batch process" / "process data"
  -> vis batch <PATH> <NAME> --dry-run first to preview
  -> Then: vis batch <PATH> <NAME> -j N --progress

User says: "compare" / "compare two simulations"
  -> Load two Simulations -> Python API with plot_difference or plot_overlay
  -> No direct CLI command

User says: "energy" / "field energy"
  -> Python API: pp.analyze.emf.field_energy("e1", iteration=50)
  -> CLI: analyze describe for basic stats

User says: "convert units"
  -> Python API: system.convert(value, QuantityKind.LENGTH, "um")
  -> No direct CLI command; units attach automatically in vis

User says: "parse deck" / "check input"
  -> deck parse <FILE> for content
  -> deck validate <FILE> for error checking
  -> deck estimate <FILE> for resource prediction
```

## Known Limitations

1. **HDF5 output not supported.** Only ZDF format. If `sim_info` shows "hdf5" format, re-run the simulation with `file_format = "zdf"`.
2. **No unit conversion without input deck.** All plots default to normalized units when no deck is available. Physical units require `Deck -> SimulationParams -> UnitSystem`.
3. **K-space requires 2-D data.** 1-D simulations will fail on `vis plot -k KSPACE`.
4. **No streaming/out-of-core for large datasets.** GridData/ParticleData are loaded entirely into memory.
5. **Single-time-step analysis per call.** Cross-iteration analysis (e.g., time evolution of total energy) requires looping in Python.
6. **Animation support is limited.** `animate_field` exists but requires all frames to fit in memory.
7. **No built-in remote data access.** Simulation directories must be locally accessible.
