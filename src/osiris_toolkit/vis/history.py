"""History timeseries visualization."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from osiris_toolkit.analysis._result_types import HistoryResult
from osiris_toolkit.vis.common import save_or_show


def plot_history_timeseries(
    result: HistoryResult,
    output: str | Path | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    title: str | None = None,
) -> Path | None:
    """Plot a single history column vs time.

    Parameters
    ----------
    result : HistoryResult
        Result from ``HistoryAnalyzer.get_timeseries()``.
    output : Path or None
        File path to save the figure. If ``None``, display interactively.
    xlabel, ylabel, title : str or None
        Axis label and title overrides. Defaults are auto-generated from
        the result metadata.

    Returns
    -------
    Path or None
        The output path if ``output`` was given, else ``None``.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(result.time, result.values, linewidth=2)
    ax.set_xlabel(xlabel or "Time")
    ax.set_ylabel(ylabel or result.column)
    ax.set_title(title or f"{result.name} — {result.column}")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save_or_show(fig, output)
    return Path(output) if output else None
