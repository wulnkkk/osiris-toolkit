---
audience: [human, agent]
topic: architecture
kind: architecture
updated: 2026-06-04
---

# Data Flow Diagrams

## 1. Real-Space Field Pipeline

```
ZDF file (binary)
  |
  v
io.read_zdf(path) --> GridData (normalized array + GridAxis descriptors)
  |
  v
QuantifiedGrid(grid_data, system=unit_system)
  |  GridData + UnitSystem combined via facade pattern
  v
plot_field(qgrid, comp="e1", ...)
  |  Renders with physical-unit axis labels, colorbars
  v
PNG / displayed figure
```

**Type contract:**
- `read_zdf(str) -> GridData`
- `QuantifiedGrid(GridData, UnitSystem) -> QuantifiedGrid`
- `plot_field(QuantifiedGrid, **kwargs) -> matplotlib.Figure`

## 2. K-Space Pipeline

```
ZDF file (binary)
  |
  v
io.read_zdf(path) --> GridData (normalized real-space array)
  |
  v
compute.fft.compute_k_space(grid_data)
  |  Pure FFT: np.fft.fft2, fftshift
  |  Returns: (complex_ndarray, kx_1d, ky_1d) in normalized units
  v
QuantifiedSpectrum.from_field(grid_data, system=unit_system)
  |  Attaches UnitSystem; stores raw spectrum + wavenumber axes
  v
plot_k_space(qspec, k_unit="k0", ...)
  |  Converts wavenumbers via UnitSystem, renders log-magnitude
  v
PNG / displayed figure
```

**Type contract:**
- `compute_k_space(GridData) -> tuple[ndarray, ndarray, ndarray]`
- `QuantifiedSpectrum.from_field(GridData, UnitSystem) -> QuantifiedSpectrum`
- `plot_k_space(QuantifiedSpectrum, **kwargs) -> matplotlib.Figure`

**Critical rule:** `compute_k_space` never touches `UnitSystem`. It does pure FFT math. The wavenumber axes it returns are in normalized units (cycles per grid cell). `QuantifiedSpectrum` and `plot_k_space` handle the conversion to physical k-units.

## 3. Unit System Initialization

```
Input deck file (text)
  |
  v
deck.parse(input_file) --> Deck AST
  |
  v
units.params.SimulationParams.from_deck(ast)
  |  Extracts: omega_p0, n0, dx, dt, box size, etc.
  v
units.converter.UnitSystem(params)
  |  Resolves QuantityKind -> scale factor for all known quantities
  v
UnitSystem instance
  |
  +--> QuantifiedGrid(system=unit_system)
  +--> QuantifiedSpectrum(system=unit_system)
  +--> plot functions (axis labels, colorbar units)
```

**Type contract:**
- `parse(str) -> Deck`
- `SimulationParams.from_deck(Deck) -> SimulationParams`
- `UnitSystem(SimulationParams) -> UnitSystem`
- `QuantifiedGrid(GridData, UnitSystem) -> QuantifiedGrid`
- `QuantifiedSpectrum(ndarray, ndarray, ndarray, UnitSystem) -> QuantifiedSpectrum`

## Null Unit System Path

When no input deck is available, `UnitSystem` is `None`. All downstream consumers must handle this:

```python
if system is None:
    # Plot with normalized units, no conversion
    label = "kx [k0]"
else:
    kx_phys = system.convert(kx, QuantityKind.WAVENUMBER, "k0")
    label = f"kx [{system.get_unit_str(QuantityKind.WAVENUMBER, 'k0')}]"
```

No silent defaults. No `omega_p=1.0` fallback. The caller decides.
