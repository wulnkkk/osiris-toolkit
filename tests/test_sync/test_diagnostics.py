"""Tests for sync.diagnostics — generation of _generated/quantities.py."""

import importlib.util
import sys
from pathlib import Path

import pytest

from osiris_toolkit.sync.diagnostics import generate

OSIRIS_SOURCE = Path(__file__).resolve().parents[3] / "osiris-1.0.0" / "source"


class TestDiagnosticsGenerate:
    @pytest.fixture(scope="class")
    def generated_path(self, tmp_path_factory) -> Path:
        if not OSIRIS_SOURCE.is_dir():
            pytest.skip("OSIRIS source not available")
        out = tmp_path_factory.mktemp("gen") / "quantities.py"
        generate(out, OSIRIS_SOURCE)
        return out

    @pytest.fixture(scope="class")
    def gen_module(self, generated_path: Path):
        spec = importlib.util.spec_from_file_location("_test_quants", generated_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_test_quants"] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_generates_file(self, generated_path: Path) -> None:
        assert generated_path.is_file()
        content = generated_path.read_text(encoding="utf-8")
        assert "GEN_QUANTITIES" in content

    def test_module_importable(self, gen_module) -> None:
        assert hasattr(gen_module, "GEN_QUANTITIES")
        assert isinstance(gen_module.GEN_QUANTITIES, dict)

    def test_has_emf_quantities(self, gen_module) -> None:
        assert "EMF" in gen_module.GEN_QUANTITIES
        quants = gen_module.GEN_QUANTITIES["EMF"]
        assert "e1" in quants
        assert "b1" in quants
        assert "ene_e" in quants

    def test_has_density_quantities(self, gen_module) -> None:
        assert "DENSITY" in gen_module.GEN_QUANTITIES
        quants = gen_module.GEN_QUANTITIES["DENSITY"]
        assert len(quants) > 0

    def test_charge_quantities_present(self, gen_module) -> None:
        """P0 Fix 3 verification: CHARGE quantities with len=* are extracted."""
        if "CHARGE" not in gen_module.GEN_QUANTITIES:
            pytest.skip("CHARGE quantities not found")
        quants = gen_module.GEN_QUANTITIES["CHARGE"]
        assert len(quants) > 0

    def test_neutral_quantities_present(self, gen_module) -> None:
        """P0 Fix 3 verification: NEUTRAL quantities with len=* are extracted."""
        if "NEUTRAL" not in gen_module.GEN_QUANTITIES:
            pytest.skip("NEUTRAL quantities not found")
        quants = gen_module.GEN_QUANTITIES["NEUTRAL"]
        assert len(quants) > 0

    def test_no_duplicates_within_kind(self, gen_module) -> None:
        for kind, quants in gen_module.GEN_QUANTITIES.items():
            assert len(quants) == len(
                set(quants)
            ), f"Duplicate quantities in {kind}"
