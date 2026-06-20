---
audience: [human, agent]
role: [user, developer]
topic: overview
kind: index
updated: 2026-06-04
---

# osiris-toolkit

Comprehensive Python toolkit for [OSIRIS](https://osiris-code.org/) PIC (Particle-in-Cell)
simulations — input deck parsing, data extraction, unit conversion, analysis, and visualization.

## Quick Navigation

| I want to... | Start here |
|-------------|-----------|
| Install and try it out | [Installation](getting-started/installation.md) → [Quick Start](getting-started/quick-start.md) |
| Parse an input deck | [Deck Parsing](user-guide/deck-parsing.md) |
| Browse simulation data | [Simulation Browsing](user-guide/simulation-browsing.md) |
| Convert to physical units | [Unit Conversion](user-guide/unit-conversion.md) |
| Generate figures | [Field Plotting](user-guide/field-plotting.md) · [K-Space](user-guide/kspace-analysis.md) · [Batch](user-guide/batch-processing.md) |
| Understand the architecture | [Architecture Overview](architecture/overview.md) |
| Look up a function or class | [API Reference](api/sim.md) |
| Use AI to help process data | [`AGENTS.md` on GitHub](https://github.com/wulnkkk/osiris-toolkit/blob/main/AGENTS.md) — AI assistants auto-load this entry point |
| Use AI to help develop | [`AGENTS.md` on GitHub](https://github.com/wulnkkk/osiris-toolkit/blob/main/AGENTS.md) — then load the dev skill |

## Key Features

- **Input deck parser & validator** — 700+ parameters across 36 section types
- **ZDF binary reader** — all 10 ZDF data types
- **Simulation browser** — auto-discovery of OSIRIS output directories
- **Unit conversion** — bidirectional normalized ↔ SI/CGS for 13 physical quantities
- **FFT k-space analysis** — 2-D spectra with unit-aware wavenumber conversion
- **Batch visualization** — parallel multi-core processing with progress feedback
- **Resource estimation** — predict memory/runtime/disk from input deck

## Architecture at a Glance

```
osiris-toolkit/
├── deck/         Input deck lexer, parser, validator
├── resource/     Resource estimation: memory, runtime, disk
├── io/           ZDF binary format reader
├── sim/          Simulation directory discovery
├── units/        Normalized ↔ physical unit system (QuantityKind + UnitSystem)
├── compute/      Pure numerical transforms (FFT, integration, deposition)
├── analysis/     Statistics, EMF energy/spectra, scattering
├── vis/          Plotting: fields, density, phasespace, k-space
├── parallel/     Multi-core / SLURM / MPI execution
├── workflow/     YAML-configurable automation pipeline
└── _generated/   Auto-generated parameter/quantity definitions
```

See [Architecture Overview](architecture/overview.md) for details.
