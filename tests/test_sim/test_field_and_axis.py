"""Tests for sim.diagnostics — GridAxis methods and Field operators."""
import numpy as np
import pytest

from osiris_toolkit.sim.diagnostics import Field, GridAxis, GridData


class TestGridAxis:
    def test_value_to_index(self):
        ax = GridAxis(name="x1", min=0.0, max=10.0, npoints=11)
        assert ax.value_to_index(0.0) == 0.0
        assert ax.value_to_index(10.0) == 10.0
        assert ax.value_to_index(5.0) == 5.0

    def test_value_to_index_raises_without_npoints(self):
        ax = GridAxis(min=0.0, max=10.0)
        with pytest.raises(ValueError, match="npoints"):
            ax.value_to_index(5.0)

    def test_index_to_value(self):
        ax = GridAxis(name="x1", min=0.0, max=10.0, npoints=11)
        assert ax.index_to_value(0) == 0.0
        assert ax.index_to_value(10) == 10.0
        assert ax.index_to_value(5) == 5.0

    def test_index_to_value_single_cell(self):
        ax = GridAxis(min=0.0, max=1.0, npoints=2)
        assert ax.index_to_value(0) == 0.0
        assert ax.index_to_value(1) == 1.0

    def test_index_to_value_raises_without_npoints(self):
        ax = GridAxis(min=0.0, max=10.0)
        with pytest.raises(ValueError, match="npoints"):
            ax.index_to_value(5.0)

    def test_npoints_default_zero(self):
        ax = GridAxis()
        assert ax.npoints == 0


class TestFieldOperators:
    def test_add_scalar(self):
        f = Field(data=np.array([1.0, 2.0, 3.0]))
        result = f + 2.0
        assert isinstance(result, Field)
        np.testing.assert_array_equal(result.data, np.array([3.0, 4.0, 5.0]))

    def test_add_field(self):
        f1 = Field(data=np.array([1.0, 2.0]))
        f2 = Field(data=np.array([3.0, 4.0]))
        result = f1 + f2
        np.testing.assert_array_equal(result.data, np.array([4.0, 6.0]))

    def test_add_field_shape_mismatch(self):
        f1 = Field(data=np.array([1.0, 2.0]))
        f2 = Field(data=np.array([1.0, 2.0, 3.0]))
        with pytest.raises(ValueError, match="Shape mismatch"):
            f1 + f2

    def test_sub_scalar(self):
        f = Field(data=np.array([5.0, 3.0]))
        result = f - 1.0
        np.testing.assert_array_equal(result.data, np.array([4.0, 2.0]))

    def test_sub_field(self):
        f1 = Field(data=np.array([5.0, 3.0]))
        f2 = Field(data=np.array([1.0, 2.0]))
        result = f1 - f2
        np.testing.assert_array_equal(result.data, np.array([4.0, 1.0]))

    def test_mul_scalar(self):
        f = Field(data=np.array([1.0, 2.0]))
        result = f * 3.0
        np.testing.assert_array_equal(result.data, np.array([3.0, 6.0]))

    def test_mul_field(self):
        f1 = Field(data=np.array([2.0, 3.0]))
        f2 = Field(data=np.array([4.0, 5.0]))
        result = f1 * f2
        np.testing.assert_array_equal(result.data, np.array([8.0, 15.0]))

    def test_truediv_scalar(self):
        f = Field(data=np.array([6.0, 3.0]))
        result = f / 3.0
        np.testing.assert_array_equal(result.data, np.array([2.0, 1.0]))

    def test_truediv_field(self):
        f1 = Field(data=np.array([6.0, 8.0]))
        f2 = Field(data=np.array([2.0, 4.0]))
        result = f1 / f2
        np.testing.assert_array_equal(result.data, np.array([3.0, 2.0]))

    def test_pow(self):
        f = Field(data=np.array([1.0, 2.0, 3.0]))
        result = f ** 2
        np.testing.assert_array_equal(result.data, np.array([1.0, 4.0, 9.0]))

    def test_neg(self):
        f = Field(data=np.array([1.0, -2.0]))
        result = -f
        np.testing.assert_array_equal(result.data, np.array([-1.0, 2.0]))

    def test_abs(self):
        f = Field(data=np.array([-1.0, 2.0, -3.0]))
        result = abs(f)
        np.testing.assert_array_equal(result.data, np.array([1.0, 2.0, 3.0]))

    def test_radd(self):
        f = Field(data=np.array([1.0, 2.0]))
        result = 10.0 + f
        np.testing.assert_array_equal(result.data, np.array([11.0, 12.0]))

    def test_rsub(self):
        f = Field(data=np.array([3.0, 4.0]))
        result = 10.0 - f
        np.testing.assert_array_equal(result.data, np.array([7.0, 6.0]))

    def test_rmul(self):
        f = Field(data=np.array([2.0, 3.0]))
        result = 4.0 * f
        np.testing.assert_array_equal(result.data, np.array([8.0, 12.0]))

    def test_operator_preserves_metadata(self):
        f = Field(data=np.array([1.0, 2.0]), iteration=42, time=3.5,
                  label="e1", units="sim")
        result = f + 1.0
        assert result.iteration == 42
        assert result.time == 3.5
        assert result.label == "e1"
        assert result.units == "sim"

    def test_operator_preserves_axes(self):
        ax = GridAxis(name="x1", min=0.0, max=1.0, npoints=2)
        f = Field(data=np.array([1.0, 2.0]), axes=[ax])
        result = f * 2.0
        assert len(result.axes) == 1
        assert result.axes[0].name == "x1"

    def test_copy_meta_does_not_share_axes(self):
        ax = GridAxis(name="x1", min=0.0, max=1.0, npoints=2)
        f1 = Field(data=np.array([1.0, 2.0]), axes=[ax])
        f2 = f1 + 1.0
        f2.axes[0].name = "modified"
        assert f1.axes[0].name == "x1"  # unchanged


class TestFieldProperties:
    def test_ndim(self):
        assert Field(data=np.array([1.0])).ndim == 1
        assert Field(data=np.zeros((3, 4))).ndim == 2

    def test_shape(self):
        assert Field(data=np.zeros((3, 4))).shape == (3, 4)

    def test_mean(self):
        f = Field(data=np.array([1.0, 2.0, 3.0]))
        assert f.mean() == 2.0

    def test_mean_with_axis(self):
        f = Field(data=np.array([[1.0, 2.0], [3.0, 4.0]]))
        result = f.mean(axis=0)
        np.testing.assert_array_equal(result, np.array([2.0, 3.0]))

    def test_std(self):
        f = Field(data=np.array([1.0, 1.0, 1.0]))
        assert f.std() == 0.0

    def test_std_with_axis(self):
        f = Field(data=np.array([[1.0, 2.0], [3.0, 4.0]]))
        result = f.std(axis=0)
        np.testing.assert_array_equal(result, np.array([1.0, 1.0]))


class TestFieldGetitem:
    def test_positional_slice_1d(self):
        f = Field(data=np.array([10.0, 20.0, 30.0, 40.0]),
                  axes=[GridAxis(name="x1", min=0.0, max=3.0, npoints=4)])
        result = f[1:3]
        assert isinstance(result, Field)
        np.testing.assert_array_equal(result.data, np.array([20.0, 30.0]))

    def test_positional_slice_2d(self):
        f = Field(data=np.arange(16.0).reshape(4, 4))
        result = f[1:3, 1:3]
        np.testing.assert_array_equal(result.data, np.array([[5., 6.], [9., 10.]]))

    def test_empty_slice_returns_empty_field(self):
        f = Field(data=np.arange(9.0).reshape(3, 3))
        result = f[5:10, 5:10]
        assert result.data.size == 0

    def test_empty_slice_preserves_field_type(self):
        f = Field(data=np.arange(9.0).reshape(3, 3))
        result = f[5:10, 5:10]
        assert isinstance(result, Field)

    def test_mixed_scalar_slice_getitem(self):
        f = Field(data=np.arange(12.0).reshape(3, 4),
                  axes=[GridAxis(name="x1", min=0, max=2, npoints=3),
                        GridAxis(name="x2", min=0, max=3, npoints=4)])
        result = f[0, 1:3]
        assert isinstance(result, Field)
        assert result.data.ndim == 1
        np.testing.assert_array_equal(result.data, np.array([1.0, 2.0]))


class TestBackwardCompatibility:
    def test_griddata_is_field(self):
        assert GridData is Field

    def test_griddata_constructor_works(self):
        g = GridData(data=np.array([1.0, 2.0]), iteration=1, time=0.5)
        assert isinstance(g, Field)
        assert g.iteration == 1

    def test_isinstance_griddata(self):
        f = Field(data=np.array([1.0]))
        assert isinstance(f, GridData)


# ── fixtures for float-indexing tests ──────────────────────

@pytest.fixture
def grid_2d():
    """2x2 Field for bilinear interpolation tests."""
    data = np.array([[1.0, 2.0], [3.0, 4.0]])
    axes = [
        GridAxis(name="x1", min=0.0, max=1.0, npoints=2),
        GridAxis(name="x2", min=0.0, max=1.0, npoints=2),
    ]
    return Field(data=data, axes=axes)


@pytest.fixture
def grid_32x32():
    """32x32 Field for slice + float interpolation tests."""
    data = np.arange(32.0 * 32.0).reshape(32, 32)
    axes = [
        GridAxis(name="x1", min=0.0, max=31.0, npoints=32),
        GridAxis(name="x2", min=0.0, max=31.0, npoints=32),
    ]
    return Field(data=data, axes=axes)


class TestFieldFloatIndexing:
    def test_float_scalar_bilinear(self, grid_2d):
        """Float index triggers bilinear interpolation."""
        result = grid_2d[0.5, 0.5]
        # grid_2d: 2x2 [[1,2],[3,4]] → bilinear at center = 2.5
        assert abs(float(result) - 2.5) < 1e-10

    def test_float_scalar_corner(self, grid_2d):
        """Float index at exact int position returns that point."""
        result = grid_2d[0.0, 1.0]
        assert abs(float(result) - 2.0) < 1e-10

    def test_float_mixed_int_float(self, grid_2d):
        """Mixed int + float where both are scalar → returns float."""
        result = grid_2d[0, 0.5]
        # At x1=0, x2=0.5: interpolate between grid_2d[0,0]=1 and grid_2d[0,1]=2
        assert abs(float(result) - 1.5) < 1e-10

    def test_int_slice_still_works(self, grid_2d):
        """Integer indexing preserved (no regression)."""
        result = grid_2d[0:2, 0:2]
        assert result.shape == (2, 2)

    def test_float_line_slice(self, grid_32x32):
        """Slice + float returns 1D Field."""
        result = grid_32x32[:, 15.5]
        assert result.ndim == 1
        assert result.data.shape[0] == 32
