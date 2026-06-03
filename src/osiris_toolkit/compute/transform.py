"""Coordinate transformations for 2-D Field data."""

from __future__ import annotations

import numpy as np

from osiris_toolkit.exceptions import ShapeError
from osiris_toolkit.sim.diagnostics import Field, GridAxis


def remap_field(
    field: Field,
    new_axes: tuple[GridAxis, GridAxis],
    interpolation: str = "bilinear",
) -> Field:
    """Remap a 2-D field to a new coordinate system.

    Parameters
    ----------
    field : Field
        Input 2-D field.
    new_axes : tuple[GridAxis, GridAxis]
        Target axes defining both coordinate mapping and output resolution.
    interpolation : str
        'nearest' or 'bilinear'.

    Returns
    -------
    Field
        Remapped field with axes set to *new_axes*.
    """
    if field.data.ndim != 2:
        raise ShapeError(f"Expected 2-D field, got shape {field.data.shape}")

    old_axes = field.axes
    if len(old_axes) < 2:
        raise ShapeError("Field must have at least 2 axes for remap")

    ny_out = new_axes[1].npoints
    nx_out = new_axes[0].npoints

    x_out = np.linspace(new_axes[0].min, new_axes[0].max, nx_out)
    y_out = np.linspace(new_axes[1].min, new_axes[1].max, ny_out)
    xx, yy = np.meshgrid(x_out, y_out)

    old_x_idx = old_axes[0].value_to_index(xx)
    old_y_idx = old_axes[1].value_to_index(yy)

    if interpolation == "nearest":
        ix = np.clip(np.round(old_x_idx).astype(int), 0, old_axes[0].npoints - 1)
        iy = np.clip(np.round(old_y_idx).astype(int), 0, old_axes[1].npoints - 1)
        remapped = field.data[iy, ix]
    else:
        x0 = np.clip(np.floor(old_x_idx).astype(int), 0, old_axes[0].npoints - 1)
        x1 = np.clip(x0 + 1, 0, old_axes[0].npoints - 1)
        y0 = np.clip(np.floor(old_y_idx).astype(int), 0, old_axes[1].npoints - 1)
        y1 = np.clip(y0 + 1, 0, old_axes[1].npoints - 1)

        wx = old_x_idx - x0
        wy = old_y_idx - y0

        remapped = (
            (1 - wy) * (1 - wx) * field.data[y0, x0]
            + (1 - wy) * wx * field.data[y0, x1]
            + wy * (1 - wx) * field.data[y1, x0]
            + wy * wx * field.data[y1, x1]
        )

    return Field(
        data=remapped.astype(field.data.dtype),
        axes=list(new_axes),
        iteration=field.iteration,
        time=field.time,
        label=field.label,
        units=field.units,
    )


def to_cylindrical(
    field: Field,
    nr: int | None = None,
    ntheta: int = 360,
    r_max: float | None = None,
    origin: tuple[float, float] | None = None,
) -> Field:
    """Convert a 2-D Cartesian field to polar (r, θ) coordinates.

    Parameters
    ----------
    field : Field
        Input 2-D Cartesian field.
    nr : int or None
        Number of radial grid points. Auto-computed if None.
    ntheta : int
        Number of angular grid points.
    r_max : float or None
        Maximum radius. Auto-computed if None.
    origin : tuple[float, float] or None
        (x0, y0) origin. Defaults to grid center.

    Returns
    -------
    Field
        Polar field with axes (r, θ).
    """
    if origin is None:
        x0 = (field.axes[0].min + field.axes[0].max) / 2
        y0 = (field.axes[1].min + field.axes[1].max) / 2
    else:
        x0, y0 = origin

    corners = [
        np.hypot(field.axes[0].min - x0, field.axes[1].min - y0),
        np.hypot(field.axes[0].max - x0, field.axes[1].min - y0),
        np.hypot(field.axes[0].min - x0, field.axes[1].max - y0),
        np.hypot(field.axes[0].max - x0, field.axes[1].max - y0),
    ]
    default_r_max = max(corners)
    if r_max is None:
        r_max = default_r_max
    if nr is None:
        nr = max(field.axes[0].npoints, field.axes[1].npoints)

    r_axis = GridAxis(
        name="r", type=0, min=0.0, max=r_max,
        label="r", units=field.axes[0].units, npoints=nr,
    )
    theta_axis = GridAxis(
        name="theta", type=0, min=0.0, max=2 * np.pi,
        label="θ", units="rad", npoints=ntheta,
    )

    return remap_field(field, (r_axis, theta_axis), interpolation="bilinear")


__all__ = ["remap_field", "to_cylindrical"]
