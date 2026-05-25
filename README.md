# osiris-toolkit

Comprehensive Python toolkit for [OSIRIS](https://osiris-code.org/) PIC (Particle-in-Cell) simulations — input deck parsing, data extraction, unit conversion, analysis, and visualization.

## Features

- **Deck parser** — Full OSIRIS input deck lexer/parser/validator with ~700 parameter schemas across 36 section types and ~46 validation rules
- **Data I/O** — ZDF (Zipped Diagnostic Format) binary reader supporting all 10 ZDF data types, chunked datasets, particles, and tracks
- **Simulation browser** — Auto-discovery of OSIRIS output directory trees with typed accessors for 12 diagnostic types (EMF, density, phasespace, raw, tracks, history, etc.)
- **Unit converter** — Bidirectional conversion between OSIRIS normalized units and physical SI/CGS units (10 physical quantities, multiple unit options)
- **Analysis** — Statistical and physics-domain analysis: field energy, spectra, Poynting flux, density profiles, temperature tensor
- **Visualization** — Plotting routines for all diagnostic types: colormaps, k-space spectra, scattering analysis, batch processing
- **Workflow** — YAML-configurable pipeline for automated deck→analyze→visualize workflows
- **Resource estimation** — Predict memory (per-node), runtime (CPU/wall-clock), and disk space from an input deck before submitting to the cluster
- **Code sync** — Automated extraction of parameter and quantity definitions from OSIRIS Fortran source

## Format Support

OSIRIS outputs simulation data in two formats: **ZDF** (default) and **HDF5**. This toolkit supports **ZDF only**.

- ZDF (Zipped Diagnostic Format) is OSIRIS's default and lighter-weight output format — all 13 diagnostic types are fully supported.
- HDF5 is **not** supported. If your simulation outputs HDF5 files, switch to ZDF by adding this to your input deck:

```
simulation {
    file_format = "zdf",
}
```

See [IO module documentation](docs/modules/io.md) for details on format coverage.

## Installation

```bash
pip install osiris-toolkit
```

For development:

```bash
git clone https://github.com/username/osiris-toolkit.git
cd osiris-toolkit
uv venv
uv sync --dev
```

**Requirements:** Python ≥ 3.10, numpy ≥ 1.20, matplotlib ≥ 3.5

## Quick Start

### Parse an input deck

```python
from osiris_toolkit.deck import parse_deck_file, lint_deck_file

# Parse
deck = parse_deck_file("input/laser-wakefield.in")
for section in deck["sections"]:
    print(f"{section['name']}: {len(section['params'])} parameters")

# Validate
report = lint_deck_file("input/laser-wakefield.in")
print(report.summary())
```

### Browse simulation output

```python
from osiris_toolkit.sim import Simulation

sim = Simulation("/path/to/simulation/output")

# List available data
print(sim.list_fields())       # ['e1', 'e2', 'e3', 'b1', ...]
print(sim.list_species())      # ['electrons', 'protons']

# Read field data
e1 = sim.get_field("e1", iteration=100)
print(e1.data.shape)           # (512, 512)
print(e1.time)                 # 30.0

# Read density
rho = sim.get_density("electrons", "charge", iteration=100)

# Read phasespace
ps = sim.get_phasespace("p1p2", "electrons", iteration=100)
```

### Unit conversion

```python
from osiris_toolkit.deck import parse_deck_file
from osiris_toolkit.units import SimulationParams, UnitConverter

# From a parsed deck
deck = parse_deck_file("input/simulation.in")
params = SimulationParams.from_deck(deck)
uc = UnitConverter(params.omega_p0)

# Convert normalized values to physical units
uc.convert(1.0, "length", "um")     # 0.0844  (skin depth in µm)
uc.convert(1.0, "time", "fs")       # 0.2817  (plasma period in fs)
uc.convert(1.0, "e_field", "GV/m")  # 6058.0  (cold wave-breaking field)

# Get axis labels
uc.get_label("e_field", "GV/m")     # 'E [GV/m]'
uc.get_length_label("um", axis="x") # 'x [um]'
```

### Analyze

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.analysis import Analyzer

sim = Simulation("/path/to/output")
ana = Analyzer(sim)

# Total EM energy
energies = ana.emf.total_em_energy(iteration=50)
# {'e_energy': 1.23e6, 'b_energy': 4.56e5, 'em_energy': 1.69e6}

# Density profile
x, profile = ana.species.density_profile("electrons", "charge", iteration=50)
```

### Visualize

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis import VisEngine

sim = Simulation("/path/to/output")
vis = VisEngine(sim)

# Plot a single field
vis.plot("EMF", quantity="e1", iteration=50, x_unit="um")

# Plot density
vis.plot("DENSITY", species="electrons", quantity="charge", iteration=50)

# Composite view
vis.plot_composite(iteration=100, x_unit="um")
```

### Workflow

```python
from osiris_toolkit.workflow import Pipeline, quick_pipeline

# Programmatic
ctx = quick_pipeline("input/sim.in", "/path/to/output").run()
print(ctx.params.omega_p0)

# From YAML
pipe = Pipeline.from_yaml("workflow.yaml")
ctx = pipe.run()
```

Example `workflow.yaml`:

```yaml
pipeline:
  - deck_parse:
      path: "./input/simulation.in"
  - deck_validate:
  - sim_load:
      path: "./output/"
  - analyze:
      quantities: ["e1", "charge"]
  - visualize:
      kinds: ["EMF", "DENSITY"]
      iteration: 100
      output_dir: "./figures/"
```

### CLI

```bash
# Deck parsing
osiris-toolkit deck parse input/simulation.in
osiris-toolkit deck lint input/simulation.in

# Simulation browsing
osiris-toolkit sim info /path/to/output/
osiris-toolkit sim list /path/to/output/

# Visualization
osiris-toolkit vis plot /path/to/output/ --kind EMF --quantity e1 --iteration 50

# Analysis
osiris-toolkit analyze describe /path/to/output/ --quantity e1 --iteration 50

# Sync from Fortran source
osiris-toolkit sync extract --osiris-path /path/to/osiris-1.0.0/source

# Resource estimation
osiris-toolkit deck estimate input/simulation.in

# Run workflow
osiris-toolkit run workflow.yaml
```

## Architecture

```
osiris-toolkit/
├── deck/         Input deck lexer, parser, validator (700+ params, 36 sections)
├── resource/     Resource estimation: memory, runtime, disk (25+ params)
├── io/           ZDF binary format reader (10 data types)
├── sim/          Simulation directory discovery, 13 diagnostic kinds
├── units/        Normalized ↔ physical unit converter (10 quantities)
├── analysis/     Statistics, EMF energy/spectra, density profiles
├── vis/          Plotting: fields, density, phasespace, k-space, scattering
├── workflow/     YAML pipeline: deck→analyze→visualize
├── sync/         Fortran source extractor (dev-time)
└── _generated/   Auto-generated definitions (59 quantities, 37 sections, 493 params)
```

## Syncing from OSIRIS Source

When OSIRIS is updated, regenerate the parameter and quantity definitions:

```bash
osiris-toolkit sync extract --osiris-path /path/to/osiris-1.0.0/source
```

This produces:
- `_generated/parameters.py` — all namelist parameters with Fortran types and defaults
- `_generated/quantities.py` — all diagnostic quantity names by type
- `_generated/sections.py` — all input section → namelist mappings

Review changes with `git diff _generated/` to see what OSIRIS changed upstream.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

### Third-party format

The ZDF (Zipped Diagnostic Format) binary format was developed at Instituto Superior Tecnico (IST) as part of the ZPIC educational code suite. The ZDF reader in this project is an independent implementation based on the format specification (`zdf/README.md`), verified against real ZDF binary files. It contains no code derived from the ZPIC/OSIRIS reference implementation.
