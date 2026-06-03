"""Visualise RAW particle diagnostic data — scatter, momentum, phasespace, energy."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osiris_toolkit._models import ParticleData
from osiris_toolkit.exceptions import DataNotFoundError

from .common import save_or_show

logger = logging.getLogger(__name__)


def plot_raw_scatter(
    raw: ParticleData,
    x_axis: str,
    y_axis: str,
    *,
    color_by: str | None = None,
    cmap: str = "viridis",
    alpha: float = 0.5,
    marker_size: float = 2.0,
    output: str | Path | None = None,
) -> Path | None:
    """2-D scatter plot of RAW particle data.

    Parameters
    ----------
    raw : ParticleData
        RAW particle data from ``Simulation.get_raw()``.
    x_axis : str
        Quantity name for the x-axis (e.g. ``'x1'``, ``'p1'``).
    y_axis : str
        Quantity name for the y-axis (e.g. ``'x2'``, ``'p2'``).
    color_by : str or None
        Quantity name to colour points by.  None = single colour.
    cmap : str
        Matplotlib colormap name (used when *color_by* is set).
    alpha : float
        Point transparency.
    marker_size : float
        Scatter marker size.
    output : str, Path, or None
        If provided, save to this path.

    Returns
    -------
    Path or None
    """
    x = raw.data.get(x_axis)
    y = raw.data.get(y_axis)
    if x is None or y is None:
        raise DataNotFoundError(
            f"Quantity '{x_axis}' or '{y_axis}' not in raw data. "
            f"Available: {list(raw.data.keys())}"
        )

    fig, ax = plt.subplots(figsize=(7, 6))

    if color_by and color_by in raw.data:
        c = raw.data[color_by]
        sc = ax.scatter(x, y, c=c, s=marker_size, alpha=alpha, cmap=cmap, linewidths=0)
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label(color_by)
    else:
        ax.scatter(x, y, s=marker_size, alpha=alpha, color="steelblue", linewidths=0)

    ax.set_xlabel(x_axis)
    ax.set_ylabel(y_axis)
    ax.set_title(
        f"RAW {raw.label}  |  iteration={raw.iteration}  |  t={raw.time:.1f}"
        f"  |  N={raw.nparts}"
    )
    ax.set_aspect("auto")

    save_or_show(fig, output)
    return Path(output) if output else None


def plot_raw_momentum(
    raw: ParticleData,
    *,
    bins: int = 80,
    log_scale: bool = False,
    cmap: str = "plasma",
    alpha: float = 0.3,
    output: str | Path | None = None,
) -> Path | None:
    """4-panel momentum distribution: p1-p2 scatter + p1/p2/p3 histograms.

    Parameters
    ----------
    raw : ParticleData
    bins : int
        Number of histogram bins for 1-D distributions.
    log_scale : bool
        If True, use log scale on histogram y-axis.
    cmap : str
        Colormap for the p1-p2 scatter panel.
    alpha : float
        Transparency for the p1-p2 scatter points.
    output : str, Path, or None

    Returns
    -------
    Path or None
    """
    _require_quant(raw, "p1")
    _require_quant(raw, "p2")
    _require_quant(raw, "p3")

    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    ((ax_scatter, ax_hist_p1), (ax_hist_p3, ax_hist_p2)) = axes

    # Top-left: p1-p2 scatter
    ax_scatter.scatter(
        raw.data["p1"], raw.data["p2"],
        s=2, alpha=alpha, c=raw.data.get("ene", "steelblue"),
        cmap=cmap if "ene" in raw.data else None,
        linewidths=0,
    )
    ax_scatter.set_xlabel("p1")
    ax_scatter.set_ylabel("p2")
    ax_scatter.set_title(f"p1-p2 scatter  |  N={raw.nparts}")
    ax_scatter.set_aspect("auto")

    # Top-right / Bottom-right / Bottom-left: 1-D histograms
    hist_configs = [
        (ax_hist_p1, "p1"),
        (ax_hist_p2, "p2"),
        (ax_hist_p3, "p3"),
    ]
    for ax_h, qkey in hist_configs:
        ax_h.hist(raw.data[qkey], bins=bins, color="steelblue", alpha=0.8, edgecolor="none")
        ax_h.set_xlabel(qkey)
        ax_h.set_ylabel("counts")
        if log_scale:
            ax_h.set_yscale("log")

    fig.suptitle(
        f"Momentum distribution — {raw.label}  |  "
        f"iteration={raw.iteration}  |  t={raw.time:.1f}",
        fontsize=13,
    )
    fig.tight_layout()

    save_or_show(fig, output)
    return Path(output) if output else None


def plot_raw_phasespace(
    raw: ParticleData,
    x_axis: str,
    p_axis: str,
    *,
    color_by: str | None = None,
    cmap: str = "viridis",
    alpha: float = 0.5,
    marker_size: float = 2.0,
    output: str | Path | None = None,
) -> Path | None:
    """Phase-space projection from RAW particle data (x vs p scatter).

    Parameters
    ----------
    raw : ParticleData
    x_axis : str
        Position axis, e.g. ``'x1'``.
    p_axis : str
        Momentum axis, e.g. ``'p1'``.
    color_by : str or None
        Quantity to colour by.
    cmap : str
    alpha : float
    marker_size : float
    output : str, Path, or None

    Returns
    -------
    Path or None
    """
    x = raw.data.get(x_axis)
    p = raw.data.get(p_axis)
    if x is None or p is None:
        raise ValueError(
            f"Quantity '{x_axis}' or '{p_axis}' not in raw data. "
            f"Available: {list(raw.data.keys())}"
        )

    fig, ax = plt.subplots(figsize=(8, 6))

    if color_by and color_by in raw.data:
        c = raw.data[color_by]
        sc = ax.scatter(x, p, c=c, s=marker_size, alpha=alpha, cmap=cmap, linewidths=0)
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label(color_by)
    else:
        ax.scatter(x, p, s=marker_size, alpha=alpha, color="steelblue", linewidths=0)

    ax.set_xlabel(x_axis)
    ax.set_ylabel(p_axis)
    ax.set_title(
        f"Phase-space {x_axis}-{p_axis} ({raw.label})  |  "
        f"iteration={raw.iteration}  |  N={raw.nparts}"
    )

    save_or_show(fig, output)
    return Path(output) if output else None


def plot_raw_energy_spectrum(
    raw: ParticleData,
    *,
    bins: int = 100,
    log_x: bool = True,
    log_y: bool = True,
    output: str | Path | None = None,
) -> Path | None:
    """Energy histogram from RAW particle data.

    Parameters
    ----------
    raw : ParticleData
    bins : int
        Number of histogram bins.
    log_x : bool
        If True, use log scale for the energy axis.
    log_y : bool
        If True, use log scale for the count axis.
    output : str, Path, or None

    Returns
    -------
    Path or None
    """
    ene = raw.data.get("ene", raw.data.get("p"))
    if ene is None or len(ene) == 0:
        raise DataNotFoundError("No energy/kinetic energy quantity in raw data")

    ene_abs = np.abs(ene)
    pos = ene_abs[ene_abs > 0]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(pos, bins=bins, color="steelblue", alpha=0.8, edgecolor="none")

    if log_x:
        ax.set_xscale("log")
    if log_y:
        ax.set_yscale("log")

    ax.set_xlabel("Energy (norm)")
    ax.set_ylabel("counts")
    ax.set_title(
        f"Energy spectrum — {raw.label}  |  "
        f"iteration={raw.iteration}  |  N={raw.nparts}"
    )

    save_or_show(fig, output)
    return Path(output) if output else None


def _require_quant(raw: ParticleData, name: str) -> None:
    """Raise ValueError if *name* is not in raw.data."""
    if name not in raw.data:
        raise DataNotFoundError(
            f"Quantity '{name}' not in raw data. Available: {list(raw.data.keys())}"
        )
