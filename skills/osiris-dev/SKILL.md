---
name: osiris-dev
description: >-
  Use when developing or maintaining the osiris-toolkit codebase:
  adding features to src/osiris_toolkit/ (analysis functions,
  visualizations, CLI commands, I/O readers, unit quantities),
  fixing bugs in any module, refactoring architecture, writing
  tests, running lint/typecheck/tests (make, ruff, mypy, pytest),
  regenerating _generated/ files, or publishing releases. Use this
  when the task modifies the toolkit itself. For processing
  simulation data (plotting, k-space analysis, unit conversion,
  deck parsing), load osiris-user instead.
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
# ---- Setup ----

# Option A: uv (recommended)
uv venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate     # Windows
uv sync --dev
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push

# Option B: pip + venv (if you don't have uv)
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate     # Windows
pip install -e .
pip install pytest pytest-cov ruff mypy pre-commit commitizen
pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push

# ---- Common tasks (both options) ----
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
- `docs/<description>` — documentation only
- `release/vX.Y.Z` — version releases

Use lowercase with hyphens (underscores are **not** allowed).

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

## Gotchas — common mistakes the tooling won't catch

These are non-obvious traps that defy reasonable assumptions. Read before writing code.

- **`* 2 * np.pi` outside `units/` is an architecture violation.** The only place `2π` should appear in unit conversion is inside `UnitSystem.convert()`. If you write it in `compute/`, `analysis/`, or `vis/`, you bypass the unit system.
- **`compute/` must never import `sim/`, `units/`, or `matplotlib`.** It does pure math on `np.ndarray` — no OSIRIS data types, no physical units, no plotting.
- **`_generated/` is overwritten without warning.** Editing those files by hand is waste — `extract_definitions.py` silently replaces them. Always regenerate.
- **`UnitConverter` is deprecated but still importable.** New code must use `UnitSystem`. `converter=` parameters are legacy — use `system=` instead.
- **Bypassing `QuantifiedSpectrum` produces wrong units.** Never compute `k_phys = kx * 2*np.pi/dx` by hand. Use `QuantifiedSpectrum.from_field(grid, system=system)` then `qspec.kx.to("k0")`.
- **`[dependency-groups]` is uv-only syntax.** `pip install -e ".[dev]"` will silently skip dev dependencies (pytest, ruff, mypy, pre-commit, commitizen) because pip doesn't understand uv's `[dependency-groups]` table. Install dev dependencies manually with pip.
- **Without an input deck, `UnitSystem` is `None` — there is no fallback.** Never assume `omega_p=1.0` or any dummy default. Callers must handle `system=None` explicitly.
- **Adding a new diagnostic type requires 6+ wiring points.** analyzer class + `_result_types` dataclass + `analysis/__init__.py` hub property + plot function + `vis/__init__.py` hub/namespace/dispatch + `batch.py` processing block. Tests need a `conftest.py` fixture and two test files with distinct basenames.
- **Changing `_parse_iter_file` return type breaks 8+ callers.** Always grep `_parse_iter_file` across the whole codebase before releasing.

## Code Style

- **Ruff**: 10 rule sets (E, W, F, I, N, UP, B, SIM, ARG, RUF), line length 120
- **mypy**: strict optional, no implicit optional
- **Docstrings**: NumPy/SciPy style
- **Naming**: `snake_case` functions/variables, `PascalCase` classes, `UPPER_CASE` constants
- **Language**: All English — code, comments, docs, commit messages

## Pre-commit Hooks

On every commit, 13 hooks run automatically: lint, format, typecheck, arch check, English check, doc sync, commitizen, whitespace, merge-conflict, debug, large-file, YAML/TOML, private-key. Pre-push hooks run `make check-all`. No manual step needed — if a hook fails, fix what it reports and commit again.

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
2. `uv run cz bump` — auto-bump version + git tag (do **not** use `--changelog`; CHANGELOG is manually maintained)
3. Create `docs/devlog/{version}.md` + add nav entry in `mkdocs.yml`
4. **Verify that every architectural change has a public decision record.**
   Check `docs/explanation/design/` and Issues with `[ADR]` label. Missing records must
   be created before releasing. See the Decision Records section below.
4. Update `CHANGELOG.md` manually: `[Unreleased]` → `[vX.Y.Z]`, fill in date.
   Maintain Keep a Changelog format — `cz bump --changelog` destroys the structure.
5. `git push --follow-tags`
6. Create GitHub Release

## Decision Records

Architectural decisions use a two-tier system:

| Tier | Format | When | Content |
|------|--------|------|---------|
| **ADR** | GitHub Issue with `[ADR]` label | Every architectural change | **Why + What** — context, decision, consequences (~200 words)
| **Design doc** | `docs/explanation/design/<topic>.md` | Only major cross-module refactors | **How** — class definitions, data flow, migration steps

- **When to create:** Before or during implementation. The ADR captures reasoning *at decision time*, not after.
- **ADR template:** `.github/ISSUE_TEMPLATE/adr.md` (Context → Decision → Consequences)
- **Design docs reference their source ADR** in a "Related" section.
- See `CONTRIBUTING.md` §Decision Records for the full policy.
- When creating or editing `docs/` files, follow the frontmatter specification in `docs/meta/documentation-standards.md`.

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
| Add documentation page | Create `.md` in `docs/`, add nav entry in `mkdocs.yml`, follow frontmatter spec in `docs/meta/documentation-standards.md` |

### Reference files

- [Development Task Map](references/task-map.md) — **Load this when you know WHAT you want to build but not WHERE to put it.** Maps intents like "add energy spectrum" or "add CLI subcommand" to specific files and code patterns.

### Deep-dive references

For architecture rationale, data flow diagrams, and design decisions beyond the rules above:

- **Architecture:** `docs/explanation/architecture/` — overview, dependency hierarchy, data flow, unit conversion, k-space pipeline, vis architecture
- **Design:** `docs/explanation/design/` — unit system, post-processor, documentation system, architecture refactor
- **Modules:** `docs/reference/modules/` — per-module API deep dives
- **Standards:** `docs/meta/documentation-standards.md` — frontmatter spec, controlled vocabularies

Load these only when you need to understand *why* a design decision was made. For routine coding, the rules and gotchas above are sufficient.

## Validation workflow

After every code change, run the full check and iterate until green:

1. `make check-all`
2. If it fails: read the error, fix the issue, go to step 1
3. Only commit or push when `make check-all` passes clean

Pre-push hooks also run `make check-all` automatically. Use `git push --no-verify` only on feature branches for exploratory work — **never on `main`**.

## Submit Checklist

Before committing or opening a PR, verify each item:

```markdown
- [ ] `ruff check src/ && ruff format --check src/ && mypy src/ && pytest -m "not slow and not data"`
      must pass locally before every commit — **never use `--no-verify` to bypass**.
      If pre-commit hooks fail, fix the reported issues and commit again.
- [ ] Language: all code/comments/docs/commits in **English**
- [ ] No internal paths, usernames, or hostnames (`/work/home/...`, `/Users/...`)
- [ ] CHANGELOG.md updated (if user-facing change)
- [ ] **Decision record exists** — if this change touches data model,
      new module, API break, or new dependency, a corresponding Issue
      with `[ADR]` label or `docs/explanation/design/` doc must exist
- [ ] Sync targets updated if applicable:
      - CLI change → `skills/osiris-user/SKILL.md` + `docs/manifest.json`
      - API change → `skills/osiris-user/SKILL.md` + `docs/manifest.json`
      - Architecture change → `CONTRIBUTING.md` + `AGENTS.md`
      - File added/removed → `mkdocs.yml` nav + `docs/manifest.json`
- [ ] `make check-all` passes (runs lint + typecheck + test + docs-build + arch check + doc sync + frontmatter validation)
```

> Tip: Pre-commit hooks catch most formatting/type issues automatically on commit.
> Pre-push hooks run `make check-all` before every push. Install them with:
> `uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push`
