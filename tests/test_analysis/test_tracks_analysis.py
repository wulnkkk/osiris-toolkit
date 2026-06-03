"""Tests for TracksAnalyzer."""

import numpy as np
import pytest

from osiris_toolkit.exceptions import DataNotFoundError


class TestTracksAnalyzer:
    """Test TracksAnalyzer with synthetic TrackData."""

    def test_list_available(self):
        """list_available returns track names from sim."""
        from unittest.mock import MagicMock

        from osiris_toolkit.analysis.tracks import TracksAnalyzer

        mock_sim = MagicMock()
        mock_sim.list_tracks.return_value = ["track_electrons", "track_ions"]

        analyzer = TracksAnalyzer(mock_sim)
        result = analyzer.list_available()

        assert result == ["track_electrons", "track_ions"]

    def test_energy_evolution(self):
        """energy_evolution extracts ene column from each track."""
        from unittest.mock import MagicMock

        from osiris_toolkit.analysis.tracks import TracksAnalyzer
        from osiris_toolkit.sim.diagnostics import TrackData

        td = TrackData(
            tracks=[np.array([[1, 2.0], [2, 3.0], [3, 4.0]])],
            quants=["n", "ene"],
            niter=3,
        )
        mock_sim = MagicMock()
        mock_sim.get_tracks.return_value = td

        analyzer = TracksAnalyzer(mock_sim)
        result = analyzer.energy_evolution("track_test")

        assert len(result) == 1
        assert result[0].tolist() == [2.0, 3.0, 4.0]

    def test_energy_evolution_no_data_raises(self):
        """energy_evolution raises ValueError when track data is missing."""
        from unittest.mock import MagicMock

        from osiris_toolkit.analysis.tracks import TracksAnalyzer

        mock_sim = MagicMock()
        mock_sim.get_tracks.return_value = None

        analyzer = TracksAnalyzer(mock_sim)
        with pytest.raises(DataNotFoundError, match="No track data"):
            analyzer.energy_evolution("nonexistent")

    def test_field_along(self):
        """field_along extracts a field component column from each track."""
        from unittest.mock import MagicMock

        from osiris_toolkit.analysis.tracks import TracksAnalyzer
        from osiris_toolkit.sim.diagnostics import TrackData

        td = TrackData(
            tracks=[np.array([[1, 5.0, 10.0], [2, 6.0, 11.0]])],
            quants=["n", "E1", "B1"],
            niter=2,
        )
        mock_sim = MagicMock()
        mock_sim.get_tracks.return_value = td

        analyzer = TracksAnalyzer(mock_sim)
        result = analyzer.field_along("track_test", "E1")

        assert len(result) == 1
        assert result[0].tolist() == [5.0, 6.0]

    def test_field_along_missing_component_raises(self):
        """field_along raises ValueError when component not in quants."""
        from unittest.mock import MagicMock

        from osiris_toolkit.analysis.tracks import TracksAnalyzer
        from osiris_toolkit.sim.diagnostics import TrackData

        td = TrackData(
            tracks=[],
            quants=["n", "ene"],
            niter=0,
        )
        mock_sim = MagicMock()
        mock_sim.get_tracks.return_value = td

        analyzer = TracksAnalyzer(mock_sim)
        with pytest.raises(DataNotFoundError, match="not found in track"):
            analyzer.field_along("track_test", "E1")
