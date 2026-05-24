# _generated — Auto-Generated Definitions

Data files produced by `sync/extractor.py` from OSIRIS Fortran source. Committed to the repo so
that `osiris-toolkit` has zero runtime dependency on `osiris-1.0.0/`. **Do not edit manually.**

## Files

| File | Content | Count |
|------|---------|-------|
| `parameters.py` | `GEN_PARAMETERS[section_name][param_name] → _GenParam` | 493 params, 36 sections |
| `quantities.py` | `GEN_QUANTITIES[diagnostic_type] → list[str]` | 59 quantities, 4 types |
| `sections.py` | `GEN_SECTIONS → list[_GenSection]` | 37 section→namelist mappings |

## Data Format

### parameters.py

```python
@dataclass
class _GenParam:
    name: str              # Fortran variable name
    fortran_type: str      # e.g. "real(p_double)", "integer", "logical"
    python_type: str       # e.g. "float", "int", "bool"
    default: str | None    # default value from Fortran source

GEN_PARAMETERS["simulation"]["omega_p0"]
# _GenParam(name='omega_p0', fortran_type='real(p_double)', python_type='float', default='0.0')
```

### quantities.py

```python
GEN_QUANTITIES["EMF"]
# ['e1', 'e2', 'e3', 'b1', 'b2', 'b3', 'ext_e1', ..., 's1', 's2', 's3']
```

### sections.py

```python
GEN_SECTIONS
# [_GenSection(name='simulation', nl_name='nl_simulation'),
#  _GenSection(name='grid', nl_name='nl_grid'),
#  ...]
```

## Relationship to deck/schemas/

`deck/schemas/parameters.py` imports from `_generated/` and adds human-maintained metadata:
- **constraints**: validation rules like `">= 0"`, `"in (cartesian, cylindrical)"`
- **condition**: conditional presence like `"if_move == 1"`
- **description**: English prose explanation of the parameter

## Regeneration

```bash
osiris-toolkit sync extract --osiris-path /path/to/osiris-1.0.0/source
git diff _generated/
```
