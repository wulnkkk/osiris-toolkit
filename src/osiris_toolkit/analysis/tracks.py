"""Track diagnostic analysis — energy evolution, field along track."""

from __future__ import annotations

import numpy as np

from osiris_toolkit.exceptions import DataNotFoundError

from ._protocol import DiagnosticAnalyzer


class TracksAnalyzer(DiagnosticAnalyzer):
    """Track diagnostic analysis.

    Parameters
    ----------
    sim : Simulation
    converter : UnitConverter or None
    """

    diagnostic_kind = "TRACKS"

    def list_available(self) -> list[str]:
        return self._sim.list_tracks()

    def energy_evolution(self, name: str) -> list[np.ndarray]:
        """Extract energy time-series for each track.

        Parameters
        ----------
        name : str
            Track diagnostic name.

        Returns
        -------
        list of np.ndarray
            One array per track, each containing the ``ene`` column values
            in iteration order.
        """
        td = self._sim.get_tracks(name)
        if td is None:
            raise DataNotFoundError(f"No track data for '{name}'")

        ene_idx = _find_quant(td.quants, "ene")
        return [track[:, ene_idx] for track in td.tracks]

    def field_along(self, name: str, component: str) -> list[np.ndarray]:
        """Extract field component along each track.

        Parameters
        ----------
        name : str
            Track diagnostic name.
        component : str
            Field component name, e.g. ``'E1'``, ``'B3'``.

        Returns
        -------
        list of np.ndarray
            One array per track, each containing the requested field column.
        """
        td = self._sim.get_tracks(name)
        if td is None:
            raise DataNotFoundError(f"No track data for '{name}'")

        idx = _find_quant(td.quants, component)
        return [track[:, idx] for track in td.tracks]


def _find_quant(quants: list[str], target: str) -> int:
    """Find index of *target* in *quants*, case-insensitive.

    Raises ValueError if not found.
    """
    target_lower = target.lower()
    for i, q in enumerate(quants):
        if q.lower() == target_lower:
            return i
    raise DataNotFoundError(f"Quantity '{target}' not found in track quants: {quants}")
