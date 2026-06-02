"""Energy and spectrum visualization for EMF analysis results."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osiris_toolkit.analysis._result_types import (
    EMDynamicsResult,
    EMSpectrumResult,
    PoyntingResult,
)
from osiris_toolkit.units import UnitConverter
from osiris_toolkit.vis.common import save_or_show


def plot_energy_timeline(
    results: list[EMDynamicsResult],
    converter: UnitConverter | None = None,
    time_unit: str = "auto",
    output: str | Path | None = None,
) -> Path | None:
    """Plot E^2, B^2, and total EM energy over time.

    Parameters
    ----------
    results : list of EMDynamicsResult
        One result per iteration.
    converter : UnitConverter or None
    time_unit : str
    output : Path or None

    Returns
    -------
    Path or None
    """
    iterations = [r.iteration for r in results]
    e2 = [r.e2_total for r in results]
    b2 = [r.b2_total for r in results]
    total = [r.total for r in results]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(iterations, e2, label=r"$\int E^2$", linewidth=2)
    ax.plot(iterations, b2, label=r"$\int B^2$", linewidth=2)
    ax.plot(iterations, total, label=r"$\int (E^2+B^2)$", linewidth=2, color="black")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Energy (norm. units)")
    ax.set_title("Electromagnetic Energy Dynamics")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save_or_show(fig, output)
    return Path(output) if output else None


def plot_spectrum(
    result: EMSpectrumResult,
    log_scale: bool = True,
    cmap: str = "jet",
    output: str | Path | None = None,
) -> Path | None:
    """Plot a 2-D k-space spectrum.

    Parameters
    ----------
    result : EMSpectrumResult
    log_scale : bool
        If True, take natural log of the amplitude.
    cmap : str
    output : Path or None
    """
    spectrum = result.spectrum
    if log_scale:
        spectrum = np.log(np.maximum(spectrum, 1e-30))

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(
        spectrum,
        origin="lower",
        aspect="auto",
        extent=[
            result.kx_k0.min() / (2 * np.pi),
            result.kx_k0.max() / (2 * np.pi),
            result.ky_k0.min() / (2 * np.pi),
            result.ky_k0.max() / (2 * np.pi),
        ],
        cmap=cmap,
    )
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("ln|FFT|" if log_scale else "|FFT|")
    ax.set_xlabel(r"$k_x\ [k_0]$")
    ax.set_ylabel(r"$k_y\ [k_0]$")
    ax.set_title(
        f"{result.quantity.upper()} k-space  |  iteration={result.iteration}"
        f"  |  t={result.time:.1f}"
    )
    fig.tight_layout()
    save_or_show(fig, output)
    return Path(output) if output else None


def plot_poynting(
    result: PoyntingResult,
    component: str = "s1",
    cmap: str = "RdBu_r",
    output: str | Path | None = None,
) -> Path | None:
    """Plot one component of the Poynting vector.

    Parameters
    ----------
    result : PoyntingResult
    component : str
        One of 's1', 's2', 's3'.
    cmap : str
    output : Path or None
    """
    data = {"s1": result.s1, "s2": result.s2, "s3": result.s3}[component]

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(data, origin="lower", aspect="auto", cmap=cmap)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Poynting flux (norm.)")
    ax.set_title(f"Poynting {component.upper()}  |  iteration={result.iteration}")
    fig.tight_layout()
    save_or_show(fig, output)
    return Path(output) if output else None
