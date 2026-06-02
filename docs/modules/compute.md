# compute — Pure Numerical Transforms

Stateless numerical functions — numpy in, numpy out. No imports from `sim/`, `units/`, or matplotlib.
Functions in this layer are reusable building blocks for `analysis/` and `vis/`.

## Modules

| File | Role |
|------|------|
| `fft.py` | `compute_k_space()`, `spectral_power()` — 2-D FFT k-space transforms |
| `integrate.py` | `mask_energy()`, `trapz_2d()`, `line_integrate()` — numerical integration |
| `deposit.py` | `particles_to_grid()` — particle→grid deposition (NEW in v0.7.0) |

## FFT

```python
from osiris_toolkit.compute import compute_k_space, spectral_power

# 2-D FFT
kx, ky, spectrum = compute_k_space(data, dx=0.1, dy=0.1, omega0_norm=3.55e15)

# Power spectrum
kx, ky, power = spectral_power(data, dx=0.1, dy=0.1, omega0_norm=3.55e15)
```

Returns k-arrays in dimensionless `k/k0` units and the fftshifted amplitude/power.

## Integration

```python
from osiris_toolkit.compute import line_integrate, mask_energy, trapz_2d

# Line-integrated 1-D profile
profile = line_integrate(data, axis=0)  # integrate over axis 0

# K-space mask energy
energy = mask_energy(spectrum, kx, ky, kx_range=(0, 1), ky_range=(-0.5, 0.5))

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
