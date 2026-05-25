"""Tests for analysis.parallel."""

import pytest

from osiris_toolkit.analysis.parallel import describe_all, field_energy_all


class TestFieldEnergyAll:
    def test_serial(self, tmp_sim_dir):
        from osiris_toolkit.sim import Simulation

        sim = Simulation(tmp_sim_dir)
        results = field_energy_all(sim, "e1", max_workers=1)

        assert isinstance(results, list)
        assert len(results) == 3  # tmp_sim_dir has 3 iterations
        for r in results:
            assert "iteration" in r
            assert "time" in r
            assert "energy" in r
            assert r["energy"] > 0

    def test_parallel(self, tmp_sim_dir):
        from osiris_toolkit.sim import Simulation

        sim = Simulation(tmp_sim_dir)
        results = field_energy_all(sim, "e1", max_workers=2)

        assert len(results) == 3
        # Verify sorted by iteration
        iterations = [r["iteration"] for r in results]
        assert iterations == sorted(iterations)

    def test_default_workers(self, tmp_sim_dir):
        from osiris_toolkit.sim import Simulation

        sim = Simulation(tmp_sim_dir)
        results = field_energy_all(sim, "e1")

        assert len(results) == 3


class TestDescribeAll:
    def test_serial(self, tmp_sim_dir):
        from osiris_toolkit.sim import Simulation

        sim = Simulation(tmp_sim_dir)
        results = describe_all(sim, "e1", max_workers=1)

        assert len(results) == 3
        for r in results:
            assert "mean" in r
            assert "std" in r
            assert "min" in r
            assert "max" in r
            assert "rms" in r

    def test_parallel(self, tmp_sim_dir):
        from osiris_toolkit.sim import Simulation

        sim = Simulation(tmp_sim_dir)
        results = describe_all(sim, "e1", max_workers=2)

        assert len(results) == 3
        iterations = [r["iteration"] for r in results]
        assert iterations == sorted(iterations)

    def test_custom_iterations(self, tmp_sim_dir):
        from osiris_toolkit.sim import Simulation

        sim = Simulation(tmp_sim_dir)
        results = describe_all(sim, "e1", iterations=[0, 10])

        assert len(results) == 2
