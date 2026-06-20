---
name: osiris-dev
description: Develop and maintain the osiris-toolkit codebase — architecture, workflow, testing, release, and code standards. Use when contributing code, fixing bugs, writing tests, or publishing releases.
---

# Agent Dev Skill — osiris-toolkit Development Manual

This document is the **Development** skill for AI agents working on the osiris-toolkit codebase. It describes the project structure, development workflow, and key architecture rules.

> 📖 This is a **specialized skill** loaded on demand. For the cross-platform entry point (always loaded per session), see [`AGENTS.md`](https://github.com/wulnkkk/osiris-toolkit/blob/main/AGENTS.md) at the project root.

> **Relationship to `CONTRIBUTING.md`:** This is the agent-facing counterpart to the human-oriented [`CONTRIBUTING.md`](https://github.com/wulnkkk/osiris-toolkit/blob/main/CONTRIBUTING.md). Both cover the same development workflow and **must be kept in sync** when the project's dev practices change (e.g., new lint rules, modified test commands, updated release process).

> For the **User** skill (how to use the toolkit to process simulation data), see [`skills/osiris-user/SKILL.md`](https://github.com/wulnkkk/osiris-toolkit/blob/main/skills/osiris-user/SKILL.md).

---

## Project Overview

```
osiris-toolkit/
├── src/osiris_toolkit/      # Source code
│   ├── deck/                Input deck parsing (lexer, parser, validator)
│   ├── io/                  ZDF/HDF5 binary reader
│   ├── sim/                 Simulation directory discovery
│   ├── units/               Unit conversion (UnitSystem)
│   ├── compute/             Pure numerical transforms (FFT, integration, deposition)
│   ├── analysis/            Physics analysis (EMF, k-space, scattering, tracking)
│   ├── vis/                 Visualization (field, density, k-space, batch, parallel)
│   ├── workflow/            YAML-configurable automation pipeline
│   ├── parallel/            Multi-core / SLURM / MPI execution
│   ├── resource/            Resource estimation (memory, runtime, disk)
│   ├── sync/                OSIRIS source synchronization
│   ├── cli.py               Click CLI entry point
│   ├── config.py            Global configuration (OsirisConfig)
│   ├── _models.py           Core data models (Field, ParticleData, GridAxis)
│   └── _generated/          Auto-generated parameter/quantity definitions
├── skills/                  Agent skills (open standard format)
├── tests/                   Test suite (pytest)
├── docs/                    Documentation (mkdocs)
├── dev-tools/               Development tools
│   └── extract_definitions.py  Regenerate _generated/ from Fortran source
└── examples/                Example analysis scripts
```

## Development Workflow

```bash
# Setup
uv sync --dev
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

# Common tasks
make lint        # ruff check
make format      # ruff format
make typecheck   # mypy
make test        # pytest
make docs-serve  # mkdocs preview
```

### Branch Naming

- `feat/<description>` — new features
- `fix/<description>` — bug fixes
- `refactor/<description>` — code restructuring
- `release/vX.Y.Z` — version releases

### Commit Messages

Conventional Commits enforced by commitizen:

```
<type>[(scope)]: <description>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`. Add `!` for breaking changes.

## Architecture Rules (DO NOT VIOLATE)

These rules are enforced by design and must never be broken:

1. **No reverse dependencies** — `compute/` cannot import `sim/` or `vis/`; `sim/` cannot import `vis/`.
2. **Compute does pure math only** — no unit conversion, no OSIRIS-specific knowledge.
3. **`_generated/` is read-only** — never edit by hand. Run `dev-tools/extract_definitions.py` to regenerate.
4. **Use `UnitSystem`, not `UnitConverter`** — `UnitConverter` is deprecated since v0.15.0.
5. **Public API through `__init__.py`** — each module exports its public symbols there.

### Module dependency hierarchy

```
base layer: exceptions  _generated  _models       ← no project imports
     ↓
low layer:  deck  io  units  compute              ← can import base
     ↓
mid layer:  sim  sync  parallel  resource         ← can import base + low
     ↓
high layer: analysis  vis  workflow               ← can import anything below
```

## Code Style

- **Ruff**: 10 rule sets (E, W, F, I, N, UP, B, SIM, ARG, RUF), line length 120
- **mypy**: strict optional, no implicit optional
- **Docstrings**: NumPy/SciPy style
- **Naming**: `snake_case` functions/variables, `PascalCase` classes, `UPPER_CASE` constants
- **Language**: All English — code, comments, docs, commit messages

## Pre-commit Hooks

On every commit, these run automatically:
1. Trailing whitespace check
2. End-of-file fixer
3. YAML/TOML syntax check
4. Large file check (>1MB)
5. Merge conflict detection
6. Debug statement detection
7. Ruff lint + format
8. mypy type check (staged files)
9. commitizen commit message validation

## Testing

```bash
pytest tests/ -v                           # full suite
pytest tests/test_units/ -v                # specific module
pytest -m "not slow and not data"          # CI subset
pytest --cov=osiris_toolkit --cov-report=html  # coverage
```

- Tests requiring real ZDF data: `@pytest.mark.data` (skipped in CI)
- Slow tests: `@pytest.mark.slow` (not run by default)

## Release Process

1. All features merged to `main`, CI passes
2. `uv run cz bump` — auto-bump version + git tag
3. Update `CHANGELOG.md`: `[Unreleased]` → `[vX.Y.Z]`
4. `git push --follow-tags`
5. Create GitHub Release

## Privacy & Security

- **No internal paths/usernames/hostnames in committed files**
- Check PRs for hardcoded cluster paths like `/work/home/...`
- `.env` and `docs/note/` are gitignored — don't commit local config

## Key Entry Points for Common Dev Tasks

| Task | File(s) |
|------|---------|
| Add a new analysis function | `src/osiris_toolkit/analysis/` + register in `__init__.py` |
| Add a new visualization | `src/osiris_toolkit/vis/` + register in `__init__.py` |
| Add a new CLI command | `src/osiris_toolkit/cli.py` — add click command group |
| Add a new data format reader | `src/osiris_toolkit/io/` + extend `Simulation` discovery |
| Add a new unit quantity | `src/osiris_toolkit/units/_quantity.py` — add `QuantityKind` instance |
| Update parameter definitions | `dev-tools/extract_definitions.py` + regenerate `_generated/` |
| Add documentation page | Create `.md` in `docs/`, add nav entry in `mkdocs.yml` |
