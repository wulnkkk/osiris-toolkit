"""Compute — pure numerical transforms (FFT, integration, interpolation).

All functions here are stateless: numpy in, numpy out. No imports from
sim/, units/, or matplotlib.
"""

from osiris_toolkit.compute.deposit import particles_to_grid
from osiris_toolkit.compute.fft import compute_k_space, spectral_power
from osiris_toolkit.compute.integrate import line_integrate, mask_energy, trapz_2d
from osiris_toolkit.compute.transform import remap_field, to_cylindrical

__all__ = [
    "compute_k_space",
    "line_integrate",
    "mask_energy",
    "particles_to_grid",
    "remap_field",
    "spectral_power",
    "to_cylindrical",
    "trapz_2d",
]
