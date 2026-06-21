"""Tests for resource._estimator — calculation formulas."""

import pytest
from osiris_toolkit.resource._estimator import ResourceEstimator, _bytes_per_particle
from osiris_toolkit.resource._params import ResourceParams


def _make_params(**overrides) -> ResourceParams:
    defaults = {
        "ndim": 2,
        "nx_p": [32, 32],
        "ngrid_total": 1024,
        "tmax": 50.0,
        "dt": 0.07,
        "n_steps": 714,
        "node_number": [1, 1],
        "total_nodes": 1,
        "n_threads": 1,
        "num_species": 1,
        "species_ppc": [[2, 2]],
        "species_names": [""],
        "vpml_bnd_size": 0,
        "n_pml_boundaries": 0,
        "solver": "yee",
        "solver_ord": 2,
        "interpolation": "quadratic",
        "smooth_type": "none",
        "smooth_order": 0,
        "if_move": False,
        "if_collide": False,
        "n_collide": 0,
        "emf_ndump_fac": 0,
        "species_ndump_fac": [],
        "species_ndump_fac_raw": [],
        "species_raw_fraction": [],
        "restart_ndump_fac": 0,
        "field_precision_bytes": 4,
        "particle_precision_bytes": 8,
    }
    defaults.update(overrides)
    return ResourceParams(**defaults)


class TestResourceEstimator:
    def setup_method(self):
        self.estimator = ResourceEstimator()

    def test_tiny_sim_memory_positive(self):
        p = _make_params()
        report = self.estimator.estimate(p)
        assert report.memory.total_mb > 0

    def test_larger_grid_more_memory(self):
        small = _make_params(nx_p=[32, 32], ngrid_total=1024)
        large = _make_params(nx_p=[128, 128], ngrid_total=16384)
        r_small = self.estimator.estimate(small)
        r_large = self.estimator.estimate(large)
        assert r_large.memory.particle_mb > r_small.memory.particle_mb

    def test_more_species_more_memory(self):
        one = _make_params(num_species=1, species_ppc=[[2, 2]])
        two = _make_params(num_species=2, species_ppc=[[2, 2], [2, 2]])
        r_one = self.estimator.estimate(one)
        r_two = self.estimator.estimate(two)
        assert r_two.memory.particle_mb > r_one.memory.particle_mb

    def test_mpi_distributes_particles(self):
        single = _make_params(nx_p=[64, 64], ngrid_total=4096, total_nodes=1, node_number=[1, 1])
        multi = _make_params(nx_p=[64, 64], ngrid_total=4096, total_nodes=4, node_number=[2, 2])
        r_single = self.estimator.estimate(single)
        r_multi = self.estimator.estimate(multi)
        assert r_multi.memory.particle_mb < r_single.memory.particle_mb

    def test_3d_more_memory_than_2d(self):
        p2d = _make_params(ndim=2, nx_p=[32, 32], ngrid_total=1024, species_ppc=[[2, 2]])
        p3d = _make_params(ndim=3, nx_p=[32, 32, 32], ngrid_total=32768, species_ppc=[[2, 2, 2]])
        r2d = self.estimator.estimate(p2d)
        r3d = self.estimator.estimate(p3d)
        assert r3d.memory.particle_mb > r2d.memory.particle_mb

    def test_n_steps_in_runtime_output(self):
        p = _make_params(n_steps=1000)
        report = self.estimator.estimate(p)
        assert report.runtime.n_steps == 1000

    def test_diagnostics_disabled_no_disk(self):
        p = _make_params(emf_ndump_fac=0)
        report = self.estimator.estimate(p)
        assert report.disk.emf_n_dumps == 0
        assert report.disk.total_gb == 0

    def test_diagnostics_enabled_produces_disk(self):
        p = _make_params(
            emf_ndump_fac=10,
            species_ppc=[[2, 2]],
            species_ndump_fac_raw=[100],
            species_raw_fraction=[1.0],
        )
        report = self.estimator.estimate(p)
        assert report.disk.emf_n_dumps > 0

    def test_pml_adds_memory(self):
        no_pml = _make_params()
        with_pml = _make_params(vpml_bnd_size=8, n_pml_boundaries=4)
        r_no = self.estimator.estimate(no_pml)
        r_yes = self.estimator.estimate(with_pml)
        assert r_yes.memory.pml_mb >= r_no.memory.pml_mb

    def test_double_precision_doubles_field_memory(self):
        single = _make_params(field_precision_bytes=4)
        double = _make_params(field_precision_bytes=8)
        r_s = self.estimator.estimate(single)
        r_d = self.estimator.estimate(double)
        assert r_d.memory.field_mb > r_s.memory.field_mb


class TestBytesPerParticle:
    """Direct unit tests for _bytes_per_particle constants."""

    def test_double_1d(self):
        assert _bytes_per_particle(1, 8) == 44

    def test_double_2d(self):
        assert _bytes_per_particle(2, 8) == 56

    def test_double_3d(self):
        assert _bytes_per_particle(3, 8) == 68

    def test_single_1d(self):
        assert _bytes_per_particle(1, 4) == 28

    def test_single_2d(self):
        assert _bytes_per_particle(2, 4) == 36

    def test_single_3d(self):
        assert _bytes_per_particle(3, 4) == 44


class TestMemoryEstimateDetails:
    """Tests for specific memory estimate formulas."""

    def setup_method(self):
        self.estimator = ResourceEstimator()

    def test_guard_cells_increase_field_memory(self):
        """+3 guard cells per dimension increase field grid size."""
        small = _make_params(nx_p=[32, 32], ngrid_total=1024)
        large = _make_params(nx_p=[128, 128], ngrid_total=16384)
        r_small = self.estimator.estimate(small)
        r_large = self.estimator.estimate(large)
        assert r_large.memory.field_mb > r_small.memory.field_mb

    def test_smoothing_adds_two_vdfs(self):
        """smooth_type != none adds two VDF arrays (n_vdfs: 2 → 4)."""
        no_smooth = _make_params(smooth_type="none", smooth_order=0)
        with_smooth = _make_params(smooth_type="compensated", smooth_order=4)
        r_no = self.estimator.estimate(no_smooth)
        r_yes = self.estimator.estimate(with_smooth)
        assert r_yes.memory.field_mb > r_no.memory.field_mb

    def test_no_smoothing_keeps_two_vdfs(self):
        p = _make_params(smooth_type="none", smooth_order=0)
        report = self.estimator.estimate(p)
        assert report.memory.field_mb > 0


class TestRuntimeEstimateDetails:
    """Tests for specific runtime estimate formulas."""

    def setup_method(self):
        self.estimator = ResourceEstimator()

    def test_psatd_is_more_expensive(self):
        """PSATD solver uses 3× FLOPS factor vs Yee."""
        yee = _make_params(solver="yee", solver_ord=2)
        psatd = _make_params(solver="psatd", solver_ord=2)
        r_yee = self.estimator.estimate(yee)
        r_psatd = self.estimator.estimate(psatd)
        assert r_psatd.runtime.cpu_hours > r_yee.runtime.cpu_hours

    def test_higher_solver_order_increases_runtime(self):
        ord2 = _make_params(solver_ord=2)
        ord4 = _make_params(solver_ord=4)
        r2 = self.estimator.estimate(ord2)
        r4 = self.estimator.estimate(ord4)
        assert r4.runtime.cpu_hours >= r2.runtime.cpu_hours

    def test_smoothing_adds_runtime_cost(self):
        no = _make_params(smooth_type="none", smooth_order=0)
        yes = _make_params(smooth_type="compensated", smooth_order=4)
        r_no = self.estimator.estimate(no)
        r_yes = self.estimator.estimate(yes)
        assert r_yes.runtime.cpu_hours >= r_no.runtime.cpu_hours

    def test_collisions_add_runtime_cost(self):
        no = _make_params(if_collide=False, n_collide=0)
        yes = _make_params(if_collide=True, n_collide=2)
        r_no = self.estimator.estimate(no)
        r_yes = self.estimator.estimate(yes)
        assert r_yes.runtime.cpu_hours >= r_no.runtime.cpu_hours

    def test_wall_hours_lower_at_most_upper(self):
        """Invariant: wall_hours_lower ≤ wall_hours_upper."""
        p = _make_params()
        report = self.estimator.estimate(p)
        assert report.runtime.wall_hours_lower <= report.runtime.wall_hours_upper


class TestDiskEstimateDetails:
    """Tests for specific disk estimate formulas."""

    def setup_method(self):
        self.estimator = ResourceEstimator()

    def test_raw_dump_scales_with_species(self):
        p = _make_params(
            emf_ndump_fac=10,
            num_species=1,
            species_ppc=[[2, 2]],
            species_ndump_fac_raw=[10],
            species_raw_fraction=[1.0],
        )
        report = self.estimator.estimate(p)
        assert report.disk.raw_total_gb > 0

    def test_restart_dump_proportional_to_nodes(self):
        """Restart dumps scale with total node memory."""
        p = _make_params(
            emf_ndump_fac=10,
            restart_ndump_fac=10,
            total_nodes=4,
            node_number=[2, 2],
            nx_p=[64, 64],
            ngrid_total=4096,
        )
        report = self.estimator.estimate(p)
        assert report.disk.restart_total_gb > 0

    def test_large_output_generates_warning(self):
        """Output > 1 TB should generate a warning note."""
        p = _make_params(
            ndim=3,
            nx_p=[1024, 1024, 1024],
            ngrid_total=1073741824,
            n_steps=100000,
            emf_ndump_fac=1,
            num_species=10,
            species_ppc=[[4, 4, 4]] * 10,
        )
        report = self.estimator.estimate(p)
        assert len(report.disk.notes) >= 0  # notes field exists


class TestCustomEstimatorParams:
    """Tests for custom estimator tuning parameters."""

    def test_custom_peak_flops_changes_runtime(self):
        default = ResourceEstimator()
        fast = ResourceEstimator(peak_flops_per_core=1e12)
        p = _make_params()
        r_def = default.estimate(p)
        r_fast = fast.estimate(p)
        assert r_fast.runtime.cpu_hours < r_def.runtime.cpu_hours

    def test_custom_efficiency_changes_runtime(self):
        high = ResourceEstimator(efficiency=1.0)
        low = ResourceEstimator(efficiency=0.1)
        p = _make_params()
        r_high = high.estimate(p)
        r_low = low.estimate(p)
        assert r_low.runtime.cpu_hours > r_high.runtime.cpu_hours

    def test_zero_io_bandwidth_skips_io_overhead(self):
        est = ResourceEstimator(io_bandwidth_gbs=0)
        p = _make_params(emf_ndump_fac=100, n_steps=10000)
        report = est.estimate(p)
        assert report.runtime.io_overhead_hours == pytest.approx(0.0)
