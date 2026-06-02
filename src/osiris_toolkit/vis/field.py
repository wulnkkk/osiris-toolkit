"""Visualise electromagnetic field components (E1, E2, E3, B1, B2, B3)."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import SymLogNorm

from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter

from .common import get_converter, load_sim, save_or_show

logger = logging.getLogger(__name__)


def plot_field(
    quantity: str,
    iteration: int,
    sim_path: str | Path | None = None,
    *,
    sim: Simulation | None = None,
    converter: UnitConverter | None = None,
    x_unit: str = "auto",
    y_unit: str = "auto",
    value_unit: str = "auto",
    time_unit: str = "auto",
    log_scale: bool = False,
    vmin: float | None = None,
    vmax: float | None = None,
    cmap: str = "RdBu_r",
    output: str | Path | None = None,
    overwrite: bool = False,
) -> Path | None:
    """Plot a 2-D field component at a given iteration.

    Parameters
    ----------
    quantity : str
        Field component name: 'e1', 'e2', 'e3', 'b1', 'b2', or 'b3'.
    iteration : int
        Iteration number to read.
    sim_path : str or Path
        Path to the simulation output directory.
    converter : UnitConverter or None
        Unit converter for physical units.  If None, units are skipped
        (data shown in normalised units).
    x_unit, y_unit : str
        Spatial axis units ('um', 'nm', 'norm', 'auto', etc.).
    value_unit : str
        Unit for the field-value colour bar.
    time_unit : str
        Unit for the time shown in the title.
    log_scale : bool
        If True, use a symmetric-log normalisation.
    vmin, vmax : float or None
        Colour range limits.  If None, auto-determined from the data.
    cmap : str
        Matplotlib colormap name.
    output : Path or None
        File path to save the figure.  If None, display interactively.
    """
    sim_obj = load_sim(sim_path, sim=sim)
    if converter is None:
        converter = get_converter(sim_obj)

    if output is None and sim_obj is not None:
        d = sim_obj.output_dir("fields")
        output = d / f"{quantity}_{iteration:06d}.png"

    grid = sim_obj.get_field(quantity, iteration)
    if grid is None:
        raise ValueError(
            f"Field {quantity!r} not found at iteration {iteration}. "
            f"Available: {sim_obj.list_fields()}"
        )

    data = grid.data
    if converter is not None:
        qtype = "b_field" if quantity.lower().startswith("b") else "e_field"
        display_val = converter.convert(data, qtype, value_unit)
    else:
        display_val = data
        value_unit = "norm"

    # Spatial extent with unit conversion
    if len(grid.axes) >= 2:
        if converter is not None:
            x_lo = converter.convert(grid.axes[0].min, "length", x_unit)
            x_hi = converter.convert(grid.axes[0].max, "length", x_unit)
            y_lo = converter.convert(grid.axes[1].min, "length", y_unit)
            y_hi = converter.convert(grid.axes[1].max, "length", y_unit)
        else:
            x_lo, x_hi = grid.axes[0].min, grid.axes[0].max
            y_lo, y_hi = grid.axes[1].min, grid.axes[1].max
        extent = [x_lo, x_hi, y_lo, y_hi]
    else:
        extent = None

    # --- 1D data: line plot ---
    if data.ndim == 1:
        fig, ax = plt.subplots(figsize=(10, 6))
        if len(grid.axes) >= 1 and grid.axes[0].npoints > 0:
            x_coord = np.linspace(grid.axes[0].min, grid.axes[0].max, len(display_val))
        else:
            x_coord = np.arange(len(display_val))

        ax.plot(x_coord, display_val, linewidth=2, color="steelblue")
        ax.grid(True, alpha=0.3)
        if converter is not None:
            ax.set_xlabel(converter.get_length_label(x_unit, "x1"))
            ax.set_ylabel(converter.get_label(qtype, value_unit))
        else:
            ax.set_xlabel(f"x1 [{grid.axes[0].units}]" if grid.axes and grid.axes[0].units else "x1")
            ax.set_ylabel(f"{grid.label} [{grid.units}]" if grid.units else grid.label)
        ax.set_title(_make_title(grid, quantity, iteration, converter, time_unit))
        save_or_show(fig, output, overwrite=overwrite)
        return Path(output) if output else None

    # --- 2D+ data: imshow ---
    fig, ax = plt.subplots(figsize=(10, 8))

    if log_scale and data.ndim == 2:
        linthresh = max(
            abs(vmin or np.nanpercentile(data, 1)),
            abs(vmax or np.nanpercentile(data, 99)),
        ) * 0.01
        norm = SymLogNorm(linthresh=linthresh if linthresh > 0 else 0.1)
    else:
        norm = None

    _vmin = vmin
    _vmax = vmax
    if converter is not None and _vmin is not None:
        _vmin = converter.convert(vmin, qtype, value_unit)
    if converter is not None and _vmax is not None:
        _vmax = converter.convert(vmax, qtype, value_unit)

    im = ax.imshow(
        display_val.T if data.ndim == 2 else display_val.reshape(-1, 1),
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap=cmap,
        vmin=_vmin,
        vmax=_vmax,
        norm=norm,
    )

    cbar = fig.colorbar(im, ax=ax)
    if converter is not None:
        cbar.set_label(converter.get_label(qtype, value_unit))
    else:
        cbar.set_label(
            f"{grid.label} [{grid.units}]" if grid.units else grid.label
        )

    if converter is not None:
        ax.set_xlabel(converter.get_length_label(x_unit, "x1"))
        if data.ndim >= 2:
            ax.set_ylabel(converter.get_length_label(y_unit, "x2"))
    else:
        ax.set_xlabel(
            f"x1 [{grid.axes[0].units}]"
            if grid.axes and grid.axes[0].units
            else "x1"
        )
        if data.ndim >= 2:
            ax.set_ylabel(
                f"x2 [{grid.axes[1].units}]"
                if len(grid.axes) > 1 and grid.axes[1].units
                else "x2"
            )

    # Title with time
    ax.set_title(_make_title(grid, quantity, iteration, converter, time_unit))

    save_or_show(fig, output, overwrite=overwrite)
    return Path(output) if output else None


def _make_title(grid, quantity, iteration, converter, time_unit):
    """Build a plot title with quantity, iteration, and time."""
    if converter is not None:
        t_disp = converter.convert(grid.time, "time", time_unit)
        t_label = converter.get_label("time", time_unit)
        return (
            f"{quantity.upper()}  |  iteration={iteration}"
            f"  |  t={t_disp:.1f} {t_label}"
        )
    return (
        f"{quantity.upper()}  |  iteration={iteration}"
        f"  |  t={grid.time:.1f}"
    )


def plot_all_fields(
    iteration: int,
    sim_path: str | Path | None = None,
    *,
    sim: Simulation | None = None,
    converter: UnitConverter | None = None,
    x_unit: str = "auto",
    y_unit: str = "auto",
    time_unit: str = "auto",
    output: str | Path | None = None,
    overwrite: bool = False,
) -> None:
    """Plot all available field components in a multi-panel figure.

    Parameters
    ----------
    iteration : int
        Iteration number to read.
    sim_path : str or Path
        Path to the simulation output directory.
    converter : UnitConverter or None
        Unit converter for physical units.
    x_unit, y_unit : str
        Spatial axis units.
    time_unit : str
        Unit for the time shown in titles.
    output : Path or None
        File path to save the figure.
    """
    sim_obj = load_sim(sim_path, sim=sim)
    if converter is None:
        converter = get_converter(sim_obj)

    fields = sim_obj.list_fields()
    n = len(fields)
    if n == 0:
        raise ValueError("No field diagnostics found.")

    cols = min(3, n)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes = np.atleast_1d(axes).flatten()

    for ax, qty in zip(axes, fields):
        grid = sim_obj.get_field(qty, iteration)
        if grid is None:
            ax.set_title(f"{qty.upper()} -- not found")
            continue
        data = grid.data
        if converter is not None:
            extent = [
                converter.convert(grid.axes[0].min, "length", x_unit),
                converter.convert(grid.axes[0].max, "length", x_unit),
                converter.convert(grid.axes[1].min, "length", y_unit),
                converter.convert(grid.axes[1].max, "length", y_unit),
            ] if len(grid.axes) >= 2 else None
        else:
            extent = (
                [
                    grid.axes[0].min,
                    grid.axes[0].max,
                    grid.axes[1].min,
                    grid.axes[1].max,
                ]
                if len(grid.axes) >= 2
                else None
            )
        im = ax.imshow(
            data.T, origin="lower", aspect="auto", extent=extent, cmap="RdBu_r"
        )
        fig.colorbar(im, ax=ax)
        if converter is not None:
            t_disp = converter.convert(grid.time, "time", time_unit)
        else:
            t_disp = grid.time
        ax.set_title(f"{qty.upper()}  t={t_disp:.1f}")
        if converter is not None:
            ax.set_xlabel(converter.get_length_label(x_unit, "x1"))
            ax.set_ylabel(converter.get_length_label(y_unit, "x2"))
        else:
            ax.set_xlabel("x1")
            ax.set_ylabel("x2")

    for ax in axes[n:]:
        ax.set_visible(False)

    fig.suptitle(f"All field components -- iteration {iteration}", fontsize=14)
    fig.tight_layout()
    save_or_show(fig, output, overwrite=overwrite)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.info(
            "Usage: python -m osiris_toolkit.vis.field SIM_PATH [ITERATION]"
        )
        sys.exit(1)

    sim_path = sys.argv[1]
    iteration = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    sim = load_sim(sim_path)
    converter = get_converter(sim)
    iters = sim.list_iterations("e1")
    it = iters[iteration] if iters and iteration < len(iters) else (iters[-1] if iters else 0)
    plot_field(
        "e1", it, sim_path=sim_path, converter=converter,
        x_unit="um", y_unit="um", time_unit="ps",
        output="field_e1.png",
    )
    logger.info("Done -- see field_e1.png")
