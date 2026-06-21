---
audience: [human, agent]
role: user
topic: field
kind: how-to
tasks: ["plot field", "plot all fields", "configure units", "customize appearance"]
api: ["plot_field", "plot_all_fields", "QuantifiedGrid"]
cli: ["vis plot --kind EMF"]
updated: 2026-06-04
---

# Field Plotting

Visualize electromagnetic field components (E1, E2, E3, B1, B2, B3) from
OSIRIS EMF diagnostics.

## Quick example

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis.field import plot_field
from osiris_toolkit.vis.common import get_system

sim = Simulation("/data/Au")
system = get_system(sim)

plot_field("e1", iteration=100, sim=sim, system=system,
           x_unit="um", y_unit="um", value_unit="GV/m",
           output="e1_0100.png")
```

## Parameters

| Parameter    | Type               | Default    | Description |
|-------------|---------------------|------------|-------------|
| `quantity`   | `str`              | *(required)* | Field component: `e1`, `e2`, `e3`, `b1`, `b2`, `b3` |
| `iteration`  | `int`              | *(required)* | Iteration number to read |
| `sim_path`   | `str` or `Path`    | `None`     | Path to simulation directory |
| `sim`        | `Simulation`       | `None`     | Pre-constructed Simulation (takes priority over `sim_path`) |
| `system`     | `UnitSystem`       | `None`     | Unit system; `None` = normalized units |
| `x_unit`     | `str`              | `"auto"`   | X-axis unit: `"um"`, `"nm"`, `"mm"`, `"norm"`, `"auto"` |
| `y_unit`     | `str`              | `"auto"`   | Y-axis unit |
| `value_unit` | `str`              | `"auto"`   | Colorbar unit: `"GV/m"`, `"TV/m"` (E), `"T"`, `"kT"` (B) |
| `time_unit`  | `str`              | `"auto"`   | Time unit in title: `"ps"`, `"fs"`, `"norm"` |
| `log_scale`  | `bool`             | `False`    | Use symmetric-log normalization |
| `vmin`       | `float`            | `None`     | Colorbar lower limit (auto if None) |
| `vmax`       | `float`            | `None`     | Colorbar upper limit |
| `cmap`       | `str`              | `"RdBu_r"` | Matplotlib colormap name |
| `output`     | `str` or `Path`    | `None`     | Output file path (`None` = show interactive) |
| `overwrite`  | `bool`             | `False`    | Overwrite existing output file |

## Auto unit selection

When `x_unit`, `y_unit`, or `value_unit` is `"auto"`, the unit is inferred from
the data range. For fields, `value_unit="auto"` selects between GV/m, TV/m, V/m,
T, kT, MT depending on the field component and magnitude.

## Using normalized units

Pass `system=None` or omit the system to display in OSIRIS normalized units:

```python
plot_field("e3", iteration=100, sim=sim)
# Axes: x1 [c/omega_p], x2 [c/omega_p]
# Colorbar: E [m_e * c * omega_p / e]
```

## Plot all fields at once

```python
from osiris_toolkit.vis.field import plot_all_fields

plot_all_fields(iteration=100, sim=sim, system=system,
                x_unit="um", y_unit="um",
                output="all_fields_0100.png")
```

Creates a multi-panel figure with one subplot per available field component
(up to 3 columns).

## Working with QuantifiedGrid

For programmatic access to converted data and coordinates:

```python
from osiris_toolkit.vis._quantified import QuantifiedGrid

grid = sim.get_field("e1", iteration=100)
qgrid = QuantifiedGrid(grid, system)

# Access spatial coordinates in physical units
x_um = qgrid.x.to("um")      # 1-D array
y_um = qgrid.y.to("um")      # 1-D array

# Access field values in physical units
e_gvm = qgrid.as_quantity("e_field").to("GV/m")

# Or use the normalized value directly
e_norm = qgrid.norm()
```

## CLI

```bash
# Plot e1 at iteration 50
osiris-toolkit vis plot /data/Au --kind EMF --quantity e1 -i 50 -o e1.png

# Plot all field components
osiris-toolkit vis plot /data/Au --kind EMF --quantity e2 -i 100 --log-scale
```
