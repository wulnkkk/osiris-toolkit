"""EMF-specific analysis — energy, spectra, Poynting flux."""

from __future__ import annotations

import numpy as np

from osiris_toolkit.sim import Simulation
from osiris_toolkit.sim.diagnostics import GridData
from osiris_toolkit.units import UnitConverter


class EMFAnalyzer:
    """Electromagnetic field analysis for a simulation.

    Parameters
    ----------
    sim : Simulation
        The loaded simulation output directory.
    converter : UnitConverter | None
        Converter for normalized-to-physical units. If None, results
        are in normalized units.
    """

    def __init__(self, sim: Simulation, converter: UnitConverter | None = None) -> None:
        self._sim = sim
        self._converter = converter

    # -- energy ----------------------------------------------------------

    def field_energy(
        self, quantity: str, iteration: int
    ) -> tuple[GridData, float]:
        """Read a field quantity and compute its integrated |E|^2 energy.

        Returns (grid_data, total_energy).
        """
        grid = self._sim.get_field(quantity, iteration)
        if grid is None:
            raise ValueError(f"No data for {quantity} at iteration {iteration}")
        total = float(np.sum(grid.data ** 2))
        return grid, total

    def total_em_energy(self, iteration: int) -> dict[str, float]:
        """Compute total E^2, B^2, and E^2+B^2 energies at a given iteration.

        Returns a dict like::

            {"e_energy": ..., "b_energy": ..., "em_energy": ...}
        """
        result: dict[str, float] = {}
        e_energy = 0.0
        b_energy = 0.0

        for q in ("e1", "e2", "e3"):
            grid = self._sim.get_field(q, iteration)
            if grid is not None:
                e_energy += float(np.sum(grid.data ** 2))

        for q in ("b1", "b2", "b3"):
            grid = self._sim.get_field(q, iteration)
            if grid is not None:
                b_energy += float(np.sum(grid.data ** 2))

        result["e_energy"] = e_energy
        result["b_energy"] = b_energy
        result["em_energy"] = e_energy + b_energy
        return result

    # -- spectrum --------------------------------------------------------

    def spectrum(
        self, quantity: str, iteration: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Compute the 2D FFT power spectrum of a field quantity.

        Returns (kx, ky, kx_shifted, ky_shifted, spectrum).

        kx, ky axes are in units of 2*pi / grid_length.
        Spectrum is |FFT| (magnitude, not power).
        """
        grid = self._sim.get_field(quantity, iteration)
        if grid is None:
            raise ValueError(f"No data for {quantity} at iteration {iteration}")

        data = grid.data
        nx, ny = data.shape[:2] if data.ndim >= 2 else (data.shape[0], 1)

        # Compute physical k axes
        if grid.axes:
            dx = (grid.axes[0].max - grid.axes[0].min) / nx
            dy = (grid.axes[1].max - grid.axes[1].min) / ny if data.ndim >= 2 else dx
        else:
            dx = dy = 1.0

        kx = 2 * np.pi * np.fft.fftfreq(nx, dx)
        ky = 2 * np.pi * np.fft.fftfreq(ny, dy)

        fft = np.abs(np.fft.fftshift(np.fft.fft2(data)))
        kx_s = np.fft.fftshift(kx)
        ky_s = np.fft.fftshift(ky)

        return kx_s, ky_s, fft

    # -- Poynting flux ---------------------------------------------------

    def poynting(
        self, iteration: int
    ) -> np.ndarray | None:
        """Compute Poynting vector S = E x B at a given iteration.

        Returns a 3-tuple (S1, S2, S3) of GridData or numpy arrays.
        """
        e1_g = self._sim.get_field("e1", iteration)
        e2_g = self._sim.get_field("e2", iteration)
        e3_g = self._sim.get_field("e3", iteration)
        b1_g = self._sim.get_field("b1", iteration)
        b2_g = self._sim.get_field("b2", iteration)
        b3_g = self._sim.get_field("b3", iteration)

        if None in (e1_g, b1_g):
            return None

        e1, e2, e3 = e1_g.data, e2_g.data, e3_g.data
        b1, b2, b3 = b1_g.data, b2_g.data, b3_g.data

        s1 = e2 * b3 - e3 * b2
        s2 = e3 * b1 - e1 * b3
        s3 = e1 * b2 - e2 * b1

        return np.array([s1, s2, s3])
