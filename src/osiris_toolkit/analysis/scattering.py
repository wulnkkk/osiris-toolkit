"""Scattering analysis — k-space energy fraction partitioning over time."""

from __future__ import annotations

import logging

from osiris_toolkit.compute.fft import compute_k_space
from osiris_toolkit.compute.integrate import mask_energy
from osiris_toolkit.exceptions import DataNotFoundError, UnitConversionError

from ._protocol import DiagnosticAnalyzer
from ._result_types import ScatteringResult

logger = logging.getLogger(__name__)

# Default k-space mask definitions (preserved from original vis/scattering.py)
DEFAULT_MASKS: dict = {
    "incident": {
        "kx_range": (-1.1, 1.1),
        "ky_range": (-1.0, 1.0),
        "label": "Incident",
    },
    "scattered": {
        "kx_range": (-0.61, 0.61),
        "ky_range": (-0.65, 0.65),
        "label": "Scattered",
    },
    "side_scatter_1": {
        "kx_range": (-0.11, 0.11),
        "ky_range": (-0.65, -0.42),
        "label": "Side-1",
    },
    "side_scatter_2": {
        "kx_range": (-0.11, 0.11),
        "ky_range": (0.42, 0.65),
        "label": "Side-2",
    },
    "back_scatter_1": {
        "kx_range": (0.47, 0.61),
        "ky_range": (-0.11, 0.11),
        "label": "Back-1",
    },
    "back_scatter_2": {
        "kx_range": (-0.61, -0.47),
        "ky_range": (-0.11, 0.11),
        "label": "Back-2",
    },
}


class ScatteringAnalyzer(DiagnosticAnalyzer):
    """K-space scattering energy fraction analysis.

    Parameters
    ----------
    sim : Simulation
    system : UnitSystem or None
    """

    diagnostic_kind = "EMF"  # scattering is a derived EMF analysis

    def list_available(self) -> list[str]:
        return self._sim.list_fields()

    def analyze(
        self,
        quantity: str,
        iterations: list[int] | None = None,
        masks: dict | None = None,
        omega0_norm: float = 1.0,
        verbose: bool = False,
    ) -> ScatteringResult:
        """Analyse k-space scattering energy fractions over time.

        Parameters
        ----------
        quantity : str
            Field component to analyse (e.g. ``'e3'``).
        iterations : list of int or None
            Iteration numbers to process. If None, all available.
        masks : dict or None
            Custom k-space mask definitions.
        omega0_norm : float
            Laser frequency in normalised units.
        verbose : bool
            If True, print per-iteration results.

        Returns
        -------
        ScatteringResult
        """
        if masks is None:
            masks = DEFAULT_MASKS

        if iterations is None:
            entries = self._sim._fields.get(quantity, [])
            iterations = sorted({e.iteration for e in entries})

        if not iterations:
            raise DataNotFoundError(f"No data found for quantity {quantity!r}")

        if self._system is None:
            raise UnitConversionError(
                "Scattering analysis requires a UnitSystem. Provide an input deck to construct one."
            )

        result = ScatteringResult(quantity=quantity, mask_info=dict(masks))

        for it in iterations:
            grid = self._sim.get_field(quantity, it)
            if grid is None:
                continue

            nx, ny = grid.data.shape
            dx = (grid.axes[0].max - grid.axes[0].min) / nx
            dy = (grid.axes[1].max - grid.axes[1].min) / ny
            kx, ky, spectrum = compute_k_space(grid.data, dx, dy)

            inc = mask_energy(
                spectrum,
                kx,
                ky,
                masks["incident"]["kx_range"],
                masks["incident"]["ky_range"],
                self._system,
            )
            sct = mask_energy(
                spectrum,
                kx,
                ky,
                masks["scattered"]["kx_range"],
                masks["scattered"]["ky_range"],
                self._system,
            )
            side1 = mask_energy(
                spectrum,
                kx,
                ky,
                masks["side_scatter_1"]["kx_range"],
                masks["side_scatter_1"]["ky_range"],
                self._system,
            )
            side2 = mask_energy(
                spectrum,
                kx,
                ky,
                masks["side_scatter_2"]["kx_range"],
                masks["side_scatter_2"]["ky_range"],
                self._system,
            )
            back1 = mask_energy(
                spectrum,
                kx,
                ky,
                masks["back_scatter_1"]["kx_range"],
                masks["back_scatter_1"]["ky_range"],
                self._system,
            )
            back2 = mask_energy(
                spectrum,
                kx,
                ky,
                masks["back_scatter_2"]["kx_range"],
                masks["back_scatter_2"]["ky_range"],
                self._system,
            )

            result.iterations.append(it)
            result.times.append(grid.time)
            result.scattered_fraction.append(sct / inc if inc > 0 else 0.0)
            result.side_scatter_fraction.append((side1 + side2) / inc if inc > 0 else 0.0)
            result.back_scatter_fraction.append((back1 + back2) / inc if inc > 0 else 0.0)

            if verbose:
                logger.info(
                    "  iteration=%06d  t=%.1f  scat=%.4f",
                    it,
                    grid.time,
                    result.scattered_fraction[-1],
                )

        return result
