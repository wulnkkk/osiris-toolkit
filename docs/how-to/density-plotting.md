---
audience: [human, agent]
role: user
topic: density
kind: guide
tasks: ["plot density", "configure colorbar", "log scale density"]
api: ["plot_density", "Simulation.get_density"]
cli: ["vis plot --kind DENSITY"]
updated: 2026-06-04
---

# Density Plotting

Visualize particle species density distributions from OSIRIS DENSITY diagnostics.

## Quick example

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis.density import plot_density
from osiris_toolkit.vis.common import get_system

sim = Simulation("/data/Au")
system = get_system(sim)

plot_density("electrons", iteration=100, sim=sim, system=system,
             quantity="charge", x_unit="um", y_unit="um",
             output="density_electrons_0100.png")
```

## Parameters

| Parameter    | Type               | Default      | Description |
|-------------|---------------------|--------------|-------------|
| `species`    | `str`              | *(required)* | Species name (e.g. `"electrons"`, `"Au"`) |
| `iteration`  | `int`              | *(required)* | Iteration number |
| `sim_path`   | `str` or `Path`    | `None`       | Path to simulation directory |
| `quantity`   | `str`              | `"charge"`   | Density data type |
| `sim`        | `Simulation`       | `None`       | Pre-constructed Simulation |
| `system`     | `UnitSystem`       | `None`       | Unit system |
| `x_unit`     | `str`              | `"auto"`     | X-axis unit |
| `y_unit`     | `str`              | `"auto"`     | Y-axis unit |
| `value_unit` | `str`              | `"auto"`     | Colorbar density unit: `"cm^-3"`, `"m^-3"`, `"norm"` |
| `time_unit`  | `str`              | `"auto"`     | Time unit in title |
| `log_scale`  | `bool`             | `False`      | Use logarithmic normalization |
| `vmin`       | `float`            | `None`       | Colorbar lower limit |
| `vmax`       | `float`            | `None`       | Colorbar upper limit |
| `cmap`       | `str`              | `"plasma"`   | Matplotlib colormap name |
| `output`     | `str` or `Path`    | `None`       | Output file path |

## Plotting with log scale

For density data spanning many orders of magnitude:

```python
plot_density("electrons", iteration=100, sim=sim, system=system,
             log_scale=True, value_unit="cm^-3",
             output="density_log.png")
```

## Multiple species

```python
for sp in sim.list_species():
    plot_density(sp, iteration=100, sim=sim, system=system,
                 output=f"density_{sp}_0100.png")
```

## CLI

```bash
# Plot density for the first species found
osiris-toolkit vis plot /data/Au --kind DENSITY --quantity charge -i 100 -o density.png
```
