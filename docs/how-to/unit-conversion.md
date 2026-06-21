---
audience: [human, agent]
role: user
topic: units
kind: guide
tasks: ["create unit system", "convert quantities", "format labels", "wavenumber setup"]
api: ["SimulationParams", "UnitSystem", "QuantityKind.to", "QuantityKind.label", "QuantityKind.latex"]
cli: []
updated: 2026-06-04
---

# Unit Conversion

Convert between OSIRIS normalized simulation units and physical units (SI, CGS,
and convenient derived units like GV/m, ps, um).

## Background

OSIRIS uses a normalized unit system where physical quantities are scaled by
combinations of the reference plasma frequency ``omega_p``, speed of light
``c``, electron mass ``m_e``, and elementary charge ``e``:

| Quantity   | Normalized unit               |
|------------|-------------------------------|
| time       | ``1 / omega_p``               |
| length     | ``c / omega_p`` (skin depth)  |
| velocity   | ``c``                         |
| momentum   | ``m_e * c``                   |
| energy     | ``m_e * c^2``                 |
| E-field    | ``m_e * c * omega_p / e``     |
| B-field    | ``m_e * omega_p / e``         |
| density    | ``n_0`` (reference density)   |

## Creating a UnitSystem

### From a parsed deck (recommended)

```python
from osiris_toolkit.deck import parse_deck_file
from osiris_toolkit.units import SimulationParams, UnitSystem

deck = parse_deck_file("input/simulation.in")
params = SimulationParams.from_deck(deck)
system = UnitSystem.from_params(params)
```

### From a known omega_p

```python
params = SimulationParams.from_omega_p0(3.55e15)
system = UnitSystem.from_params(params)
```

### Direct construction

```python
params = SimulationParams(omega_p0=3.55e15, omega0_norm=10.0)
system = UnitSystem(omega_p=3.55e15, params=params)
```

The `params` argument is optional but required for wavenumber
conversion (see below).

### Auto-discovery from simulation directory

```python
params = SimulationParams.from_sim_path("/data/Au")
system = UnitSystem.from_params(params)
```

Or use the convenience helper when working with a Simulation:

```python
from osiris_toolkit.vis.common import get_system

sim = Simulation("/data/Au")
system = get_system(sim)  # auto-parses .in file in sim dir
```

## Converting values

Each physical quantity is accessible as an attribute or dict key on `UnitSystem`.
Call `.to()` to convert from normalized to physical units:

```python
# Length
x_um = system.length.to(10.0, "um")       # 10 norm units -> um
x_nm = system["length"].to(10.0, "nm")    # dict-style access

# Time
t_ps = system.time.to(5.0, "ps")

# E-field
e_gvm = system.e_field.to(0.1, "GV/m")

# B-field  
b_tesla = system.b_field.to(0.05, "T")

# Density
n_cm3 = system.density.to(1.0, "cm^-3")

# Energy
e_mev = system.energy.to(100.0, "MeV")

# Frequency
f_thz = system.frequency.to(1.0, "THz")
```

### Auto units

Pass `"auto"` (or omit the unit argument) to use the default physical unit
for each quantity:

```python
system.length.to(10.0)         # "um" (default for length)
system.time.to(5.0)            # "ps"
system.e_field.to(0.1)         # "GV/m"
system.density.to(1.0)         # "cm^-3"
system.energy.to(100.0)        # "MeV"
```

### Normalized units

Pass `"norm"` to keep values in OSIRIS normalized units (identity conversion):

```python
system.length.to(10.0, "norm")  # returns 10.0
```

### Vectorized conversion

`.to()` accepts both scalars and numpy arrays:

```python
import numpy as np
x_norm = np.linspace(0, 100, 1000)
x_um = system.length.to(x_norm, "um")
```

## Formatting labels

Each quantity provides `label()` for human-readable axis labels and `latex()`
for matplotlib rendering:

```python
print(system.length.label("um"))    # "x [um]"
print(system.time.label("ps"))      # "t [ps]"
print(system.e_field.latex("GV/m")) # "$E\ [\mathrm{GV/m}]$"
print(system.length.label("norm"))  # "[c/omega_p]"

# In matplotlib:
ax.set_xlabel(system.length.latex("um"))
ax.set_ylabel(system.e_field.latex("GV/m"))
```

## Available quantities and units

| Quantity      | Attr           | Units                                      | Default (auto) |
|---------------|----------------|--------------------------------------------|----------------|
| length        | `.length`      | norm, m, mm, um, nm, A                     | um             |
| time          | `.time`        | norm, s, fs, ps, ns                        | ps             |
| velocity      | `.velocity`    | norm, m/s, c                               | c              |
| momentum      | `.momentum`    | norm, kg*m/s, MeV/c                        | MeV/c          |
| energy        | `.energy`      | norm, J, eV, keV, MeV, GeV                 | MeV            |
| e_field       | `.e_field`     | norm, V/m, GV/m, TV/m                      | GV/m           |
| b_field       | `.b_field`     | norm, T, kT, MT                            | T              |
| density       | `.density`     | norm, m^-3, cm^-3                          | cm^-3          |
| frequency     | `.frequency`   | norm, rad/s, THz                           | THz            |
| charge        | `.charge`      | norm, C, nC, pC                            | nC             |
| current       | `.current`     | norm, A/m^2                                | A/m^2          |
| mass          | `.mass`        | norm, kg                                   | kg             |
| wavenumber    | `.wavenumber`  | norm, rad/m, rad/um, rad/nm, um^-1, k0     | k0             |

All quantities also support dict-style access: `system["length"]`.

## Wavenumber (k0 unit)

The `k0` unit requires `omega0_norm` (normalized laser frequency). Without it,
`k0` is unavailable:

```python
# k0 available when omega0_norm is known
params = SimulationParams(omega_p0=3.55e15, omega0_norm=10.0)
system = UnitSystem(omega_p=3.55e15, params=params)
k_k0 = system.wavenumber.to(5.0, "k0")  # works

# Without omega0_norm, k0 raises UnitConversionError
system2 = UnitSystem(omega_p=3.55e15)  # no params
system2.wavenumber.to(5.0, "k0")       # UnitConversionError
```

Override `omega0_norm` at runtime:

```python
from dataclasses import replace

scales = dict(system.wavenumber.scales)
scales["k0"] = 1.0 / 20.0  # custom omega0
system.wavenumber = replace(system.wavenumber, scales=scales)
```

## `system=None` fallback

All visualization functions accept `system=None`. When no unit system is
provided, axes and colorbars are displayed in normalized units:

```python
from osiris_toolkit.vis.field import plot_field

plot_field("e1", iteration=100, sim=sim, system=None)
# Axes labeled in normalized units: x1 [c/omega_p], x2 [c/omega_p]
```

## Migration: UnitConverter -> UnitSystem

`UnitConverter` is deprecated since v0.14.0. Migrate as follows:

```python
# Old (deprecated)
from osiris_toolkit.units import UnitConverter, SimulationParams
params = SimulationParams.from_deck(deck)
uc = UnitConverter(params.omega_p0)
val = uc.convert(10.0, "length", "um")
label = uc.get_label("length", "um")

# New (recommended)
from osiris_toolkit.units import UnitSystem
system = UnitSystem.from_params(params)
val = system.length.to(10.0, "um")
label = system.length.label("um")
```

## API Reference

| Class / Method | Description |
|---|---|
| `SimulationParams(omega_p0, n0, gamma, omega0_norm)` | Physical parameters dataclass |
| `SimulationParams.from_deck(deck)` | Extract from parsed deck dict |
| `SimulationParams.from_omega_p0(val)` | Create from known omega_p0 |
| `SimulationParams.from_sim_path(path)` | Auto-discover .in file in sim dir |
| `UnitSystem(omega_p, params)` | Unit system with resolved scales |
| `UnitSystem.from_params(params)` | Create from SimulationParams |
| `QuantityKind.to(data, unit="auto")` | Convert normalized data to target unit |
| `QuantityKind.label(unit="auto")` | Human-readable axis label |
| `QuantityKind.latex(unit="auto")` | LaTeX-formatted axis label |
