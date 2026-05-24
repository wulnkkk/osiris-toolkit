"""Tests for analysis.stats module."""

import numpy as np
import pytest

from osiris_toolkit.analysis.stats import (
    describe,
    mean,
    minmax,
    rms,
    std,
    total_energy,
)
from osiris_toolkit.sim.diagnostics import GridData


@pytest.fixture
def grid_2d() -> GridData:
    data = np.array([[1.0, 2.0], [3.0, 4.0]])
    return GridData(data=data, iteration=5, time=1.0, label="test")


class TestStats:
    def test_mean(self, grid_2d: GridData) -> None:
        assert mean(grid_2d) == 2.5

    def test_std(self, grid_2d: GridData) -> None:
        assert std(grid_2d) == pytest.approx(1.118, rel=0.01)

    def test_minmax(self, grid_2d: GridData) -> None:
        mn, mx = minmax(grid_2d)
        assert mn == 1.0
        assert mx == 4.0

    def test_rms(self, grid_2d: GridData) -> None:
        expected = np.sqrt(np.mean(np.array([1.0, 2.0, 3.0, 4.0]) ** 2))
        assert rms(grid_2d) == pytest.approx(expected)

    def test_total_energy(self, grid_2d: GridData) -> None:
        # Sum of squares
        assert total_energy(grid_2d) == pytest.approx(30.0)

    def test_describe(self, grid_2d: GridData) -> None:
        result = describe(grid_2d)
        assert result["shape"] == [2, 2]
        assert result["mean"] == 2.5
        assert result["iteration"] == 5
        assert result["time"] == 1.0
