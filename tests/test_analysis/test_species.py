"""Tests for SpeciesAnalyzer."""

import numpy as np
import pytest

from osiris_toolkit.exceptions import DataNotFoundError


class TestMomentumStats:
    """Test momentum_stats with synthetic ParticleData."""

    def test_basic_stats(self):
        """momentum_stats returns correct means and particle count."""
        from unittest.mock import MagicMock

        from osiris_toolkit.analysis.species import SpeciesAnalyzer
        from osiris_toolkit.sim.diagnostics import ParticleData

        mock_sim = MagicMock()
        raw = ParticleData(
            data={
                "p1": np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
                "p2": np.array([0.0, 0.0, 0.0, 0.0, 0.0]),
                "p3": np.array([-1.0, 0.0, 1.0, 0.0, -1.0]),
            },
            nparts=5,
            iteration=50,
            time=10.0,
        )
        mock_sim.get_raw.return_value = raw

        analyzer = SpeciesAnalyzer(mock_sim)
        result = analyzer.momentum_stats("electrons", 50)

        assert result.species == "electrons"
        assert result.nparts == 5
        assert result.p1_mean == 3.0
        assert result.p2_mean == 0.0
        assert result.p3_mean == pytest.approx(-0.2)

    def test_no_data_raises(self):
        """momentum_stats raises ValueError when raw data is missing."""
        from unittest.mock import MagicMock

        from osiris_toolkit.analysis.species import SpeciesAnalyzer

        mock_sim = MagicMock()
        mock_sim.get_raw.return_value = None

        analyzer = SpeciesAnalyzer(mock_sim)
        with pytest.raises(DataNotFoundError, match="No raw particle data"):
            analyzer.momentum_stats("electrons", 50)
