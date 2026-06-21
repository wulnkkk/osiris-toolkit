"""Tests for analysis.stats — enhance with edge cases."""

from osiris_toolkit.analysis.stats import describe, mean, minmax, rms, std, total_energy


class TestStatsEdgeCases:
    def test_mean_on_1d(self, grid_1d):
        assert mean(grid_1d) == 3.0

    def test_rms_on_ones(self, grid_zeros):
        assert rms(grid_zeros) == 0.0

    def test_total_energy_zeros(self, grid_zeros):
        assert total_energy(grid_zeros) == 0.0

    def test_describe_has_all_keys(self, grid_2d):
        result = describe(grid_2d)
        for key in ("shape", "mean", "std", "min", "max", "rms", "iteration", "time"):
            assert key in result

    def test_minmax_symmetry(self, grid_32x32):
        mn, mx = minmax(grid_32x32)
        assert mn <= mx

    def test_mean_32x32(self, grid_32x32):
        m = mean(grid_32x32)
        assert 0.3 < m < 0.7

    def test_all_zero_grid(self, grid_zeros):
        assert mean(grid_zeros) == 0.0
        assert std(grid_zeros) == 0.0
        assert rms(grid_zeros) == 0.0
