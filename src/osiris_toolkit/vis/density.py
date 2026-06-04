"""Visualise particle species density diagnostics."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

from osiris_toolkit.exceptions import DataNotFoundError
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units.converter import UnitSystem

from .common import get_system, load_sim, save_or_show

logger = logging.getLogger(__name__)


def plot_density(
    species: str,
    iteration: int,
    sim_path: str | Path | None = None,
    quantity: str = "charge",
    *,
    sim: Simulation | None = None,
    system: UnitSystem | None = None,
    x_unit: str = "auto",
    y_unit: str = "auto",
    value_unit: str = "auto",
    time_unit: str = "auto",
    log_scale: bool = False,
    vmin: float | None = None,
    vmax: float | None = None,
    cmap: str = "plasma",
    output: str | Path | None = None,
) -> Path | None:
    """Plot a 2-D particle density distribution at a given iteration.

    Parameters
    ----------
    species : str
        Particle species name (e.g. 'electrons', 'Au').
    iteration : int
        Iteration number to read.
    sim_path : str or Path
        Path to the simulation output directory.
    quantity : str
        Density data type (default ``'charge'``).
    system : UnitSystem or None
        Unit system for physical unit conversion.
    x_unit, y_unit : str
        Spatial axis units.
    value_unit : str
        Unit for the density colour bar.
    time_unit : str
        Unit for the time shown in the title.
    log_scale : bool
        If True, use a logarithmic normalisation.
    vmin, vmax : float or None
        Colour range limits.  If None, auto-determined from the data.
    cmap : str
        Matplotlib colormap name.
    output : Path or None
        File path to save the figure.
    """
    sim_obj = load_sim(sim_path, sim=sim)
    if system is None:
        system = get_system(sim_obj)

    if output is None and sim_obj is not None:
        d = sim_obj.output_dir("density")
        output = d / f"{species}_{iteration:06d}.png"

    grid = sim_obj.get_density(species, quantity, iteration)
    if grid is None:
        raise DataNotFoundError(
            f"Density for {species!r}/{quantity!r} not found"
            f" at iteration {iteration}."
        )

    data = grid.data

    if system is not None:
        extent = [
            system["length"].to(grid.axes[0].min, x_unit),
            system["length"].to(grid.axes[0].max, x_unit),
            system["length"].to(grid.axes[1].min, y_unit),
            system["length"].to(grid.axes[1].max, y_unit),
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

    fig, ax = plt.subplots(figsize=(10, 8))

    if log_scale:
        norm = LogNorm(
            vmin=vmin or max(data[data > 0].min(), 1e-30),
            vmax=vmax or data.max(),
        )
    else:
        norm = None

    if system is not None:
        display_data = system["density"].to(data, value_unit)
    else:
        display_data = data
        value_unit = "norm"

    im = ax.imshow(
        display_data,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        norm=norm,
    )

    cbar = fig.colorbar(im, ax=ax)
    if system is not None:
        cbar.set_label(system["density"].label(value_unit))
    else:
        cbar.set_label(
            f"{grid.label} [{grid.units}]" if grid.units else grid.label
        )

    if system is not None:
        ax.set_xlabel(system.length.label(x_unit))
        if data.ndim >= 2:
            ax.set_ylabel(system.length.label(y_unit))
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

    if system is not None:
        t_disp = system.time.to(grid.time, time_unit)
        ax.set_title(
            f"Density ({species}, {quantity})  |  iteration={iteration}"
            f"  |  t={t_disp:.1f}"
        )
    else:
        ax.set_title(
            f"Density ({species}, {quantity})  |  iteration={iteration}"
            f"  |  t={grid.time:.1f}"
        )

    save_or_show(fig, output)
    return Path(output) if output else None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.info(
            "Usage: python -m osiris_toolkit.vis.density SIM_PATH [ITERATION]"
        )
        sys.exit(1)

    sim_path = sys.argv[1]
    iteration = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    sim = load_sim(sim_path)
    system = get_system(sim)
    species_list = sim.list_species()
    logger.info("Available species: %s", species_list)
    if species_list:
        sp = species_list[0]
        sp_entries = sim._density.get(sp, {})
        iters = sorted(
            {e.iteration for entries in sp_entries.values() for e in entries}
        )
        it = iters[iteration] if iters else 0
        plot_density(
            sp, it, sim_path=sim_path, system=system,
            x_unit="um", y_unit="um", time_unit="ps",
            output=f"density_{sp}.png",
        )
        logger.info("Done -- see density_%s.png", sp)
