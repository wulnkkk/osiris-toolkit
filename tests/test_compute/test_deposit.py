"""Tests for compute.deposit — particle-to-grid mapping."""
import numpy as np
import pytest
from osiris_toolkit.compute.deposit import particles_to_grid
from osiris_toolkit.sim.diagnostics import Field


class TestParticlesToGrid:
    def test_ngp_single_particle_1d(self):
        positions = np.array([[5.0]])
        result = particles_to_grid(positions, None, (10,), shape_function="ngp")
        assert isinstance(result, Field)
        assert result.shape == (10,)
        assert result.data[5] == 1.0
        assert result.data.sum() == 1.0

    def test_ngp_multiple_particles_1d(self):
        positions = np.array([[0.0], [2.0], [2.0]])
        result = particles_to_grid(positions, None, (5,), shape_function="ngp")
        assert result.data[0] == 1.0
        assert result.data[2] == 2.0
        assert result.data.sum() == 3.0

    def test_weights(self):
        positions = np.array([[0.0], [1.0]])
        weights = np.array([2.0, 3.0])
        result = particles_to_grid(positions, weights, (3,), shape_function="ngp")
        assert result.data[0] == 2.0
        assert result.data[1] == 3.0
        assert result.data.sum() == 5.0

    def test_default_weights_are_one(self):
        positions = np.array([[0.0], [0.0], [0.0]])
        result = particles_to_grid(positions, None, (2,), shape_function="ngp")
        assert result.data[0] == 3.0

    def test_tophat_conservation(self):
        rng = np.random.default_rng(123)
        # Top-hat (CIC) should conserve total within floating-point error
        positions = rng.uniform(1, 9, size=(1000, 2))
        weights = rng.uniform(0, 1, size=1000)
        result = particles_to_grid(positions, weights, (10, 10),
                                   shape_function="tophat")
        assert abs(result.data.sum() - weights.sum()) < 1e-10

    def test_triangular_runs(self):
        """Triangular (quadratic B-spline) produces output without error."""
        rng = np.random.default_rng(456)
        positions = rng.uniform(0, 10, size=(500, 1))
        weights = rng.uniform(0, 2, size=500)
        result = particles_to_grid(positions, weights, (10,),
                                   shape_function="triangular")
        assert isinstance(result, Field)
        assert result.shape == (10,)
        assert result.data.sum() >= 0

    def test_spline3_runs(self):
        """Cubic spline produces output without error."""
        rng = np.random.default_rng(789)
        positions = rng.uniform(0, 10, size=(500, 1))
        weights = rng.uniform(0, 2, size=500)
        result = particles_to_grid(positions, weights, (10,),
                                   shape_function="spline3")
        assert isinstance(result, Field)
        assert result.shape == (10,)
        assert result.data.sum() >= 0

    def test_invalid_shape_function(self):
        positions = np.array([[0.0]])
        with pytest.raises(ValueError, match="Unknown shape function"):
            particles_to_grid(positions, None, (3,), shape_function="invalid")

    def test_returns_field_with_axes(self):
        from osiris_toolkit.sim.diagnostics import GridAxis
        positions = np.array([[0.0]])
        axes = [GridAxis(name="x1", min=-5.0, max=5.0, npoints=10)]
        result = particles_to_grid(positions, None, (10,), axes=axes,
                                   shape_function="ngp")
        assert len(result.axes) == 1
        assert result.axes[0].name == "x1"

    def test_empty_particles(self):
        positions = np.empty((0, 2))
        result = particles_to_grid(positions, None, (4, 4), shape_function="ngp")
        assert result.data.sum() == 0.0

    def test_ngp_2d(self):
        positions = np.array([[0.1, 0.1], [4.1, 4.1]])
        result = particles_to_grid(positions, None, (5, 5), shape_function="ngp")
        assert result.data.sum() == 2.0
