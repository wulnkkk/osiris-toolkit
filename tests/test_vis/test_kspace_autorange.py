"""Tests for vis.kspace — _auto_k_range axis detection."""

import numpy as np
import pytest

from osiris_toolkit.exceptions import ShapeError
from osiris_toolkit.units.converter import UnitSystem
from osiris_toolkit.vis.kspace import _auto_k_range


@pytest.fixture
def system_with_k0() -> UnitSystem:
    from osiris_toolkit.units.params import SimulationParams

    params = SimulationParams(omega_p0=3.55e15, omega0_norm=1.0)
    return UnitSystem(3.55e15, params=params)


class TestAutoKRange:
    """Tests for _auto_k_range axis auto-detection."""

    def test_x_axis_projection(self, system_with_k0):
        """When k_norm matches spectrum.shape[0], projects on axis=1 (correct for x)."""
        # spectrum (3600, 4000) — asymmetric
        rng = np.random.default_rng(1)
        spectrum = rng.random((36, 40))
        kx = np.linspace(-5, 5, 36)  # length matches shape[0]=36

        k_min, k_max = _auto_k_range(kx, spectrum, "k0", system_with_k0.wavenumber)
        assert k_min < k_max
        assert np.isfinite(k_min) and np.isfinite(k_max)

    def test_y_axis_projection(self, system_with_k0):
        """When k_norm matches spectrum.shape[1], projects on axis=0 (correct for y)."""
        rng = np.random.default_rng(2)
        spectrum = rng.random((36, 40))
        ky = np.linspace(-4, 4, 40)  # length matches shape[1]=40

        k_min, k_max = _auto_k_range(ky, spectrum, "k0", system_with_k0.wavenumber)
        assert k_min < k_max
        assert np.isfinite(k_min) and np.isfinite(k_max)

    def test_mismatch_raises(self, system_with_k0):
        """When k_norm matches neither axis, raises ShapeError."""
        spectrum = np.ones((10, 10))
        k_bad = np.linspace(0, 1, 7)  # matches neither 10 nor 10

        with pytest.raises(ShapeError, match="k_norm length"):
            _auto_k_range(k_bad, spectrum, "k0", system_with_k0.wavenumber)

    def test_empty_signal_returns_full_range(self, system_with_k0):
        """When no signal above threshold, returns full k range."""
        spectrum = np.zeros((20, 30))
        kx = np.linspace(-3, 3, 20)

        k_min, k_max = _auto_k_range(kx, spectrum, "k0", system_with_k0.wavenumber, threshold_frac=0.01)
        # Should return the full converted range
        conv = system_with_k0.wavenumber.to(kx, "k0")
        assert k_min == pytest.approx(float(conv.min()))
        assert k_max == pytest.approx(float(conv.max()))

    def test_strong_peak_narrows_range(self, system_with_k0):
        """A strong isolated peak should narrow the auto range."""
        spectrum = np.zeros((50, 60))
        spectrum[20:30, 25:35] = 100.0  # peak in middle
        kx = np.linspace(-5, 5, 50)

        k_min, k_max = _auto_k_range(kx, spectrum, "k0", system_with_k0.wavenumber, threshold_frac=0.01, margin=0.0)
        # Narrowed range should be inside the full range
        conv = system_with_k0.wavenumber.to(kx, "k0")
        assert k_min > float(conv.min())
        assert k_max < float(conv.max())
