---
audience: [human]
role: user
topic: installation
kind: tutorial
updated: 2026-06-04
---

# Installation

## Requirements

- Python >= 3.10
- numpy >= 1.20
- matplotlib >= 3.5
- click >= 8.0
- pyyaml >= 6.0

## pip (recommended)

```bash
# (Optional but recommended) Create and activate a virtual environment first:
#   python -m venv .venv
#   source .venv/bin/activate      # Linux/macOS
#   .venv\Scripts\activate          # Windows

pip install osiris-toolkit
```

## Development install

### With uv (recommended)

```bash
git clone https://github.com/wulnkkk/osiris-toolkit.git
cd osiris-toolkit
uv venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate     # Windows
uv sync --dev
```

### Without uv

```bash
git clone https://github.com/wulnkkk/osiris-toolkit.git
cd osiris-toolkit
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate     # Windows
pip install -e .
pip install pytest pytest-cov ruff mypy pre-commit commitizen
```

> **Note:** `pyproject.toml` uses uv's `[dependency-groups]` for dev dependencies.
> Standard pip does not recognize this table, so `pip install -e ".[dev]"` won't
> install the dev tools. Install them manually as shown above.

## Optional: Documentation tools

```bash
pip install "osiris-toolkit[docs]"
mkdocs serve   # preview docs locally at http://localhost:8000
```

## Optional: HDF5 support

```bash
pip install "osiris-toolkit[hdf5]"
```

## Optional: VTK export

```bash
pip install "osiris-toolkit[vtk]"
```

## Verifying

```bash
osiris-toolkit --version
python -c "import osiris_toolkit; print(osiris_toolkit.__version__)"
```
