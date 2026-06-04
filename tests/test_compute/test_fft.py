"""Tests for compute.fft module."""

import numpy as np
import pytest

from osiris_toolkit.compute.fft import compute_k_space, spectral_power
from osiris_toolkit.exceptions import ShapeError


class TestComputeKSpace:
    """Tests for compute_k_space."""

    def test_basic_fft_shape(self):
        """Output arrays have correct shapes."""
        data = np.random.randn(64, 64)
        kx, ky, spectrum = compute_k_space(data, dx=0.1, dy=0.1)

        assert kx.shape == (64,)
        assert ky.shape == (64,)
        assert spectrum.shape == (64, 64)

    def test_kx_range(self):
        """kx values are symmetric around zero."""
        data = np.random.randn(32, 32)
        dx = 0.2
        kx, ky, _ = compute_k_space(data, dx=dx, dy=dx)

        # kx should be symmetric around 0
        assert abs(kx[len(kx) // 2]) < 0.1 * abs(kx[0])
        # kx max = pi / dx in angular wavenumber units (rad / (c/ω_p))
        expected_kmax = np.pi / dx
        assert kx[0] == pytest.approx(-expected_kmax, rel=0.01)

    def test_raises_on_1d(self):
        """1-D input raises ValueError."""
        data = np.random.randn(64)
        with pytest.raises(ShapeError, match="Expected 2-D"):
            compute_k_space(data, dx=0.1, dy=0.1)

    def test_monochromatic_wave(self):
        """A single sine wave -> peak at the expected k."""
        nx = ny = 128
        dx = dy = 0.1
        k_mode = 5  # mode number
        x = np.arange(nx) * dx
        _y = np.arange(ny) * dy
        data = np.sin(2 * np.pi * k_mode * x[:, None] / (nx * dx))

        kx, ky, spectrum = compute_k_space(data, dx, dy)

        # Find peak location
        idx = np.unravel_index(np.argmax(spectrum), spectrum.shape)
        k_peak_x = kx[idx[0]]
        expected_k = 2 * np.pi * k_mode / (nx * dx)
        assert abs(k_peak_x) == pytest.approx(expected_k, rel=0.02)


class TestSpectralPower:
    """Tests for spectral_power."""

    def test_power_is_spectrum_squared(self):
        """spectral_power returns |FFT|^2."""
        data = np.random.randn(32, 32)
        _, _, power = spectral_power(data, dx=0.1, dy=0.1)
        _, _, spectrum = compute_k_space(data, dx=0.1, dy=0.1)

        np.testing.assert_allclose(power, spectrum ** 2)
