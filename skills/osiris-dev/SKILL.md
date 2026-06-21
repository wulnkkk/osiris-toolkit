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
make bump        # version bump + git tag
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
3. **Verify that every architectural change has a public decision record.**
   Check `docs/design/` and Issues with `[ADR]` label. Missing records must
   be created before releasing. See the Decision Records section below.
4. Update `CHANGELOG.md`: `[Unreleased]` → `[vX.Y.Z]`
5. `git push --follow-tags`
6. Create GitHub Release

## Decision Records

Architectural decisions use a two-tier system:

| Tier | Format | When | Content |
|------|--------|------|---------|
| **ADR** | GitHub Issue with `[ADR]` label | Every architectural change | **Why + What** — context, decision, consequences (~200 words)
| **Design doc** | `docs/design/<topic>.md` | Only major cross-module refactors | **How** — class definitions, data flow, migration steps

- **When to create:** Before or during implementation. The ADR captures reasoning *at decision time*, not after.
- **ADR template:** `.github/ISSUE_TEMPLATE/adr.md` (Context → Decision → Consequences)
- **Design docs reference their source ADR** in a "Related" section.
- See `CONTRIBUTING.md` §Decision Records for the full policy.

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

### Reference files

- [Development Task Map](references/task-map.md) — intent-to-code-location mapping for common development tasks

### Human documentation reference

For architecture details, design decisions, and module internals beyond this skill:

- [Architecture Overview](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/architecture/overview.md)
- [Dependency Hierarchy](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/architecture/dependency-hierarchy.md)
- [Data Flow](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/architecture/data-flow.md)
- [Unit Conversion Architecture](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/architecture/unit-conversion.md)
- [K-Space Pipeline](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/architecture/k-space-pipeline.md)
- [Vis Architecture](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/architecture/vis-architecture.md)
- [Design: Unit System](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/design/unit-system-architecture.md)
- [Design: PostProcessor](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/design/postproc-architecture.md)
- [Design: Documentation System](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/design/doc-system-architecture.md)
- [Design: Architecture Refactor v0.14](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/design/architecture-refactor.md)
- [Module Docs](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/modules/) — per-module deep dives
- [Contributing (mkdocs version)](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/contributing.md)
- [Devlogs](https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/devlog/) — version history and technical decisions

## Submit Checklist

Before committing or opening a PR, verify each item:

```markdown
- [ ] `make lint` — ruff passes on `src/`
- [ ] `make typecheck` — mypy has no new errors
- [ ] `make test-quick` — all fast tests pass
- [ ] `make format-check` — ruff formatting is clean
- [ ] Language: all code/comments/docs/commits in **English**
- [ ] No internal paths, usernames, or hostnames (`/work/home/...`, `/Users/...`)
- [ ] CHANGELOG.md updated (if user-facing change)
- [ ] **Decision record exists** — if this change touches data model,
      new module, API break, or new dependency, a corresponding Issue
      with `[ADR]` label or `docs/design/` doc must exist
- [ ] Sync targets updated if applicable:
      - CLI change → `skills/osiris-user/SKILL.md` + `docs/manifest.json`
      - API change → `skills/osiris-user/SKILL.md` + `docs/manifest.json`
      - Architecture change → `CONTRIBUTING.md` + `AGENTS.md`
      - File added/removed → `mkdocs.yml` nav + `docs/manifest.json`
- [ ] `make check-all` passes (runs lint + typecheck + test + docs-build + arch check)
```

> Tip: Pre-commit hooks catch most formatting/type issues automatically on commit.
> Pre-push hooks run `make check-all` before every push. Install them with:
> `uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push`
