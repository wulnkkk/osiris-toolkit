---
audience: [human, agent]
topic: architecture
kind: architecture
updated: 2026-06-04
---

# K-Space Pipeline

## Complete Pipeline

```
compute_k_space (pure FFT)
    |
    v
QuantifiedSpectrum.from_field (attaches UnitSystem)
    |
    v
qspec.kx.to("k0") (UnitSystem-driven conversion)
    |
    v
plot_k_space (renders)
```

## Step 1: compute_k_space — Pure FFT

```python
from osiris_toolkit.compute.fft import compute_k_space

# Input: GridData (normalized real-space field)
# Output: tuple[ndarray, ndarray, ndarray]
#   - spectrum: complex 2-D FFT result, fftshifted
#   - kx: 1-D wavenumber axis in normalized units (cycles/grid-cell)
#   - ky: 1-D wavenumber axis in normalized units (cycles/grid-cell)
spectrum, kx_norm, ky_norm = compute_k_space(grid_data)
```

**What this step does NOT do:**
- No `* 2 * np.pi` anywhere.
- No access to `UnitSystem`, `SimulationParams`, or `dx`.
- No physical-unit strings or axis labels.

## Step 2: QuantifiedSpectrum.from_field — Attach Unit System

```python
from osiris_toolkit.vis._quantified import QuantifiedSpectrum

# Input: GridData + UnitSystem
# Output: QuantifiedSpectrum
#   - Internally stores: raw_spectrum, kx_norm, ky_norm, system
#   - Provides: .kx, .ky accessors for unit-aware wavenumber queries
qspec = QuantifiedSpectrum.from_field(grid_data, system=unit_system)
```

## Step 3: Wavenumber Conversion

```python
# Convert normalized wavenumber axis to k0 units
kx_k0 = qspec.kx.to("k0")  # UnitSystem converts: k_norm * N_cells
ky_k0 = qspec.ky.to("k0")

# Also supported:
kx_si = qspec.kx.to("1/m")   # Radians per meter
kx_cgs = qspec.kx.to("1/cm") # Radians per centimeter
```

The conversion is handled entirely by `UnitSystem`. The `QuantifiedSpectrum` accessor delegates:

```
qspec.kx.to("k0")
  --> UnitSystem.convert(kx_norm, QuantityKind.WAVENUMBER, "k0")
  --> kx_norm * (2 * pi) / dx  /  (2 * pi / L) = kx_norm * N_cells
```

## Step 4: plot_k_space — Render

```python
from osiris_toolkit.vis.kspace import plot_k_space

# Input: QuantifiedSpectrum + rendering params
# Output: matplotlib.Figure
fig = plot_k_space(qspec, k_unit="k0", log=True, clim=(-4, 2))
```

The plot function reads wavenumber axes via `qspec.kx.to(k_unit)` and applies formatting. It never accesses raw normalized numbers directly — it always goes through the QuantifiedSpectrum accessor.

## Key Rule

> If you find yourself writing `* 2 * np.pi` or `/ (2 * np.pi)` in any module outside `units/`, the architecture has been violated.

The only place `2 * pi` should appear in k-space conversion is inside `UnitSystem.convert()` when handling `QuantityKind.WAVENUMBER`.

## Common Pitfall: Manual K-Space Construction

```python
# WRONG — bypasses UnitSystem
spectrum, kx, ky = compute_k_space(grid)
kx_phys = kx * 2 * np.pi / dx  # Architecture violation!
plt.imshow(np.log10(np.abs(spectrum)), extent=[kx_phys[0], kx_phys[-1], ...])

# CORRECT — goes through QuantifiedSpectrum
qspec = QuantifiedSpectrum.from_field(grid, system=system)
plot_k_space(qspec, k_unit="1/m")
```
