"""VTK structured grid export via pyevtk (optional dependency).

Requires ``pyevtk``:  ``pip install osiris-toolkit[vtk]``
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from osiris_toolkit._models import Field
from osiris_toolkit.exceptions import MissingDependencyError


def to_vtk(
    field: Field,
    output: str | Path,
    converter=None,
    x_unit: str = "um",
    y_unit: str = "um",
    z_unit: str = "um",
) -> Path:
    """Export a Field to VTK structured grid format.

    - 1-D data → ``.vtr`` (RectilinearGrid)
    - 2-D data → ``.vtr`` (RectilinearGrid)
    - 3-D data → ``.vts`` (StructuredGrid)

    Requires ``pyevtk`` (``pip install pyevtk``).

    Parameters
    ----------
    field : Field
        The field to export.
    output : str or Path
        Output file path (without extension — .vtr/.vts is appended).
    converter : UnitConverter or None
        Unit converter for physical coordinates.
    x_unit, y_unit, z_unit : str
        Physical units for spatial axes.

    Returns
    -------
    Path
        The output file path (with extension).
    """
    try:
        from pyevtk.hl import gridToVTK
    except ImportError:
        raise MissingDependencyError("pyevtk is required for VTK export. Install with: pip install osiris-toolkit[vtk]")

    output = Path(output)
    ndim = field.data.ndim
    label = field.label or "data"

    # Build coordinate arrays from axes
    if field.axes:
        x = _axis_coords(field.axes[0])
        y = _axis_coords(field.axes[1]) if ndim >= 2 and len(field.axes) >= 2 else None
        z = _axis_coords(field.axes[2]) if ndim >= 3 and len(field.axes) >= 3 else None
    else:
        x = np.arange(field.data.shape[0], dtype=np.float64)
        y = np.arange(field.data.shape[1], dtype=np.float64) if ndim >= 2 else None
        z = np.arange(field.data.shape[2], dtype=np.float64) if ndim >= 3 else None

    if ndim == 1:
        if y is None:
            y = np.zeros(1, dtype=np.float64)
        if z is None:
            z = np.zeros(1, dtype=np.float64)
        data_3d = field.data[:, np.newaxis, np.newaxis]
    elif ndim == 2:
        if z is None:
            z = np.zeros(1, dtype=np.float64)
        data_3d = field.data[:, :, np.newaxis]
    else:
        data_3d = field.data

    data_3d = np.ascontiguousarray(data_3d)
    x_arr = np.ascontiguousarray(x, dtype=np.float64)
    y_arr = np.ascontiguousarray(y if y is not None else np.zeros(1, dtype=np.float64), dtype=np.float64)
    z_arr = np.ascontiguousarray(z if z is not None else np.zeros(1, dtype=np.float64), dtype=np.float64)

    output_str = str(output).replace(".vts", "").replace(".vtr", "").replace(".vti", "")
    gridToVTK(output_str, x_arr, y_arr, z_arr, pointData={label: data_3d})

    # pyevtk auto-determines extension based on coordinate dimensions
    for ext in (".vtr", ".vts", ".vti"):
        candidate = Path(output_str + ext)
        if candidate.exists():
            return candidate
    return Path(output_str + ".vts")  # fallback (should not happen)


def _axis_coords(axis) -> np.ndarray:
    """Build coordinate array from a GridAxis."""
    n = axis.npoints if axis.npoints > 0 else 1
    return np.linspace(axis.min, axis.max, n, dtype=np.float64)
