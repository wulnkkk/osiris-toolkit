"""K-space analysis — FFT-based spectral analysis for field data."""

from __future__ import annotations

from osiris_toolkit.compute.fft import compute_k_space
from osiris_toolkit.exceptions import DataNotFoundError, ShapeError

from ._protocol import DiagnosticAnalyzer
from ._result_types import EMSpectrumResult


class KSpaceAnalyzer(DiagnosticAnalyzer):
    """K-space spectral analysis for field quantities.

    Parameters
    ----------
    sim : Simulation
    converter : UnitConverter or None
    """

    diagnostic_kind = "KSPACE"

    def list_available(self) -> list[str]:
        return self._sim.list_fields()

    def spectrum(
        self,
        quantity: str,
        iteration: int,
        omega0_norm: float = 1.0,
    ) -> EMSpectrumResult:
        """Compute the 2-D FFT spectrum of a field quantity.

        Parameters
        ----------
        quantity : str
            Field component name.
        iteration : int
            Iteration number.
        omega0_norm : float
            Reference frequency for k/k0 normalization.

        Returns
        -------
        EMSpectrumResult
        """
        grid = self._sim.get_field(quantity, iteration)
        if grid is None:
            raise DataNotFoundError(f"No data for {quantity} at iteration {iteration}")

        data = grid.data
        if data.ndim < 2:
            raise ShapeError(f"K-space requires 2-D data, got shape {data.shape}")

        nx, ny = data.shape
        dx = (grid.axes[0].max - grid.axes[0].min) / nx
        dy = (grid.axes[1].max - grid.axes[1].min) / ny

        kx, ky, spectrum = compute_k_space(data, dx, dy)

        return EMSpectrumResult(
            quantity=quantity,
            iteration=iteration,
            time=grid.time,
            kx_k0=kx,
            ky_k0=ky,
            spectrum=spectrum,
        )
