"""Tests for compute.integrate module."""

import numpy as np
import pytest

from osiris_toolkit.compute.integrate import line_integrate, mask_energy, trapz_2d
from osiris_toolkit.units.converter import UnitSystem
from osiris_toolkit.units.params import SimulationParams


@pytest.fixture
def kspace_system():
    """UnitSystem with omega0_norm=1 so k0 units equal normalized units."""
    params = SimulationParams(omega_p0=3.55e15, omega0_norm=1.0)
    return UnitSystem(3.55e15, params=params)


class TestMaskEnergy:
    """Tests for mask_energy."""

    def test_full_mask_equals_total(self, kspace_system):
        """Summing over a mask covering all k-space equals total |spectrum|^2."""
        spectrum = np.ones((32, 32))
        kx = np.fft.fftshift(np.fft.fftfreq(32, 0.1)) * 2 * np.pi
        ky = np.fft.fftshift(np.fft.fftfreq(32, 0.1)) * 2 * np.pi

        total = mask_energy(
            spectrum, kx, ky,
            kx_range=(-100, 100),
            ky_range=(-100, 100),
            system=kspace_system,
        )
        assert total == pytest.approx(float(np.sum(spectrum ** 2)))

    def test_empty_mask_zero(self, kspace_system):
        """A mask covering no k-space returns 0."""
        spectrum = np.ones((16, 16))
        kx = np.fft.fftshift(np.fft.fftfreq(16, 0.1)) * 2 * np.pi
        ky = np.fft.fftshift(np.fft.fftfreq(16, 0.1)) * 2 * np.pi

        total = mask_energy(
            spectrum, kx, ky,
            kx_range=(1e10, 1e11),
            ky_range=(1e10, 1e11),
            system=kspace_system,
        )
        assert total == 0.0


class TestTrapz2D:
    """Tests for trapz_2d."""

    def test_constant(self):
        """Integral of a constant field."""
        data = np.ones((10, 10))
        result = trapz_2d(data, dx=1.0, dy=1.0)
        assert result == pytest.approx(81.0)  # (10-1)*(10-1)

    def test_different_spacing(self):
        """dx != dy handled correctly."""
        data = np.ones((10, 10))
        result = trapz_2d(data, dx=0.5, dy=2.0)
        assert result == pytest.approx(81.0)


class TestLineIntegrate:
    """Tests for line_integrate."""

    def test_integrate_over_x(self):
        """Integrate over axis 1 -> 1-D profile along axis 0."""
        data = np.ones((5, 10))
        result = line_integrate(data, axis=0)
        assert result.shape == (5,)
        np.testing.assert_allclose(result, 10.0)

    def test_integrate_over_y(self):
        """Integrate over axis 0 -> 1-D profile along axis 1."""
        data = np.ones((5, 10))
        result = line_integrate(data, axis=1)
        assert result.shape == (10,)
        np.testing.assert_allclose(result, 5.0)

    def test_1d_data_unchanged(self):
        """1-D data returns unchanged."""
        data = np.array([1.0, 2.0, 3.0])
        result = line_integrate(data, axis=0)
        np.testing.assert_array_equal(result, data)
