"""K-space analysis — FFT-based spectral analysis for field data."""

from __future__ import annotations

from osiris_toolkit.exceptions import DataNotFoundError, ShapeError, UnitConversionError
from osiris_toolkit.vis._quantified import QuantifiedSpectrum

from ._protocol import DiagnosticAnalyzer


class KSpaceAnalyzer(DiagnosticAnalyzer):
    """K-space spectral analysis for field quantities.

    Parameters
    ----------
    sim : Simulation
    system : UnitSystem or None
    """

    diagnostic_kind = "KSPACE"

    def list_available(self) -> list[str]:
        return self._sim.list_fields()

    def spectrum(
        self,
        quantity: str,
        iteration: int,
    ) -> QuantifiedSpectrum:
        """Compute the 2-D FFT spectrum of a field quantity.

        Parameters
        ----------
        quantity : str
            Field component name.
        iteration : int
            Iteration number.

        Returns
        -------
        QuantifiedSpectrum
        """
        if self._system is None:
            raise UnitConversionError("K-space spectrum requires a UnitSystem. Provide an input deck to construct one.")

        grid = self._sim.get_field(quantity, iteration)
        if grid is None:
            raise DataNotFoundError(f"No data for {quantity} at iteration {iteration}")

        if grid.data.ndim < 2:
            raise ShapeError(f"K-space requires 2-D data, got shape {grid.data.shape}")

        return QuantifiedSpectrum.from_field(grid, self._system)
