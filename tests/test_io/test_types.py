"""Tests for io._types — ZDF metadata dataclasses."""

from osiris_toolkit.io._types import (
    ZdfAxis,
    ZdfFileInfo,
    ZdfGridInfo,
    ZdfIteration,
    ZdfPartInfo,
    ZdfRecord,
    ZdfTrackInfo,
)


class TestZdfRecord:
    def test_creation(self):
        r = ZdfRecord(pos=0, id=0x00030000, name="TYPE", length=12)
        assert r.pos == 0
        assert r.name == "TYPE"
        assert r.length == 12

    def test_default_invalid(self):
        r = ZdfRecord(pos=0, id=0, name="", length=0)
        assert r.name == ""


class TestZdfIteration:
    def test_creation(self):
        it = ZdfIteration(n=42, t=1.5, tunits="1/\\omega_p")
        assert it.n == 42
        assert it.t == 1.5
        assert it.tunits == "1/\\omega_p"


class TestZdfAxis:
    def test_defaults(self):
        ax = ZdfAxis()
        assert ax.name == ""
        assert ax.axis_type == 0
        assert ax.min == 0.0
        assert ax.max == 0.0

    def test_full(self):
        ax = ZdfAxis(name="x1", axis_type=0, min=0.0, max=10.0, label="x1", units="c/\\omega_p")
        assert ax.label == "x1"
        assert ax.units == "c/\\omega_p"


class TestZdfGridInfo:
    def test_defaults(self):
        gi = ZdfGridInfo()
        assert gi.ndims == 0
        assert gi.nx == []
        assert gi.has_axis is False
        assert gi.axes == []

    def test_with_dims(self):
        gi = ZdfGridInfo(ndims=2, nx=[32, 32], label="e1", units="sim")
        assert gi.ndims == 2
        assert gi.nx == [32, 32]

    def test_with_axes(self):
        ax = ZdfAxis(name="x1", axis_type=0, min=0.0, max=1.0)
        gi = ZdfGridInfo(ndims=1, nx=[32], has_axis=True, axes=[ax])
        assert gi.has_axis is True
        assert len(gi.axes) == 1
        assert gi.axes[0].name == "x1"


class TestZdfPartInfo:
    def test_defaults(self):
        pi = ZdfPartInfo()
        assert pi.nparts == 0
        assert pi.nquants == 0
        assert pi.quants == []

    def test_full(self):
        pi = ZdfPartInfo(
            label="electrons", nparts=1000, nquants=3,
            quants=["x1", "x2", "p1"],
            qlabels={"x1": "x1", "x2": "x2", "p1": "p1"},
            qunits={"x1": "c/\\omega_p", "x2": "c/\\omega_p", "p1": "m_e c"},
        )
        assert pi.nparts == 1000
        assert pi.quants == ["x1", "x2", "p1"]
        assert pi.qlabels["x1"] == "x1"


class TestZdfTrackInfo:
    def test_defaults(self):
        ti = ZdfTrackInfo()
        assert ti.ntracks == 0
        assert ti.ndump == 0
        assert ti.niter == 0

    def test_full(self):
        ti = ZdfTrackInfo(
            label="test", ntracks=2, ndump=3, niter=100, nquants=3,
            quants=["x1", "p1", "ene"],
            qlabels=["x1", "p1", "ene"],
            qunits=["c/\\omega_p", "m_e c", "m_e c^2"],
        )
        assert ti.ntracks == 2
        assert ti.quants == ["x1", "p1", "ene"]


class TestZdfFileInfo:
    def test_defaults(self):
        fi = ZdfFileInfo()
        assert fi.file_type == ""
        assert fi.grid is None
        assert fi.particles is None
        assert fi.tracks is None
        assert fi.iteration is None

    def test_grid_info_composite(self):
        gi = ZdfGridInfo(ndims=2, nx=[4, 4])
        it = ZdfIteration(n=0, t=0.0, tunits="1/\\omega_p")
        fi = ZdfFileInfo(file_type="grid", grid=gi, iteration=it)
        assert fi.file_type == "grid"
        assert fi.grid.ndims == 2
        assert fi.iteration.n == 0

    def test_simulation_info_default_none(self):
        fi = ZdfFileInfo()
        assert fi.simulation_info is None

    def test_simulation_info_with_value(self):
        fi = ZdfFileInfo(file_type="grid", simulation_info="OSIRIS v1.0.0\nCompiled: 2025-01-01")
        assert fi.file_type == "grid"
        assert "OSIRIS" in fi.simulation_info
