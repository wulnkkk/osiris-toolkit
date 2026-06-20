"""Shared utility functions for OSIRIS visualization scripts."""

import logging
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

from osiris_toolkit.exceptions import ConfigurationError
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter

logger = logging.getLogger(__name__)


def load_sim(
    path: str | Path | None = None,
    *,
    sim: Simulation | None = None,
) -> Simulation:
    """Load or reuse a Simulation object.

    Parameters
    ----------
    path : str or Path
        Path to the OSIRIS simulation output directory.
    sim : Simulation or None
        Pre-constructed Simulation to reuse.  Takes priority over *path*.

    Returns
    -------
    Simulation
        The loaded or reused simulation object.

    Raises
    ------
    ValueError
        If neither *sim* nor a valid *path* is provided.
    """
    if sim is not None:
        return sim
    if path is None:
        raise ConfigurationError("Either sim or a valid path is required.")
    if isinstance(path, str) and path.strip() == "":
        raise ConfigurationError("A simulation path is required.")
    return Simulation(path)


def get_system(sim):
    """Get or build a UnitSystem for the simulation.

    Tries ``sim.system`` first, then parses the input deck.
    Returns None if no deck is available.
    """
    from osiris_toolkit.units.converter import UnitSystem
    from osiris_toolkit.units.params import SimulationParams

    if hasattr(sim, "system") and sim.system is not None:
        return sim.system
    try:
        params = SimulationParams.from_sim_path(sim.path)
        return UnitSystem.from_params(params)
    except Exception:
        return None


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
    warnings.warn(
        "get_converter() is deprecated. Use get_system() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
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


def save_or_show(
    fig: plt.Figure,
    filepath: str | Path | None = None,
    overwrite: bool | None = None,
) -> None:
    """Save the figure to file or display it interactively.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to save or show.
    filepath : str, Path, or None
        If provided, save the figure to this path (DPI 150, tight bbox).
        Parent directories are created automatically.
        If None, display the figure with ``plt.show()``.
    overwrite : bool
        If False (default), raise FileExistsError when *filepath*
        already exists.  Set to True to silently overwrite.
    """
    if filepath:
        if overwrite is None:
            from osiris_toolkit.config import OsirisConfig

            overwrite = OsirisConfig.get().overwrite
        p = Path(filepath)
        if p.exists() and not overwrite:
            raise FileExistsError(f"Output file {p} already exists. Use overwrite=True to replace.")
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(p), dpi=150, bbox_inches="tight")
        logger.info("Saved to %s", p)
    else:
        plt.show()
    plt.close(fig)
