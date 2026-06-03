"""Tests for resource._params — ResourceParams extraction."""

import pytest

from osiris_toolkit.exceptions import MissingParameterError
from osiris_toolkit.resource._params import ResourceParams


def _make_deck(sections: list[dict]) -> dict:
    return {"filename": "test.in", "sections": sections}


def _make_section(name: str, params: dict) -> dict:
    return {"name": name, "params": params}


class TestResourceParams:
    def test_minimal_2d(self):
        deck = _make_deck([
            _make_section("grid", {"nx_p": [32, 32]}),
            _make_section("time", {"tmax": 50.0}),
            _make_section("time_step", {"dt": 0.07}),
        ])
        p = ResourceParams.from_deck(deck)
        assert p.ndim == 2
        assert p.nx_p == [32, 32]
        assert p.ngrid_total == 1024
        assert p.n_steps == 714

    def test_defaults_1_node(self):
        deck = _make_deck([
            _make_section("grid", {"nx_p": [32, 32]}),
            _make_section("time", {"tmax": 10.0}),
            _make_section("time_step", {"dt": 0.1}),
        ])
        p = ResourceParams.from_deck(deck)
        assert p.total_nodes == 1
        assert p.n_threads == 1
        assert p.emf_ndump_fac == 0
        assert p.vpml_bnd_size == 0

    def test_missing_grid_raises(self):
        deck = _make_deck([
            _make_section("time", {"tmax": 50.0}),
            _make_section("time_step", {"dt": 0.07}),
        ])
        with pytest.raises(MissingParameterError, match="grid"):
            ResourceParams.from_deck(deck)

    def test_missing_tmax_raises(self):
        deck = _make_deck([
            _make_section("grid", {"nx_p": [32, 32]}),
            _make_section("time_step", {"dt": 0.07}),
        ])
        with pytest.raises(MissingParameterError, match="time"):
            ResourceParams.from_deck(deck)

    def test_missing_dt_raises(self):
        deck = _make_deck([
            _make_section("grid", {"nx_p": [32, 32]}),
            _make_section("time", {"tmax": 50.0}),
        ])
        with pytest.raises(MissingParameterError, match="dt"):
            ResourceParams.from_deck(deck)

    def test_with_species(self):
        deck = _make_deck([
            _make_section("grid", {"nx_p": [64, 64]}),
            _make_section("time", {"tmax": 100.0}),
            _make_section("time_step", {"dt": 0.05}),
            _make_section("particles", {"num_species": 2}),
            _make_section("species", {"num_par_x": [2, 2], "rqm": -1.0}),
            _make_section("species", {"num_par_x": [4, 4]}),
        ])
        p = ResourceParams.from_deck(deck)
        assert p.num_species == 2
        assert p.species_ppc == [[2, 2], [4, 4]]
        assert p.total_particles == 4096 * 4 + 4096 * 16  # 64*64 * 4 + 64*64 * 16

    def test_with_mpi(self):
        deck = _make_deck([
            _make_section("grid", {"nx_p": [128, 128]}),
            _make_section("time", {"tmax": 10.0}),
            _make_section("time_step", {"dt": 0.1}),
            _make_section("node_conf", {"node_number": [4, 2], "n_threads": 2}),
        ])
        p = ResourceParams.from_deck(deck)
        assert p.total_nodes == 8
        assert p.n_threads == 2

    def test_with_diagnostics(self):
        deck = _make_deck([
            _make_section("grid", {"nx_p": [32, 32]}),
            _make_section("time", {"tmax": 100.0}),
            _make_section("time_step", {"dt": 0.1}),
            _make_section("diag_emf", {"ndump_fac": 10, "prec": 8}),
            _make_section("diag_species", {"ndump_fac_raw": 50, "raw_fraction": 0.1}),
        ])
        p = ResourceParams.from_deck(deck)
        assert p.emf_ndump_fac == 10
        assert p.field_precision_bytes == 8
        assert p.species_ndump_fac_raw == [50]
        assert p.species_raw_fraction == [0.1]

    def test_wrapped_dict_values(self):
        """Test values wrapped in dict with 'value' key (sliced params from deck parser)."""
        deck = _make_deck([
            _make_section("grid", {"nx_p": {"value": [64, 64]}}),
            _make_section("time", {"tmax": {"value": 20.0}}),
            _make_section("time_step", {"dt": 0.1}),
        ])
        p = ResourceParams.from_deck(deck)
        assert p.nx_p == [64, 64]
        assert p.tmax == 20.0
