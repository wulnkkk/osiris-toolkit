---
audience: [agent]
topic: agent
kind: recipe
updated: 2026-06-04
---

# Recipe: Discover Simulations

Find and validate all OSIRIS simulation outputs in a directory tree.

## Step 1: Identify candidate directories

An OSIRIS simulation output directory contains an `MS/` subdirectory with ZDF files. Scan the target root for such directories:

```bash
find /path/to/data -type d -name "MS" | while read ms; do
    dir=$(dirname "$ms")
    echo "$dir"
done
```

## Step 2: Validate each candidate

For each candidate, load it as a `Simulation` and check its diagnostics:

```python
from pathlib import Path
from osiris_toolkit.sim import Simulation

def validate_sim(path: str) -> dict | None:
    """Return summary dict if valid, None if not."""
    try:
        sim = Simulation(path)
    except Exception:
        return None

    fmt = sim.detected_format
    if fmt == "hdf5":
        return None  # Not supported

    fields = sim.list_fields()
    if not fields:
        return None  # No diagnostic data

    # Pick first field, get iteration range
    iters = sim.list_iterations(fields[0])

    return {
        "path": path,
        "format": fmt,
        "fields": fields,
        "species": sim.list_species(),
        "iterations": f"{min(iters)}..{max(iters)} ({len(iters)} frames)" if iters else "none",
        "has_phasespace": len(sim.list_phasespaces()) > 0,
        "has_tracks": len(sim.list_tracks()) > 0,
    }

# Scan a root directory
root = Path("/path/to/data")
for ms_dir in root.rglob("MS"):
    sim_dir = ms_dir.parent
    info = validate_sim(str(sim_dir))
    if info:
        print(f"  {info['path']}")
        print(f"    Format: {info['format']}")
        print(f"    Fields: {', '.join(info['fields'])}")
        print(f"    Species: {', '.join(info['species'])}")
        print(f"    Iterations: {info['iterations']}")
        print()
```

## Step 3: Use CLI for quick inspection

For an individual directory, use the built-in `sim info` command:

```bash
osiris-toolkit sim info /path/to/sim/output
osiris-toolkit sim info /path/to/sim/output -o json  # machine-readable
```

## Step 4: Filter by criteria

Common filters to apply after discovery:

- **Has enough iterations:** `len(iters) >= 10`
- **Has specific fields:** `"e1" in fields and "b1" in fields`
- **Supports k-space:** `len(fields) > 0` and 2-D grid (check GridData shape)
- **ZDF format only:** `sim.detected_format == "zdf"`
- **Has specific species:** `"electrons" in sim.list_species()`

## Step 5: Build a simulation catalog

For repeated use, save the discovery results:

```python
import json

catalog = []
for sim_dir in all_dirs:
    info = validate_sim(str(sim_dir))
    if info:
        catalog.append(info)

with open("sim_catalog.json", "w") as f:
    json.dump(catalog, f, indent=2, default=str)
```

## Verification

- Each listed simulation directory has a non-empty MS/ subdirectory
- `detected_format` returns `"zdf"` or `"mixed"` (not `"hdf5"` alone)
- At least one field quantity is listed with iterations >= 1
