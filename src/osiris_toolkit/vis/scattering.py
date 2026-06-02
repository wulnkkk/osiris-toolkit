"""k-space scattering energy fraction analysis.

Converted from the MATLAB script ``rushetoushefene.m``.  Integrates
|FFT(E)|^2 over regions of k-space to compute incident, scattered,
side-scattered, and back-scattered energy fractions as functions of time.
"""

import logging
import warnings
from pathlib import Path

logger = logging.getLogger(__name__)

import matplotlib.pyplot as plt
import numpy as np

from osiris_toolkit.analysis._result_types import ScatteringResult  # re-export
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter

from .common import get_converter, load_sim, save_or_show

DEFAULT_MASKS = {
    "incident": {
        "kx_range": (-1.1, 1.1),
        "ky_range": (-1.0, 1.0),
        "label": "Incident",
    },
    "scattered": {
        "kx_range": (-0.61, 0.61),
        "ky_range": (-0.65, 0.65),
        "label": "Scattered",
    },
    "side_scatter_1": {
        "kx_range": (-0.11, 0.11),
        "ky_range": (-0.65, -0.42),
        "label": "Side-1",
    },
    "side_scatter_2": {
        "kx_range": (-0.11, 0.11),
        "ky_range": (0.42, 0.65),
        "label": "Side-2",
    },
    "back_scatter_1": {
        "kx_range": (0.47, 0.61),
        "ky_range": (-0.11, 0.11),
        "label": "Back-1",
    },
    "back_scatter_2": {
        "kx_range": (-0.61, -0.47),
        "ky_range": (-0.11, 0.11),
        "label": "Back-2",
    },
}


# ScatteringResult is re-exported from osiris_toolkit.analysis._result_types
# _mask_energy is re-exported from osiris_toolkit.compute.integrate


def analyze_scattering(
    quantity: str,
    sim_path: str | Path | None = None,
    *,
    sim: Simulation | None = None,
    iterations: list[int] | None = None,
    masks: dict | None = None,
    omega0_norm: float = 1.0,
    verbose: bool = True,
) -> ScatteringResult:
    """Analyse k-space scattering energy fractions over time.

    .. deprecated::
        Use ``ScatteringAnalyzer`` from ``osiris_toolkit.analysis.scattering``
        instead. This function is kept for backward compatibility.

    Parameters
    ----------
    quantity : str
        Field component to analyse (e.g. ``'e3'``).
    sim_path : str or Path
        Path to the simulation output directory.
    iterations : list of int or None
        Iteration numbers to process.
    masks : dict or None
        Custom k-space mask definitions.
    omega0_norm : float
        Laser frequency in normalised units.
    verbose : bool
        If True, print per-iteration results.

    Returns
    -------
    ScatteringResult
        Time series of energy fractions.
    """
    warnings.warn(
        "vis.scattering.analyze_scattering is deprecated. "
        "Use osiris_toolkit.analysis.scattering.ScatteringAnalyzer instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from osiris_toolkit.analysis.scattering import ScatteringAnalyzer

    sim_obj = load_sim(sim_path, sim=sim)
    analyzer = ScatteringAnalyzer(sim_obj)
    return analyzer.analyze(
        quantity=quantity,
        iterations=iterations,
        masks=masks,
        omega0_norm=omega0_norm,
        verbose=verbose,
    )


def plot_scattering_fraction(
    result: ScatteringResult,
    converter: UnitConverter | None = None,
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
    converter : UnitConverter or None
        Unit converter for the time axis.
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

    if converter is not None:
        t = converter.convert(np.array(result.times), "time", time_unit)
        t_label = converter.get_label("time", time_unit)
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
        logger.info(
            "Usage: python -m osiris_toolkit.vis.scattering SIM_PATH [QUANTITY]"
        )
        sys.exit(1)

    sim_path = sys.argv[1]
    quantity = sys.argv[2] if len(sys.argv) > 2 else "e3"

    sim = load_sim(sim_path)
    converter = get_converter(sim)

    logger.info("Analysing %s (%s)...", quantity, sim_path)

    all_iters = sim.list_iterations(quantity)
    logger.info("  %s iterations total", len(all_iters))

    result = analyze_scattering(quantity, sim_path=sim_path, verbose=True)
    plot_scattering_fraction(
        result, converter=converter, time_unit="ps",
        output=f"scattering_{quantity}.png",
    )
    logger.info("Done -- see scattering_%s.png", quantity)
