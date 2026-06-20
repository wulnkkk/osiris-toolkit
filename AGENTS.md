# osiris-toolkit

Comprehensive Python toolkit for [OSIRIS](https://osiris-code.org/) PIC (Particle-in-Cell) simulations — input deck parsing, data extraction, unit conversion, analysis, and visualization.

## Quick Start

```bash
# Install
pip install osiris-toolkit

# Setup development
uv sync --dev
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

# Common commands
make lint        # ruff check
make format      # ruff format
make test        # pytest
```

## Agent Skills

This project provides two specialized agent skills, one for each role:

### 👤 User Skill — Using the toolkit

Use when the task involves processing simulation data, plotting fields, converting units, or analyzing results.

```
Skill: docs/agent-user/skill.md
Tasks: parse deck, browse sim, plot field, k-space analysis, batch process, unit conversion
```

### 🛠 Developer Skill — Building the toolkit

Use when the task involves adding features, fixing bugs, running tests, or publishing releases.

```
Skill: docs/agent-dev/dev-skill.md
Tasks: add analysis function, add visualization, add CLI command, write tests, release
```

## Key Rules

| Rule | Detail |
|------|--------|
| **Language** | All code, docs, commits must be in **English** |
| **Commits** | [Conventional Commits](https://www.conventionalcommits.org/): `feat:` / `fix:` / `docs:` / `refactor:` / `test:` / `chore:` |
| **Architecture** | No reverse dependencies: `base → low → mid → high` layers |
| **Generated code** | `src/osiris_toolkit/_generated/` — never edit by hand, run `dev-tools/extract_definitions.py` to regenerate |
| **Unit system** | Use `UnitSystem`, not `UnitConverter` (deprecated since v0.15.0) |
| **Public API** | Every module exports its public symbols through `__init__.py` |

## Project Structure

```
osiris-toolkit/
├── src/osiris_toolkit/      # Source code
│   ├── deck/                Input deck parsing (lexer, parser, validator)
│   ├── io/                  ZDF/HDF5 binary reader
│   ├── sim/                 Simulation directory discovery
│   ├── units/               Unit conversion (UnitSystem)
│   ├── compute/             Pure numerical transforms (FFT, integration)
│   ├── analysis/            Physics analysis (EMF, k-space, scattering)
│   ├── vis/                 Visualization (field, density, k-space, batch)
│   ├── workflow/            YAML-configurable automation pipeline
│   ├── parallel/            Multi-core / SLURM / MPI execution
│   ├── resource/            Resource estimation (memory, runtime, disk)
│   ├── sync/                OSIRIS source synchronization
│   ├── cli.py               Click CLI entry point
│   ├── config.py            Global configuration
│   └── _generated/          Auto-generated parameter definitions
├── tests/                   Test suite (pytest)
├── docs/                    Documentation (mkdocs)
└── examples/                Example analysis scripts
```

## Important Paths

| What | Path |
|------|------|
| CLI entry point | `src/osiris_toolkit/cli.py` |
| All tests | `tests/` |
| Documentation config | `mkdocs.yml` |
| Contribution guide | `CONTRIBUTING.md` |
| Changelog | `CHANGELOG.md` |
