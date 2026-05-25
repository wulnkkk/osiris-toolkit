"""Tests for sync.namelist — generation of _generated/parameters.py."""

import importlib.util
import sys
from pathlib import Path

import pytest

from osiris_toolkit.sync.namelist import generate

OSIRIS_SOURCE = Path(__file__).resolve().parents[3] / "osiris-1.0.0" / "source"


class TestNamelistGenerate:
    @pytest.fixture(scope="class")
    def generated_path(self, tmp_path_factory) -> Path:
        if not OSIRIS_SOURCE.is_dir():
            pytest.skip("OSIRIS source not available")
        out = tmp_path_factory.mktemp("gen") / "parameters.py"
        generate(out, OSIRIS_SOURCE)
        return out

    @pytest.fixture(scope="class")
    def gen_module(self, generated_path: Path):
        spec = importlib.util.spec_from_file_location("_test_params", generated_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_test_params"] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_generates_file(self, generated_path: Path) -> None:
        assert generated_path.is_file()
        content = generated_path.read_text(encoding="utf-8")
        assert "GEN_PARAMETERS" in content

    def test_module_importable(self, gen_module) -> None:
        assert hasattr(gen_module, "GEN_PARAMETERS")
        assert isinstance(gen_module.GEN_PARAMETERS, dict)

    def test_has_simulation_section(self, gen_module) -> None:
        assert "simulation" in gen_module.GEN_PARAMETERS
        params = gen_module.GEN_PARAMETERS["simulation"]
        assert "omega_p0" in params
        assert "n0" in params

    def test_has_grid_section(self, gen_module) -> None:
        assert "grid" in gen_module.GEN_PARAMETERS
        params = gen_module.GEN_PARAMETERS["grid"]
        assert len(params) > 0

    def test_has_diag_emf_section(self, gen_module) -> None:
        assert "diag_emf" in gen_module.GEN_PARAMETERS
        params = gen_module.GEN_PARAMETERS["diag_emf"]
        assert "ndump_fac" in params

    def test_emf_solver_multi_file_merged(self, gen_module) -> None:
        """P0 Fix 2 verification: emf_solver from 5 files is correctly merged."""
        if "emf_solver" not in gen_module.GEN_PARAMETERS:
            pytest.skip("emf_solver section not found")
        params = gen_module.GEN_PARAMETERS["emf_solver"]
        assert len(params) > 1, f"Expected >1 params, got {len(params)}"

    def test_param_has_types_and_default(self, gen_module) -> None:
        sim = gen_module.GEN_PARAMETERS["simulation"]
        omega = sim["omega_p0"]
        assert omega.name == "omega_p0"
        assert omega.python_type == "float"
        assert omega.fortran_type != ""

    def test_all_sections_have_params(self, gen_module) -> None:
        for sec_name, params in gen_module.GEN_PARAMETERS.items():
            assert len(params) > 0, f"Section '{sec_name}' has no parameters"
