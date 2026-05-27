"""Integration utilities — k-space masking, 2-D trapezoidal, line integration."""

from __future__ import annotations

import numpy as np


def mask_energy(
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
        FFT amplitude (not power) from ``compute_k_space``.
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
    return float(np.sum(region ** 2))


def trapz_2d(
    data: np.ndarray,
    dx: float,
    dy: float,
) -> float:
    """2-D trapezoidal integration.

    Parameters
    ----------
    data : 2-D array
        Data to integrate.
    dx, dy : float
        Grid spacing.

    Returns
    -------
    float
        Numerical integral.
    """
    return float(np.trapezoid(np.trapezoid(data, dx=dy, axis=1), dx=dx, axis=0))


def line_integrate(
    data: np.ndarray,
    axis: int = 0,
) -> np.ndarray:
    """Integrate data over all axes except *axis*, returning a 1-D profile.

    Parameters
    ----------
    data : ndarray
        Input grid data.
    axis : int
        Axis along which to NOT integrate.

    Returns
    -------
    1-D array
        Line-integrated profile.
    """
    axes_to_sum = tuple(i for i in range(data.ndim) if i != axis)
    return np.sum(data, axis=axes_to_sum) if axes_to_sum else data
