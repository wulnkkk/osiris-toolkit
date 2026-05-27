"""Compute — pure numerical transforms (FFT, integration, interpolation).

All functions here are stateless: numpy in, numpy out. No imports from
sim/, units/, or matplotlib.
"""

from osiris_toolkit.compute.fft import compute_k_space, spectral_power
from osiris_toolkit.compute.integrate import line_integrate, mask_energy, trapz_2d

__all__ = [
    "compute_k_space",
    "line_integrate",
    "mask_energy",
    "spectral_power",
    "trapz_2d",
]
