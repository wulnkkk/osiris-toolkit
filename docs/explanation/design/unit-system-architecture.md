---
audience: [human]
role: developer
topic: design
kind: explanation
updated: 2026-06-04
---

# UnitSystem Architecture Design — Comprehensive Unit Handling Refactoring

> Date: 2026-06-04
> Type: Design Document
> Target Version: v0.15.0 (or v1.0.0)
> Upstream Analysis:
>   - GitHub Issue [#2](https://github.com/wulnkkk/osiris-toolkit/issues/2) — Agent-driven data processing review
>   - GitHub Issue [#3](https://github.com/wulnkkk/osiris-toolkit/issues/3) — UnitSystem + k-space 2π fix

---

## 1. Motivation

The current `UnitConverter` has the following structural deficiencies:

1. **K-space completely bypasses it** — `compute_k_space`, `plot_k_space`, `mask_energy` perform ad-hoc unit conversions (×2π, /ω₀, ÷2π) without going through UnitConverter, causing axis labels to deviate from 2π and xlim to be hardcoded and mismatched with the data
2. **Monolithic coupling** — All unit scales are hardcoded in a single 100-line `_build_scales()` function; adding a new dimension requires modifying the function body
3. **Code duplication** — Every vis function repeats `if converter is not None` branches × 3-5 times (value conversion, coordinate conversion, label generation)
4. **No type safety** — `convert(data, "length", "um")` uses three raw strings; typos are only exposed at runtime
5. **Not extensible** — Third parties cannot register custom dimensions

## 2. Design Principles

- **The compute layer only does math; the units layer handles units** — FFT does not touch normalization parameters
- **Data and the unit system are composed through a Facade** — `GridData` stays pure; `QuantifiedGrid` layers unit capabilities on top
- **Auto-inference first, explicit disambiguation second** — `grid.to("um")` auto-detects length; when ambiguous, use `grid.as_quantity("e_field").to("um")`
- **Hard switch, incompatible with old API** — Completed in a single major version update; `UnitConverter` → `UnitSystem`, `converter` parameter → `system` parameter
- **Strict error reporting** — Without a system, only `"norm"` units can be used; any non-norm query raises an exception, no fictitious omega_p is assumed

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│  UnitSystem (omega_p, params)                            │
│  ├── length: QuantityKind                                │
│  ├── time: QuantityKind                                  │
│  ├── e_field: QuantityKind                               │
│  ├── b_field: QuantityKind                               │
│  ├── wavenumber: QuantityKind      ← NEW                 │
│  ├── momentum: QuantityKind                              │
│  ├── energy: QuantityKind                                │
│  ├── density: QuantityKind                               │
│  ├── frequency: QuantityKind                             │
│  ├── velocity: QuantityKind                              │
│  ├── charge: QuantityKind                                │
│  ├── current: QuantityKind                               │
│  └── mass: QuantityKind                                  │
└──────────────┬───────────────────────────────────────────┘
               │ attach to data
               ▼
┌──────────────────────────────────────────────────────────┐
│  QuantifiedGrid(grid, system)                            │
│  ├── .to(unit)          → auto-infer quantity            │
│  ├── .as_quantity(name) → explicit quantity view         │
│  ├── .norm()            → raw normalized data            │
│  ├── .x / .y / .time    → _AxisView with .to(), .label() │
│  └── .label / .latex()  → unit-aware labels              │
└──────────────┬───────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│  QuantifiedSpectrum(result, system)                      │
│  ├── .kx / .ky            → _QuantityView (wavenumber)   │
│  ├── .spectrum            → np.ndarray                   │
│  └── from_field(grid)     → factory                      │
└──────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│  vis / analysis layer                                    │
│  - Accept system parameter (replaces converter)           │
│  - Internally use QuantifiedGrid / QuantifiedSpectrum    │
│  - Labels obtained from QuantityKind.latex()              │
│  - Unit conversions go through the single UnitSystem      │
│  - CLI exposes --k-unit, --omega0-norm, --xlim, --ylim...│
└──────────────────────────────────────────────────────────┘
```

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
    label_template: str          # r"x [${unit}$]"  — uses "${unit}$" placeholder
    latex_template: str | None   # r"$x\ [\mathrm{${unit}$}]$"  — same placeholder
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
        """Auto-infer quantity from unit → convert data."""

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
    k_p_si: float,                   # ω_p / c  [rad/m]
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
        scales["k0"] = 1.0 / params.omega0_norm   # k/k₀
    return scales
```

### 5.2 K-space Pipeline

```
ZDF grid → compute_k_space(data, dx, dy) → kx, ky (normalized angular wavenumber)
         → QuantifiedSpectrum.from_field(grid, system)
         → qspec.kx.to("k0")  →  k/k₀  (via system.wavenumber)
         → no more handwritten /(2π)
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
    omega0_norm: float | None = None   # ← NEW

    @classmethod
    def from_deck(cls, deck: dict) -> "SimulationParams":
        # Extract omega0 from antenna / zpulse / laser section
```

## 7. vis/analysis Module Changes

### 7.1 Uniform Signature Change

All vis functions change `converter: UnitConverter | None = None` → `system: UnitSystem | None = None`.

Internally, data is accessed via `QuantifiedGrid` / `QuantifiedSpectrum`, and labels are obtained from `QuantityKind`.

### 7.2 Affected Files

| File | Change |
|------|--------|
| `compute/fft.py` | `compute_k_space` removes `omega0_norm` parameter |
| `compute/integrate.py` | `mask_energy` adds `system` parameter, removes `/2π` |
| `vis/common.py` | `get_converter()` → `get_system()` |
| `vis/field.py` | converter → system |
| `vis/density.py` | converter → system |
| `vis/phasespace.py` | converter → system |
| `vis/kspace.py` | converter → system, removes `/2π`, adds `_auto_k_range` |
| `vis/energy.py` | `plot_spectrum` removes `/2π`, converter → system |
| `vis/scattering.py` | converter → system |
| `vis/composite.py` | converter → system |
| `vis/comparison.py` | converter → system |
| `vis/batch.py` | converter → system, adds wavenumber diagnostic support + progress |
| `vis/__init__.py` | PostVisHub converter → system |
| `analysis/kspace.py` | KSpaceAnalyzer returns `QuantifiedSpectrum` |
| `analysis/_protocol.py` | `_converter` → `_system` |
| `analysis/__init__.py` | PostAnalysisHub converter → system |
| `units/converter.py` | Retain old `UnitConverter` with DeprecationWarning; add `UnitSystem` + `QuantityKind` |
| `units/params.py` | `SimulationParams` adds `omega0_norm` |
| `postproc.py` | PostProcessor converter → system |
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
| 5 | Migrate all vis functions: `converter` → `system` | **Yes** |
| 6 | Migrate analysis modules: `_converter` → `_system` | **Yes** |
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
  - GitHub Issue [#2](https://github.com/wulnkkk/osiris-toolkit/issues/2) — Agent-driven data processing review
  - GitHub Issue [#3](https://github.com/wulnkkk/osiris-toolkit/issues/3) — UnitSystem + k-space 2π fix
- Downstream Plan: GitHub Issue [#3](https://github.com/wulnkkk/osiris-toolkit/issues/3)
