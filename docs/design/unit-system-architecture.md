---
audience: [human]
role: developer
topic: design
kind: design
updated: 2026-06-04
language: en
---

# UnitSystem Architecture Design â€?Comprehensive Unit Handling Refactoring

> Date: 2026-06-04
> Type: Design Document
> Target Version: v0.15.0 (or v1.0.0)
> Upstream Analysis:
>   - GitHub Issue [#2](https://github.com/wulnkkk/osiris-toolkit/issues/2) â€?Agent-driven data processing review
>   - GitHub Issue [#3](https://github.com/wulnkkk/osiris-toolkit/issues/3) â€?UnitSystem + k-space 2Ï€ fix

---

## 1. Motivation

The current `UnitConverter` has the following structural deficiencies:

1. **K-space completely bypasses it** â€?`compute_k_space`, `plot_k_space`, `mask_energy` perform ad-hoc unit conversions (Ã—2Ï€, /Ï‰â‚€, Ã·2Ï€) without going through UnitConverter, causing axis labels to deviate from 2Ï€ and xlim to be hardcoded and mismatched with the data
2. **Monolithic coupling** â€?All unit scales are hardcoded in a single 100-line `_build_scales()` function; adding a new dimension requires modifying the function body
3. **Code duplication** â€?Every vis function repeats `if converter is not None` branches Ã— 3-5 times (value conversion, coordinate conversion, label generation)
4. **No type safety** â€?`convert(data, "length", "um")` uses three raw strings; typos are only exposed at runtime
5. **Not extensible** â€?Third parties cannot register custom dimensions

## 2. Design Principles

- **The compute layer only does math; the units layer handles units** â€?FFT does not touch normalization parameters
- **Data and the unit system are composed through a Facade** â€?`GridData` stays pure; `QuantifiedGrid` layers unit capabilities on top
- **Auto-inference first, explicit disambiguation second** â€?`grid.to("um")` auto-detects length; when ambiguous, use `grid.as_quantity("e_field").to("um")`
- **Hard switch, incompatible with old API** â€?Completed in a single major version update; `UnitConverter` â†?`UnitSystem`, `converter` parameter â†?`system` parameter
- **Strict error reporting** â€?Without a system, only `"norm"` units can be used; any non-norm query raises an exception, no fictitious omega_p is assumed

## 3. Architecture Overview

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”?â”? UnitSystem (omega_p, params)                            â”?â”? â”œâ”€â”€ length: QuantityKind                                â”?â”? â”œâ”€â”€ time: QuantityKind                                  â”?â”? â”œâ”€â”€ e_field: QuantityKind                               â”?â”? â”œâ”€â”€ b_field: QuantityKind                               â”?â”? â”œâ”€â”€ wavenumber: QuantityKind      â†?NEW                 â”?â”? â”œâ”€â”€ momentum: QuantityKind                              â”?â”? â”œâ”€â”€ energy: QuantityKind                                â”?â”? â”œâ”€â”€ density: QuantityKind                               â”?â”? â”œâ”€â”€ frequency: QuantityKind                             â”?â”? â”œâ”€â”€ velocity: QuantityKind                              â”?â”? â”œâ”€â”€ charge: QuantityKind                                â”?â”? â”œâ”€â”€ current: QuantityKind                               â”?â”? â””â”€â”€ mass: QuantityKind                                  â”?â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”?               â”?attach to data
               â–?â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”?â”? QuantifiedGrid(grid, system)                            â”?â”? â”œâ”€â”€ .to(unit)          â†?auto-infer quantity            â”?â”? â”œâ”€â”€ .as_quantity(name) â†?explicit quantity view         â”?â”? â”œâ”€â”€ .norm()            â†?raw normalized data            â”?â”? â”œâ”€â”€ .x / .y / .time    â†?_AxisView with .to(), .label() â”?â”? â””â”€â”€ .label / .latex()  â†?unit-aware labels              â”?â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”?               â”?               â–?â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”?â”? QuantifiedSpectrum(result, system)                      â”?â”? â”œâ”€â”€ .kx / .ky            â†?_QuantityView (wavenumber)   â”?â”? â”œâ”€â”€ .spectrum            â†?np.ndarray                   â”?â”? â””â”€â”€ from_field(grid)     â†?factory                      â”?â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”?               â”?               â–?â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”?â”? vis / analysis layer                                    â”?â”? - Accept system parameter (replaces converter)           â”?â”? - Internally use QuantifiedGrid / QuantifiedSpectrum    â”?â”? - Labels obtained from QuantityKind.latex()              â”?â”? - Unit conversions go through the single UnitSystem      â”?â”? - CLI exposes --k-unit, --omega0-norm, --xlim, --ylim...â”?â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”?```

## 4. Core Components

### 4.1 QuantityKind

Each physical quantity is an independent frozen dataclass instance, immutable.

```python
@dataclass(frozen=True)
class QuantityKind:
    name: str                    # "length", "wavenumber", ...
    description: str             # "Spatial coordinate"
    norm_unit_label: str         # "c/omega_p"
    norm_unit_latex: str         # r"c/\omega_p"
    scales: dict[str, float]     # {"norm": 1.0, "um": ..., "nm": ...}
    auto_unit: str               # "um" for length
    label_template: str          # r"x [${unit}$]"  â€?uses "${unit}$" placeholder
    latex_template: str | None   # r"$x\ [\mathrm{${unit}$}]$"  â€?same placeholder
    axis_types: tuple[int, ...]  # e.g., (0, 1) for spatial axes

    def to(self, data, unit="auto") -> np.ndarray: ...
    def label(self, unit="auto") -> str: ...
    def latex(self, unit="auto") -> str: ...
```

Predefined instances: `LENGTH`, `TIME`, `E_FIELD`, `B_FIELD`, `WAVENUMBER`, `MOMENTUM`, `ENERGY`, `DENSITY`, `FREQUENCY`, `VELOCITY`, `CHARGE`, `CURRENT`, `MASS`.

The concrete values in `scales` are computed and populated in `UnitSystem.__init__` (via `dataclasses.replace`).

### 4.2 UnitSystem

```python
class UnitSystem:
    def __init__(self, omega_p: float, params: SimulationParams | None = None):
        # omega_p must be > 0
        # params is optional; dimensions like Wavenumber access additional simulation parameters via params
        
    # Attribute access: system.length, system.wavenumber, ...
    def __getitem__(self, name: str) -> QuantityKind: ...
    
    @classmethod
    def from_params(cls, params: SimulationParams) -> "UnitSystem": ...
```

### 4.3 QuantifiedGrid

```python
@dataclass
class QuantifiedGrid:
    grid: GridData
    system: UnitSystem | None
    
    def to(self, unit="auto") -> np.ndarray:
        """Auto-infer quantity from unit â†?convert data."""
        
    def as_quantity(self, name: str) -> _QuantityView: ...
    def norm(self) -> np.ndarray: ...  # always works
    
    @property
    def x(self) -> _AxisView: ...
    @property
    def y(self) -> _AxisView: ...
    @property
    def time(self) -> _AxisView: ...
```

When `system=None`:
- `.to(unit)` works only when `unit in ("auto", "norm")`, raises `UnitConversionError` otherwise
- `.as_quantity()` always raises an exception
- `.norm()` is always available
- `_AxisView.to(unit)` behaves the same; `_AxisView.label()` falls back to `GridAxis.units`

### 4.4 QuantifiedSpectrum

```python
@dataclass
class QuantifiedSpectrum:
    kx_norm: np.ndarray
    ky_norm: np.ndarray
    spectrum: np.ndarray
    quantity: str
    iteration: int
    time: float
    system: UnitSystem
    
    @property
    def kx(self) -> _QuantityView: ...
    @property
    def ky(self) -> _QuantityView: ...
    
    @classmethod
    def from_field(cls, grid: GridData, system: UnitSystem) -> "QuantifiedSpectrum": ...
```

### 4.5 Auxiliary Classes

```python
@dataclass
class _QuantityView:
    data: np.ndarray
    quantity: QuantityKind
    def to(self, unit="auto") -> np.ndarray: ...
    def label(self, unit="auto") -> str: ...
    def latex(self, unit="auto") -> str: ...

@dataclass
class _AxisView:
    grid: GridData
    axis_index: int
    system: UnitSystem | None
    force_quantity: str | None = None
    def to(self, unit="auto") -> tuple[float, float]: ...  # (min, max)
    def label(self, unit="auto") -> str: ...
    def latex(self, unit="auto") -> str: ...
```

## 5. Wavenumber Dimension

### 5.1 `_build_wavenumber_scales`

```python
def _build_wavenumber_scales(
    k_p_si: float,                   # Ï‰_p / c  [rad/m]
    params: SimulationParams | None,
) -> dict[str, float]:
    scales = {
        "norm": 1.0,                 # k/k_p
        "rad/m": k_p_si,
        "rad/um": k_p_si / 1e6,
        "rad/nm": k_p_si / 1e9,
        "um^-1": k_p_si / (2 * np.pi * 1e6),
    }
    if params is not None and params.omega0_norm is not None:
        scales["k0"] = 1.0 / params.omega0_norm   # k/kâ‚€
    return scales
```

### 5.2 K-space Pipeline

```
ZDF grid â†?compute_k_space(data, dx, dy) â†?kx, ky (normalized angular wavenumber)
         â†?QuantifiedSpectrum.from_field(grid, system)
         â†?qspec.kx.to("k0")  â†? k/kâ‚€  (via system.wavenumber)
         â†?no more handwritten /(2Ï€)
```

### 5.3 Adaptive xlim

```python
def _auto_k_range(k_norm, spectrum, unit, quantity, threshold_frac=0.01, margin=0.1):
    """Automatically determine the display range based on the region where spectrum amplitude exceeds 1% of the peak."""
```

When `xlim=None`, the range is computed automatically; users can override it manually via parameters.

## 6. SimulationParams Extension

```python
@dataclass
class SimulationParams:
    omega_p0: float
    n0: float | None = None
    gamma: float | None = None
    omega0_norm: float | None = None   # â†?NEW

    @classmethod
    def from_deck(cls, deck: dict) -> "SimulationParams":
        # Extract omega0 from antenna / zpulse / laser section
```

## 7. vis/analysis Module Changes

### 7.1 Uniform Signature Change

All vis functions change `converter: UnitConverter | None = None` â†?`system: UnitSystem | None = None`.

Internally, data is accessed via `QuantifiedGrid` / `QuantifiedSpectrum`, and labels are obtained from `QuantityKind`.

### 7.2 Affected Files

| File | Change |
|------|--------|
| `compute/fft.py` | `compute_k_space` removes `omega0_norm` parameter |
| `compute/integrate.py` | `mask_energy` adds `system` parameter, removes `/2Ï€` |
| `vis/common.py` | `get_converter()` â†?`get_system()` |
| `vis/field.py` | converter â†?system |
| `vis/density.py` | converter â†?system |
| `vis/phasespace.py` | converter â†?system |
| `vis/kspace.py` | converter â†?system, removes `/2Ï€`, adds `_auto_k_range` |
| `vis/energy.py` | `plot_spectrum` removes `/2Ï€`, converter â†?system |
| `vis/scattering.py` | converter â†?system |
| `vis/composite.py` | converter â†?system |
| `vis/comparison.py` | converter â†?system |
| `vis/batch.py` | converter â†?system, adds wavenumber diagnostic support + progress |
| `vis/__init__.py` | PostVisHub converter â†?system |
| `analysis/kspace.py` | KSpaceAnalyzer returns `QuantifiedSpectrum` |
| `analysis/_protocol.py` | `_converter` â†?`_system` |
| `analysis/__init__.py` | PostAnalysisHub converter â†?system |
| `units/converter.py` | Retain old `UnitConverter` with DeprecationWarning; add `UnitSystem` + `QuantityKind` |
| `units/params.py` | `SimulationParams` adds `omega0_norm` |
| `postproc.py` | PostProcessor converter â†?system |
| `cli.py` | Add `--k-unit`, `--omega0-norm`, `--xlim`, `--ylim`, `--clim`, `--white-low`, `--dry-run`, `--progress` |

## 8. CLI Changes

### 8.1 `vis plot`

```bash
osiris-toolkit vis plot --kind KSPACE --quantity e1 --iteration 50 <path> \
    --k-unit k0 \           # k0 | rad/um | rad/nm | um^-1 | norm
    --omega0-norm 10.0 \    # optional, auto-extracted from deck if present
    --xlim -3.0,3.0 \
    --ylim -3.0,3.0 \
    --clim -5.0,2.0 \
    --white-low 0.05 \
    --log-scale / --no-log-scale
```

`--k-unit` and other k-space parameters only apply when `--kind KSPACE`; they are ignored for other kinds.

### 8.2 `vis batch`

```bash
osiris-toolkit vis batch --dry-run <path> Au     # preview
osiris-toolkit vis batch <path> Au --progress    # tqdm progress
osiris-toolkit vis batch <path> Au --kinds k_space  # k-space only
```

### 8.3 `sim info`

```bash
osiris-toolkit sim info <path> --output json
# Adds structured output, including omega0_norm
```

## 9. Migration Steps

| Step | Content | Breaking |
|-----|---------|----------|
| 1 | Add `QuantityKind` + `UnitSystem` (retain old `UnitConverter`) | No |
| 2 | Add `QuantifiedGrid`, `QuantifiedSpectrum`, `_AxisView`, `_QuantityView` | No |
| 3 | Add `SimulationParams.omega0_norm` + `_extract_omega0` | No |
| 4 | Rewrite `compute_k_space` (remove `omega0_norm` parameter) | **Yes** |
| 5 | Migrate all vis functions: `converter` â†?`system` | **Yes** |
| 6 | Migrate analysis modules: `_converter` â†?`_system` | **Yes** |
| 7 | Deprecate `UnitConverter` (DeprecationWarning) | No (transition period) |
| 8 | Add CLI k-space parameters | No |
| 9 | Add wavenumber + UnitSystem tests, update existing tests | No |
| 10 | Remove `UnitConverter` + old API | **Yes** |

### User API Changes

```python
# Old
converter = UnitConverter(omega_p=3.55e15)
plot_field("e1", 100, sim=sim, converter=converter, x_unit="um")
plot_k_space("e1", 100, sim=sim, converter=converter, omega0_norm=10.0)

# New
system = UnitSystem(omega_p=3.55e15, params=params)
plot_field("e1", 100, sim=sim, system=system, x_unit="um")
plot_k_space("e1", 100, sim=sim, system=system, k_unit="k0")
```

## References

- Upstream Analysis:
  - GitHub Issue [#2](https://github.com/wulnkkk/osiris-toolkit/issues/2) â€?Agent-driven data processing review
  - GitHub Issue [#3](https://github.com/wulnkkk/osiris-toolkit/issues/3) â€?UnitSystem + k-space 2Ï€ fix
- Downstream Plan: GitHub Issue [#3](https://github.com/wulnkkk/osiris-toolkit/issues/3)
