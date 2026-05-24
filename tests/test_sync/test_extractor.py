"""Tests for sync.extractor module."""

from pathlib import Path

import pytest

from osiris_toolkit.sync.extractor import FortranScanner

OSIRIS_SOURCE = (
    Path(__file__).resolve().parents[3] / "osiris-1.0.0" / "source"
)


class TestFortranScanner:
    @pytest.fixture(scope="class")
    def scanner(self) -> FortranScanner:
        if not OSIRIS_SOURCE.is_dir():
            pytest.skip("OSIRIS source not available")
        s = FortranScanner(OSIRIS_SOURCE)
        s.scan()
        return s

    def test_finds_namelists(self, scanner: FortranScanner) -> None:
        assert len(scanner.namelists) > 10

    def test_finds_simulation_namelist(self, scanner: FortranScanner) -> None:
        entry = scanner.get_namelist("nl_simulation")
        assert entry is not None
        var_names = [v.name for v in entry.variables]
        assert "omega_p0" in var_names
        assert "n0" in var_names
        assert "gamma" in var_names

    def test_finds_diag_emf_namelist(self, scanner: FortranScanner) -> None:
        entry = scanner.get_namelist("nl_diag_emf")
        assert entry is not None
        var_names = [v.name for v in entry.variables]
        assert "ndump_fac" in var_names
        assert "reports" in var_names

    def test_finds_emf_quantities(self, scanner: FortranScanner) -> None:
        emf_quants = None
        for q in scanner.quantities:
            if "emf-diag-define" in q.file_path.lower():
                emf_quants = q
                break
        assert emf_quants is not None
        assert "e1" in emf_quants.quantities
        assert "b1" in emf_quants.quantities
        assert "ene_e" in emf_quants.quantities
        assert "chargecons" in emf_quants.quantities

    def test_finds_sections(self, scanner: FortranScanner) -> None:
        section_names = {s.section_name for s in scanner.sections if s.section_name}
        assert "simulation" in section_names
        assert "grid" in section_names
        assert "diag_emf" in section_names
        assert "species" in section_names

    def test_continuation_merging(self) -> None:
        lines = [
            "namelist /nl_test/ a, b, &",
            "  c, d",
        ]
        merged = FortranScanner._merge_continuations(lines)
        assert len(merged) == 1
        # After merging, all variables should appear on one line
        compact = merged[0].replace(" ", "")
        assert "a," in compact
        assert "b," in compact
        assert "c," in compact
        assert "d" in compact
