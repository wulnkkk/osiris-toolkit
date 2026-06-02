"""Energy summary visualization — timeseries, spectrum colormap, Poynting vectors."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osiris_toolkit.analysis._result_types import (
    EMSpectrumResult,
    FieldEnergyResult,
    PoyntingResult,
)
from osiris_toolkit.vis.common import save_or_show


def plot_energy_timeseries(
    results: list[FieldEnergyResult],
    converter=None,
    time_unit: str = "auto",
    label: str | None = None,
    output: Path | None = None,
    overwrite: bool = False,
) -> Path | None:
    """Plot field energy vs time from a list of FieldEnergyResult.

    Parameters
    ----------
    results : list[FieldEnergyResult]
        Output from analysis.emf.field_energy_all().
    converter : UnitConverter or None
    time_unit : str
        Time unit for x-axis.
    label : str or None
        Legend label.
    output : Path or None
    overwrite : bool

    Returns
    -------
    Path or None
    """
    times = []
    energies = []
    for r in results:
        t = r.time
        if converter is not None:
            t = converter.convert(t, "time", time_unit)
        times.append(t)
        energies.append(r.total_energy)

    quantity = results[0].quantity if results else "?"
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(times, energies, linewidth=2, label=label or quantity)
    ax.set_xlabel(f"Time [{time_unit}]" if converter else "Time (norm)")
    ax.set_ylabel("Total Energy (norm)")
    ax.set_title(f"Field Energy — {quantity}")
    ax.grid(True, alpha=0.3)
    if label or quantity:
        ax.legend()
    fig.tight_layout()
    save_or_show(fig, output, overwrite=overwrite)
    return Path(output) if output else None


def plot_spectrum_colormap(
    result: EMSpectrumResult,
    log_scale: bool = True,
    cmap: str = "inferno",
    output: Path | None = None,
    overwrite: bool = False,
) -> Path | None:
    """Plot FFT k-space spectrum as a 2-D colormap.

    Parameters
    ----------
    result : EMSpectrumResult
    log_scale : bool
        If True, plot log10 of the spectrum.
    cmap : str
    output : Path or None
    overwrite : bool

    Returns
    -------
    Path or None
    """
    spectrum = result.spectrum
    if log_scale:
        spectrum = np.log10(np.maximum(spectrum, 1e-30))

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(
        spectrum,
        origin="lower",
        aspect="auto",
        extent=[
            result.kx_k0.min(),
            result.kx_k0.max(),
            result.ky_k0.min(),
            result.ky_k0.max(),
        ],
        cmap=cmap,
    )
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("log10|FFT|" if log_scale else "|FFT|")
    ax.set_xlabel("kx / k0")
    ax.set_ylabel("ky / k0")
    ax.set_title(
        f"k-space Spectrum — {result.quantity.upper()}  |  "
        f"iteration={result.iteration}  |  t={result.time:.1f}"
    )
    fig.tight_layout()
    save_or_show(fig, output, overwrite=overwrite)
    return Path(output) if output else None


def plot_poynting_vector(
    result: PoyntingResult,
    component: str = "s1",
    cmap: str = "RdBu_r",
    output: Path | None = None,
    overwrite: bool = False,
) -> Path | None:
    """Plot a single Poynting vector component.

    Parameters
    ----------
    result : PoyntingResult
    component : str
        's1', 's2', or 's3'.
    cmap : str
    output : Path or None
    overwrite : bool

    Returns
    -------
    Path or None
    """
    data = {"s1": result.s1, "s2": result.s2, "s3": result.s3}[component]

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(data, origin="lower", aspect="auto", cmap=cmap)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Poynting flux (norm)")
    ax.set_title(
        f"Poynting {component.upper()}  |  iteration={result.iteration}"
    )
    fig.tight_layout()
    save_or_show(fig, output, overwrite=overwrite)
    return Path(output) if output else None


__all__ = ["plot_energy_timeseries", "plot_spectrum_colormap", "plot_poynting_vector"]
