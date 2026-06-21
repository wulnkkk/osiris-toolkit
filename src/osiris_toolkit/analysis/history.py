"""Time-series history analysis for OSIRIS HISTORY diagnostic."""

from __future__ import annotations

from osiris_toolkit.exceptions import DataNotFoundError

from ._protocol import DiagnosticAnalyzer
from ._result_types import HistoryResult


class HistoryAnalyzer(DiagnosticAnalyzer):
    """Time-series history analysis.

    Reads OSIRIS HISTORY text files (e.g. ``ene``, ``pwr``, ``field``)
    and extracts single-column timeseries for plotting or further analysis.

    Parameters
    ----------
    sim : Simulation
    converter : UnitConverter | None

    Examples
    --------
    >>> analyzer = HistoryAnalyzer(sim)
    >>> analyzer.list_available()
    ['ene', 'pwr']
    >>> result = analyzer.get_timeseries("ene", "total")
    >>> result.time.shape
    (1001,)
    """

    diagnostic_kind = "HISTORY"

    def list_available(self) -> list[str]:
        """Return the names of available HISTORY files."""
        return self._sim.list_history()

    def get_timeseries(self, name: str, column: str) -> HistoryResult:
        """Read a history file and return a single column as a timeseries.

        Parameters
        ----------
        name : str
            History file name (e.g. ``"ene"``, ``"pwr"``).
        column : str
            Column name to extract (e.g. ``"total"``, ``"field"``).

        Returns
        -------
        HistoryResult
            Named tuple with ``name``, ``column``, ``time``, ``values``.

        Raises
        ------
        DataNotFoundError
            If the history file or column does not exist.
        """
        hd = self._sim.get_history(name)
        if hd is None or not hd.columns:
            raise DataNotFoundError(f"No history data for '{name}'")
        if column not in hd.columns:
            raise DataNotFoundError(
                f"Column '{column}' not found in history '{name}'. Available: {', '.join(hd.columns)}"
            )
        # Try "time" column first, fall back to first column
        time_col = "time" if "time" in hd.data else hd.columns[0]
        return HistoryResult(
            name=name,
            column=column,
            time=hd.data[time_col],
            values=hd.data[column],
        )
