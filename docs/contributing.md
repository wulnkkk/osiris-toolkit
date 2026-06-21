---
audience: [human]
role: developer
topic: contributing
kind: how-to
updated: 2026-06-20
---

# Contributing to osiris-toolkit

Thank you for your interest in contributing!

> **📖 For a detailed guide (including release process, full checklist) see [`CONTRIBUTING.md`](https://github.com/wulnkkk/osiris-toolkit/blob/main/CONTRIBUTING.md).**
> This page is the mkdocs site version, focused on quick reference.

## Setup

```bash
git clone https://github.com/wulnkkk/osiris-toolkit.git
cd osiris-toolkit
uv venv && uv sync --dev
```

## Development workflow

1. Create branch: `feat/<name>` or `fix/<name>`
2. Implement changes following TDD: `uv run pytest` before and after
3. Lint: `uv run ruff check src/`
4. Type check: `uv run mypy src/`
5. Commit using Conventional Commits: `<type>: <description>` (feat/fix/refactor/docs/test/chore)
6. Push, open PR

### Pre-commit hooks

After `uv sync --dev`, install the hooks:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

This automatically runs ruff, mypy, and commitizen on every commit.

### Makefile shortcuts

```bash
make lint        # ruff check
make format      # ruff format
make typecheck   # mypy
make test        # pytest
make docs-serve  # mkdocs serve
make bump        # version bump + changelog
```

## Architecture rules

See [Architecture Overview](explanation/architecture/overview.md). Key rules:
- No reverse dependencies (compute → sim is forbidden)
- Compute layer does pure math, never unit conversion
- Use `UnitSystem`, not `UnitConverter` (deprecated since v0.15.0)

## Testing

```bash
uv run pytest                    # full suite
uv run pytest tests/test_units/  # specific module
uv run pytest -m "not slow"      # CI-friendly subset
```

## Documentation

```bash
# Build and preview
uv run mkdocs serve

# Strict build (catch all warnings)
uv run mkdocs build --strict
```

## Questions?

Open an issue on GitHub: <https://github.com/wulnkkk/osiris-toolkit/issues>
