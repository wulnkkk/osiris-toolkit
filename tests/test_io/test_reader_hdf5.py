"""Tests for HDF5 reader — _reader_hdf5.py."""

import numpy as np
import pytest

from osiris_toolkit.exceptions import FormatError

h5py = pytest.importorskip("h5py", reason="h5py not installed")


def _make_grid_h5(
    path,
    nx=(10,),
    ndims=1,
    label="e1",
    units="sim",
    it_n=0,
    it_t=0.0,
    it_tunits="1/\\omega_p",
    axis_info=None,
    sim_info=None,
):
    """Create a minimal OSIRIS grid HDF5 file."""
    with h5py.File(path, "w") as f:
        f.attrs["TYPE"] = np.bytes_("grid")
        if sim_info:
            f.attrs["SIMULATION"] = np.bytes_(sim_info)

        grp = f.create_group("GRID_INFO")
        grp.attrs["NDIMS"] = ndims
        grp.create_dataset("NX", data=np.array(nx, dtype="<u8"))
        grp.attrs["LABEL"] = np.bytes_(label)
        grp.attrs["UNITS"] = np.bytes_(units)

        if axis_info:
            for i, ax in enumerate(axis_info):
                ag = grp.create_group(f"AXIS{i + 1}")
                ag.attrs["NAME"] = np.bytes_(ax.get("name", f"x{i + 1}"))
                ag.attrs["TYPE"] = ax.get("type", 0)
                ag.attrs["MIN"] = ax.get("min", 0.0)
                ag.attrs["MAX"] = ax.get("max", 1.0)
                ag.attrs["LABEL"] = np.bytes_(ax.get("label", ""))
                ag.attrs["UNITS"] = np.bytes_(ax.get("units", ""))

        ig = f.create_group("ITERATION")
        ig.attrs["N"] = it_n
        ig.attrs["T"] = it_t
        ig.attrs["TUNITS"] = np.bytes_(it_tunits)

        data = np.arange(np.prod(nx), dtype="<f4").reshape(nx[::-1])
        f.create_dataset("DATA", data=data)


def _make_particles_h5(
    path, nparts=100, quants=None, it_n=0, it_t=0.0, it_tunits="1/\\omega_p", label="electrons", sim_info=None
):
    """Create a minimal OSIRIS particles HDF5 file."""
    with h5py.File(path, "w") as f:
        f.attrs["TYPE"] = np.bytes_("particles")
        if sim_info:
            f.attrs["SIMULATION"] = np.bytes_(sim_info)

        if quants is None:
            quants = {"x1": {"label": "x1", "units": "c/\\omega_p"}}

        pi = f.create_group("PART_INFO")
        pi.attrs["LABEL"] = np.bytes_(label)
        pi.attrs["NPARTS"] = nparts
        pi.attrs["NQUANTS"] = len(quants)

        qg = pi.create_group("QUANTS")
        for qname, qinfo in quants.items():
            qgrp = qg.create_group(qname)
            qgrp.attrs["LABEL"] = np.bytes_(qinfo["label"])
            qgrp.attrs["UNITS"] = np.bytes_(qinfo["units"])

        ig = f.create_group("ITERATION")
        ig.attrs["N"] = it_n
        ig.attrs["T"] = it_t
        ig.attrs["TUNITS"] = np.bytes_(it_tunits)

        for qname in quants:
            f.create_dataset(qname, data=np.random.rand(nparts).astype("<f4"))


def _make_tracks_h5(path, ntracks=2, ndump=3, niter=10, quants=None, sim_info=None):
    """Create a minimal OSIRIS tracks HDF5 file."""
    with h5py.File(path, "w") as f:
        f.attrs["TYPE"] = np.bytes_("tracks")
        if sim_info:
            f.attrs["SIMULATION"] = np.bytes_(sim_info)

        if quants is None:
            quants = ["q", "ene", "x1", "x2", "x3", "p1", "p2", "p3"]

        ti = f.create_group("TRACK_INFO")
        ti.attrs["NTRACKS"] = ntracks
        ti.attrs["NDUMP"] = ndump
        ti.attrs["NITER"] = niter
        ti.attrs["NQUANTS"] = len(quants)

        qg = ti.create_group("QUANTS")
        for q in quants:
            qgrp = qg.create_group(q)
            qgrp.attrs["LABEL"] = np.bytes_(q)
            qgrp.attrs["UNITS"] = np.bytes_("sim")

        itermap = np.array([[1, 3], [1, 2], [2, 4], [2, 1]], dtype="<i4")
        f.create_dataset("ITERMAP", data=itermap)

        total_points = itermap[:, 1].sum()
        data = np.random.rand(total_points, len(quants)).astype("<f4")
        f.create_dataset("DATA", data=data)


class TestReadInfoGrid:
    def test_read_info_grid_basic(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_info

        path = tmp_path / "test.h5"
        _make_grid_h5(path, nx=(10,), ndims=1, label="e1", units="m_e c \\omega_p e^{-1}", it_n=50, it_t=5.0)
        info = read_info(str(path))
        assert info.file_type == "grid"
        assert info.grid is not None
        assert info.grid.ndims == 1
        assert info.grid.nx == [10]
        assert info.grid.label == "e1"
        assert info.grid.units == "m_e c \\omega_p e^{-1}"
        assert info.iteration is not None
        assert info.iteration.n == 50
        assert info.iteration.t == 5.0

    def test_read_info_grid_with_simulation(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_info

        path = tmp_path / "test.h5"
        _make_grid_h5(path, nx=(4, 4), ndims=2, sim_info="OSIRIS v1.0.0\nCompiled: 2024")
        info = read_info(str(path))
        assert info.file_type == "grid"
        assert info.simulation_info == "OSIRIS v1.0.0\nCompiled: 2024"

    def test_read_info_grid_with_axes(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_info

        path = tmp_path / "test.h5"
        axis_info = [
            {"name": "x1", "type": 0, "min": 0.0, "max": 10.0, "label": "x_1", "units": "c/\\omega_p"},
        ]
        _make_grid_h5(path, nx=(10,), ndims=1, axis_info=axis_info)
        info = read_info(str(path))
        assert info.grid.has_axis is True
        assert len(info.grid.axes) == 1
        assert info.grid.axes[0].name == "x1"
        assert info.grid.axes[0].min == 0.0
        assert info.grid.axes[0].max == 10.0


class TestReadGrid:
    def test_read_grid_1d(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_grid

        path = tmp_path / "test.h5"
        _make_grid_h5(path, nx=(10,), ndims=1, label="e1")
        data, gi, it = read_grid(str(path))
        assert data.shape == (10,)
        assert gi.ndims == 1
        assert gi.nx == [10]
        assert it.n == 0

    def test_read_grid_2d(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_grid

        path = tmp_path / "test.h5"
        _make_grid_h5(path, nx=(8, 6), ndims=2)
        data, gi, it = read_grid(str(path))
        assert data.shape == (6, 8)
        assert gi.ndims == 2
        assert gi.nx == [8, 6]


class TestReadParticles:
    def test_read_particles_basic(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_particles

        path = tmp_path / "test.h5"
        quants = {"x1": {"label": "x1", "units": "c/\\omega_p"}, "p1": {"label": "p1", "units": "m_e c"}}
        _make_particles_h5(path, nparts=50, quants=quants, it_n=10, it_t=1.0)
        data, pi, it = read_particles(str(path))
        assert pi.nparts == 50
        assert pi.nquants == 2
        assert set(pi.quants) == {"x1", "p1"}
        assert pi.qlabels["x1"] == "x1"
        assert "x1" in data
        assert "p1" in data
        assert len(data["x1"]) == 50
        assert it.n == 10
        assert it.t == 1.0

    def test_read_particles_empty(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_particles

        path = tmp_path / "test.h5"
        _make_particles_h5(path, nparts=0, quants={"x1": {"label": "x1", "units": "c/\\omega_p"}})
        data, pi, it = read_particles(str(path))
        assert pi.nparts == 0
        assert len(data["x1"]) == 0


class TestReadTracks:
    def test_read_tracks_basic(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_tracks

        path = tmp_path / "test.h5"
        qlist = ["q", "ene", "x1", "x2", "x3", "p1", "p2", "p3"]
        _make_tracks_h5(path, ntracks=2, ndump=3, niter=10, quants=qlist)
        tracks, ti = read_tracks(str(path))
        assert ti.ntracks == 2
        assert ti.nquants == 8
        assert len(tracks) == 2
        assert tracks[0].shape == (5, 8)
        assert tracks[1].shape == (5, 8)


class TestReadInfoParticles:
    def test_read_info_particles(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_info

        path = tmp_path / "test.h5"
        _make_particles_h5(
            path, nparts=200, label="ions", quants={"x1": {"label": "x1", "units": "c/\\omega_p"}}, it_n=5, it_t=0.5
        )
        info = read_info(str(path))
        assert info.file_type == "particles"
        assert info.particles is not None
        assert info.particles.nparts == 200
        assert info.particles.label == "ions"
        assert info.iteration is not None
        assert info.iteration.n == 5


class TestReadInfoTracks:
    def test_read_info_tracks(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_info

        path = tmp_path / "test.h5"
        _make_tracks_h5(path, ntracks=3, ndump=2, niter=20)
        info = read_info(str(path))
        assert info.file_type == "tracks"
        assert info.tracks is not None
        assert info.tracks.ntracks == 3
        assert info.tracks.nquants == 8


class TestListRecords:
    def test_list_records_grid(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import list_records

        path = tmp_path / "test.h5"
        _make_grid_h5(path, nx=(10,))
        records = list_records(str(path))
        assert len(records) > 0
        assert all(hasattr(r, "name") for r in records)


class TestErrorHandling:
    def test_not_hdf5_file(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_info

        path = tmp_path / "not_hdf5.h5"
        path.write_text("not an HDF5 file")
        with pytest.raises(FormatError, match="Not a valid HDF5 file"):
            read_info(str(path))

    def test_missing_type_attr(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_info

        path = tmp_path / "test.h5"
        with h5py.File(path, "w") as _f:
            pass
        with pytest.raises(FormatError, match="Missing TYPE attribute"):
            read_info(str(path))

    def test_unknown_file_type(self, tmp_path):
        from osiris_toolkit.io._reader_hdf5 import read_info

        path = tmp_path / "test.h5"
        with h5py.File(path, "w") as f:
            f.attrs["TYPE"] = np.bytes_("unknown_type")
        with pytest.raises(FormatError, match="Unknown HDF5 file type"):
            read_info(str(path))
