"""EMF-specific analysis — energy, spectra, Poynting flux."""

from __future__ import annotations

import numpy as np

from osiris_toolkit.compute.fft import compute_k_space

from ._protocol import DiagnosticAnalyzer
from ._result_types import EMDynamicsResult, EMSpectrumResult, FieldEnergyResult, PoyntingResult


class EMFAnalyzer(DiagnosticAnalyzer):
    """Electromagnetic field analysis for a simulation.

    Parameters
    ----------
    sim : Simulation
        The loaded simulation output directory.
    converter : UnitConverter | None
        Converter for normalized-to-physical units.
    """

    diagnostic_kind = "EMF"

    def list_available(self) -> list[str]:
        return self._sim.list_fields()

    # -- energy ----------------------------------------------------------

    def field_energy(self, quantity: str, iteration: int) -> FieldEnergyResult:
        """Read a field quantity and compute its integrated |E|^2 energy."""
        grid = self._sim.get_field(quantity, iteration)
        if grid is None:
            raise ValueError(f"No data for {quantity} at iteration {iteration}")
        total = float(np.sum(grid.data ** 2))
        return FieldEnergyResult(
            quantity=quantity,
            iteration=iteration,
            time=grid.time,
            total_energy=total,
            grid=grid,
        )

    def em_dynamics(self, iteration: int) -> EMDynamicsResult:
        """Compute total E^2, B^2, and E^2+B^2 energies at one iteration."""
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

        # pick up time from the first available field
        time = 0.0
        for q in ("e1", "e2", "e3", "b1", "b2", "b3"):
            grid = self._sim.get_field(q, iteration)
            if grid is not None:
                time = grid.time
                break

        return EMDynamicsResult(
            iteration=iteration,
            time=time,
            e2_total=e_energy,
            b2_total=b_energy,
            total=e_energy + b_energy,
        )

    # -- spectrum --------------------------------------------------------

    def spectrum(self, quantity: str, iteration: int) -> EMSpectrumResult:
        """Compute 2-D FFT amplitude spectrum."""
        grid = self._sim.get_field(quantity, iteration)
        if grid is None:
            raise ValueError(f"No data for {quantity} at iteration {iteration}")

        data = grid.data
        if data.ndim < 2:
            raise ValueError(f"spectrum requires 2-D data, got shape {data.shape}")

        nx, ny = data.shape
        dx = (grid.axes[0].max - grid.axes[0].min) / nx
        dy = (grid.axes[1].max - grid.axes[1].min) / ny

        kx_k0, ky_k0, spectrum = compute_k_space(data, dx, dy)

        return EMSpectrumResult(
            quantity=quantity,
            iteration=iteration,
            time=grid.time,
            kx_k0=kx_k0,
            ky_k0=ky_k0,
            spectrum=spectrum,
        )

    # -- Poynting flux ---------------------------------------------------

    def poynting(self, iteration: int) -> PoyntingResult | None:
        """Compute Poynting vector S = E x B at a given iteration."""
        e1_g = self._sim.get_field("e1", iteration)
        e2_g = self._sim.get_field("e2", iteration)
        e3_g = self._sim.get_field("e3", iteration)
        b1_g = self._sim.get_field("b1", iteration)
        b2_g = self._sim.get_field("b2", iteration)
        b3_g = self._sim.get_field("b3", iteration)

        if any(g is None for g in (e1_g, e2_g, e3_g, b1_g, b2_g, b3_g)):
            return None

        e1, e2, e3 = e1_g.data, e2_g.data, e3_g.data
        b1, b2, b3 = b1_g.data, b2_g.data, b3_g.data

        s1 = e2 * b3 - e3 * b2
        s2 = e3 * b1 - e1 * b3
        s3 = e1 * b2 - e2 * b1

        return PoyntingResult(
            iteration=iteration,
            time=e1_g.time,
            s1=s1,
            s2=s2,
            s3=s3,
        )
