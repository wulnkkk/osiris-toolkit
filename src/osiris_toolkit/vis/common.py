"""Shared utility functions for OSIRIS visualization scripts."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter


def load_sim(path: str | Path) -> Simulation:
    """Load a simulation from the given directory path.

    Parameters
    ----------
    path : str or Path
        Path to the OSIRIS simulation output directory.

    Returns
    -------
    Simulation
        The loaded simulation object.

    Raises
    ------
    ValueError
        If *path* is None or an empty string.
    """
    if path is None:
        raise ValueError("A simulation path is required.")
    if isinstance(path, str) and path.strip() == "":
        raise ValueError("A simulation path is required.")
    return Simulation(path)


def get_converter(sim: Simulation) -> UnitConverter | None:
    """Get a UnitConverter for the given simulation.

    Tries to use ``sim.converter`` if available (set by attaching a
    converter instance to the Simulation after construction).  Otherwise
    returns None, which callers should handle by falling back to
    normalised units.

    Parameters
    ----------
    sim : Simulation
        The simulation object.

    Returns
    -------
    UnitConverter or None
        A converter instance, or None if no converter is available.
    """
    if hasattr(sim, "converter") and sim.converter is not None:
        return sim.converter
    return None


def safe_log_norm(
    data: np.ndarray,
    vmin: float | None = None,
    vmax: float | None = None,
) -> LogNorm:
    """Create a safe logarithmic normalisation that handles non-positive data.

    Parameters
    ----------
    data : np.ndarray
        The data array to normalise.
    vmin : float or None
        Minimum value for the colour range.  If None, auto-detected from
        the smallest positive value in *data*.
    vmax : float or None
        Maximum value for the colour range.  If None, auto-detected from
        the global maximum in *data*.

    Returns
    -------
    LogNorm
        A matplotlib ``LogNorm`` instance with safe limits.
    """
    positive = data[data > 0]
    if positive.size > 0:
        floor = positive.min()
        ceiling = data.max()
    else:
        floor = 1e-30
        ceiling = 1.0
    _vmin = vmin if vmin is not None else floor
    _vmax = vmax if vmax is not None else ceiling
    if _vmin <= 0:
        _vmin = 1e-30
    if _vmax <= _vmin:
        _vmax = _vmin * 10
    return LogNorm(vmin=_vmin, vmax=_vmax)


def save_or_show(fig: plt.Figure, filepath: str | Path | None = None) -> None:
    """Save the figure to file or display it interactively.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to save or show.
    filepath : str, Path, or None
        If provided, save the figure to this path (DPI 150, tight bbox).
        If None, display the figure with ``plt.show()``.
    """
    if filepath:
        fig.savefig(filepath, dpi=150, bbox_inches="tight")
        print(f"Saved to {filepath}")
    else:
        plt.show()
    plt.close(fig)
