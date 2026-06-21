"""Tests for vis.history — plot_history_timeseries."""

from pathlib import Path

from osiris_toolkit.analysis._result_types import HistoryResult
from osiris_toolkit.vis.history import plot_history_timeseries
import numpy as np


class TestPlotHistoryTimeseries:
    def test_saves_to_file(self, tmp_path):
        result = HistoryResult(
            name="ene",
            column="total",
            time=np.array([0.0, 1.0, 2.0, 3.0]),
            values=np.array([0.0, 0.5, 1.0, 2.0]),
        )
        output = tmp_path / "history_ene_total.png"
        fpath = plot_history_timeseries(result, output=str(output))
        assert fpath is not None
        assert Path(fpath).exists()

    def test_returns_none_without_output(self):
        result = HistoryResult(
            name="ene",
            column="total",
            time=np.array([0.0, 1.0]),
            values=np.array([0.0, 1.0]),
        )
        fpath = plot_history_timeseries(result)
        assert fpath is None
