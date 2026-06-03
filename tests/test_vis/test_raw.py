"""Tests for vis.raw — RAW particle visualization."""

import numpy as np
import pytest

from osiris_toolkit.exceptions import DataNotFoundError


def _make_fake_raw(nparts=1000, seed=42):
    """Build a synthetic ParticleData for testing."""
    from osiris_toolkit.sim.diagnostics import ParticleData

    rng = np.random.default_rng(seed)
    return ParticleData(
        data={
            "x1": rng.uniform(0, 10, nparts),
            "x2": rng.uniform(0, 10, nparts),
            "x3": rng.uniform(0, 10, nparts),
            "p1": rng.normal(0, 1, nparts),
            "p2": rng.normal(0, 0.5, nparts),
            "p3": rng.normal(0, 1, nparts),
            "ene": rng.exponential(1, nparts) + 0.1,
            "q": rng.choice([-1.0, 1.0], nparts),
        },
        nparts=nparts,
        iteration=50,
        time=10.0,
        label="electrons",
    )


class TestPlotRawScatter:
    """Test plot_raw_scatter."""

    def test_saves_to_file(self, tmp_path):
        """plot_raw_scatter saves a PNG file."""
        from osiris_toolkit.vis.raw import plot_raw_scatter

        raw = _make_fake_raw()
        out = tmp_path / "scatter.png"
        result = plot_raw_scatter(raw, "x1", "x2", output=str(out))
        assert result is not None
        assert out.exists()

    def test_color_by_energy(self, tmp_path):
        """Scatter with color_by saves correctly."""
        from osiris_toolkit.vis.raw import plot_raw_scatter

        raw = _make_fake_raw()
        out = tmp_path / "scatter_color.png"
        plot_raw_scatter(raw, "x1", "x2", color_by="ene", output=str(out))
        assert out.exists()


class TestPlotRawMomentum:
    """Test plot_raw_momentum."""

    def test_saves_to_file(self, tmp_path):
        """plot_raw_momentum saves a PNG with 4-panel layout."""
        from osiris_toolkit.vis.raw import plot_raw_momentum

        raw = _make_fake_raw()
        out = tmp_path / "momentum.png"
        result = plot_raw_momentum(raw, output=str(out))
        assert result is not None
        assert out.exists()


class TestPlotRawPhasespace:
    """Test plot_raw_phasespace."""

    def test_saves_to_file(self, tmp_path):
        """plot_raw_phasespace saves a PNG."""
        from osiris_toolkit.vis.raw import plot_raw_phasespace

        raw = _make_fake_raw()
        out = tmp_path / "phasespace.png"
        result = plot_raw_phasespace(raw, "x1", "p1", output=str(out))
        assert result is not None
        assert out.exists()


class TestPlotRawEnergySpectrum:
    """Test plot_raw_energy_spectrum."""

    def test_saves_to_file(self, tmp_path):
        """plot_raw_energy_spectrum saves a PNG."""
        from osiris_toolkit.vis.raw import plot_raw_energy_spectrum

        raw = _make_fake_raw()
        out = tmp_path / "energy_spectrum.png"
        result = plot_raw_energy_spectrum(raw, output=str(out))
        assert result is not None
        assert out.exists()

    def test_empty_data_raises(self):
        """Raises ValueError when particle data has no energy."""
        from osiris_toolkit.sim.diagnostics import ParticleData
        from osiris_toolkit.vis.raw import plot_raw_energy_spectrum

        raw = ParticleData(data={}, nparts=0)
        with pytest.raises(DataNotFoundError, match="No energy"):
            plot_raw_energy_spectrum(raw)
