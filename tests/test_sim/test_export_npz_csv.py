"""Tests for Field.to_npz/.to_csv and ParticleData.to_npz/.to_csv."""

import numpy as np


class TestFieldExport:
    """Test Field NPZ/CSV export."""

    def test_field_to_npz_1d(self, tmp_path):
        """to_npz saves 1D field data + metadata."""
        from osiris_toolkit.sim.diagnostics import Field

        f = Field(
            data=np.array([1.0, 2.0, 3.0]),
            axes=[],
            iteration=10,
            time=5.0,
            label="e1",
            units="norm",
        )
        out = tmp_path / "field.npz"
        result = f.to_npz(str(out))
        assert result == out
        assert out.exists()

        loaded = np.load(str(out))
        np.testing.assert_array_equal(loaded["data"], f.data)
        assert loaded["iteration"] == 10
        assert loaded["time"] == 5.0
        assert str(loaded["label"]) == "e1"
        assert str(loaded["units"]) == "norm"

    def test_field_to_csv_1d(self, tmp_path):
        """to_csv exports 1D field with index,value columns."""
        from osiris_toolkit.sim.diagnostics import Field

        f = Field(
            data=np.array([1.0, 2.0, 3.0]),
            axes=[],
            iteration=10,
            time=5.0,
            label="e1",
            units="norm",
        )
        out = tmp_path / "field.csv"
        result = f.to_csv(str(out))
        assert result == out
        assert out.exists()

        data = np.loadtxt(str(out), delimiter=",", skiprows=1)
        assert data.shape == (3, 2)  # index, value

    def test_field_to_csv_2d(self, tmp_path):
        """to_csv exports 2D field with x1,x2,value columns."""
        from osiris_toolkit.sim.diagnostics import Field

        f = Field(
            data=np.arange(6).reshape(2, 3).astype(float),
            axes=[],
            iteration=0,
            time=0.0,
            label="e1",
            units="",
        )
        out = tmp_path / "field2d.csv"
        f.to_csv(str(out))
        assert out.exists()

        data = np.loadtxt(str(out), delimiter=",", skiprows=1)
        assert data.shape == (6, 3)  # x1, x2, value


class TestParticleDataExport:
    """Test ParticleData NPZ/CSV export."""

    def test_particle_data_to_npz(self, tmp_path):
        """to_npz saves all particle arrays."""
        from osiris_toolkit.sim.diagnostics import ParticleData

        pd = ParticleData(
            data={
                "x1": np.array([0.1, 0.2]),
                "p1": np.array([1.0, 2.0]),
            },
            nparts=2,
            iteration=50,
            time=10.0,
            label="electrons",
        )
        out = tmp_path / "particles.npz"
        result = pd.to_npz(str(out))
        assert result == out
        assert out.exists()

        loaded = np.load(str(out))
        np.testing.assert_array_equal(loaded["x1"], pd.data["x1"])
        np.testing.assert_array_equal(loaded["p1"], pd.data["p1"])
        assert loaded["nparts"] == 2

    def test_particle_data_to_csv(self, tmp_path):
        """to_csv exports one-row-per-particle CSV."""
        from osiris_toolkit.sim.diagnostics import ParticleData

        pd = ParticleData(
            data={
                "x1": np.array([0.1, 0.2]),
                "ene": np.array([5.0, 10.0]),
            },
            nparts=2,
            iteration=50,
            time=10.0,
            label="electrons",
        )
        out = tmp_path / "particles.csv"
        result = pd.to_csv(str(out))
        assert result == out
        assert out.exists()

        data = np.loadtxt(str(out), delimiter=",", skiprows=1)
        assert data.shape == (2, 2)
