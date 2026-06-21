---
name: osiris-user
description: >-
  Use when processing OSIRIS PIC simulation data with osiris-toolkit:
  browsing simulation output, plotting fields (EMF, density,
  phasespace), analyzing k-space spectra, converting units, parsing
  input decks, batch processing, or estimating resources. Use this
  when the task involves reading simulation data or producing
  plots/analysis. For developing or modifying the toolkit itself
  (adding features, fixing bugs, running tests, publishing releases),
  load osiris-dev instead.
---

# Agent Skill — osiris-toolkit Operation Manual

## Overview

osiris-toolkit is a Python CLI and library for post-processing OSIRIS PIC simulation data. It handles input deck parsing, ZDF binary file I/O, unit conversion, numerical analysis, and visualization.

> 📖 This is a **specialized skill** loaded on demand. For the cross-platform entry point (always loaded per session), see [`AGENTS.md`](https://github.com/wulnkkk/osiris-toolkit/blob/main/AGENTS.md) at the project root.

## Installation

```bash
pip install osiris-toolkit
```

Requires Python >= 3.10. Optional extras: `[docs]`, `[hdf5]`, `[vtk]`.

For full installation guidance including development setup, see the
[Installation tutorial](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/tutorials/installation.md).

## CLI Quick Reference

| Command group | Quick examples | Full reference |
|---------------|----------------|----------------|
| `deck` | `parse`, `lint`, `validate`, `estimate` | [CLI Reference](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/how-to/cli-reference.md#deck-parse) |
| `sim` | `info`, `list` | [CLI Reference](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/how-to/cli-reference.md#sim-info) |
| `vis` | `plot` (EMF/KSPACE/DENSITY/PHASESPACE), `batch` | [CLI Reference](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/how-to/cli-reference.md#vis-plot) |
| `analyze` | `describe` | [CLI Reference](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/how-to/cli-reference.md#analyze-describe) |
| `run` | `<workflow.yaml>` | [CLI Reference](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/how-to/cli-reference.md#run) |
| `sync` | `extract` | [CLI Reference](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/how-to/cli-reference.md#sync-extract) |

> See the **[complete CLI reference](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/how-to/cli-reference.md)** for detailed usage, all options, and examples.

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

# 4a2. History
result = pp.analyze.history.get_timeseries("ene", "total")
pp.vis.history.timeseries(result)

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
sim.list_history()         # -> ["ene", "pwr"]
sim.list_tracks()          # -> ["track1"]

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

## Gotchas — common mistakes when processing data

These are non-obvious traps that defy reasonable assumptions. Read before writing code.

- **Physical units require an input deck.** Without a parsed deck, `UnitSystem` is `None` and all plots default to normalized units. Never assume `omega_p=1.0` — if the user wants physical units, ask for the input deck file.
- **K-space requires 2-D field data.** 1-D simulations will fail on k-space analysis. Check `sim.list_fields()` and verify the grid dimensions before running FFT.
- **Simulation directories are read-only.** Never write plots or output files into the simulation directory. Always save to a separate output path.
- **Large datasets load entirely into memory.** `GridData` and `ParticleData` are not streamed — loading many iterations at once can cause OOM. Process one iteration at a time or use batch mode.
- **Use `UnitSystem`, not `UnitConverter`.** `UnitConverter` is deprecated since v0.15.0. The `system=` parameter name is the current API — `converter=` is legacy.
- **Remote data must be locally accessible.** There is no built-in SSH/NFS support. Simulation directories must be on a locally mounted filesystem.

## Known Limitations

1. **HDF5 output supported since v0.12.0.** Both ZDF and HDF5 formats are auto-detected and handled transparently. No additional configuration is needed. The optional `hdf5` extra is required: `pip install osiris-toolkit[hdf5]`.
2. **No unit conversion without input deck.** All plots default to normalized units when no deck is available. Physical units require `Deck -> SimulationParams -> UnitSystem`.
3. **K-space requires 2-D data.** 1-D simulations will fail on `vis plot -k KSPACE`.
4. **No streaming/out-of-core for large datasets.** GridData/ParticleData are loaded entirely into memory.
5. **Single-time-step analysis per call.** Cross-iteration analysis (e.g., time evolution of total energy) requires looping in Python.
6. **Animation support is limited.** `animate_field` exists but requires all frames to fit in memory.
7. **No built-in remote data access.** Simulation directories must be locally accessible.

### Reference files

- [User Task Map](references/task-map.md) — **Load this when you know WHAT the user wants to do but not WHICH command to use.** Maps intents like "plot field" or "compare simulations" to CLI commands and Python API calls.
- [Recipes](references/recipes/) — step-by-step walkthroughs for multi-step workflows

### Deep-dive references

For detailed guides, API signatures, and architecture docs beyond this skill:

- **How-to guides:** `docs/how-to/` — deck parsing, simulation browsing, unit conversion, field/k-space/density/phasespace plotting, batch/parallel processing, CLI reference
- **API reference:** `docs/reference/api/` — per-module class signatures, method parameters, return types
- **Tutorials:** `docs/tutorials/` — installation, quick start, basic workflow
- **Other:** `docs/reference/modules/` (module deep dives), `docs/faq.md`

Load these only when you need detailed API signatures or step-by-step instructions beyond what's covered above.
