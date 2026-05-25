"""Tests for sync.sections — generation of _generated/sections.py."""

import importlib.util
import sys
from pathlib import Path

import pytest

from osiris_toolkit.sync.sections import generate

OSIRIS_SOURCE = Path(__file__).resolve().parents[3] / "osiris-1.0.0" / "source"


class TestSectionsGenerate:
    @pytest.fixture(scope="class")
    def generated_path(self, tmp_path_factory) -> Path:
        if not OSIRIS_SOURCE.is_dir():
            pytest.skip("OSIRIS source not available")
        out = tmp_path_factory.mktemp("gen") / "sections.py"
        generate(out, OSIRIS_SOURCE)
        return out

    @pytest.fixture(scope="class")
    def gen_module(self, generated_path: Path):
        spec = importlib.util.spec_from_file_location("_test_sections", generated_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_test_sections"] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_generates_file(self, generated_path: Path) -> None:
        assert generated_path.is_file()
        content = generated_path.read_text(encoding="utf-8")
        assert "GEN_SECTIONS" in content
        assert "SECTION_NAMES" in content

    def test_module_importable(self, gen_module) -> None:
        assert hasattr(gen_module, "GEN_SECTIONS")
        assert isinstance(gen_module.GEN_SECTIONS, list)
        assert hasattr(gen_module, "SECTION_NAMES")
        assert isinstance(gen_module.SECTION_NAMES, list)

    def test_has_core_sections(self, gen_module) -> None:
        names = {s.name for s in gen_module.GEN_SECTIONS}
        assert "simulation" in names
        assert "grid" in names
        assert "diag_emf" in names
        assert "species" in names

    def test_no_duplicate_sections(self, gen_module) -> None:
        names = [s.name for s in gen_module.GEN_SECTIONS]
        assert len(names) == len(set(names)), f"Duplicate sections: {names}"

    def test_each_section_has_nl_name(self, gen_module) -> None:
        for s in gen_module.GEN_SECTIONS:
            assert s.nl_name.startswith("nl_"), f"Bad nl_name for {s.name}: {s.nl_name}"

    def test_section_names_match(self, gen_module) -> None:
        gen_names = {s.name for s in gen_module.GEN_SECTIONS}
        assert gen_names == set(gen_module.SECTION_NAMES)
