"""FFT utilities — 2-D k-space spectra and spectral power."""

from __future__ import annotations

import numpy as np

from osiris_toolkit.exceptions import ShapeError


def compute_k_space(
    data: np.ndarray,
    dx: float,
    dy: float,
    omega0_norm: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the 2-D FFT k-space spectrum.

    Parameters
    ----------
    data : 2-D array
        Input field data (real space).
    dx, dy : float
        Grid spacing in each direction.
    omega0_norm : float
        Reference frequency for k/k0 normalization (default 1.0).

    Returns
    -------
    kx_k0 : 1-D array
        kx/k0 values, fftshifted.
    ky_k0 : 1-D array
        ky/k0 values, fftshifted.
    spectrum : 2-D array
        |FFT| amplitude (not power), fftshifted.
    """
    if data.ndim != 2:
        raise ShapeError(f"Expected 2-D data, got shape {data.shape}")
    nx, ny = data.shape

    kx = 2.0 * np.pi * np.fft.fftfreq(nx, d=dx)
    ky = 2.0 * np.pi * np.fft.fftfreq(ny, d=dy)

    fft_result = np.fft.fft2(data)
    spectrum = np.abs(np.fft.fftshift(fft_result))

    kx_k0 = np.fft.fftshift(kx) / omega0_norm
    ky_k0 = np.fft.fftshift(ky) / omega0_norm

    return kx_k0, ky_k0, spectrum


def spectral_power(
    data: np.ndarray,
    dx: float,
    dy: float,
    omega0_norm: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the 2-D spectral power |FFT|^2.

    Parameters
    ----------
    data : 2-D array
        Input field data (real space).
    dx, dy : float
        Grid spacing.
    omega0_norm : float
        Reference frequency for k/k0 normalization.

    Returns
    -------
    kx_k0, ky_k0 : 1-D arrays
        k/k0 coordinate arrays.
    power : 2-D array
        |FFT|^2 amplitude, fftshifted.
    """
    kx_k0, ky_k0, spectrum = compute_k_space(data, dx, dy, omega0_norm)
    return kx_k0, ky_k0, spectrum ** 2
