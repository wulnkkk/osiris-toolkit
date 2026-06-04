---
audience: [human, agent]
topic: modules
kind: reference
module: sync
updated: 2026-06-04
---

# sync — Fortran Source Extraction

Dev-time tool that scans OSIRIS Fortran source files and extracts parameter definitions,
diagnostic quantity lists, and section-to-namelist mappings. Generates `_generated/*.py` data files.

## Architecture

```
osiris-1.0.0/source/*.F90
        │
        ▼
FortranScanner (extractor.py)
    ├── namelist /nl_*/ → NamelistEntry (param names, types, defaults)
    ├── p_report_quants  → QuantitiesEntry (diagnostic quantity strings)
    └── call get_namelist → SectionEntry (section → namelist mapping)
        │
        ├──▶ namelist.py  → _generated/parameters.py
        ├──▶ diagnostics.py → _generated/quantities.py
        └──▶ sections.py  → _generated/sections.py
```

**Files:**

| File | Role |
|------|------|
| `extractor.py` | `FortranScanner`: regex-based parser for namelist declarations, type defs, defaults, quantity arrays, `get_namelist` calls, continuation line merging |
| `namelist.py` | Generates `_generated/parameters.py`: ~493 params across 36 sections |
| `diagnostics.py` | Generates `_generated/quantities.py`: 59 quantities across 4 diagnostic types |
| `sections.py` | Generates `_generated/sections.py`: 37 section→namelist entries |

## Usage

```bash
# Extract from OSIRIS source
osiris-toolkit sync extract --osiris-path /path/to/osiris-1.0.0/source

# Review changes
git diff _generated/
```

## Key Design Decisions

- **Dev-time only**: `sync/` runs at development time, not at runtime. The generated `_generated/`
  files are committed to the repo and shipped with the package.
- **Zero runtime dependency on OSIRIS**: `pip install osiris-toolkit` does not require `osiris-1.0.0/`.
- **Audit trail**: when OSIRIS is upgraded, re-run the sync command and `git diff _generated/` to
  see exactly what changed upstream.
- **Generated → Manual pipeline**: `_generated/` provides the raw extracted data (parameter names,
  types, defaults). `deck/schemas/` layers human-curated constraints, descriptions, and ordering
  rules on top.

## Current Extraction Results

| Category | Count |
|----------|-------|
| Sections | 36 |
| Parameters | 493 |
| Diagnostic types | 4 (EMF, DENSITY, UDIST, CURRENT) |
| Diagnostic quantities | 59 |

## Known Gaps

- `emf_solver`: 5 solvers share the same namelist name across 5 files — the extractor only captures
  one. Needs per-file merging.
- `CHARGE` (3 quantities) and `NEUTRAL` (2 quantities): file routing not yet configured in
  `diagnostics.py`.
- Constraint extraction: `if (var <= 0)` patterns in Fortran source are not yet parsed.
