---
audience: [human, agent]
role: user
topic: phasespace
kind: how-to
tasks: ["plot phasespace", "list available", "configure momentum units"]
api: ["plot_phasespace", "Simulation.list_phasespaces", "Simulation.get_phasespace"]
cli: ["vis plot --kind PHASESPACE", "sim list --kind PHASESPACE"]
updated: 2026-06-04
---

# Phasespace Plotting

Visualize phase-space distributions (p1-p2, x1-p1, etc.) from OSIRIS PHA
diagnostics.

## Listing available phasespaces

```python
from osiris_toolkit.sim import Simulation

sim = Simulation("/data/Au")
for ps_name, species in sim.list_phasespaces():
    print(f"  {ps_name} / {species}")
# Output:
#   p1p2 / electrons
#   x1p1 / electrons
#   x1x2 / electrons
```

## Quick example

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis.phasespace import plot_phasespace
from osiris_toolkit.vis.common import get_system

sim = Simulation("/data/Au")
system = get_system(sim)

plot_phasespace("p1p2", "electrons", iteration=100,
                sim=sim, system=system,
                p_unit="MeV/c", log_scale=True,
                output="phasespace_p1p2_0100.png")
```

## Parameters

| Parameter    | Type               | Default      | Description |
|-------------|---------------------|--------------|-------------|
| `ps_name`    | `str`              | *(required)* | Phase-space name (e.g. `"p1p2"`, `"x1p1"`) |
| `species`    | `str`              | *(required)* | Species name |
| `iteration`  | `int`              | *(required)* | Iteration number |
| `sim_path`   | `str` or `Path`    | `None`       | Path to simulation directory |
| `sim`        | `Simulation`       | `None`       | Pre-constructed Simulation |
| `system`     | `UnitSystem`       | `None`       | Unit system |
| `p_unit`     | `str`              | `"norm"`     | Momentum unit: `"MeV/c"`, `"kg*m/s"`, `"norm"` |
| `time_unit`  | `str`              | `"auto"`     | Time unit in title |
| `log_scale`  | `bool`             | `True`       | Use logarithmic normalization (recommended) |
| `vmin`       | `float`            | `None`       | Colorbar lower limit |
| `vmax`       | `float`            | `None`       | Colorbar upper limit |
| `cmap`       | `str`              | `"plasma"`   | Matplotlib colormap name |
| `output`     | `str` or `Path`    | `None`       | Output file path |

## Momentum units

The `p_unit` parameter controls the axis labels. For momentum-space phasespaces
like `p1p2`, use `"MeV/c"` for physical units:

```python
plot_phasespace("p1p2", "electrons", iteration=100,
                sim=sim, system=system, p_unit="MeV/c")
```

For spatial phasespaces like `x1x2`, the axes are in length units
(automatically handled).

## Log scale

Phasespace distributions typically span many orders of magnitude. Log scale is
enabled by default and recommended:

```python
# Default: log scale on
plot_phasespace("p1p2", "electrons", iteration=100, sim=sim, system=system)

# Linear scale for uniform distributions
plot_phasespace("x1x2", "electrons", iteration=100,
                sim=sim, system=system, log_scale=False)
```

## Reading phasespace data programmatically

```python
ps = sim.get_phasespace("p1p2", "electrons", iteration=100)
# PhasespaceData:
#   .data -> 2-D ndarray (deposited particle weight)
#   .axes -> list of axis dicts with name, label, units, min, max
#   .iteration, .time, .deposited_quantity

print(ps.data.shape)
print(ps.axes[0]["name"], ps.axes[0]["units"])  # e.g. "p1", "p1c"
print(ps.deposited_quantity)  # e.g. "charge"
```

## CLI

```bash
# List available phasespaces
osiris-toolkit sim list /data/Au --kind PHASESPACE

# Plot phasespace
osiris-toolkit vis plot /data/Au --kind PHASESPACE --quantity charge -i 100 -o ps.png
```
