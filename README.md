# osiris-toolkit

Comprehensive Python toolkit for [OSIRIS](https://osiris-code.org/) PIC (Particle-in-Cell)
simulations — input deck parsing, data extraction, unit conversion, analysis, and visualization.

## Install

```bash
pip install osiris-toolkit
```

Requires Python >= 3.10, numpy >= 1.20, matplotlib >= 3.5.

## Quick Start

```python
from osiris_toolkit.deck import parse_deck_file
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import SimulationParams, UnitSystem

# Parse input deck
deck = parse_deck_file("input/simulation.in")
params = SimulationParams.from_deck(deck)
system = UnitSystem.from_params(params)

# Browse simulation output
sim = Simulation("/path/to/output")
print(sim.list_fields())          # ['e1', 'e2', 'e3', 'b1', ...]

# Read a field
e1 = sim.get_field("e1", iteration=100)
print(e1.data.shape)              # e.g. (4000, 3600)

# Convert to physical units
x_um = system.length.to(e1.axes[0].max, "um")
e_gvm = system.e_field.to(e1.data.max(), "GV/m")
print(f"Domain size: {x_um:.1f} um, max E: {e_gvm:.1f} GV/m")
```

```bash
# CLI equivalents
osiris-toolkit deck parse input/simulation.in
osiris-toolkit sim info /path/to/output/
osiris-toolkit vis plot /path/to/output/ --kind EMF --quantity e1 --iteration 50
osiris-toolkit vis batch -o ./figures /path/to/output MySim
```

## Documentation

Full documentation: `pip install "osiris-toolkit[docs]" && mkdocs serve`

## License

MIT. See [LICENSE](LICENSE).

## Community

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Agent Skills (AI-assisted development)](AGENTS.md)
