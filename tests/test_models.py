"""Smoke tests for _models.py — data classes are correctly importable and usable."""
import numpy as np

from osiris_toolkit._models import (
    Field,
    GridAxis,
    GridData,
    HistoryData,
    ParticleData,
    PhasespaceData,
    TimingsData,
)


class TestGridAxis:
    def test_defaults(self):
        ax = GridAxis()
        assert ax.name == ""
        assert ax.npoints == 0

    def test_coordinate_conversion(self):
        ax = GridAxis(name="x1", min=0.0, max=10.0, npoints=11)
        assert ax.index_to_value(0) == 0.0
        assert ax.index_to_value(10) == 10.0
        assert ax.value_to_index(5.0) == 5.0


class TestField:
    def test_basic(self):
        f = Field(data=np.arange(10.0), iteration=5, time=1.0)
        assert f.ndim == 1
        assert f.shape == (10,)
        assert f.iteration == 5

    def test_arithmetic(self):
        f1 = Field(data=np.array([1.0, 2.0, 3.0]))
        f2 = Field(data=np.array([4.0, 5.0, 6.0]))
        result = f1 + f2
        assert isinstance(result, Field)
        np.testing.assert_array_equal(result.data, [5.0, 7.0, 9.0])

    def test_scalar_mul(self):
        f = Field(data=np.array([1.0, 2.0, 3.0]))
        result = f * 2.0
        np.testing.assert_array_equal(result.data, [2.0, 4.0, 6.0])

    def test_slicing(self):
        f = Field(data=np.arange(20.0).reshape(4, 5))
        sub = f[1:3, 1:4]
        assert sub.shape == (2, 3)


class TestParticleData:
    def test_basic(self):
        pd = ParticleData(
            data={"x1": np.array([1.0, 2.0, 3.0])},
            nparts=3, iteration=0, label="electrons",
        )
        assert len(pd) == 3

    def test_filter(self):
        pd = ParticleData(
            data={"x1": np.array([1.0, 5.0, 3.0])},
            nparts=3,
        )
        filtered = pd.filter("x1 > 2")
        assert filtered.nparts == 2

    def test_compress(self):
        pd = ParticleData(
            data={"x1": np.array([1.0, 2.0, 3.0])},
            nparts=3,
        )
        compressed = pd.compress()
        assert compressed.nparts == 3
        assert compressed.data["x1"].flags["C_CONTIGUOUS"]


class TestGridDataAlias:
    def test_griddata_is_field(self):
        assert GridData is Field


class TestOtherDataClasses:
    def test_phasespace_data(self):
        ps = PhasespaceData(data=np.zeros((10, 10)), deposited_quantity="charge")
        assert ps.deposited_quantity == "charge"

    def test_history_data(self):
        hd = HistoryData(columns=["time", "energy"], data={"time": np.array([0, 1])})
        assert hd.columns == ["time", "energy"]

    def test_timings_data(self):
        td = TimingsData(events=["push", "solve"], columns=["Total [s]"])
        assert len(td.events) == 2
