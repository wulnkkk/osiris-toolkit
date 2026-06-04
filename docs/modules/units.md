---
audience: [human, agent]
topic: modules
kind: reference
module: units
updated: 2026-06-04
---

# units — Unit Conversion

Bidirectional conversion between OSIRIS normalized simulation units and physical SI/CGS units.
Driven by physical parameters extracted from a parsed input deck.

## Architecture

```
Deck ──▶ SimulationParams(omega_p0, n0, gamma, omega0_norm)
                │
                ▼
         UnitSystem(omega_p, params)          ← registry (v0.15.0)
                │
                ├── length: QuantityKind      ← immutable descriptor
                ├── time: QuantityKind
                ├── e_field: QuantityKind
                ├── b_field: QuantityKind
                ├── wavenumber: QuantityKind   ← NEW
                ├── momentum: QuantityKind
                ├── energy: QuantityKind
                ├── density: QuantityKind
                ├── frequency: QuantityKind
                ├── velocity: QuantityKind
                ├── charge: QuantityKind
                ├── current: QuantityKind
                └── mass: QuantityKind
```

**Files:**

| File | Role |
|------|------|
| `_quantity.py` | `QuantityKind` frozen dataclass + 13 pre-defined instance templates (v0.15.0) |
| `converter.py` | `UnitSystem` class (v0.15.0) — scale resolution, `__getitem__`, factory methods; `UnitConverter` (deprecated) |
| `params.py` | `SimulationParams` dataclass: extracts `omega_p0`, `n0`, `gamma`, `omega0_norm` from parsed deck |

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
| `wavenumber` | `omega_p/c` (k_p) | k0 | norm, k0, rad/m, rad/um, rad/nm, um⁻¹ |
| `current` | `e * n_0 * c` | A/m² | norm |
| `mass` | `m_e` | kg | norm, kg |

## Usage

```python
from osiris_toolkit.deck import parse_deck_file
from osiris_toolkit.units import SimulationParams, UnitSystem

# From a parsed deck (recommended)
deck = parse_deck_file("simulation.in")
params = SimulationParams.from_deck(deck)
system = UnitSystem.from_params(params)   # UnitSystem, not UnitConverter

# Convert via attribute access
system.length.to(1.0, "um")              # 0.0844  (skin depth)
system.time.to(10.0, "fs")              # 2.817
system.e_field.to(1.0, "GV/m")          # 6058.0

# Dict-style access for dynamic quantity selection
system["wavenumber"].to(100.0, "k0")     # 10.0 (k/k₀, needs omega0_norm)

# Auto-unit convenience (uses each quantity's auto_unit)
system.length.to(1.0)                    # defaults to "um"

# LaTeX-rendered axis labels
system.length.latex("um")               # "$x\ [\mathrm{um}]$"
system.wavenumber.latex("k0")           # "$k\ [\mathrm{k_0}]$"
system.e_field.label("GV/m")            # "E [GV/m]"
```

### With QuantifiedGrid (vis/analysis facade)

```python
from osiris_toolkit.vis._quantified import QuantifiedGrid

qgrid = QuantifiedGrid(grid, system)
qgrid.x.to("um")                         # axis extent in μm
qgrid.as_quantity("e_field").to("GV/m")  # field values in GV/m
qgrid.x.latex("um")                      # LaTeX axis label
```

## Key Design Decisions

- **QuantityKind + UnitSystem split**: `QuantityKind` is an immutable descriptor (frozen dataclass). `UnitSystem` resolves physics-dependent scales at construction time via `dataclasses.replace()`, producing new instances without mutating templates.
- **Deck-driven, not regex-driven**: `SimulationParams.from_deck()` uses the full parser output — accurate for all syntax variants.
- **Precomputed scale table**: scales are resolved once at `UnitSystem` construction. `to()` is a dict lookup + multiply — no branching.
- **Strict fallback**: `UnitSystem` requires valid `omega_p`. Without a deck, the system is `None` and callers can only use `"norm"` unit — no silent fallback to dummy values.
- **Deprecated**: `UnitConverter` is kept for backward compatibility but emits `DeprecationWarning`. Migrate to `UnitSystem`.
