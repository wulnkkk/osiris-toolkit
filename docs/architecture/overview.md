---
audience: [human, agent]
topic: architecture
kind: architecture
updated: 2026-06-04
---

# Architecture Overview

## Design Principles

1. **Compute layer does pure math, never unit conversion.** FFT, integration, deposition functions receive normalized arrays and return normalized arrays. All physical-unit conversion happens via `UnitSystem`.
2. **Read-only data extraction, write-only visualization.** `sim/` reads ZDF into `GridData`; `vis/` produces PNGs. No module writes to simulation directories.
3. **No reverse dependencies.** Dependency flows: foundation --> bottom --> middle --> top. `compute/` cannot import `sim/`. `io/` cannot import `vis/`.
4. **Facade pattern for unit coupling.** `GridData` is pure normalized data. `QuantifiedGrid` combines it with `UnitSystem`. Analysis/vis layers consume `Quantified*`, never raw data + converter.
5. **Strict fallback, no silent defaults.** Without a parsed input deck, `UnitSystem` is `None`. Callers must handle this explicitly. No dummy `omega_p=1.0`.

## Module Map

```
+---------------------------------------------------+
|  upper   postproc  workflow  parallel  cli        |
+---------------------------------------------------+
|  middle  sim  analysis  vis  resource             |
+---------------------------------------------------+
|  bottom  deck  io  units  compute  sync           |
+---------------------------------------------------+
|  base    exceptions  _models  _generated          |
+---------------------------------------------------+
```

Each layer may only import from layers below it. Violations are caught by CI lint rules.

## Key Data Types

| Type | Layer | Role |
|------|-------|------|
| `GridData` | base | Normalized field data + axis descriptors |
| `ParticleData` | base | Normalized particle data |
| `QuantityKind` | units | Immutable physical quantity descriptor |
| `UnitSystem` | units | Registry of resolved quantity scales |
| `QuantifiedGrid` | vis | `GridData` + `UnitSystem` facade |
| `QuantifiedSpectrum` | vis | FFT result + wavenumber conversion facade |

## Cross-Cutting Rules

- **No `print()` in library code.** Use `logging` or raise exceptions.
- **CLI output:** `click.echo` for user-facing text, `--output json` for machine-readable.
- **Configuration:** `OsirisConfig` singleton for global settings.
- **Testing:** pytest + ruff. `uv run pytest` and `uv run ruff check src/`.
