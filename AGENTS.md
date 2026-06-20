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
Skill: skills/osiris-user/SKILL.md
Tasks: parse deck, browse sim, plot field, k-space analysis, batch process, unit conversion
```

### 🛠 Developer Skill — Building the toolkit

Use when the task involves adding features, fixing bugs, running tests, or publishing releases.

```
Skill: skills/osiris-dev/SKILL.md
Tasks: add analysis function, add visualization, add CLI command, write tests, release
```

## Configuring Your AI Tool

These skills follow the [Agent Skills open standard](https://agentskills.io/). Depending on your AI tool, configure them as follows:

### Claude Code

```bash
# The skills/ directory is automatically detected. Load on demand:
/osiris-user     # User skill — data processing
/osiris-dev      # Developer skill — code contribution
```

### Cursor

Add rules pointing to the skill files in `.cursor/rules/`:

```yaml
# .cursor/rules/osiris-user.mdc
description: osiris-toolkit user skill — CLI/Python API for simulation data
globs: ["**/*.py", "**/*.md"]
alwaysApply: false
---
See skills/osiris-user/SKILL.md for CLI commands, API usage, and decision trees.
```

```yaml
# .cursor/rules/osiris-dev.mdc
description: osiris-toolkit dev skill — architecture, workflow, testing
globs: ["**/*.py", "**/*.md"]
alwaysApply: false
---
See skills/osiris-dev/SKILL.md for architecture rules, dev workflow, and testing guidelines.
```

### GitHub Copilot

Add a reference in `.github/copilot-instructions.md`:

```markdown
For data processing tasks, refer to skills/osiris-user/SKILL.md.
For code contribution tasks, refer to skills/osiris-dev/SKILL.md.
```

### Reasonix

```bash
/osiris-user     # User skill — data processing
/osiris-dev      # Developer skill — code contribution
```

### Any other tool

Point your AI tool to read these files when relevant:
- `skills/osiris-user/SKILL.md` — operational instructions
- `skills/osiris-dev/SKILL.md` — development instructions

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
├── skills/                  Agent skills (open standard format)
│   ├── osiris-user/         User skill — data processing
│   └── osiris-dev/          Developer skill — code contribution
├── tests/                   Test suite (pytest)
├── docs/                    Documentation (mkdocs)
└── examples/                Example analysis scripts
```

## Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/).
Current version: `0.y.z` (initial development).

During 0.y.z, both `BREAKING CHANGE` and `feat` increment MINOR.
See `[tool.commitizen.bump_map]` in `pyproject.toml`.

## Important Paths

| What | Path |
|------|------|
| CLI entry point | `src/osiris_toolkit/cli.py` |
| All tests | `tests/` |
| Documentation config | `mkdocs.yml` |
| Contribution guide | `CONTRIBUTING.md` |
| Changelog | `CHANGELOG.md` |
