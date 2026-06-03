"""Tests for vis.energy plotting functions."""

import numpy as np

from osiris_toolkit.analysis._result_types import (
    EMDynamicsResult,
    EMSpectrumResult,
    PoyntingResult,
)


class TestPlotEnergyTimeline:
    """Test plot_energy_timeline with synthetic results."""

    def test_saves_to_file(self, tmp_path):
        """plot_energy_timeline saves a PNG file."""
        from osiris_toolkit.vis.energy import plot_energy_timeline

        results = [
            EMDynamicsResult(iteration=i, time=i * 0.1,
                             e2_total=float(i), b2_total=float(i * 2),
                             total=float(i * 3))
            for i in range(5)
        ]
        out = tmp_path / "energy.png"
        plot_energy_timeline(results, output=str(out))
        assert out.exists()


class TestPlotSpectrum:
    """Test plot_spectrum with synthetic data."""

    def test_saves_to_file(self, tmp_path):
        """plot_spectrum saves a PNG file."""
        from osiris_toolkit.vis.energy import plot_spectrum

        kx = np.fft.fftshift(np.fft.fftfreq(32, 0.1)) * 2 * np.pi
        result = EMSpectrumResult(
            quantity="e1", iteration=50, time=10.0,
            kx_k0=kx, ky_k0=kx,
            spectrum=np.random.rand(32, 32),
        )
        out = tmp_path / "spectrum.png"
        plot_spectrum(result, output=str(out))
        assert out.exists()


class TestPlotPoynting:
    """Test plot_poynting with synthetic data."""

    def test_saves_to_file(self, tmp_path):
        """plot_poynting saves a PNG file."""
        from osiris_toolkit.vis.energy import plot_poynting

        arr = np.random.randn(16, 16)
        result = PoyntingResult(iteration=50, time=10.0, s1=arr, s2=arr, s3=arr)
        out = tmp_path / "poynting.png"
        plot_poynting(result, component="s1", output=str(out))
        assert out.exists()
