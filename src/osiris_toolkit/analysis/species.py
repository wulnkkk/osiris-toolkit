"""Species/density analysis — profiles, integrals, temperature."""

from __future__ import annotations

import numpy as np

from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter


class SpeciesAnalyzer:
    """Particle and density analysis for a simulation.

    Parameters
    ----------
    sim : Simulation
        The loaded simulation output directory.
    converter : UnitConverter | None
        Converter for normalized-to-physical units.
    """

    def __init__(self, sim: Simulation, converter: UnitConverter | None = None) -> None:
        self._sim = sim
        self._converter = converter

    def density_profile(
        self, species: str, quantity: str, iteration: int, axis: int = 0
    ) -> tuple[np.ndarray, np.ndarray]:
        """Line-integrated density profile along one axis.

        Returns (coord, density_profile).
        """
        grid = self._sim.get_density(species, quantity, iteration)
        if grid is None:
            raise ValueError(
                f"No {quantity} density for species '{species}' at iteration {iteration}"
            )

        # Integrate over all axes except the one of interest
        axes_to_sum = tuple(i for i in range(grid.data.ndim) if i != axis)
        profile = np.sum(grid.data, axis=axes_to_sum) if axes_to_sum else grid.data

        if grid.axes and len(grid.axes) > axis:
            n = grid.data.shape[axis]
            coord = np.linspace(grid.axes[axis].min, grid.axes[axis].max, n)
        else:
            coord = np.arange(len(profile))

        return coord, profile

    def total_charge(self, species: str, iteration: int) -> float:
        """Total charge for a species at a given iteration."""
        grid = self._sim.get_density(species, "charge", iteration)
        if grid is None:
            raise ValueError(
                f"No charge density for species '{species}' at iteration {iteration}"
            )
        return float(np.sum(grid.data))

    def energy_spectrum(
        self, species: str, iteration: int, bins: int = 100
    ) -> tuple[np.ndarray, np.ndarray]:
        """Energy histogram from raw particle data."""
        raw = self._sim.get_raw(species, iteration)
        if raw is None:
            raise ValueError(
                f"No raw particle data for species '{species}' at iteration {iteration}"
            )

        # Use kinetic energy if available
        ene = raw.data.get("ene", raw.data.get("p"))
        if ene is None:
            raise ValueError("No energy/kinetic energy quantity in raw data")

        counts, edges = np.histogram(np.abs(ene), bins=bins)
        centers = 0.5 * (edges[:-1] + edges[1:])
        return centers, counts

    def temperature(
        self, species: str, iteration: int
    ) -> dict[str, float]:
        """Compute temperature tensor components from udist diagnostics.

        Returns dict with keys like T11, T22, T33 (diagonal components).
        """
        result: dict[str, float] = {}
        for comp in ("T11", "T22", "T33"):
            grid = self._sim.get_udist(species, comp, iteration)
            if grid is not None:
                result[comp] = float(np.mean(grid.data))
        return result

    def list_available(self) -> dict[str, list[str]]:
        """Return available species and their quantities."""
        available: dict[str, list[str]] = {}
        for sp in self._sim.list_species():
            available[sp] = []
        return available
