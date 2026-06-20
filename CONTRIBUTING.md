# Contributing to osiris-toolkit

Welcome! This document covers development setup, code style, commit conventions, testing, and release processes.

> **📖 Full contributing guide at** [docs/contributing.md](docs/contributing.md)

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

# Install pre-commit hooks (run automatically on every commit)
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

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
- [ ] Branch rebased onto latest main

> See [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) for the full template.

---

## Release Process

1. Ensure all features are merged to `main` and CI passes
2. Run `uv run cz bump` to auto-bump version and create a git tag
3. Update `CHANGELOG.md`: rename `[Unreleased]` → `[vX.Y.Z]`, fill in release date
4. Push the tag: `git push --follow-tags`
5. Create a GitHub Release linked to the tag

> Versions follow [Semantic Versioning 2.0](https://semver.org/).

---

## Architecture Rules

- **Data flow**: base layer → low-level → mid-level → high-level. No reverse dependencies.
- **No circular imports**: `sim/` module cannot import `vis/` or other high-level modules.
- **`_generated/`**: Auto-generated — never edit by hand. Run `dev-tools/extract_definitions.py` to regenerate.
- All modules export their public API through `__init__.py`.

See [Architecture Overview](docs/architecture/overview.md) for details.

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
- [ ] Update `docs/modules/*.md` if module behavior changed
- [ ] Update `docs/agent-user/task-map.md` if CLI or Python API changed
- [ ] Update `docs/agent-dev/dev-task-map.md` if development entry points changed
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
- [ ] Review `docs/architecture/` — still reflects current design
- [ ] Review `.pre-commit-config.yaml` hook versions
- [ ] Review `docs/agent-user/` and `docs/agent-dev/` — still match actual capabilities

## Feedback

- 🐛 Report a bug: use the [Bug Report template](https://github.com/wulnkkk/osiris-toolkit/issues/new?labels=bug&template=bug_report.md)
- ✨ Suggest a feature: use the [Feature Request template](https://github.com/wulnkkk/osiris-toolkit/issues/new?labels=enhancement&template=feature_request.md)
- 💬 Start a discussion: [GitHub Discussions](https://github.com/wulnkkk/osiris-toolkit/discussions)
