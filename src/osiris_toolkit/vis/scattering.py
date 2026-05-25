"""k-space scattering energy fraction analysis.

Converted from the MATLAB script ``rushetoushefene.m``.  Integrates
|FFT(E)|^2 over regions of k-space to compute incident, scattered,
side-scattered, and back-scattered energy fractions as functions of time.
"""

from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter

from .common import get_converter, load_sim, save_or_show
from .kspace import compute_k_space

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


@dataclass
class ScatteringResult:
    """Container for scattering analysis results.

    Attributes
    ----------
    iterations : list of int
        Iteration numbers analysed.
    times : list of float
        Simulation times (normalised).
    scattered_fraction : list of float
        Scattered energy / incident energy at each step.
    side_scatter_fraction : list of float
        Side-scattered energy / incident energy at each step.
    back_scatter_fraction : list of float
        Back-scattered energy / incident energy at each step.
    quantity : str
        Field quantity analysed.
    mask_info : dict
        Copy of the k-space mask definitions used.
    """

    iterations: list[int] = field(default_factory=list)
    times: list[float] = field(default_factory=list)
    scattered_fraction: list[float] = field(default_factory=list)
    side_scatter_fraction: list[float] = field(default_factory=list)
    back_scatter_fraction: list[float] = field(default_factory=list)
    quantity: str = ""
    mask_info: dict = field(default_factory=dict)


def _mask_energy(
    spectrum: np.ndarray,
    kx_k0: np.ndarray,
    ky_k0: np.ndarray,
    kx_range: tuple[float, float],
    ky_range: tuple[float, float],
) -> float:
    """Integrate |spectrum|^2 over a rectangular k-space mask.

    Parameters
    ----------
    spectrum : 2-D array
        FFT amplitude from ``compute_k_space``.
    kx_k0, ky_k0 : 1-D arrays
        k/k0 coordinate arrays.
    kx_range, ky_range : (float, float)
        Mask boundaries in k/k0 units.

    Returns
    -------
    float
        Sum of |spectrum|^2 within the mask region.
    """
    kx_mask = (kx_k0 / (2 * np.pi) >= kx_range[0]) & (
        kx_k0 / (2 * np.pi) <= kx_range[1]
    )
    ky_mask = (ky_k0 / (2 * np.pi) >= ky_range[0]) & (
        ky_k0 / (2 * np.pi) <= ky_range[1]
    )
    region = spectrum[np.ix_(kx_mask, ky_mask)]
    return float(np.sum(region**2))


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

    Parameters
    ----------
    quantity : str
        Field component to analyse (e.g. ``'e3'``).
    sim_path : str or Path
        Path to the simulation output directory.
    iterations : list of int or None
        Iteration numbers to process.  If None, all available iterations
        for *quantity* are used.
    masks : dict or None
        Custom k-space mask definitions.  If None, ``DEFAULT_MASKS`` is
        used.
    omega0_norm : float
        Laser frequency in normalised units.
    verbose : bool
        If True, print per-iteration results.

    Returns
    -------
    ScatteringResult
        Time series of energy fractions.
    """
    sim_obj = load_sim(sim_path, sim=sim)
    if masks is None:
        masks = DEFAULT_MASKS

    if iterations is None:
        entries = sim_obj._fields.get(quantity, [])
        iterations = sorted({e.iteration for e in entries})

    if not iterations:
        raise ValueError(f"No data found for quantity {quantity!r}")

    result = ScatteringResult(quantity=quantity, mask_info=dict(masks))

    for it in iterations:
        grid = sim_obj.get_field(quantity, it)
        if grid is None:
            continue

        kx_k0, ky_k0, spectrum = compute_k_space(grid, omega0_norm)

        inc = _mask_energy(
            spectrum,
            kx_k0,
            ky_k0,
            masks["incident"]["kx_range"],
            masks["incident"]["ky_range"],
        )

        sct = _mask_energy(
            spectrum,
            kx_k0,
            ky_k0,
            masks["scattered"]["kx_range"],
            masks["scattered"]["ky_range"],
        )

        side1 = _mask_energy(
            spectrum,
            kx_k0,
            ky_k0,
            masks["side_scatter_1"]["kx_range"],
            masks["side_scatter_1"]["ky_range"],
        )
        side2 = _mask_energy(
            spectrum,
            kx_k0,
            ky_k0,
            masks["side_scatter_2"]["kx_range"],
            masks["side_scatter_2"]["ky_range"],
        )

        back1 = _mask_energy(
            spectrum,
            kx_k0,
            ky_k0,
            masks["back_scatter_1"]["kx_range"],
            masks["back_scatter_1"]["ky_range"],
        )
        back2 = _mask_energy(
            spectrum,
            kx_k0,
            ky_k0,
            masks["back_scatter_2"]["kx_range"],
            masks["back_scatter_2"]["ky_range"],
        )

        result.iterations.append(it)
        result.times.append(grid.time)
        result.scattered_fraction.append(
            sct / inc if inc > 0 else 0.0
        )
        result.side_scatter_fraction.append(
            (side1 + side2) / inc if inc > 0 else 0.0
        )
        result.back_scatter_fraction.append(
            (back1 + back2) / inc if inc > 0 else 0.0
        )

        if verbose:
            print(
                f"  iteration={it:06d}  t={grid.time:.1f}  "
                f"scat={result.scattered_fraction[-1]:.4f}  "
                f"side={result.side_scatter_fraction[-1]:.4f}  "
                f"back={result.back_scatter_fraction[-1]:.4f}"
            )

    return result


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
        print(
            "Usage: python -m osiris_toolkit.vis.scattering SIM_PATH [QUANTITY]"
        )
        sys.exit(1)

    sim_path = sys.argv[1]
    quantity = sys.argv[2] if len(sys.argv) > 2 else "e3"

    sim = load_sim(sim_path)
    converter = get_converter(sim)

    print(f"Analysing {quantity} ({sim_path})...")

    all_iters = sim.list_iterations(quantity)
    print(f"  {len(all_iters)} iterations total")

    result = analyze_scattering(quantity, sim_path=sim_path, verbose=True)
    plot_scattering_fraction(
        result, converter=converter, time_unit="ps",
        output=f"scattering_{quantity}.png",
    )
    print(f"Done -- see scattering_{quantity}.png")
