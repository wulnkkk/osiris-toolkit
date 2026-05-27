"""Species/particle analysis — energy spectra, temperature."""

from __future__ import annotations

import numpy as np

from ._protocol import DiagnosticAnalyzer
from ._result_types import ParticleSpectrumResult, TemperatureResult


class SpeciesAnalyzer(DiagnosticAnalyzer):
    """Particle analysis for a simulation.

    Density-related methods have moved to ``DensityAnalyzer``.

    Parameters
    ----------
    sim : Simulation
    converter : UnitConverter or None
    """

    diagnostic_kind = "RAW"  # species analysis operates on RAW particle data

    def list_available(self) -> list[str]:
        return self._sim.list_species()

    def energy_spectrum(
        self, species: str, iteration: int, bins: int = 100
    ) -> ParticleSpectrumResult:
        """Energy histogram from raw particle data."""
        raw = self._sim.get_raw(species, iteration)
        if raw is None:
            raise ValueError(
                f"No raw particle data for species '{species}' at iteration {iteration}"
            )

        ene = raw.data.get("ene", raw.data.get("p"))
        if ene is None:
            raise ValueError("No energy/kinetic energy quantity in raw data")

        counts, edges = np.histogram(np.abs(ene), bins=bins)
        centers = 0.5 * (edges[:-1] + edges[1:])
        return ParticleSpectrumResult(
            species=species,
            iteration=iteration,
            time=0.0,
            bin_centers=centers,
            counts=counts.astype(float),
        )

    def temperature(self, species: str, iteration: int) -> TemperatureResult:
        """Compute temperature tensor components from udist diagnostics."""
        result: dict[str, float] = {}
        for comp in ("T11", "T22", "T33"):
            grid = self._sim.get_udist(species, comp, iteration)
            if grid is not None:
                result[comp] = float(np.mean(grid.data))
        return TemperatureResult(
            species=species,
            iteration=iteration,
            time=0.0,
            components=result,
        )
