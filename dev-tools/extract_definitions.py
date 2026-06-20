#!/usr/bin/env python3
"""Extract parameter, quantity, and section definitions from OSIRIS Fortran source.

Usage:
    python dev-tools/extract_definitions.py /path/to/osiris-1.0.0/source

Generates files in src/osiris_toolkit/_generated/:
    - parameters.py  — namelist parameter names, types, defaults
    - quantities.py  — diagnostic quantity lists
    - sections.py    — input section names
"""

from __future__ import annotations

import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PACKAGE_DIR = _THIS_DIR.parent / "src" / "osiris_toolkit"
_GENERATED_DIR = _PACKAGE_DIR / "_generated"


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/osiris-1.0.0/source")
        sys.exit(1)

    source_dir = Path(sys.argv[1])
    if not source_dir.is_dir():
        print(f"Error: not a directory: {source_dir}")
        sys.exit(1)

    _GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # Add package to path (needed when running as standalone script)
    sys.path.insert(0, str(_PACKAGE_DIR.parent))

    from osiris_toolkit.sync.namelist import generate as gen_params
    from osiris_toolkit.sync.diagnostics import generate as gen_quants
    from osiris_toolkit.sync.sections import generate as gen_sections

    print(f"Extracting from: {source_dir}")
    print(f"Writing to:      {_GENERATED_DIR}")

    gen_params(_GENERATED_DIR / "parameters.py", source_dir)
    print(f"  → parameters.py ({len(list(source_dir.rglob('*')))} files scanned)")

    gen_quants(_GENERATED_DIR / "quantities.py", source_dir)
    print(f"  → quantities.py")

    gen_sections(_GENERATED_DIR / "sections.py", source_dir)
    print(f"  → sections.py")

    print("Done.")


if __name__ == "__main__":
    main()
