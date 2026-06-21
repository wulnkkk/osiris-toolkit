"""Tests for analysis.history — HistoryAnalyzer."""

import pytest
from osiris_toolkit.analysis.history import HistoryAnalyzer
from osiris_toolkit.analysis._result_types import HistoryResult
from osiris_toolkit.exceptions import DataNotFoundError
from osiris_toolkit.sim import Simulation


class TestHistoryAnalyzer:
    def test_list_available(self, tmp_sim_dir_hist):
        sim = Simulation(tmp_sim_dir_hist)
        analyzer = HistoryAnalyzer(sim)
        names = analyzer.list_available()
        assert "ene" in names

    def test_get_timeseries_basic(self, tmp_sim_dir_hist):
        sim = Simulation(tmp_sim_dir_hist)
        analyzer = HistoryAnalyzer(sim)
        result = analyzer.get_timeseries("ene", "total")
        assert isinstance(result, HistoryResult)
        assert result.name == "ene"
        assert result.column == "total"
        assert len(result.time) == 5
        assert len(result.values) == 5
        assert result.values[0] == pytest.approx(0.0)
        assert result.values[-1] == pytest.approx(3.5)

    def test_get_timeseries_unknown_file_raises(self, tmp_sim_dir_hist):
        sim = Simulation(tmp_sim_dir_hist)
        analyzer = HistoryAnalyzer(sim)
        with pytest.raises(DataNotFoundError):
            analyzer.get_timeseries("nonexistent", "total")

    def test_get_timeseries_unknown_column_raises(self, tmp_sim_dir_hist):
        sim = Simulation(tmp_sim_dir_hist)
        analyzer = HistoryAnalyzer(sim)
        with pytest.raises(DataNotFoundError):
            analyzer.get_timeseries("ene", "nonexistent")
