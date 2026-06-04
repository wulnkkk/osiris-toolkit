# Contributing to osiris-toolkit

Thank you for your interest in contributing! This guide covers how to set up your environment, follow project conventions, and submit changes.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/wulnkkk/osiris-toolkit.git
cd osiris-toolkit

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install with dev dependencies
uv sync --dev
```

## Branch Naming

- **Feature branches**: `feat/<description>` (e.g. `feat/add-scattering-analyzer`)
- **Bug fixes**: `fix/<description>` (e.g. `fix/zdf-chunk-read-bounds`)
- **Release branches**: `release/vX.Y.Z`
- Use lowercase with hyphens between words, no underscores.

## Commit Messages

Format: `<type>: <short description>`

| Type       | Usage                           |
|------------|---------------------------------|
| `feat`     | New feature or enhancement      |
| `fix`      | Bug fix                         |
| `refactor` | Code restructuring (no behavior change) |
| `docs`     | Documentation only              |
| `test`     | Test additions or fixes         |
| `chore`    | Build, CI, config, generators   |

Examples:
- `feat: add k-space spectrum analyzer`
- `fix: boundary check in chunked ZDF read`
- `docs: update module docs for v0.6.0`
- `chore: regenerate _generated files`

## Pull Request Workflow

1. Create a feature/fix branch from `main`.
2. Make your changes, adhering to the conventions below.
3. Run tests and linting: `uv run pytest` and `uv run ruff check src/ tests/`.
4. Push your branch and open a PR against `main`.
5. Ensure CI passes before requesting review.

## Architecture Rules

See [Architecture Overview](architecture/overview.md) for the full module hierarchy. Key rules:

- **Data flow**: base layer -> low-level -> mid-level -> high-level. No reverse dependencies.
- **No circular imports**: modules in `sim/` cannot import from `vis/`, etc.
- **`_generated/`** is auto-generated — never edit by hand. Run `scripts/extract_definitions.py` to regenerate.
- All modules export their public API through `__init__.py`.

## Code Style

- **Python >= 3.10** with type annotations on new functions.
- **Line length**: 120 characters (configured in ruff).
- **Naming**: `snake_case` for functions, variables, and modules.
- **Docstrings**: NumPy/SciPy style, matching existing conventions.
- **Imports**: organized by ruff (isort rules enabled).

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=osiris_toolkit

# Run a specific test file
uv run pytest tests/test_units.py

# Run linting
uv run ruff check src/ tests/

# Auto-fix linting issues
uv run ruff check --fix src/ tests/
```

Tests requiring real ZDF simulation data are marked with `@pytest.mark.data` and are skipped in CI.

## Documentation

We use MkDocs with Material theme:

```bash
# Install docs dependencies
uv pip install mkdocs mkdocs-material "mkdocstrings[python]"

# Serve live preview
uv run mkdocs serve

# Build static site
uv run mkdocs build --strict
```

Module documentation lives in `docs/modules/` and should be updated whenever a module's API changes.

## Release Process

See [Architecture Overview](architecture/overview.md) for the full module hierarchy, and `docs/devlog/` for historical changelogs. Releases follow a checklist in CLAUDE.md (see "Version Release Checklist").

## Questions?

Open an issue on GitHub: <https://github.com/wulnkkk/osiris-toolkit/issues>
