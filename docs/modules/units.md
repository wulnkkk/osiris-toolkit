# units — Unit Conversion

Bidirectional conversion between OSIRIS normalized simulation units and physical SI/CGS units.
Driven by physical parameters extracted from a parsed input deck, not by fragile regex.

## Architecture

```
Deck ──▶ SimulationParams(omega_p0, n0, gamma) ──▶ UnitConverter(omega_p)
                                                          │
                                                          ├── _build_scales()
                                                          ├── convert(data, quantity, unit)
                                                          └── get_label(quantity, unit)
```

**Files:**

| File | Role |
|------|------|
| `params.py` | `SimulationParams` dataclass: extracts `omega_p0`, `n0`, `gamma` from a parsed deck dict |
| `converter.py` | `UnitConverter` class: scale factors, `convert()`, label generation, legacy SI→norm helpers |

## Supported Quantities

| Quantity | Normalization | Auto unit | Available units |
|----------|--------------|-----------|-----------------|
| `time` | `1/omega_p` | ps | s, fs, ps, ns |
| `length` | `c/omega_p` (skin depth) | um | m, mm, um, nm, A |
| `velocity` | `c` | c | m/s, c |
| `momentum` | `m_e * c` | MeV/c | kg·m/s, MeV/c |
| `energy` | `m_e * c^2` | MeV | J, eV, keV, MeV, GeV |
| `e_field` | `m_e * c * omega_p / e` | GV/m | V/m, GV/m, TV/m |
| `b_field` | `m_e * omega_p / e` | T | T, kT, MT |
| `density` | `n_0` | cm^-3 | m^-3, cm^-3 |
| `frequency` | `omega_p` | THz | rad/s, THz |
| `charge` | `e` | nC | C, nC, pC |

## Usage

```python
from osiris_toolkit.deck import parse_deck_file
from osiris_toolkit.units import SimulationParams, UnitConverter

# From a parsed deck (recommended)
deck = parse_deck_file("simulation.in")
params = SimulationParams.from_deck(deck)
uc = UnitConverter(params.omega_p0)

# Convert
uc.convert(1.0, "length", "um")      # 0.0844  (skin depth)
uc.convert(10.0, "time", "fs")       # 2.817
uc.convert(1.0, "e_field", "GV/m")   # 6058.0  (cold wave-breaking field)

# Auto-unit convenience
uc.convert(1.0, "length", "auto")    # 0.0844 um (auto picks 'um')

# Axis labels for plots
uc.get_time_label("ps")              # 't [ps]'
uc.get_length_label("um", axis="x")  # 'x [um]'
uc.get_label("e_field", "GV/m")      # 'E [GV/m]'

# Reference density
uc.n0_cm3                            # 3.97e21 cm^-3
```

## Key Design Decisions

- **Deck-driven, not regex-driven**: the old `UnitConverter.from_simulation()` used regex to find
  `omega_p0` in `.in` files. Now `SimulationParams.from_deck()` uses the full parser output — accurate
  for all syntax variants.
- **Precomputed scale table**: `_build_scales(omega_p)` builds a nested dict `{quantity: {unit: factor}}` once.
  `convert()` is a dict lookup + multiply — no branching.
- **SI → normalized helpers**: legacy functions (`normalize_time()`, `normalize_length()`, etc.)
  are kept for convenience but marked as legacy.
