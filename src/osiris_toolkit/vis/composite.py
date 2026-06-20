"""Generate a multi-panel composite overview of the simulation state."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osiris_toolkit.sim import Simulation
from osiris_toolkit.units.converter import UnitSystem

from .common import get_system, load_sim, safe_log_norm, save_or_show

logger = logging.getLogger(__name__)


def plot_composite(
    iteration: int,
    sim_path: str | Path | None = None,
    *,
    sim: Simulation | None = None,
    system: UnitSystem | None = None,
    field_quantities: list[str] | None = None,
    species: str | None = None,
    phasespace: str = "p1p2",
    x_unit: str = "auto",
    y_unit: str = "auto",
    p_unit: str = "norm",
    time_unit: str = "auto",
    output: str | Path | None = None,
) -> Path | None:
    """Generate a composite overview figure for a single time step.

    Creates a multi-panel figure showing field components, density, and
    optionally a phase-space histogram.

    Parameters
    ----------
    iteration : int
        Iteration number to plot.
    sim_path : str or Path
        Path to the simulation output directory.
    system : UnitSystem or None
        Unit system for physical unit conversion.
    field_quantities : list of str or None
        Field components to include.  Defaults to ``['e1', 'b3']`` (plus
        ``'e2'`` if available).
    species : str or None
        Particle species for density / phase-space panels.  If None,
        auto-detected from the simulation.
    phasespace : str
        Phase-space name (default ``'p1p2'``).
    x_unit, y_unit : str
        Spatial axis units.
    p_unit : str
        Momentum unit for the phase-space panel.
    time_unit : str
        Unit for the time shown in titles.
    output : Path or None
        File path to save the figure.
    """
    sim_obj = load_sim(sim_path, sim=sim)
    if system is None:
        system = get_system(sim_obj)

    if output is None and sim_obj is not None:
        d = sim_obj.output_dir("composite")
        output = d / f"composite_{iteration:06d}.png"

    if field_quantities is None:
        available = sim_obj.list_fields()
        preferred = ["e1", "b3"]
        field_quantities = [q for q in preferred if q in available]
        if "e2" in available:
            field_quantities.append("e2")

    if species is None:
        sp_list = sim_obj.list_species()
        species = sp_list[0] if sp_list else "electrons"

    n_panels = len(field_quantities) + 1
    has_ps = bool(sim_obj.list_phasespaces())
    if has_ps:
        n_panels += 1

    cols = min(3, n_panels)
    rows = (n_panels + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows))
    axes = np.atleast_1d(axes).flatten()

    panel_idx = 0

    # --- Field panels ---
    for qty in field_quantities:
        ax = axes[panel_idx]
        grid = sim_obj.get_field(qty, iteration)
        if grid is not None:
            data = grid.data
            if system is not None:
                extent = (
                    [
                        system["length"].to(grid.axes[0].min, x_unit),
                        system["length"].to(grid.axes[0].max, x_unit),
                        system["length"].to(grid.axes[1].min, y_unit),
                        system["length"].to(grid.axes[1].max, y_unit),
                    ]
                    if len(grid.axes) >= 2
                    else None
                )
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
                data,
                origin="lower",
                aspect="auto",
                extent=extent,
                cmap="RdBu_r",
            )
            fig.colorbar(im, ax=ax)
            if system is not None:
                t_disp = system.time.to(grid.time, time_unit)
            else:
                t_disp = grid.time
            ax.set_title(f"{qty.upper()}  t={t_disp:.1f}")
            if system is not None:
                ax.set_xlabel(system.length.label(x_unit))
                ax.set_ylabel(system.length.label(y_unit))
            else:
                ax.set_xlabel("x1")
                ax.set_ylabel("x2")
        else:
            ax.set_title(f"{qty.upper()} -- not found")
        panel_idx += 1

    # --- Density panel ---
    ax = axes[panel_idx]
    grid = sim_obj.get_density(species, "charge", iteration)
    if grid is not None:
        data = grid.data
        if system is not None:
            extent = (
                [
                    system["length"].to(grid.axes[0].min, x_unit),
                    system["length"].to(grid.axes[0].max, x_unit),
                    system["length"].to(grid.axes[1].min, y_unit),
                    system["length"].to(grid.axes[1].max, y_unit),
                ]
                if len(grid.axes) >= 2
                else None
            )
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
            data,
            origin="lower",
            aspect="auto",
            extent=extent,
            cmap="plasma",
            norm=safe_log_norm(data),
        )
        fig.colorbar(im, ax=ax)
        if system is not None:
            t_disp = system.time.to(grid.time, time_unit)
        else:
            t_disp = grid.time
        ax.set_title(f"Density ({species})  t={t_disp:.1f}")
        if system is not None:
            ax.set_xlabel(system.length.label(x_unit))
            ax.set_ylabel(system.length.label(y_unit))
        else:
            ax.set_xlabel("x1")
            ax.set_ylabel("x2")
    else:
        ax.set_title("Density -- not found")
    panel_idx += 1

    # --- Phase-space panel ---
    if has_ps:
        ax = axes[panel_idx]
        ps_list = sim_obj.list_phasespaces()
        ps_name = phasespace if any(p[0] == phasespace for p in ps_list) else ps_list[0][0]
        ps_sp = species if any(p[1] == species for p in ps_list) else ps_list[0][1]
        ps = sim_obj.get_phasespace(ps_name, ps_sp, iteration)
        if ps is not None:
            data = ps.data
            if len(ps.axes) >= 2:
                p1_min = float(ps.axes[0].get("min", 0))
                p1_max = float(ps.axes[0].get("max", 1))
                p2_min = float(ps.axes[1].get("min", 0))
                p2_max = float(ps.axes[1].get("max", 1))
                if system is not None:
                    extent = [
                        system["momentum"].to(p1_min, p_unit),
                        system["momentum"].to(p1_max, p_unit),
                        system["momentum"].to(p2_min, p_unit),
                        system["momentum"].to(p2_max, p_unit),
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
                cmap="plasma",
                norm=safe_log_norm(data),
            )
            fig.colorbar(im, ax=ax)
            if system is not None:
                ax.set_xlabel(system["momentum"].label(p_unit))
                ax.set_ylabel(system["momentum"].label(p_unit))
                t_disp = system.time.to(ps.time, time_unit)
            else:
                ax.set_xlabel(f"{ps.axes[0].get('name', 'p1')}" if ps.axes else "p1")
                ax.set_ylabel(f"{ps.axes[1].get('name', 'p2')}" if len(ps.axes) > 1 else "p2")
                t_disp = ps.time
            ax.set_title(f"Phasespace {ps_name} ({ps_sp})  t={t_disp:.1f}")
        else:
            ax.set_title("Phasespace -- not found")
        panel_idx += 1

    for ax in axes[panel_idx:]:
        ax.set_visible(False)

    fig.suptitle(f"Simulation overview -- iteration {iteration}", fontsize=16, y=1.01)
    fig.tight_layout()
    save_or_show(fig, output)
    return Path(output) if output else None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.info("Usage: python -m osiris_toolkit.vis.composite SIM_PATH [ITERATION]")
        sys.exit(1)

    sim_path = sys.argv[1]
    iteration = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    sim = load_sim(sim_path)
    system = get_system(sim)
    iters = sim.list_iterations("e1")
    if iters:
        it = iters[iteration] if iteration < len(iters) else iters[-1]
        plot_composite(
            it,
            sim_path=sim_path,
            system=system,
            x_unit="um",
            y_unit="um",
            time_unit="ps",
            output="composite.png",
        )
        logger.info("Done -- see composite.png")
    else:
        logger.info("No data found.")
