---
audience: [human, agent]
topic: modules
kind: reference
module: compute
updated: 2026-06-04
---

# compute — Pure Numerical Transforms

Stateless numerical functions — numpy in, numpy out. No imports from `sim/`, `units/`, or matplotlib.
Functions in this layer are reusable building blocks for `analysis/` and `vis/`.

## Modules

| File | Role |
|------|------|
| `fft.py` | `compute_k_space()`, `spectral_power()` — 2-D FFT k-space transforms |
| `integrate.py` | `mask_energy()`, `trapz_2d()`, `line_integrate()` — numerical integration |
| `deposit.py` | `particles_to_grid()` — particle→grid deposition (NEW in v0.7.0) |
| `transform.py` | `remap_field()`, `to_cylindrical()` — coordinate transforms (NEW in v0.8.0) |

## FFT

```python
from osiris_toolkit.compute import compute_k_space, spectral_power

# 2-D FFT — returns raw normalized angular wavenumber (rad / (c/ω_p))
kx, ky, spectrum = compute_k_space(data, dx=0.1, dy=0.1)

# Convert to k/k₀ via UnitSystem
from osiris_toolkit.units import UnitSystem
system = UnitSystem(omega_p=3.55e15, params=params)
kx_k0 = system.wavenumber.to(kx, "k0")

# Power spectrum
kx, ky, power = spectral_power(data, dx=0.1, dy=0.1)
```

Returns k-arrays in normalized angular wavenumber (rad / (c/ω_p)). Use `UnitSystem.wavenumber.to()` for unit conversion to k/k₀ or physical units. The `omega0_norm` parameter was removed in v0.15.0 — normalization is now done through `UnitSystem`.

## Integration

```python
from osiris_toolkit.compute import line_integrate, mask_energy, trapz_2d

# Line-integrated 1-D profile
profile = line_integrate(data, axis=0)

# K-space mask energy (v0.15.0: requires system parameter)
energy = mask_energy(spectrum, kx, ky, kx_range=(0, 1), ky_range=(-0.5, 0.5), system=system)

# 2-D trapezoidal integration
total = trapz_2d(data, dx=0.1, dy=0.1)
```

## Particle-to-Grid Deposition (NEW in v0.7.0)

```python
from osiris_toolkit.compute import particles_to_grid

grid = particles_to_grid(
    positions,            # (nparts, ndim) — in grid-index space (0..nx-1)
    weights=None,         # (nparts,) or None (default: all 1.0)
    grid_shape=(64, 64),
    axes=None,            # optional list[GridAxis]
    shape_function="tophat",  # "ngp" | "tophat" | "triangular" | "spline3"
    use_numba=False,      # enable Numba JIT if installed
)
```

Returns a `Field` with deposited grid data.

**Shape functions:**

| Name | Order | Cells/dim | Description |
|------|-------|-----------|-------------|
| `ngp` | 0 | 1 | Nearest Grid Point — fastest, blocky |
| `tophat` | 1 | 2 | Cloud-In-Cell (CIC) — linear interpolation |
| `triangular` | 2 | 3 | Quadratic B-spline — smoother |
| `spline3` | 3 | 4 | Cubic B-spline — smoothest, most expensive |

Numba acceleration: install `numba` as an optional dependency and set `use_numba=True` for JIT-compiled deposition kernels.

## Coordinate Transforms (NEW in v0.8.0)

```python
from osiris_toolkit.compute import remap_field, to_cylindrical

# Generic 2-D field remap to arbitrary axes
remapped = remap_field(field, (r_axis, theta_axis), interpolation="bilinear")

# Cartesian → polar convenience
polar = to_cylindrical(field, nr=512, ntheta=360)
```

`remap_field` supports `"nearest"` and `"bilinear"` interpolation. `to_cylindrical` auto-computes the grid center as origin and the corner radius as `r_max` if not specified.
