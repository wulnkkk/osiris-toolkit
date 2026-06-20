---
audience: [human, agent]
role: user
topic: workflow
kind: tutorial
tasks: ["discover simulations", "validate data", "batch process", "verify output"]
api: ["Simulation", "get_system", "process_simulation"]
cli: ["sim info", "vis batch --dry-run", "vis batch"]
updated: 2026-06-04
---

# Basic Workflow

Typical post-processing workflow for OSIRIS simulation data.

## Phase 1: Discover

```bash
# Find output directories (look for MS/ subdirectories)
find /data/ -name "MS" -type d -exec dirname {} \;
```

```python
from osiris_toolkit.sim import Simulation

sim = Simulation("/data/Au")
print(sim.list_fields())      # ['e1', 'e2', 'e3', 'b1', 'b2', 'b3']
print(sim.list_species())     # ['electrons']
```

## Phase 2: Validate

```bash
osiris-toolkit sim info /data/Au --output json
```

Verify:
- Field components are complete (e1/e2/e3 or plus b1/b2/b3)
- Iteration count is reasonable
- Format is ZDF (not HDF5)

## Phase 3: Preview

```bash
osiris-toolkit vis batch --dry-run /data/Au Au
# Simulation: Au (zdf format)
#   Fields: e1, e2, e3, b1, b2, b3
#   Iterations: 50 (0..44100)
#   Would generate:
#     fields/      300 PNGs  (~500 MB)
#     k_space/     300 PNGs  (~200 MB)
#     density/      50 PNGs  (~100 MB)
#     scattering/    3 PNGs  (~1 MB)
#   Total: 653 PNGs, ~800 MB
```

## Phase 4: Process

```bash
# Sequential with progress bar
osiris-toolkit vis batch --progress /data/Au Au

# Parallel with 8 workers
osiris-toolkit vis batch -j 8 --progress /data/Au Au
```

## Phase 5: Verify

```bash
# Count generated files
find figures/Au/ -name "*.png" | wc -l

# Check for zero-byte or suspiciously small files
find figures/Au/ -name "*.png" -size -1k

# Spot-check a few images
ls -lh figures/Au/fields/ | head -10
```
