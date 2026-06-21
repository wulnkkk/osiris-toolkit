# Contributing to osiris-toolkit

Welcome! This document covers development setup, code style, commit conventions, testing, and release processes.

> ## 🤖 AI-Assisted Development
>
> This project provides a dedicated **agent development skill** that AI coding tools (Claude Code, Cursor, GitHub Copilot, etc.) use to understand the codebase:
>
> - **Canonical skill file**: `skills/osiris-dev/SKILL.md` (Agent Skills open standard format)
> - **What it covers**: project structure, architecture rules (no reverse deps, layer hierarchy), dev workflow, code style, testing, release process, key entry point maps
> - **How to use**: In Claude Code, run `/osiris-dev`; in Cursor, reference the `.claude/` rules; in Reasonix, run `/osiris-dev`. The skill loads on demand — the cross-platform entry point [`AGENTS.md`](AGENTS.md) is auto-loaded every session.
> - **Keep in sync**: If you update dev practices here (e.g., new lint rules, modified test commands), also update `skills/osiris-dev/SKILL.md`.

> This is the canonical contribution guide. A quick-reference version for the docs site is at [`docs/contributing.md`](docs/contributing.md).

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/wulnkkk/osiris-toolkit.git
cd osiris-toolkit

# Create virtual environment and install dependencies (including dev)
uv venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
uv sync --dev

# Install pre-commit hooks (run automatically on commit and push)
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
```

> Pre-push hooks run `make check-all` before every `git push`. If they fail,
> the push is blocked. Use `git push --no-verify` to bypass (not recommended).

### Without uv

If you don't have uv installed, use pip + venv instead:

```bash
# Create and activate virtual environment
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate

# Install the project in editable mode
pip install -e .

# Install development dependencies (listed in [dependency-groups] in pyproject.toml)
pip install pytest pytest-cov ruff mypy pre-commit commitizen

# Install pre-commit hooks
pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
```

> **Note:** `pyproject.toml` uses uv's `[dependency-groups]` for dev dependencies.
> Standard pip does not recognize this table, so `pip install -e ".[dev]"` won't
> install the dev tools. Install them manually as shown above.

---

## Branch Naming

| Purpose | Format | Example |
|---------|--------|---------|
| New feature | `feat/<description>` | `feat/add-scattering-analyzer` |
| Bug fix | `fix/<description>` | `fix/zdf-chunk-read-bounds` |
| Refactor | `refactor/<description>` | `refactor/converter-to-system` |
| Documentation | `docs/<description>` | `docs/api-reference` |
| Release | `release/vX.Y.Z` | `release/v0.16.0` |

Use lowercase with hyphens between words (underscores are **not** allowed).

---

## Commit Message Convention

This project uses **Conventional Commits**, enforced by `commitizen` at `commit-msg` stage:

```
<type>[(scope)]: <description>
```

### Common Types

| Type | Usage | Triggers version bump |
|------|-------|:-:|
| `feat` | New feature | ✨ minor |
| `fix` | Bug fix | 🩹 patch |
| `refactor` | Code restructuring (no behavior change) | — |
| `refactor!` | Breaking refactor | 💥 major |
| `docs` | Documentation only | — |
| `test` | Test-related | — |
| `chore` | Build, CI, config, code generation | — |
| `perf` | Performance optimization | 🚀 patch |

### Examples

```
feat(analysis): add angular k-space spectrum analyzer
fix(vis): auto-detect projection axis in _auto_k_range
refactor!: migrate converter→system across the codebase
docs: update module docs for v0.15.0
test: add edge case tests for unit converter
```

> 💡 You can also use `uv run cz commit` to generate a compliant commit message interactively.

---

## Code Style

### Ruff (configured)

```bash
# Check code
uv run ruff check src/

# Auto-fix
uv run ruff check --fix src/

# Format
uv run ruff format src/
```

Enabled rule sets: `E`, `W`, `F`, `I`, `N`, `UP`, `B`, `SIM`, `ARG`, `RUF`

### mypy (configured)

```bash
# Type check
uv run mypy src/
```

### Language

All project content **must be in English**:

- Source code: comments, docstrings, variable names, type annotations
- Documentation: `.md` files, code examples, doc site
- Configuration: CI configs, Makefile, GitHub templates
- Git: commit messages, PR/issue descriptions
- Tests: test names, assertions, comments, HPC scripts

The only exceptions are:
- `docs/note/` — local workspace notes (gitignored)
- Test data exercising Unicode parsing (e.g., Chinese in input deck lexer tests)

### pre-commit

After installation, every `git commit` automatically runs:

1. Trailing whitespace check
2. End-of-file fixer
3. YAML/TOML syntax check
4. Large file check (>1MB warning)
5. Merge conflict marker detection
6. Debug statement detection
7. Ruff lint + format
8. mypy type check (staged files only)
9. commitizen commit message validation

---

## Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=osiris_toolkit

# Run a specific test file
uv run pytest tests/test_units.py -v

# Run tests by marker
uv run pytest -m "not slow"

# View coverage report
uv run pytest --cov=osiris_toolkit --cov-report=html
```

- Tests requiring real ZDF data are marked `@pytest.mark.data` (skipped in CI)
- Slow tests are marked `@pytest.mark.slow` (not run by default)
- Test files live in `tests/`, organized by module

---

## Documentation

```bash
# Build and preview locally
uv run mkdocs serve

# Strict mode build (catch all warnings)
uv run mkdocs build --strict
```

Documentation source is in `docs/`, uses mkdocs-material theme + mkdocstrings for auto-generated API docs.

### Sync Suggestions

When you modify code, run this to see which documentation files may need updating:

```bash
# Changes since last commit
uv run python dev-tools/suggest_updates.py --since HEAD~1

# Branch diff against main
uv run python dev-tools/suggest_updates.py --since origin/main
```

It outputs a checklist based on the [sync matrix](#when-addingchanging-public-api).

---

## CHANGELOG

Before each release, add the changes to `CHANGELOG.md` under `[Unreleased]`:

- **Added** — New features
- **Changed** — Non-breaking changes (refactors, optimizations)
- **Deprecated** — Features to be removed
- **Removed** — Removed features
- **Fixed** — Bug fixes
- **Security** — Security fixes

When releasing, rename `[Unreleased]` to the new version number and start a fresh `[Unreleased]` section.

---

## PR Checklist

Before submitting a PR, confirm each item:

- [ ] Code follows ruff style (`uv run ruff check src/`)
- [ ] Type annotations complete (`uv run mypy src/` — no new errors)
- [ ] All tests pass (`uv run pytest -v`)
- [ ] CHANGELOG.md updated
- [ ] **No internal paths, usernames, or hostnames leaked**
- [ ] **All text is in English** — code comments, docstrings, docs, and commit messages
- [ ] **Make check-all passes** — runs lint + typecheck + test + docs-build + arch check + doc sync + english check
- [ ] **Decision record exists** — if this PR introduces an architectural change (data model, new module, API break, new dependency), a corresponding Issue with `[ADR]` label or `docs/explanation/design/` doc must exist and be referenced
- [ ] **Sync targets updated if applicable** (see When Adding/Changing Public API above)
- [ ] Branch rebased onto latest main

> See [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) for the full template.

---

## Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/).

**Current phase**: `0.y.z` — initial development. API is not yet stable.

During 0.y.z, both `BREAKING CHANGE` and `feat` increment MINOR:

| Commit type | Bump | Example |
|-------------|------|---------|
| `feat:` (new feature) | MINOR | `0.15.0` → `0.16.0` |
| `fix:` (bug fix) | PATCH | `0.15.0` → `0.15.1` |
| `refactor!:` / `BREAKING CHANGE` | MINOR | `0.15.0` → `0.16.0` |

See `[tool.commitizen.bump_map]` in `pyproject.toml` for the current mapping.
When ready to release 1.0.0, that section must be removed so that
`BREAKING CHANGE` increments MAJOR as per standard SemVer.

## Release Process

1. Ensure all features are merged to `main` and CI passes
2. Run `uv run cz bump` to auto-bump version and create a git tag
3. **Verify that every architectural change in this release has a public decision record.**
   Check `docs/explanation/design/` and GitHub Issues for each new feature / breaking change.
   Missing records must be created before proceeding. See [Decision Records](#decision-records) below.
4. Update `CHANGELOG.md`: rename `[Unreleased]` → `[vX.Y.Z]`, fill in release date
5. Push the tag: `git push --follow-tags`
6. Create a GitHub Release linked to the tag

> Versions follow [Semantic Versioning 2.0](https://semver.org/).

---

## Decision Records

Architectural decisions must be recorded publicly so that anyone reading the code
can understand **why** it was designed that way without reverse-engineering.

Decision records have two tiers:

| Tier | Format | When | Content depth | Updates |
|------|--------|------|---------------|---------|
| **ADR** | GitHub Issue with `[ADR]` label | Every architectural change | **Why + What** — context, decision, consequences (~200 words) | Written once, never updated |
| **Design doc** | `docs/explanation/design/<topic>.md` | Only major cross-module refactors | **How** — class definitions, data flow, migration steps, code examples | Maintained, `updated` frontmatter refreshed |

**Relationship:** An ADR is the lightweight entry log. A design doc exists only when
the architecture is complex enough to need ongoing maintenance documentation.
Design docs **reference their source ADR** in a "Related" section.

| Change type | Required record | Upgrade to design doc? | Example |
|-------------|----------------|------------------------|---------|
| New module / data model | Issue `[ADR]` | Only if cross-layer dependency changes | `#5 [ADR] Core Data Model` |
| API breaking change | Issue `[ADR]` | No | `#3 [ADR] UnitSystem` |
| New optional dependency | Issue `[ADR]` | No | — |
| Architecture refactor | Issue `[ADR]` | Yes — `docs/explanation/design/` doc needed | `#1` + `docs/explanation/design/architecture-refactor.md` |
| Bug fix / minor improvement | devlog only | No | `docs/devlog/0.16.0.md` |

**ADR template:** See `.github/ISSUE_TEMPLATE/adr.md`.

**When to create:** Before or during implementation, not after. The ADR captures
the reasoning *at decision time*, not reconstructed afterward.

---

## CI Policy

All CI checks must pass before merging or releasing. If CI reports a failure:

1. **Fix the root cause** — do not bypass CI by force-pushing or skipping tests
2. **Re-run CI** — push the fix and wait for CI to pass all checks
3. **No `git push --no-verify` on main** — bypassing pre-push hooks is allowed on
   feature branches for exploratory work, but the final commit to `main` must
   pass all pre-push checks
4. **CI is gating, not advisory** — a red CI is treated as a blocker, not a warning

## Architecture Rules

These rules are enforced by design and must never be broken:

1. **No reverse dependencies** — `compute/` cannot import `sim/` or `vis/`; `sim/` cannot import `vis/`.
2. **Compute does pure math only** — no unit conversion, no OSIRIS-specific knowledge.
3. **`_generated/` is read-only** — never edit by hand. Run `dev-tools/extract_definitions.py` to regenerate.
4. **Use `UnitSystem`, not `UnitConverter`** — `UnitConverter` is deprecated since v0.15.0.
5. **Public API through `__init__.py`** — each module exports its public symbols there.

See [Architecture Overview](docs/explanation/architecture/overview.md) for design principles.
For documentation conventions (frontmatter spec, controlled vocabularies), see
[Documentation Standards](docs/meta/documentation-standards.md).

---

## Project Maintenance Checklist

Items to verify when making changes, grouped by frequency.

### Every Commit (pre-commit enforces most)

- [ ] `ruff check src/` — no new errors
- [ ] `mypy src/` — type annotations on new functions
- [ ] `pytest tests/ -v` — all tests pass
- [ ] Commit message follows Conventional Commits
- [ ] No internal paths/usernames/hostnames

### When Adding/Changing Public API

- [ ] Update `__init__.py` `__all__` — every new public symbol must be exported
- [ ] Write NumPy-style docstring — feeds mkdocstrings API docs
- [ ] Update `docs/reference/modules/*.md` if module behavior changed
- [ ] Update `skills/osiris-user/SKILL.md` and `skills/osiris-user/references/task-map.md` if CLI or Python API changed
- [ ] Update `skills/osiris-dev/SKILL.md` and `skills/osiris-dev/references/task-map.md` if development entry points changed
- [ ] Update `docs/manifest.json` if entry point paths changed

### When Adding/Removing Files

- [ ] `mkdocs.yml` nav — add or remove the corresponding entry
- [ ] Frontmatter `role` and `audience` — matches the file's actual purpose
- [ ] `docs/` file exists on disk → nav entry exists → mkdocs build passes

### Before Release

- [ ] `uv run cz bump` — version + git tag
- [ ] `CHANGELOG.md` — `[Unreleased]` → `[vX.Y.Z]` + date
- [ ] `docs/devlog/X.Y.Z.md` — new version devlog with technical decisions
- [ ] `pyproject.toml` version = git tag = CHANGELOG version
- [ ] `make docs-build` — strict mode passes with no broken links
- [ ] `git push --follow-tags` + GitHub Release

### Quarterly / As-Needed

- [ ] Review `examples/` and `dev-tools/` — paths and references still valid
- [ ] Review `docs/explanation/architecture/` — still reflects current design
- [ ] Review `.pre-commit-config.yaml` hook versions
- [ ] Review `skills/osiris-user/` and `skills/osiris-dev/` — still match actual capabilities

## Feedback

- 🐛 Report a bug: use the [Bug Report template](https://github.com/wulnkkk/osiris-toolkit/issues/new?labels=bug&template=bug_report.md)
- ✨ Suggest a feature: use the [Feature Request template](https://github.com/wulnkkk/osiris-toolkit/issues/new?labels=enhancement&template=feature_request.md)
- 💬 Start a discussion: [GitHub Discussions](https://github.com/wulnkkk/osiris-toolkit/discussions)
