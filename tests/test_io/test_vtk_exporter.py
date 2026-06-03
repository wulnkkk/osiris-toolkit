"""Tests for VTK export."""

import numpy as np
import pytest

pyevtk = pytest.importorskip("pyevtk", reason="pyevtk not installed")


class TestVTKExport:
    """Test to_vtk() function."""

    def test_export_1d_to_vtr(self, tmp_path):
        """1D Field exports to .vtr."""
        from osiris_toolkit.io.vtk_exporter import to_vtk
        from osiris_toolkit.sim.diagnostics import Field

        f = Field(
            data=np.random.rand(10),
            axes=[],
            iteration=0,
            time=0.0,
            label="e1",
        )
        out = tmp_path / "test"
        result = to_vtk(f, str(out))
        assert result.name.startswith("test")
        assert result.exists()
        assert result.stat().st_size > 0

    def test_export_2d_to_vts(self, tmp_path):
        """2D Field exports to .vts."""
        from osiris_toolkit.io.vtk_exporter import to_vtk
        from osiris_toolkit.sim.diagnostics import Field

        f = Field(
            data=np.random.rand(8, 8),
            axes=[],
            iteration=0,
            time=0.0,
            label="e1",
        )
        out = tmp_path / "test2d"
        result = to_vtk(f, str(out))
        assert result.exists()
        assert result.stat().st_size > 0

    def test_field_to_vtk_method(self, tmp_path):
        """Field.to_vtk() convenience method works."""
        from osiris_toolkit.sim.diagnostics import Field

        f = Field(
            data=np.random.rand(8, 8),
            axes=[],
            iteration=0,
            time=0.0,
            label="e1",
        )
        out = tmp_path / "via_method"
        result = f.to_vtk(str(out))
        assert result.exists()
