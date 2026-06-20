"""Density analysis — profiles, integrals for DENSITY diagnostics."""

from __future__ import annotations

import numpy as np

from osiris_toolkit.compute.integrate import line_integrate
from osiris_toolkit.exceptions import DataNotFoundError

from ._protocol import DiagnosticAnalyzer
from ._result_types import DensityIntegralResult, DensityProfileResult


class DensityAnalyzer(DiagnosticAnalyzer):
    """Density diagnostic analysis.

    Parameters
    ----------
    sim : Simulation
    converter : UnitConverter or None
    """

    diagnostic_kind = "DENSITY"

    def list_available(self) -> list[str]:
        return self._sim.list_species()

    def profile(
        self,
        species: str,
        quantity: str = "charge",
        iteration: int = 0,
        axis: int = 0,
    ) -> DensityProfileResult:
        """Line-integrated density profile along one axis.

        Parameters
        ----------
        species : str
            Species name.
        quantity : str
            Density quantity (default ``'charge'``).
        iteration : int
            Iteration number.
        axis : int
            Axis along which to NOT integrate (0 or 1).

        Returns
        -------
        DensityProfileResult
        """
        grid = self._sim.get_density(species, quantity, iteration)
        if grid is None:
            raise DataNotFoundError(f"No {quantity} density for species '{species}' at iteration {iteration}")

        profile = line_integrate(grid.data, axis=axis)

        if grid.axes and len(grid.axes) > axis:
            n = grid.data.shape[axis]
            coord = np.linspace(grid.axes[axis].min, grid.axes[axis].max, n)
        else:
            coord = np.arange(len(profile))

        return DensityProfileResult(
            species=species,
            quantity=quantity,
            iteration=iteration,
            time=grid.time,
            axis=axis,
            coord=coord,
            profile=profile,
        )

    def total(
        self,
        species: str,
        quantity: str = "charge",
        iteration: int = 0,
    ) -> DensityIntegralResult:
        """Total integrated density quantity for a species.

        Parameters
        ----------
        species : str
            Species name.
        quantity : str
            Density quantity (default ``'charge'``).
        iteration : int
            Iteration number.

        Returns
        -------
        DensityIntegralResult
        """
        grid = self._sim.get_density(species, quantity, iteration)
        if grid is None:
            raise DataNotFoundError(f"No {quantity} density for species '{species}' at iteration {iteration}")
        return DensityIntegralResult(
            species=species,
            quantity=quantity,
            iteration=iteration,
            time=grid.time,
            total=float(np.sum(grid.data)),
        )
