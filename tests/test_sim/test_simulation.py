"""Tests for sim.simulation — Simulation class."""

import pytest

from osiris_toolkit.sim import Simulation
from osiris_toolkit.sim.diagnostics import GridData


class TestSimulationInit:
    def test_init_valid_dir(self, tmp_sim_dir):
        sim = Simulation(tmp_sim_dir)
        assert sim is not None

    def test_init_nonexistent_dir(self, tmp_path):
        with pytest.raises(NotADirectoryError):
            Simulation(tmp_path / "nonexistent")

    def test_init_file_not_dir(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("not a dir")
        with pytest.raises(NotADirectoryError):
            Simulation(f)

    def test_init_empty_dir(self, tmp_sim_dir_empty):
        sim = Simulation(tmp_sim_dir_empty)
        assert sim.list_fields() == []
        assert sim.list_species() == []


class TestSimulationDiscovery:
    def test_discovers_fld(self, tmp_sim_dir):
        sim = Simulation(tmp_sim_dir)
        assert "e1" in sim.list_fields()

    def test_list_fields_sorted(self, tmp_sim_dir):
        sim = Simulation(tmp_sim_dir)
        fields = sim.list_fields()
        assert fields == sorted(fields)

    def test_list_iterations(self, tmp_sim_dir):
        sim = Simulation(tmp_sim_dir)
        iters = sim.list_iterations("e1")
        assert len(iters) == 3
        assert iters == sorted(iters)

    def test_no_density_when_missing(self, tmp_sim_dir):
        sim = Simulation(tmp_sim_dir)
        species = sim.list_species()
        assert "electrons" not in species  # No DENSITY dir

    def test_density_discovery(self, tmp_sim_dir_density):
        sim = Simulation(tmp_sim_dir_density)
        species = sim.list_species()
        assert "electrons" in species
        assert "protons" in species


class TestRunInfo:
    def test_run_info_exists(self, tmp_sim_dir):
        sim = Simulation(tmp_sim_dir)
        info = sim.run_info
        # run-info parsing uses key: value format
        assert len(info) > 0

    def test_run_info_missing(self, tmp_sim_dir_empty):
        sim = Simulation(tmp_sim_dir_empty)
        assert sim.run_info == {}


class TestGetField:
    def test_get_field_exists(self, tmp_sim_dir):
        sim = Simulation(tmp_sim_dir)
        grid = sim.get_field("e1", iteration=0)
        assert grid is not None
        assert isinstance(grid, GridData)
        assert grid.iteration == 0

    def test_get_field_wrong_iteration(self, tmp_sim_dir):
        sim = Simulation(tmp_sim_dir)
        grid = sim.get_field("e1", iteration=999)
        assert grid is None

    def test_get_field_unknown_quantity(self, tmp_sim_dir):
        sim = Simulation(tmp_sim_dir)
        grid = sim.get_field("nonexistent", iteration=0)
        assert grid is None


class TestGetDensity:
    def test_get_density_exists(self, tmp_sim_dir_density):
        sim = Simulation(tmp_sim_dir_density)
        grid = sim.get_density("electrons", "charge", iteration=0)
        assert grid is not None
        assert isinstance(grid, GridData)

    def test_get_density_wrong_species(self, tmp_sim_dir_density):
        sim = Simulation(tmp_sim_dir_density)
        grid = sim.get_density("nonexistent", "charge", iteration=0)
        assert grid is None

    def test_get_density_wrong_iteration(self, tmp_sim_dir_density):
        sim = Simulation(tmp_sim_dir_density)
        grid = sim.get_density("electrons", "charge", iteration=999)
        assert grid is None
