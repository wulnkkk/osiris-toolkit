"""Generic statistical operations on diagnostic data containers."""

from __future__ import annotations

import numpy as np

from osiris_toolkit._models import GridData


def mean(data: GridData) -> float:
    """Mean value of grid data."""
    return float(np.mean(data.data))


def std(data: GridData) -> float:
    """Standard deviation of grid data."""
    return float(np.std(data.data))


def minmax(data: GridData) -> tuple[float, float]:
    """Return (min, max) of grid data."""
    return float(np.min(data.data)), float(np.max(data.data))


def energy_weighted_center(data: GridData, axis: int = 0) -> float:
    """Compute the energy-weighted center along a spatial axis.

    Returns the center position in axis coordinates.
    """
    arr = np.abs(data.data)
    total = np.sum(arr)
    if total == 0:
        return 0.0
    # Flatten all axes except the one of interest
    axes_to_sum = tuple(i for i in range(arr.ndim) if i != axis)
    profile = np.sum(arr, axis=axes_to_sum)
    grid = np.arange(len(profile))
    return float(np.sum(grid * profile) / total)


def rms(data: GridData) -> float:
    """Root-mean-square of grid data."""
    return float(np.sqrt(np.mean(data.data ** 2)))


def total_energy(grid: GridData, dx: float = 1.0) -> float:
    """Total integrated |value|^2 over the grid."""
    return float(np.sum(grid.data ** 2) * dx)


def lineout(data: GridData, index: int, axis: int = 0) -> np.ndarray:
    """Extract a 1D slice along the specified axis."""
    slc = [slice(None)] * data.data.ndim
    slc[axis] = index
    return data.data[tuple(slc)]


def histogram(data: np.ndarray, bins: int = 100) -> tuple[np.ndarray, np.ndarray]:
    """Compute histogram of data values."""
    return np.histogram(data, bins=bins)


def describe(grid: GridData) -> dict:
    """Return a summary dict with common statistics."""
    d = grid.data
    return {
        "shape": list(d.shape),
        "mean": float(np.mean(d)),
        "std": float(np.std(d)),
        "min": float(np.min(d)),
        "max": float(np.max(d)),
        "rms": float(np.sqrt(np.mean(d ** 2))),
        "iteration": grid.iteration,
        "time": grid.time,
    }
