---
audience: [human, agent]
topic: architecture
kind: architecture
updated: 2026-06-04
---

# Unit Conversion Architecture

## Why QuantityKind + UnitSystem Split

The unit conversion system has two distinct responsibilities:

1. **QuantityKind** — Defines *what* a physical quantity is. Immutable descriptor: name, dimension, base SI unit, valid display-unit strings. Examples: `LENGTH`, `TIME`, `WAVENUMBER`, `E_FIELD`.

2. **UnitSystem** — Resolves *how much* one normalized unit equals in physical units, given a specific simulation's parameters. Holds a registry of `QuantityKind -> scale_factor` mappings, computed from `SimulationParams`.

This split exists because:
- A `QuantityKind` instance is global and reusable across simulations (it describes the *kind* of thing, not the *scale*).
- A `UnitSystem` is per-simulation (the scale factors depend on `omega_p0`, `n0`, `dx`, etc. from the input deck).
- Without the split, the old `UnitConverter` class conflated both, leading to fragile state and confusing "which converter am I holding?" bugs.

## Why Compute Layer Must Not Do Unit Conversion

The `compute/` layer is pure math. FFT, integration, and deposition functions operate on normalized arrays with no knowledge of physical units.

**Design invariant:** If you find yourself writing `* 2 * np.pi` or `/ (2 * np.pi)` in any module outside `units/`, the architecture has been violated.

This rule exists because:
- Unit conversion factors depend on simulation parameters (`omega_p0`, `n0`, etc.) which `compute/` has no business knowing.
- Mixing conversion into compute makes functions non-reusable across simulations with different parameters.
- It makes testing harder: you cannot test the FFT independently of unit conversion.

## Wavenumber's Special Dependency

Wavenumber conversion is the most common source of bugs. The normalized wavenumber k_norm (cycles per grid cell) converts to physical k as:

```
k_phys = k_norm * (2 * pi) / dx
```

Or in "k0" units (multiples of the fundamental wavenumber):

```
k_in_k0 = k_norm * N_cells
```

where `N_cells` is the number of grid cells in that dimension.

These conversions require `dx` and `N_cells` from `SimulationParams`, which only `UnitSystem` has. The `compute/` layer MUST return k_norm and let the caller convert.

## System=None Strict Behavior

When no input deck is available, `UnitSystem` is `None`. This is intentional, not a bug:

- Plot functions receive `system=None` and must handle it explicitly.
- Axis labels fall back to normalized notation: `kx [k0]`, `|E| [a.u.]`.
- No `omega_p=1.0` dummy default. A dummy default would silently produce wrong physical units, which is worse than refusing to convert.

Callers that need physical units must provide a parsed deck:

```python
system = UnitSystem.from_deck("input.txt") if deck_available else None
```

## Migration from UnitConverter

The old `UnitConverter` class has been deprecated in favor of `UnitSystem`:

| Old (`UnitConverter`) | New (`UnitSystem`) |
|---|---|
| Mutable state, setters for each param | Immutable after construction |
| Single class, mixed concerns | `QuantityKind` + `UnitSystem` split |
| `converter.length_to_si(value)` | `system.convert(value, QuantityKind.LENGTH, "m")` |
| Ad-hoc unit strings | Registered unit strings per `QuantityKind` |
| No wavenumber support | Full wavenumber support (k0, 1/m, etc.) |

`UnitConverter` remains available as a deprecated shim that wraps `UnitSystem` internally. New code must use `UnitSystem` directly.
