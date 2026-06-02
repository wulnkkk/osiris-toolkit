"""Symmetric diverging colormaps for field visualization."""

from __future__ import annotations

import numpy as np
from matplotlib.colors import LinearSegmentedColormap


def symmetrical_colormap(
    positive_cmap: str = "Reds",
    negative_cmap: str = "Blues",
    n_colors: int = 256,
    white_center: bool = True,
) -> LinearSegmentedColormap:
    """Build a diverging colormap from two existing matplotlib colormaps.

    Parameters
    ----------
    positive_cmap : str
        Matplotlib colormap name for positive values.
    negative_cmap : str
        Matplotlib colormap name for negative values.
    n_colors : int
        Total number of colors.
    white_center : bool
        If True, insert a white band at the center (zero region).

    Returns
    -------
    LinearSegmentedColormap
    """
    import matplotlib.pyplot as plt

    half = n_colors // 2
    if white_center:
        half = max(1, half - 1)

    pos = plt.colormaps[positive_cmap](np.linspace(0.3, 1.0, half))
    neg = plt.colormaps[negative_cmap](np.linspace(1.0, 0.3, half))

    if white_center:
        white = np.array([[1.0, 1.0, 1.0, 1.0]])
        colors = np.vstack([neg, white, white, pos])
    else:
        colors = np.vstack([neg, pos])

    return LinearSegmentedColormap.from_list(
        f"{negative_cmap}_{positive_cmap}", colors, N=len(colors)
    )


def register_cmaps() -> None:
    """Register EField and BField symmetric colormaps with matplotlib."""
    import matplotlib

    matplotlib.colormaps.register(
        cmap=symmetrical_colormap("Reds", "Blues"), name="EField"
    )
    matplotlib.colormaps.register(
        cmap=symmetrical_colormap("Oranges", "Greens"), name="BField"
    )


__all__ = ["symmetrical_colormap", "register_cmaps"]
