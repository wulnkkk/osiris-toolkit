---
audience: [human, agent]
topic: kspace
kind: guide
tasks: ["compute FFT", "plot k-space", "configure k0 unit", "set axis limits"]
api: ["plot_k_space", "QuantifiedSpectrum", "KSpaceAnalyzer.spectrum", "compute_k_space"]
cli: ["vis plot --kind KSPACE"]
updated: 2026-06-04
---

# K-Space Analysis

Compute and visualize the 2-D FFT spectrum of OSIRIS field data in k-space.

## Quick example

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis.kspace import plot_k_space
from osiris_toolkit.vis.common import get_system

sim = Simulation("/data/Au")
system = get_system(sim)

plot_k_space("e1", iteration=100, sim=sim, system=system,
             k_unit="k0", output="kspace_e1_0100.png")
```

## How it works

1. Reads the 2-D field data from the simulation
2. Computes the 2-D FFT via `compute_k_space()` (direct FFT, no windowing)
3. Creates kx, ky arrays from grid spacing dx, dy
4. Converts wavenumber axes via `system.wavenumber.to(k_unit)`
5. Auto-determines the plot range via `_auto_k_range()` (projects the
   spectrum onto each axis, thresholds at 1% of max amplitude, adds 10% margin)
6. Renders the log-scaled amplitude as a heatmap

## Parameters

| Parameter    | Type               | Default    | Description |
|-------------|---------------------|------------|-------------|
| `quantity`   | `str`              | *(required)* | Field component name |
| `iteration`  | `int`              | *(required)* | Iteration number |
| `sim_path`   | `str` or `Path`    | `None`     | Path to simulation directory |
| `sim`        | `Simulation`       | `None`     | Pre-constructed Simulation |
| `system`     | `UnitSystem`       | `None`     | Unit system (auto-detected if None) |
| `k_unit`     | `str`              | `"k0"`     | Wavenumber unit: `"k0"`, `"rad/um"`, `"rad/nm"`, `"um^-1"`, `"norm"` |
| `time_unit`  | `str`              | `"auto"`   | Time unit in title |
| `log_scale`  | `bool`             | `True`     | Take natural log of FFT amplitude |
| `clim`       | `(float, float)`   | `None`     | Color limits `(vmin, vmax)` for imshow |
| `cmap`       | `str`              | `"jet"`    | Matplotlib colormap name |
| `xlim`       | `(float, float)`   | `None`     | kx-axis range (auto if None) |
| `ylim`       | `(float, float)`   | `None`     | ky-axis range (auto if None) |
| `white_low`  | `float`            | `0.05`     | Fraction of colormap low end faded to white |
| `output`     | `str` or `Path`    | `None`     | Output file path |

## Wavenumber units

The `k0` unit is the default and requires `omega0_norm` to be set:

```python
# system.wavenumber.scales includes "k0" when omega0_norm is known
from osiris_toolkit.units import SimulationParams

params = SimulationParams.from_sim_path("/data/Au")
system = UnitSystem.from_params(params)
# system.wavenumber.scales["k0"] = 1.0 / omega0_norm

# Convert 5.0 normalized wavenumbers to k0
k_k0 = system.wavenumber.to(5.0, "k0")

# Alternative units
k_rad_um = system.wavenumber.to(5.0, "rad/um")
k_um_inv = system.wavenumber.to(5.0, "um^-1")  # k0/(2*pi) equivalent
k_norm  = system.wavenumber.to(5.0, "norm")     # identity
```

### Override omega0_norm at runtime

```python
from dataclasses import replace

scales = dict(system.wavenumber.scales)
scales["k0"] = 1.0 / 20.0  # custom laser frequency
system.wavenumber = replace(system.wavenumber, scales=scales)

plot_k_space("e1", iteration=100, sim=sim, system=system, k_unit="k0")
```

## Auto axis limits

When `xlim` and `ylim` are `None` (the default) and a `UnitSystem` is
available, `_auto_k_range()` determines the plot range automatically:

```python
# The algorithm:
# 1. Project the 2-D spectrum onto each k-axis
# 2. Find where the projection exceeds 1% of the spectrum maximum
# 3. Add 10% margin on each side of the active region
```

To set explicit limits:

```python
plot_k_space("e1", iteration=100, sim=sim, system=system,
             xlim=(-5, 5), ylim=(-5, 5))
```

## QuantifiedSpectrum (programmatic access)

```python
from osiris_toolkit.vis._quantified import QuantifiedSpectrum

grid = sim.get_field("e1", iteration=100)
qspec = QuantifiedSpectrum.from_field(grid, system)

# Access k-space coordinates in physical units
kx_k0 = qspec.kx.to("k0")  # 1-D array
ky_k0 = qspec.ky.to("k0")  # 1-D array

# The raw spectrum (2-D |FFT| amplitude)
spectrum = qspec.spectrum

# Metadata
print(qspec.quantity)   # "e1"
print(qspec.iteration)  # 100
print(qspec.time)       # simulation time
```

## KSpaceAnalyzer

```python
from osiris_toolkit.analysis.kspace import KSpaceAnalyzer

analyzer = KSpaceAnalyzer(sim, system)
spec = analyzer.spectrum("e1", iteration=100)
# Returns a QuantifiedSpectrum object
```

## CLI

```bash
# Basic k-space plot with k0 units
osiris-toolkit vis plot /data/Au --kind KSPACE --quantity e1 -i 100 -o ks.png

# Custom k-unit and limits
osiris-toolkit vis plot /data/Au --kind KSPACE --quantity e1 -i 100 \
    --k-unit rad/um --xlim -5,5 --ylim -5,5

# Override omega0_norm for k0 scaling
osiris-toolkit vis plot /data/Au --kind KSPACE --quantity e1 -i 100 \
    --omega0-norm 20.0

# Custom color range
osiris-toolkit vis plot /data/Au --kind KSPACE --quantity e1 -i 100 \
    --clim -5,10 --white-low 0.1

# Linear scale (no log)
osiris-toolkit vis plot /data/Au --kind KSPACE --quantity e1 -i 100 \
    --no-log-scale
```

## API Reference

| Function / Class | Description |
|---|---|
| `plot_k_space(qty, iter, ...)` | Plot 2-D FFT spectrum of a field |
| `QuantifiedSpectrum.from_field(grid, system)` | Create quantified spectrum from GridData |
| `KSpaceAnalyzer(sim, system)` | K-space analysis hub |
| `KSpaceAnalyzer.spectrum(qty, iter)` | Compute FFT spectrum, return `QuantifiedSpectrum` |
| `KSpaceAnalyzer.list_available()` | List fields available for k-space analysis |
| `_auto_k_range(k_norm, spectrum, unit, quantity)` | Auto-determine plot range from signal extent |
| `batch_k_space(qty, iters, sim_path, ...)` | Generate k-space images for multiple iterations |
