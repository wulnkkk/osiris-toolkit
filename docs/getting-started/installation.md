---
audience: [human]
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
pip install osiris-toolkit
```

## Development install

```bash
git clone https://github.com/wulnkkk/osiris-toolkit.git
cd osiris-toolkit
uv venv
uv sync --dev
```

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
