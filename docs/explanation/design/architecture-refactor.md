---
audience: [human]
role: developer
topic: design
kind: design
updated: 2026-06-04
---

# Architecture Refactor — Data Model Downlift + Simulation Split + Dead Code Cleanup

> 2026-06-04 | Design Specification
> Version Iteration: v0.14.0

---

## Goals

Eliminate architectural debt through two-phase refactoring:
1. **Data Model Downlift** — Extract data classes from `diagnostics.py` into `_models.py`, eliminating 3 reverse dependencies
2. **Simulation Split + Dead Code Cleanup** — Split the 1,120-line `Simulation` into independently testable modules; remove deprecated APIs

## Motivation

Three pain points in the current architecture share a common root cause:

```
Root Cause: diagnostics.py data models placed in the middle layer (sim/)
  ↓
Symptom 1: io/compute reverse-depend on sim (#60)
Symptom 2: Simulation is 1,120 lines (#62), mixing discovery + parsing + access + metadata
Symptom 3: Deprecated APIs remain undeleted, PostProcessor/PostVisHub only partially supersedes
```

---

## Phase 1: Data Model Downlift

### Current Dependency Hierarchy

```
Bottom layer:  exceptions  _generated  deck  io  units  compute
Middle layer:  sim (contains diagnostics.py data classes)
Upper layer:   analysis  vis  postproc  workflow
```

### After Fix

```
Base layer:    exceptions  _generated  _models  ← NEW
Bottom layer:  deck  io  units  compute        ← can safely import _models
Middle layer:  sim (diagnostics.py → shim)
Upper layer:   analysis  vis  postproc  workflow
```

### New `src/osiris_toolkit/_models.py`

All content from `diagnostics.py` (~643 lines) is moved into `_models.py`. Content unchanged:

- `GridAxis` — dataclass + `value_to_index()`/`index_to_value()`
- `Field` / `GridData` (alias) — dataclass + operator overloading + physical slicing + `to_npz`/`to_csv`/`to_vtk`
- `ParticleData` — dataclass + `filter()`/`compress()`/`to_npz`/`to_csv`
- `PhasespaceData`, `TrackData`, `HistoryData`, `TimingsData` — pure dataclass
- `FieldInfo`, `ParticleInfo`, `TrackInfo` — lightweight metadata dataclass
- `_eval_particle_expr()` — `ParticleData.filter()` helper function

### `sim/diagnostics.py` → Re-export Shim

```python
"""Backward-compatible re-exports. Import from _models directly for new code."""
from osiris_toolkit._models import (
    Field, FieldInfo, GridAxis, GridData, HistoryData,
    ParticleData, ParticleInfo, PhasespaceData, TimingsData,
    TrackData, TrackInfo, _eval_particle_expr,
)
__all__ = [...]
```

### Import Updates

| File | Old Import | New Import |
|------|-----------|-----------|
| `io/vtk_exporter.py` | `from sim.diagnostics import Field` | `from _models import Field` |
| `compute/deposit.py` | `from sim.diagnostics import Field, GridAxis` | `from _models import Field, GridAxis` |
| `compute/transform.py` | `from sim.diagnostics import Field, GridAxis` | `from _models import Field, GridAxis` |
| `analysis/stats.py` | `from sim.diagnostics import GridData` | `from _models import GridData` |
| `analysis/_result_types.py` | `from sim.diagnostics import GridData` | `from _models import GridData` |
| `vis/raw.py` | `from sim.diagnostics import ParticleData` | `from _models import ParticleData` |
| `vis/tracks.py` | `from sim.diagnostics import TrackData` | `from _models import TrackData` |
| `vis/kspace.py` | `from sim import GridData, Simulation` | `from _models import GridData; from sim import Simulation` |
| `sim/simulation.py` | `from sim.diagnostics import ...` | `from _models import ...` |
| `sim/catalog.py` | `from sim.diagnostics import GridData` | `from _models import GridData` |
| `sim/__init__.py` | `from sim.diagnostics import ...` | `from _models import ...` |
| `__init__.py` | `from sim import Field, ...` | Unchanged (sim/__init__.py still re-exports) |

---

## Phase 2: Simulation Split + Dead Code Cleanup

### 2A. Simulation Split

`simulation.py` (1,120 lines) → 4 files:

```
sim/
├── _parse.py         # NEW: ~80 lines, parsing helpers
│   ├── _ITER_FILE_RE
│   ├── _parse_iter_file()
│   ├── _parse_quantity()
│   ├── _REPORT_SUFFIXES
│   ├── _parse_history_file()
│   └── _parse_timings_file()
│
├── _accessors.py     # NEW: ~400 lines, data accessor mixin
│   └── class _DataAccessors:
│       ├── get_field() / get_density() / get_cell_avg()
│       ├── get_udist() / get_raw() / get_tracks()
│       ├── get_phasespace() / get_chargecons()
│       ├── get_current() / get_ion() / get_wall()
│       ├── _read_grid() / _read_particle() / _read_phasespace() / _read_tracks()
│       └── list_fields() / list_species() / list_*()
│
├── _info.py          # NEW: ~80 lines, metadata accessor mixin
│   └── class _InfoAccessors:
│       ├── info_field() / info_raw() / info_tracks()
│       └── _read_info()
│
├── simulation.py     # ~400 lines, Simulation core
│   └── class Simulation(_DataAccessors, _InfoAccessors):
│       ├── __init__() / _discover() / _discover_ms()
│       ├── _discover_fld() / _discover_chargecons() / ...
│       ├── to_dict() / from_dict()
│       └── path / output_root / config / run_info and other properties
```

`Simulation` obtains accessor methods via multiple inheritance; the external API remains completely unchanged.

### 2B. Dead Code Cleanup

| Location | Content | Action | Rationale |
|------|------|------|------|
| `analysis/__init__.py` | `Analyzer` base class (deprecated) | Remove | `Protocol` has superseded it |
| `vis/__init__.py` | `VisEngine` (deprecated) | Remove | `PostVisHub` fully supersedes |
| `vis/kspace.py:25` | `compute_k_space` (deprecated wrapper) | Remove | Users should use `compute.fft.compute_k_space` |
| `vis/scattering.py:61` | `analyze_scattering` (deprecated) | Remove | Users should use `analysis.scattering.ScatteringAnalyzer` |

Confirm no residual references before removal:
```bash
grep -rn "VisEngine\|from.*Analyzer[^s]\|vis\.kspace\.compute_k_space\|vis\.scattering\.analyze_scattering" src/ tests/
```

---

## Public API Guarantees

After Phase 2 is complete, all of the following usage patterns remain unchanged:

```python
# Top-level imports
from osiris_toolkit import Field, Simulation, GridData, ParticleData

# sim-level imports
from osiris_toolkit.sim import Field, Simulation
from osiris_toolkit.sim.diagnostics import Field  # still works via shim

# Simulation usage is completely unchanged
sim = Simulation("/path/to/output")
field = sim.get_field("e1", iteration=50)
info = sim.info_field("e1", iteration=50)
sim.list_fields()

# PostVisHub unchanged
from osiris_toolkit.vis import PostVisHub
hub = PostVisHub(sim)
hub.plot_field("e1", iteration=50)
```

---

## Tests

| File | Test Content |
|------|-------------|
| `tests/test_models.py` (new) | Field operators, slicing, serialization; ParticleData filter/compress; GridAxis coordinate conversion |
| `tests/test_sim/test_parse.py` (new) | _parse_iter_file edge cases; _parse_quantity modifier detection |
| `tests/test_sim/test_accessors.py` (new) | get_field/get_raw/get_tracks; each diagnostic type accessor; _read_* error handling |
| `tests/test_sim/test_info.py` (new) | info_field/info_raw/info_tracks metadata reading |
| Existing tests | All import paths remain compatible (via shim), all should pass |

## File Change Summary

| Action | File | Lines |
|------|------|------|
| New | `_models.py` | +643 |
| Rewrite | `sim/diagnostics.py` | 643→15 |
| New | `sim/_parse.py` | +80 |
| New | `sim/_accessors.py` | +400 |
| New | `sim/_info.py` | +80 |
| Rewrite | `sim/simulation.py` | 1,120→400 |
| Update | Import paths in 12 files | ~30 |
| Delete | 4 dead-code locations | -120 |
| New | 4 test files | +~40 tests |

---

## Scope Boundaries

### In Scope
- Extract data models to `_models.py`
- Split Simulation into parse + accessors + info
- Remove 4 dead-code locations
- Update imports in 12 files
- Backward-compatible shim
- New tests

### Out of Scope
- New features (HISTORY/UDIST, etc.)
- PostPostProcessor/PostVisHub refactoring
- Refactoring of other modules

## References

- ADR: GitHub Issue [#1](https://github.com/wulnkkk/osiris-toolkit/issues/1) — [ADR] Architecture Refactor
