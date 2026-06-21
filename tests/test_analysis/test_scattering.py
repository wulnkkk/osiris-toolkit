"""Tests for ScatteringAnalyzer."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from osiris_toolkit.analysis.scattering import DEFAULT_MASKS, ScatteringAnalyzer
from osiris_toolkit.exceptions import UnitConversionError
from osiris_toolkit.sim.diagnostics import FieldInfo, GridAxis, GridData
from osiris_toolkit.units.converter import UnitSystem
from osiris_toolkit.units.params import SimulationParams


@pytest.fixture
def unit_system_with_k0() -> UnitSystem:
    """UnitSystem with omega0_norm so k0 wavenumber unit is available."""
    params = SimulationParams(omega_p0=3.55e15, omega0_norm=1.0)
    return UnitSystem(3.55e15, params=params)


def _make_grid_data_2d(data: np.ndarray, iteration: int = 0, time: float = 0.0) -> GridData:
    """Helper: create a 2-D GridData with axis metadata."""
    ny, nx = data.shape
    axes = [
        GridAxis(name="x1", type=0, min=0.0, max=float(nx), label="x1", units="c/\\omega_p"),
        GridAxis(name="x2", type=1, min=0.0, max=float(ny), label="x2", units="c/\\omega_p"),
    ]
    return GridData(data=data, axes=axes, iteration=iteration, time=time, label="e1")


class TestScatteringAnalyzer:
    """Tests for ScatteringAnalyzer.analyze()."""

    def test_analyze_without_system_raises(self):
        """analyze() raises UnitConversionError when system is None."""
        mock_sim = MagicMock()
        mock_sim._fields = {"e1": [FieldInfo(iteration=0, time=0.0, label="e1")]}

        analyzer = ScatteringAnalyzer(mock_sim, system=None)
        with pytest.raises(UnitConversionError, match="Scattering analysis requires a UnitSystem"):
            analyzer.analyze("e1")

    def test_analyze_basic(self, unit_system_with_k0):
        """analyze() returns ScatteringResult with correct structure."""
        mock_sim = MagicMock()
        mock_sim._fields = {"e1": [FieldInfo(iteration=0, time=1.0, label="e1")]}
        # Small random field: 16x16
        rng = np.random.default_rng(42)
        grid = _make_grid_data_2d(rng.random((16, 16), dtype=np.float64), iteration=0, time=1.0)
        mock_sim.get_field.return_value = grid

        analyzer = ScatteringAnalyzer(mock_sim, system=unit_system_with_k0)
        result = analyzer.analyze("e1")

        assert result.quantity == "e1"
        assert len(result.iterations) == 1
        assert result.iterations[0] == 0
        assert result.times == [1.0]
        # Energy fractions should be finite numbers
        assert np.isfinite(result.scattered_fraction[0])
        assert np.isfinite(result.side_scatter_fraction[0])
        assert np.isfinite(result.back_scatter_fraction[0])

    def test_analyze_multiple_iterations(self, unit_system_with_k0):
        """analyze() processes multiple iterations correctly."""
        mock_sim = MagicMock()
        mock_sim._fields = {
            "e3": [
                FieldInfo(iteration=10, time=5.0, label="e3"),
                FieldInfo(iteration=20, time=10.0, label="e3"),
                FieldInfo(iteration=30, time=15.0, label="e3"),
            ]
        }
        rng = np.random.default_rng(99)
        grid0 = _make_grid_data_2d(rng.random((16, 16), dtype=np.float64), iteration=10, time=5.0)
        grid1 = _make_grid_data_2d(rng.random((16, 16), dtype=np.float64), iteration=20, time=10.0)
        grid2 = _make_grid_data_2d(rng.random((16, 16), dtype=np.float64), iteration=30, time=15.0)
        mock_sim.get_field.side_effect = [grid0, grid1, grid2]

        analyzer = ScatteringAnalyzer(mock_sim, system=unit_system_with_k0)
        result = analyzer.analyze("e3")

        assert result.quantity == "e3"
        assert len(result.iterations) == 3
        assert result.iterations == [10, 20, 30]
        assert result.times == [5.0, 10.0, 15.0]
        assert len(result.scattered_fraction) == 3
        assert len(result.side_scatter_fraction) == 3
        assert len(result.back_scatter_fraction) == 3

    def test_analyze_with_custom_masks(self, unit_system_with_k0):
        """analyze() accepts custom mask definitions."""
        mock_sim = MagicMock()
        mock_sim._fields = {"e1": [FieldInfo(iteration=0, time=1.0, label="e1")]}
        rng = np.random.default_rng(7)
        grid = _make_grid_data_2d(rng.random((16, 16), dtype=np.float64), iteration=0, time=1.0)
        mock_sim.get_field.return_value = grid

        custom_masks = {
            "incident": {"kx_range": (-1.0, 1.0), "ky_range": (-1.0, 1.0), "label": "Inc"},
            "scattered": {"kx_range": (-0.5, 0.5), "ky_range": (-0.5, 0.5), "label": "Sct"},
            "side_scatter_1": {"kx_range": (-0.1, 0.1), "ky_range": (-0.6, -0.4), "label": "S1"},
            "side_scatter_2": {"kx_range": (-0.1, 0.1), "ky_range": (0.4, 0.6), "label": "S2"},
            "back_scatter_1": {"kx_range": (0.4, 0.6), "ky_range": (-0.1, 0.1), "label": "B1"},
            "back_scatter_2": {"kx_range": (-0.6, -0.4), "ky_range": (-0.1, 0.1), "label": "B2"},
        }

        analyzer = ScatteringAnalyzer(mock_sim, system=unit_system_with_k0)
        result = analyzer.analyze("e1", masks=custom_masks)

        assert result.mask_info == custom_masks
        assert len(result.iterations) == 1


class TestDefaultMasks:
    """Tests for DEFAULT_MASKS structure."""

    REQUIRED_KEYS = [
        "incident",
        "scattered",
        "side_scatter_1",
        "side_scatter_2",
        "back_scatter_1",
        "back_scatter_2",
    ]

    def test_has_required_keys(self):
        """DEFAULT_MASKS contains all 6 required regions."""
        for key in self.REQUIRED_KEYS:
            assert key in DEFAULT_MASKS, f"Missing mask key: {key}"

    def test_each_mask_has_required_fields(self):
        """Each mask has kx_range, ky_range, and label."""
        for key, mask in DEFAULT_MASKS.items():
            assert "kx_range" in mask, f"{key} missing kx_range"
            assert "ky_range" in mask, f"{key} missing ky_range"
            assert "label" in mask, f"{key} missing label"
            assert len(mask["kx_range"]) == 2
            assert len(mask["ky_range"]) == 2
            assert mask["kx_range"][0] < mask["kx_range"][1], f"{key}: kx_range not ordered"
            assert mask["ky_range"][0] < mask["ky_range"][1], f"{key}: ky_range not ordered"
