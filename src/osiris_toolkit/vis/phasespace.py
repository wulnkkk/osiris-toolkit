"""Visualise phase-space diagnostic data (e.g. p1-p2, x1-p1)."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt

from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter

from .common import get_converter, load_sim, safe_log_norm, save_or_show

logger = logging.getLogger(__name__)


def plot_phasespace(
    ps_name: str,
    species: str,
    iteration: int,
    sim_path: str | Path | None = None,
    *,
    sim: Simulation | None = None,
    converter: UnitConverter | None = None,
    p_unit: str = "norm",
    time_unit: str = "auto",
    log_scale: bool = True,
    vmin: float | None = None,
    vmax: float | None = None,
    cmap: str = "plasma",
    output: str | Path | None = None,
) -> Path | None:
    """Plot a 2-D phase-space histogram at a given iteration.

    Parameters
    ----------
    ps_name : str
        Phase-space name (e.g. ``'p1p2'``, ``'x1p1'``).
    species : str
        Particle species name.
    iteration : int
        Iteration number to read.
    sim_path : str or Path
        Path to the simulation output directory.
    converter : UnitConverter or None
        Unit converter for physical units.
    p_unit : str
        Momentum unit: ``'norm'``, ``'MeV/c'``, ``'kg*m/s'``.
    time_unit : str
        Unit for the time shown in the title.
    log_scale : bool
        If True, use a logarithmic normalisation (recommended).
    vmin, vmax : float or None
        Colour range limits.
    cmap : str
        Matplotlib colormap name.
    output : Path or None
        File path to save the figure.
    """
    sim_obj = load_sim(sim_path, sim=sim)
    if converter is None:
        converter = get_converter(sim_obj)

    if output is None and sim_obj is not None:
        d = sim_obj.output_dir("phasespace")
        output = d / f"{ps_name}_{species}_{iteration:06d}.png"

    ps = sim_obj.get_phasespace(ps_name, species, iteration)
    if ps is None:
        raise ValueError(
            f"Phasespace {ps_name!r}/{species!r} not found"
            f" at iteration {iteration}. "
            f"Available: {sim.list_phasespaces()}"
        )

    data = ps.data
    if data.ndim < 2:
        raise ValueError(
            f"Expected 2-D phase-space data, got shape {data.shape}"
        )

    fig, ax = plt.subplots(figsize=(8, 8))

    norm = safe_log_norm(data, vmin, vmax) if log_scale else None

    if len(ps.axes) >= 2:
        p1_min = float(ps.axes[0].get("min", 0))
        p1_max = float(ps.axes[0].get("max", 1))
        p2_min = float(ps.axes[1].get("min", 0))
        p2_max = float(ps.axes[1].get("max", 1))
        if converter is not None:
            extent = [
                converter.convert(p1_min, "momentum", p_unit),
                converter.convert(p1_max, "momentum", p_unit),
                converter.convert(p2_min, "momentum", p_unit),
                converter.convert(p2_max, "momentum", p_unit),
            ]
        else:
            extent = [p1_min, p1_max, p2_min, p2_max]
    else:
        extent = None

    im = ax.imshow(
        data,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        norm=norm,
    )

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(ps.deposited_quantity or "counts")

    if converter is not None:
        ax.set_xlabel(converter.get_label("momentum", p_unit))
        if len(ps.axes) >= 2:
            ax.set_ylabel(converter.get_label("momentum", p_unit))
    else:
        ax.set_xlabel(
            f"{ps.axes[0].get('name', 'axis0')}"
            f" [{ps.axes[0].get('units', '')}]"
        )
        if len(ps.axes) >= 2:
            ax.set_ylabel(
                f"{ps.axes[1].get('name', 'axis1')}"
                f" [{ps.axes[1].get('units', '')}]"
            )

    if converter is not None:
        t_disp = converter.convert(ps.time, "time", time_unit)
        ax.set_title(
            f"Phasespace {ps_name} ({species})  |  iteration={iteration}"
            f"  |  t={t_disp:.1f}"
        )
    else:
        ax.set_title(
            f"Phasespace {ps_name} ({species})  |  iteration={iteration}"
            f"  |  t={ps.time:.1f}"
        )

    save_or_show(fig, output)
    return Path(output) if output else None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.info(
            "Usage: python -m osiris_toolkit.vis.phasespace SIM_PATH [ITERATION]"
        )
        sys.exit(1)

    sim_path = sys.argv[1]
    iteration = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    sim = load_sim(sim_path)
    converter = get_converter(sim)
    ps_list = sim.list_phasespaces()
    if ps_list:
        ps_name, sp = ps_list[0]
        entries = sim._phasespace.get(ps_name, {}).get(sp, [])
        iters = sorted({e.iteration for e in entries})
        it = iters[iteration] if iters else 0
        plot_phasespace(
            ps_name, sp, it, sim_path=sim_path, converter=converter,
            p_unit="MeV/c", time_unit="ps",
            output=f"phasespace_{ps_name}_{sp}.png",
        )
        logger.info("Done -- see phasespace_%s_%s.png", ps_name, sp)
