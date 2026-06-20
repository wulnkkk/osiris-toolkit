---
audience: [human, agent]
role: developer
topic: modules
kind: reference
module: exceptions
updated: 2026-06-04
---

# exceptions — Custom Exception Hierarchy (v0.13.0)

All osiris-toolkit exceptions inherit from `OsirisToolkitError`, enabling callers
(including AI agents) to catch a single base class or target specific error types
for fine-grained recovery.

## Hierarchy

```
OsirisToolkitError
├── DataNotFoundError        — requested data/quantity/diagnostic doesn't exist
├── FormatError              — invalid or unrecognised file format
│   └── UnsupportedVersionError  — ZDF/HDF5 record version too new
├── ValidationError          — parameter/input validation failed
│   ├── ShapeError           — array dimensions/shape mismatch
│   └── MissingParameterError — required parameter/config section missing
├── PipelineError            — pipeline step prerequisite not met
├── ConfigurationError       — Simulation/OsirisConfig invalid
├── UnitConversionError      — unit conversion failed (missing omega_p, unknown unit)
└── MissingDependencyError   — optional dependency (h5py, pyevtk) not installed
```

## Usage

```python
from osiris_toolkit.exceptions import DataNotFoundError, FormatError, OsirisToolkitError

# Catch all toolkit errors
try:
    field = sim.get_field("e1", iteration=999)
except OsirisToolkitError as e:
    print(f"Toolkit error: {e}")

# Catch specific types
try:
    field = sim.get_field("e1", iteration=999)
except DataNotFoundError:
    print("No data for this iteration — skipping")
except FormatError:
    print("File is corrupted — aborting")
```
