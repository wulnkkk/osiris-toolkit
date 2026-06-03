"""Tests for ParticleData.filter() and compress()."""

import numpy as np
import pytest

from osiris_toolkit.exceptions import ValidationError


def _make_test_data():
    from osiris_toolkit.sim.diagnostics import ParticleData

    return ParticleData(
        data={
            "x1": np.array([0.1, 0.5, 0.9, 0.3]),
            "p1": np.array([-1.0, 0.0, 2.0, 1.0]),
            "ene": np.array([0.5, 1.5, 3.0, 2.0]),
        },
        nparts=4,
        iteration=10,
        time=5.0,
        label="electrons",
    )


class TestParticleFilter:
    """Test ParticleData.filter()."""

    def test_filter_simple_condition(self):
        """filter('p1 > 0') keeps only particles with p1 > 0."""
        raw = _make_test_data()
        result = raw.filter("p1 > 0")
        assert result.nparts == 2
        np.testing.assert_array_equal(result.data["p1"], np.array([2.0, 1.0]))

    def test_filter_chain(self):
        """Chaining two filters works."""
        raw = _make_test_data()
        result = raw.filter("p1 > 0").filter("ene < 2.5")
        assert result.nparts == 1
        assert result.data["p1"][0] == 1.0

    def test_filter_keeps_metadata(self):
        """filter preserves iteration, time, label."""
        raw = _make_test_data()
        result = raw.filter("p1 > 0")
        assert result.iteration == 10
        assert result.time == 5.0
        assert result.label == "electrons"

    def test_filter_empty_result(self):
        """filter with impossible condition returns nparts=0."""
        raw = _make_test_data()
        result = raw.filter("p1 > 100")
        assert result.nparts == 0
        assert len(result.data["p1"]) == 0

    def test_filter_invalid_expr_raises(self):
        """filter with invalid expression raises ValueError."""
        raw = _make_test_data()
        with pytest.raises(ValidationError, match="Failed to evaluate"):
            raw.filter("nonexistent_key > 0")

    def test_compress_returns_copy(self):
        """compress() returns contiguous copy independent of original."""
        raw = _make_test_data()
        filtered = raw.filter("p1 > 0")
        compact = filtered.compress()
        # Modify compact, verify filtered unchanged
        compact.data["p1"][0] = 999.0
        assert filtered.data["p1"][0] != 999.0

    def test_len(self):
        """__len__ returns nparts."""
        raw = _make_test_data()
        assert len(raw) == 4
