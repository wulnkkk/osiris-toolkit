"""Visualise TRACKS particle trajectory data — orbit, energy, field along track."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osiris_toolkit._models import TrackData
from osiris_toolkit.exceptions import DataNotFoundError, ValidationError

from .common import save_or_show

logger = logging.getLogger(__name__)


def _find_col(quants: list[str], target: str) -> int:
    """Case-insensitive column index lookup."""
    t = target.lower()
    for i, q in enumerate(quants):
        if q.lower() == t:
            return i
    raise DataNotFoundError(
        f"Quantity '{target}' not found in track quants: {quants}"
    )


_VALID_PROJ = {"x1-x2", "x1-x3", "x2-x3"}


def _resolve_proj(proj: str) -> tuple[str, str]:
    """Parse 'x1-x2' style projection into two column names."""
    if proj not in _VALID_PROJ:
        raise ValidationError(
            f"Invalid projection '{proj}'. Expected one of: {sorted(_VALID_PROJ)}."
        )
    parts = proj.split("-")
    return parts[0], parts[1]


def plot_tracks_orbit(
    td: TrackData,
    proj: str = "x1-x2",
    *,
    highlight_tracks: list[int] | None = None,
    output: str | Path | None = None,
) -> Path | None:
    """Orbit plot — 2-D position projection of particle tracks.

    Parameters
    ----------
    td : TrackData
    proj : str
        Projection plane: ``'x1-x2'``, ``'x1-x3'``, or ``'x2-x3'``.
    highlight_tracks : list of int or None
        Indices of tracks to draw in thick lines.  Other tracks are drawn
        in thin grey lines.  If None, all tracks get the same thickness.
    output : str, Path, or None

    Returns
    -------
    Path or None
    """
    qx, qy = _resolve_proj(proj)
    ix = _find_col(td.quants, qx)
    iy = _find_col(td.quants, qy)

    fig, ax = plt.subplots(figsize=(7, 7))

    n_tracks = len(td.tracks)
    highlight = set(highlight_tracks or [])

    for i, track in enumerate(td.tracks):
        if i in highlight:
            ax.plot(track[:, ix], track[:, iy], linewidth=1.5, alpha=0.9,
                    label=f"track {i}")
        else:
            ax.plot(track[:, ix], track[:, iy], linewidth=0.5,
                    alpha=0.4, color="grey")

    ax.set_xlabel(qx)
    ax.set_ylabel(qy)
    ax.set_title(f"Orbit {proj}  |  {n_tracks} tracks  |  {td.niter} points")
    ax.set_aspect("auto")
    if highlight:
        ax.legend(fontsize=8)

    save_or_show(fig, output)
    return Path(output) if output else None


def plot_tracks_energy(
    td: TrackData,
    *,
    per_track: bool = True,
    output: str | Path | None = None,
) -> Path | None:
    """Energy evolution along particle tracks.

    Parameters
    ----------
    td : TrackData
    per_track : bool
        If True, draw one curve per track.  If False, draw mean ± 1 std.
    output : str, Path, or None

    Returns
    -------
    Path or None
    """
    itime = _find_col(td.quants, "time")
    iene = _find_col(td.quants, "ene")

    fig, ax = plt.subplots(figsize=(8, 5))

    if per_track:
        for i, track in enumerate(td.tracks):
            ax.plot(track[:, itime], track[:, iene],
                    linewidth=0.8, alpha=0.7, label=f"track {i}")
        if len(td.tracks) <= 10:
            ax.legend(fontsize=7)
    else:
        # Align to common time grid via interpolation
        all_t = np.concatenate([t[:, itime] for t in td.tracks])
        t_min, t_max = float(all_t.min()), float(all_t.max())
        t_grid = np.linspace(t_min, t_max, 500)
        interp_vals = []
        for track in td.tracks:
            t = track[:, itime]
            e = track[:, iene]
            if len(t) >= 2:
                interp_vals.append(np.interp(t_grid, t, e))
        if interp_vals:
            stacked = np.array(interp_vals)
            mean = np.mean(stacked, axis=0)
            std = np.std(stacked, axis=0)
            ax.plot(t_grid, mean, color="steelblue", linewidth=2, label="mean")
            ax.fill_between(t_grid, mean - std, mean + std,
                            color="steelblue", alpha=0.2, label="±1 std")
            ax.legend()

    ax.set_xlabel("Time (norm)")
    ax.set_ylabel("Energy (norm)")
    ax.set_title(f"Energy evolution  |  {len(td.tracks)} tracks  |  {td.niter} pts")

    save_or_show(fig, output)
    return Path(output) if output else None


def plot_tracks_field(
    td: TrackData,
    component: str,
    *,
    vs: str = "time",
    highlight_tracks: list[int] | None = None,
    output: str | Path | None = None,
) -> Path | None:
    """Field component along particle tracks.

    Parameters
    ----------
    td : TrackData
    component : str
        Field component name, e.g. ``'E1'``, ``'B3'``, ``'p1'``.
    vs : str
        X-axis: ``'time'`` or the name of any position quantity.
    highlight_tracks : list of int or None
    output : str, Path, or None

    Returns
    -------
    Path or None
    """
    icomp = _find_col(td.quants, component)
    ix = _find_col(td.quants, vs)

    fig, ax = plt.subplots(figsize=(8, 5))

    highlight = set(highlight_tracks or [])

    for i, track in enumerate(td.tracks):
        if i in highlight:
            ax.plot(track[:, ix], track[:, icomp],
                    linewidth=1.2, alpha=0.9, label=f"track {i}")
        else:
            ax.plot(track[:, ix], track[:, icomp],
                    linewidth=0.5, alpha=0.4, color="grey")

    ax.set_xlabel(vs)
    ax.set_ylabel(component)
    ax.set_title(
        f"{component} along track  |  "
        f"{len(td.tracks)} tracks  |  {td.niter} pts"
    )
    if highlight:
        ax.legend(fontsize=8)

    save_or_show(fig, output)
    return Path(output) if output else None
