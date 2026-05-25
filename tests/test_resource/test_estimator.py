"""Tests for resource._estimator — calculation formulas."""

from osiris_toolkit.resource._params import ResourceParams
from osiris_toolkit.resource._estimator import ResourceEstimator


def _make_params(**overrides) -> ResourceParams:
    defaults = {
        "ndim": 2, "nx_p": [32, 32], "ngrid_total": 1024,
        "tmax": 50.0, "dt": 0.07, "n_steps": 714,
        "node_number": [1, 1], "total_nodes": 1, "n_threads": 1,
        "num_species": 1, "species_ppc": [[2, 2]], "species_names": [""],
        "vpml_bnd_size": 0, "n_pml_boundaries": 0,
        "solver": "yee", "solver_ord": 2, "interpolation": "quadratic",
        "smooth_type": "none", "smooth_order": 0,
        "if_move": False, "if_collide": False, "n_collide": 0,
        "emf_ndump_fac": 0, "species_ndump_fac": [], "species_ndump_fac_raw": [],
        "species_raw_fraction": [], "restart_ndump_fac": 0,
        "field_precision_bytes": 4, "particle_precision_bytes": 8,
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
        p = _make_params(emf_ndump_fac=10, species_ppc=[[2, 2]], species_ndump_fac_raw=[100], species_raw_fraction=[1.0])
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
