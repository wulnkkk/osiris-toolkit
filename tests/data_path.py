"""Resolve the path to real OSIRIS simulation data for testing.

Priority:
1. OSIRIS_TOOLKIT_DATA_PATH environment variable
2. ../osiris-1.0.0/<sim_owner>/ relative to the toolkit root (pigsproject layout)
3. None — real-data tests will skip
"""

import os
from pathlib import Path

_ENV_VAR = "OSIRIS_TOOLKIT_DATA_PATH"


def get_data_path() -> Path | None:
    """Return the root of real simulation data, or None if not available."""
    env = os.environ.get(_ENV_VAR)
    if env:
        p = Path(env)
        if p.is_dir():
            return p

    # Fallback: try the known pigsproject layout
    toolkit_root = Path(__file__).resolve().parents[1]
    candidate = toolkit_root.parent / "osiris-1.0.0" / "<sim_owner>"
    if candidate.is_dir():
        return candidate

    return None


def require_data_path() -> Path:
    """Return the data path or raise RuntimeError with a helpful message."""
    p = get_data_path()
    if p is None:
        raise RuntimeError(
            f"Real simulation data not found. Set {_ENV_VAR} or place "
            f"<sim_owner>/ alongside osiris-toolkit/ under osiris-1.0.0/."
        )
    return p
