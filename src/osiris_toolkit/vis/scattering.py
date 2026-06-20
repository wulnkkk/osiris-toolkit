"""k-space scattering energy fraction analysis.

Converted from the MATLAB script ``rushetoushefene.m``.  Integrates
|FFT(E)|^2 over regions of k-space to compute incident, scattered,
side-scattered, and back-scattered energy fractions as functions of time.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osiris_toolkit.analysis._result_types import ScatteringResult  # re-export
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units.converter import UnitSystem

from .common import save_or_show

logger = logging.getLogger(__name__)

# ScatteringResult is re-exported from osiris_toolkit.analysis._result_types
# _mask_energy is re-exported from osiris_toolkit.compute.integrate


def plot_scattering_fraction(
    result: ScatteringResult,
    system: UnitSystem | None = None,
    time_unit: str = "auto",
    output: str | Path | None = None,
    *,
    sim: Simulation | None = None,
) -> Path | None:
    """Plot scattering energy fractions as a function of time.

    Parameters
    ----------
    result : ScatteringResult
        Results from ``analyze_scattering``.
    system : UnitSystem or None
        Unit system for the time axis.
    time_unit : str
        Time unit for the plot.
    output : Path or None
        File path to save the figure.  If None and *sim* is provided,
        auto-generated under ``sim.output_root/scattering/``.
    sim : Simulation or None
        Simulation object for auto-output path derivation.

    Returns
    -------
    Path or None
        The output file path if saved, None if shown interactively.
    """
    if output is None and sim is not None:
        d = sim.output_dir("scattering")
        output = d / f"scattering_{result.quantity}.png"

    if system is not None:
        t = system.time.to(np.array(result.times), time_unit)
        t_label = system.time.label(time_unit)
    else:
        t = np.array(result.times)
        t_label = "t [1/omega_p]"

    fig, axes = plt.subplots(1, 3, figsize=(21, 6))

    def _style(ax, ylabel, title):
        ax.set_xlabel(t_label, fontsize=14)
        ax.set_ylabel(ylabel, fontsize=14)
        ax.set_title(title, fontsize=14)
        ax.grid(True, alpha=0.3)

    ax = axes[0]
    ax.plot(t, result.scattered_fraction, "o-", markersize=4)
    _style(ax, "Scattered / Incident", "Scattered fraction")

    ax = axes[1]
    ax.plot(t, result.side_scatter_fraction, "o-", markersize=4)
    _style(ax, "Side scattered / Incident", "Side-scatter fraction")

    ax = axes[2]
    ax.plot(t, result.back_scatter_fraction, "o-", markersize=4)
    _style(ax, "Back scattered / Incident", "Back-scatter fraction")

    fig.suptitle(
        f"Scattering analysis -- {result.quantity.upper()}",
        fontsize=16,
        y=1.02,
    )
    fig.tight_layout()
    save_or_show(fig, output)
    return Path(output) if output else None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.info("Usage: python -m osiris_toolkit.vis.scattering SIM_PATH [QUANTITY]")
        sys.exit(1)

    sim_path = sys.argv[1]
    quantity = sys.argv[2] if len(sys.argv) > 2 else "e3"

    from osiris_toolkit.analysis.scattering import ScatteringAnalyzer
    from osiris_toolkit.units.converter import UnitSystem
    from osiris_toolkit.units.params import SimulationParams

    sim = Simulation(str(sim_path))

    system = None
    try:
        params = SimulationParams.from_sim_path(sim_path)
        if params.omega_p0 > 0:
            system = UnitSystem.from_params(params)
    except Exception:
        pass

    logger.info("Analysing %s (%s)...", quantity, sim_path)

    all_iters = sim.list_iterations(quantity)
    logger.info("  %s iterations total", len(all_iters))

    analyzer = ScatteringAnalyzer(sim)
    result = analyzer.analyze(quantity=quantity, verbose=True)
    plot_scattering_fraction(
        result,
        system=system,
        time_unit="ps",
        output=f"scattering_{quantity}.png",
    )
    logger.info("Done -- see scattering_%s.png", quantity)
