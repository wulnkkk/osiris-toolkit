"""FFT utilities — 2-D k-space spectra and spectral power."""

from __future__ import annotations

import numpy as np

from osiris_toolkit.exceptions import ShapeError


def compute_k_space(
    data: np.ndarray,
    dx: float,
    dy: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the 2-D FFT k-space spectrum.

    Parameters
    ----------
    data : 2-D array
        Input field data (real space).
    dx, dy : float
        Grid spacing in each direction.

    Returns
    -------
    kx : 1-D array
        Angular wavenumber in normalized units (rad / (c/ω_p)), fftshifted.
    ky : 1-D array
        Angular wavenumber in normalized units (rad / (c/ω_p)), fftshifted.
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

    kx = np.fft.fftshift(kx)
    ky = np.fft.fftshift(ky)

    return kx, ky, spectrum


def spectral_power(
    data: np.ndarray,
    dx: float,
    dy: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the 2-D spectral power |FFT|^2.

    Parameters
    ----------
    data : 2-D array
        Input field data (real space).
    dx, dy : float
        Grid spacing.

    Returns
    -------
    kx, ky : 1-D arrays
        Angular wavenumber in normalized units (rad / (c/ω_p)).
    power : 2-D array
        |FFT|^2 amplitude, fftshifted.
    """
    kx, ky, spectrum = compute_k_space(data, dx, dy)
    return kx, ky, spectrum ** 2
