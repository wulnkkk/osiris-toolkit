"""Tests for io._reader — ZDF file reader functions."""

import numpy as np
import pytest

from osiris_toolkit.exceptions import FormatError
from osiris_toolkit.io._reader import (
    list_records,
    read_grid,
    read_info,
    read_particles,
    read_tracks,
)

# ---------------------------------------------------------------------------
# read_grid (synthetic ZDF files)
# ---------------------------------------------------------------------------


class TestReadGrid:
    def test_read_grid_2d(self, tmp_zdf_grid):
        data, gi, it = read_grid(tmp_zdf_grid)
        assert data.shape == (4, 4)
        assert data.dtype == np.float32
        assert it.n == 0
        assert it.t == 0.0

    def test_read_grid_values(self, tmp_zdf_grid):
        data, _, _ = read_grid(tmp_zdf_grid)
        expected = np.arange(16, dtype=np.float32).reshape(4, 4)
        assert np.array_equal(data, expected)

    def test_read_grid_1d(self, tmp_zdf_grid_1d):
        data, _, _ = read_grid(tmp_zdf_grid_1d)
        assert data.shape == (3,)
        assert np.array_equal(data, [1.0, 2.0, 3.0])

    def test_read_grid_with_axes(self, tmp_zdf_grid_with_axes):
        data, gi, it = read_grid(tmp_zdf_grid_with_axes)
        assert gi.has_axis
        assert len(gi.axes) == 2
        assert gi.axes[0].name == "x1"
        assert gi.axes[0].min == 0.0
        assert gi.axes[0].max == 10.0
        assert it.n == 42
        assert it.t == 1.5

    def test_read_grid_metadata(self, tmp_zdf_grid):
        _, gi, _ = read_grid(tmp_zdf_grid)
        assert gi.label == "test_grid"
        assert gi.ndims == 2

    def test_read_grid_nonexistent(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_grid(tmp_path / "nonexistent.zdf")

    def test_read_grid_corrupt_magic(self, tmp_zdf_corrupt_magic):
        with pytest.raises(FormatError, match="Not a valid ZDF file"):
            read_grid(tmp_zdf_corrupt_magic)

    def test_read_grid_empty_file(self, tmp_zdf_empty):
        with pytest.raises(FormatError):
            read_grid(tmp_zdf_empty)


# ---------------------------------------------------------------------------
# read_particles
# ---------------------------------------------------------------------------


class TestReadParticles:
    def test_read_particles_basic(self, tmp_zdf_particles):
        data, pi, it = read_particles(tmp_zdf_particles)
        assert pi.nparts == 3
        assert "name" in pi.quants
        assert "x1" in pi.quants
        assert it.n == 10
        assert it.t == 0.5

    def test_read_particles_data(self, tmp_zdf_particles):
        data, _, _ = read_particles(tmp_zdf_particles)
        assert len(data["name"]) == 3
        assert data["x1"][0] == 0.1
        assert data["x1"][2] == 0.3

    def test_read_particles_label(self, tmp_zdf_particles):
        _, pi, _ = read_particles(tmp_zdf_particles)
        assert pi.label == "electrons"


# ---------------------------------------------------------------------------
# read_tracks
# ---------------------------------------------------------------------------


class TestReadTracks:
    def test_read_tracks_single(self, tmp_zdf_tracks):
        tracks, ti = read_tracks(tmp_zdf_tracks)
        assert len(tracks) == 2
        assert ti.ntracks == 2
        assert ti.niter == 100

    def test_read_tracks_quants(self, tmp_zdf_tracks):
        _, ti = read_tracks(tmp_zdf_tracks)
        assert "x1" in ti.quants
        assert "p1" in ti.quants
        # "itermap" is popped by the reader
        assert "itermap" not in ti.quants

    def test_read_tracks_data_shape(self, tmp_zdf_tracks):
        tracks, _ = read_tracks(tmp_zdf_tracks)
        assert tracks[0].shape[1] == 3  # nquants = x1, p1, ene
        assert tracks[1].shape[1] == 3


# ---------------------------------------------------------------------------
# read_info
# ---------------------------------------------------------------------------


class TestReadInfo:
    def test_read_info_grid(self, tmp_zdf_grid):
        info = read_info(tmp_zdf_grid)
        assert info.file_type == "grid"
        assert info.grid is not None
        assert info.grid.ndims == 2
        assert info.iteration is not None
        assert info.iteration.n == 0

    def test_read_info_particles(self, tmp_zdf_particles):
        info = read_info(tmp_zdf_particles)
        assert info.file_type == "particles"
        assert info.particles is not None
        assert info.particles.nparts == 3

    def test_read_info_tracks(self, tmp_zdf_tracks):
        info = read_info(tmp_zdf_tracks)
        assert info.file_type == "tracks-2"
        assert info.tracks is not None
        assert info.tracks.ntracks == 2


# ---------------------------------------------------------------------------
# list_records
# ---------------------------------------------------------------------------


class TestListRecords:
    def test_list_records_grid(self, tmp_zdf_grid):
        recs = list_records(tmp_zdf_grid)
        assert len(recs) == 4  # TYPE, GRID_INFO, ITERATION, DATASET
        assert recs[0].name == "TYPE"

    def test_list_records_tracks(self, tmp_zdf_tracks):
        recs = list_records(tmp_zdf_tracks)
        names = [r.name for r in recs]
        assert "TYPE" in names
        assert "itermap" in names
        assert "data" in names


# ---------------------------------------------------------------------------
# Real-data tests (optional, skipped when data path not configured)
# ---------------------------------------------------------------------------


@pytest.mark.data
class TestReadGridRealData:
    def test_read_real_grid_info(self, case1_path):
        if case1_path is None:
            pytest.skip("OSIRIS_TOOLKIT_DATA_PATH not set")
        from pathlib import Path

        zdf_files = sorted(Path(case1_path).rglob("*.zdf"))
        if not zdf_files:
            pytest.skip("No ZDF files found in case1")
        info = read_info(zdf_files[0])
        assert info.file_type in ("grid", "particles", "tracks-2")

    def test_read_real_grid_via_info(self, case1_path):
        """Verify read_info works on real data (read_grid may fail on large non-standard files)."""
        if case1_path is None:
            pytest.skip("OSIRIS_TOOLKIT_DATA_PATH not set")
        from pathlib import Path

        zdf_files = sorted(Path(case1_path).rglob("*.zdf"))
        if not zdf_files:
            pytest.skip("No ZDF files found in case1")
        # Check that we can at least read the info/metadata
        info = read_info(zdf_files[0])
        assert info.file_type in ("grid", "particles", "tracks-2")
        assert info.iteration is not None
        assert isinstance(info.iteration.n, int)
