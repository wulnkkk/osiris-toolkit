---
audience: [human, agent]
role: [user, developer]
topic: architecture
kind: architecture
updated: 2026-06-04
---

# Dependency Hierarchy

## Five-Layer Stack

Each layer may only import from layers below it. Importing upward, or sideways within the same layer, is a violation.

| Layer | Modules | Allowed Imports |
|-------|---------|-----------------|
| **Base** (0) | `exceptions`, `_models`, `_generated`, `_logging` | Standard library, numpy only |
| **Bottom** (1) | `deck`, `io`, `units`, `compute`, `sync`, `config` | Base layer |
| **Middle** (2) | `sim`, `analysis`, `vis`, `resource` | Base + Bottom layers |
| **Upper** (3) | `postproc`, `workflow`, `parallel`, `cli` | Base + Bottom + Middle layers |

## Import Direction

```
Base (0)
  ^
  |
Bottom (1)
  ^
  |
Middle (2)
  ^
  |
Upper (3)
```

Arrows point in the allowed import direction (upper layers import from lower layers).

## Violation Examples

### Forbidden: Middle importing from Middle

```python
# sim/simulation.py — VIOLATION
from osiris_toolkit.vis import plot_field  # sim cannot import vis
```

### Forbidden: Bottom importing from Middle

```python
# io/_reader.py — VIOLATION
from osiris_toolkit.sim import Simulation  # io cannot import sim
```

### Forbidden: Bottom importing sideways

```python
# units/converter.py — VIOLATION
from osiris_toolkit.compute import fft  # cannot import peer bottom module
```

### Allowed: Middle importing from Base

```python
# sim/simulation.py — OK
from osiris_toolkit._models import GridData
from osiris_toolkit.exceptions import SimulationNotFoundError
```

### Allowed: Middle importing from Bottom

```python
# analysis/emf.py — OK
from osiris_toolkit.io import read_zdf
from osiris_toolkit.units import UnitSystem
from osiris_toolkit.compute.fft import compute_k_space
```

## Enforcement

CI runs a custom lint rule (in `.ruff.toml` or a pre-commit script) that checks for forbidden import patterns. The base list of banned imports is generated from the layer table above.
