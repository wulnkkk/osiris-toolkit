"""Tests for vis.tracks — TRACKS trajectory visualization."""

import numpy as np
import pytest


def _make_fake_tracks(ntracks=3, niter=100, seed=42):
    """Build a synthetic TrackData with x1,x2,x3,p1,p2,p3,ene,time."""
    from osiris_toolkit.sim.diagnostics import TrackData

    rng = np.random.default_rng(seed)
    quants = ["time", "x1", "x2", "x3", "p1", "p2", "p3", "ene"]
    tracks = []
    for _ in range(ntracks):
        n = rng.integers(niter // 2, niter)
        t = np.linspace(0, 10, n)
        data = np.column_stack([
            t,
            np.cumsum(rng.normal(0, 0.1, n)),   # x1: random walk
            np.cumsum(rng.normal(0, 0.1, n)),   # x2
            np.cumsum(rng.normal(0, 0.05, n)),  # x3
            rng.normal(0, 1, n),                # p1
            rng.normal(0, 1, n),                # p2
            rng.normal(0, 1, n),                # p3
            np.abs(rng.normal(5, 2, n)),        # ene
        ])
        tracks.append(data)
    return TrackData(tracks=tracks, quants=quants, niter=sum(len(t) for t in tracks))


class TestPlotTracksOrbit:
    """Test plot_tracks_orbit."""

    def test_saves_to_file(self, tmp_path):
        """plot_tracks_orbit saves a PNG."""
        from osiris_toolkit.vis.tracks import plot_tracks_orbit

        td = _make_fake_tracks()
        out = tmp_path / "orbit.png"
        result = plot_tracks_orbit(td, "x1-x2", output=str(out))
        assert result is not None
        assert out.exists()

    def test_invalid_proj_raises(self):
        """Raises ValueError for invalid projection name."""
        from osiris_toolkit.vis.tracks import plot_tracks_orbit
        from osiris_toolkit.sim.diagnostics import TrackData

        td = TrackData(tracks=[], quants=[], niter=0)
        with pytest.raises(ValueError, match="Invalid projection"):
            plot_tracks_orbit(td, "invalid-proj")


class TestPlotTracksEnergy:
    """Test plot_tracks_energy."""

    def test_saves_to_file_individual(self, tmp_path):
        """plot_tracks_energy saves per-track energy curves."""
        from osiris_toolkit.vis.tracks import plot_tracks_energy

        td = _make_fake_tracks()
        out = tmp_path / "energy_tracks.png"
        result = plot_tracks_energy(td, per_track=True, output=str(out))
        assert result is not None
        assert out.exists()

    def test_saves_to_file_mean(self, tmp_path):
        """plot_tracks_energy saves mean±std energy with fill_between."""
        from osiris_toolkit.vis.tracks import plot_tracks_energy

        td = _make_fake_tracks()
        out = tmp_path / "energy_mean.png"
        result = plot_tracks_energy(td, per_track=False, output=str(out))
        assert result is not None
        assert out.exists()

    def test_no_ene_raises(self):
        """Raises ValueError when 'ene' is not in quants."""
        from osiris_toolkit.vis.tracks import plot_tracks_energy
        from osiris_toolkit.sim.diagnostics import TrackData

        td = TrackData(tracks=[], quants=["time", "x1"], niter=0)
        with pytest.raises(ValueError, match="not found in track"):
            plot_tracks_energy(td)


class TestPlotTracksField:
    """Test plot_tracks_field."""

    def test_saves_to_file(self, tmp_path):
        """plot_tracks_field saves field-along-track plot."""
        from osiris_toolkit.vis.tracks import plot_tracks_field

        td = _make_fake_tracks()
        out = tmp_path / "field_along.png"
        result = plot_tracks_field(td, "p1", vs="time", output=str(out))
        assert result is not None
        assert out.exists()
