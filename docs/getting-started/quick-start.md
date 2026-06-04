---
audience: [human, agent]
topic: quick-start
kind: tutorial
tasks: ["parse deck", "load sim", "convert units", "plot field", "plot k-space"]
api: ["parse_deck_file", "Simulation", "UnitSystem", "plot_field", "plot_k_space"]
cli: ["deck parse", "sim info", "vis plot"]
updated: 2026-06-04
---

# Quick Start

A walk-through of a complete OSIRIS data processing workflow.

## 1. Parse the input deck

```python
from osiris_toolkit.deck import parse_deck_file

deck = parse_deck_file("input/simulation.in")
for sec in deck["sections"]:
    name = sec["name"]
    n_params = len(sec.get("params", {}))
    print(f"  {name}: {n_params} parameters")
```

## 2. Set up unit conversion

```python
from osiris_toolkit.units import SimulationParams, UnitSystem

params = SimulationParams.from_deck(deck)
system = UnitSystem.from_params(params)
print(system)  # UnitSystem(omega_p=3.55e+15 rad/s)
```

## 3. Browse simulation output

```python
from osiris_toolkit.sim import Simulation

sim = Simulation("/path/to/simulation/MS/..")
print(sim.list_fields())          # ['e1', 'e2', 'e3', 'b1', 'b2', 'b3']
print(sim.list_species())         # ['electrons']
print(sim.list_iterations("e1"))  # [0, 100, 200, ...]
```

## 4. Read and convert a field

```python
e1 = sim.get_field("e1", iteration=100)
print(e1.data.shape)              # (4000, 3600)

# Convert coordinates and values to physical units
x_max_um = system.length.to(e1.axes[0].max, "um")
e_max_gvm = system.e_field.to(e1.data.max(), "GV/m")
print(f"Domain: {x_max_um:.1f} um, max |E|: {e_max_gvm:.1f} GV/m")
```

## 5. Plot a field

```python
from osiris_toolkit.vis.field import plot_field

plot_field("e1", iteration=100, sim=sim, system=system,
           x_unit="um", y_unit="um", output="e1_0100.png")
```

## 6. Plot k-space (FFT spectrum)

```python
from osiris_toolkit.vis.kspace import plot_k_space

plot_k_space("e1", iteration=100, sim=sim, system=system,
             k_unit="k0", output="k_e1_0100.png")
```

## CLI equivalents

```bash
# Parse deck
osiris-toolkit deck parse input/simulation.in

# Browse data
osiris-toolkit sim info /path/to/output/

# Plot field
osiris-toolkit vis plot /path/to/output/ --kind EMF --quantity e1 -i 50 -o e1.png

# Plot k-space
osiris-toolkit vis plot /path/to/output/ --kind KSPACE --quantity e1 -i 50 --k-unit k0
```
