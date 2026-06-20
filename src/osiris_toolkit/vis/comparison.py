"""Field comparison plots — difference maps and overlay views."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osiris_toolkit.exceptions import DataNotFoundError, ValidationError
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units.converter import UnitSystem
from osiris_toolkit.vis.common import get_system, load_sim, save_or_show


def plot_difference(
    quantity: str,
    iter_a: int,
    iter_b: int,
    sim_path: str | Path | None = None,
    *,
    sim: Simulation | None = None,
    system: UnitSystem | None = None,
    x_unit: str = "auto",
    y_unit: str = "auto",
    cmap: str = "RdBu_r",
    output: Path | None = None,
    overwrite: bool = False,
) -> Path | None:
    """Plot the spatial difference between two iterations of the same field.

    Parameters
    ----------
    quantity : str
    iter_a, iter_b : int
        Two iteration numbers. Plots data_b - data_a.
    sim, sim_path, system : standard
    x_unit, y_unit : str
    cmap : str
    output, overwrite : standard

    Returns
    -------
    Path or None
    """
    sim_obj = load_sim(sim_path, sim=sim)
    if system is None:
        system = get_system(sim_obj)

    grid_a = sim_obj.get_field(quantity, iter_a)
    grid_b = sim_obj.get_field(quantity, iter_b)
    if grid_a is None or grid_b is None:
        raise DataNotFoundError(f"Field {quantity!r} not found at requested iterations")

    diff = grid_b.data.astype(np.float64) - grid_a.data.astype(np.float64)

    if len(grid_a.axes) >= 2:
        x_lo, x_hi = grid_a.axes[0].min, grid_a.axes[0].max
        y_lo, y_hi = grid_a.axes[1].min, grid_a.axes[1].max
        if system is not None:
            x_lo = system["length"].to(x_lo, x_unit)
            x_hi = system["length"].to(x_hi, x_unit)
            y_lo = system["length"].to(y_lo, y_unit)
            y_hi = system["length"].to(y_hi, y_unit)
        extent = [x_lo, x_hi, y_lo, y_hi]
    else:
        extent = None

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(diff, origin="lower", aspect="auto", extent=tuple(extent) if extent is not None else None, cmap=cmap)  # type: ignore[arg-type]
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(f"Delta({quantity})")
    ax.set_xlabel(f"x1 [{x_unit}]" if system else "x1")
    ax.set_ylabel(f"x2 [{y_unit}]" if system else "x2")
    ax.set_title(f"Delta {quantity.upper()}  |  iter {iter_b} - {iter_a}")
    fig.tight_layout()
    save_or_show(fig, output, overwrite=overwrite)
    return Path(output) if output else None


def plot_overlay(
    quantities: list[str],
    iteration: int,
    sim_path: str | Path | None = None,
    *,
    sim: Simulation | None = None,
    system: UnitSystem | None = None,
    x_unit: str = "auto",
    y_unit: str = "auto",
    alpha: float = 0.5,
    output: Path | None = None,
    overwrite: bool = False,
) -> Path | None:
    """Overlay two field components at the same iteration.

    Parameters
    ----------
    quantities : list[str]
        Two field quantities (e.g. ['e1', 'b3']).
    iteration : int
    sim, sim_path, system : standard
    x_unit, y_unit : str
    alpha : float
        Transparency of the overlay layer.
    output, overwrite : standard

    Returns
    -------
    Path or None
    """
    if len(quantities) != 2:
        raise ValidationError("plot_overlay requires exactly 2 quantities")

    sim_obj = load_sim(sim_path, sim=sim)
    if system is None:
        system = get_system(sim_obj)

    grids = []
    for q in quantities:
        g = sim_obj.get_field(q, iteration)
        if g is None:
            raise DataNotFoundError(f"Field {q!r} not found at iteration {iteration}")
        grids.append(g)

    g0, g1 = grids
    if len(g0.axes) >= 2:
        x_lo, x_hi = g0.axes[0].min, g0.axes[0].max
        y_lo, y_hi = g0.axes[1].min, g0.axes[1].max
        if system is not None:
            x_lo = system["length"].to(x_lo, x_unit)
            x_hi = system["length"].to(x_hi, x_unit)
            y_lo = system["length"].to(y_lo, y_unit)
            y_hi = system["length"].to(y_hi, y_unit)
        extent = [x_lo, x_hi, y_lo, y_hi]
    else:
        extent = None

    fig, ax = plt.subplots(figsize=(10, 8))

    im0 = ax.imshow(
        g0.data,
        origin="lower",
        aspect="auto",
        extent=tuple(extent) if extent is not None else None,  # type: ignore[arg-type]
        cmap="RdBu_r",
    )
    cbar0 = fig.colorbar(im0, ax=ax, location="left")
    cbar0.set_label(quantities[0])

    im1 = ax.imshow(
        g1.data,
        origin="lower",
        aspect="auto",
        extent=tuple(extent) if extent is not None else None,  # type: ignore[arg-type]
        cmap="Blues",
        alpha=alpha,
    )
    cbar1 = fig.colorbar(im1, ax=ax, location="right")
    cbar1.set_label(quantities[1])

    ax.set_xlabel(f"x1 [{x_unit}]" if system else "x1")
    ax.set_ylabel(f"x2 [{y_unit}]" if system else "x2")
    ax.set_title(f"Overlay: {' + '.join(q.upper() for q in quantities)}  |  iter={iteration}")
    fig.tight_layout()
    save_or_show(fig, output, overwrite=overwrite)
    return Path(output) if output else None


__all__ = ["plot_difference", "plot_overlay"]
