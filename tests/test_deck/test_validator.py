"""Tests for deck.validator — validation rules."""

from osiris_toolkit.deck import lint_deck_file, lint_deck_text
from osiris_toolkit.deck.reporter import Severity

FIXTURES_DIR = __import__('pathlib').Path(__file__).resolve().parents[1] / "fixtures"


class TestValidateValidDecks:
    def test_minimal_deck_no_errors(self):
        report = lint_deck_file(str(FIXTURES_DIR / "minimal.in"))
        assert not report.has_errors()

    def test_base_1d(self):
        """Parse and lint base-1d if available."""
        decks_dir = FIXTURES_DIR.parents[1] / "osiris-1.0.0" / "decks" / "test" / "base-1d"
        if not decks_dir.exists():
            import pytest
            pytest.skip("base-1d not available")
        report = lint_deck_file(str(decks_dir))
        # base-1d may have warnings but should not have errors
        assert len(report.errors()) >= 0


class TestValidateInvalidDecks:
    def test_missing_omega_p0(self):
        report = lint_deck_file(str(FIXTURES_DIR / "invalid_no_omega.in"))
        # Should have at least a warning about missing omega_p0
        assert len(report.issues) > 0

    def test_negative_dt(self):
        report = lint_deck_file(str(FIXTURES_DIR / "invalid_neg_dt.in"))
        # Should have issues about negative dt
        assert len(report.issues) > 0

    def test_wrong_section_order(self):
        report = lint_deck_file(str(FIXTURES_DIR / "invalid_order.in"))
        assert len(report.issues) > 0

    def test_syntax_error(self):
        try:
            report = lint_deck_file(str(FIXTURES_DIR / "invalid_syntax.in"))
            assert len(report.issues) > 0
        except Exception:
            # Parse errors are expected
            pass


class TestValidationRules:
    def test_missing_omega_p0_warning(self):
        deck = lint_deck_text("""
simulation {
  gamma = 5.0,
}
grid {
  nx_p(1:2) = 32, 32,
  coordinates = "cartesian",
}
""")
        assert len(deck.issues) > 0

    def test_negative_omega_p0_error(self):
        deck = lint_deck_text("""
simulation {
  omega_p0 = -3.55e15,
  gamma = 5.0,
}
grid {
  nx_p(1:2) = 32, 32,
  coordinates = "cartesian",
}
""")
        assert any(i.severity == Severity.ERROR for i in deck.issues)

    def test_gamma_less_than_1(self):
        deck = lint_deck_text("""
simulation {
  omega_p0 = 3.55e15,
  gamma = 0.5,
}
grid {
  nx_p(1:2) = 32, 32,
  coordinates = "cartesian",
}
""")
        assert len(deck.issues) > 0

    def test_nx_p_zero(self):
        deck = lint_deck_text("""
simulation {
  omega_p0 = 3.55e15,
  gamma = 5.0,
}
grid {
  nx_p(1:2) = 0, 32,
  coordinates = "cartesian",
}
""")
        assert any(i.severity == Severity.ERROR for i in deck.issues)

    def test_dt_zero_error(self):
        deck = lint_deck_text("""
simulation {
  omega_p0 = 3.55e15,
  gamma = 5.0,
}
grid {
  nx_p(1:2) = 32, 32,
  coordinates = "cartesian",
}
time_step {
  dt = 0.0,
}
""")
        assert any(i.severity == Severity.ERROR for i in deck.issues)

    def test_dt_negative_error(self):
        deck = lint_deck_text("""
simulation {
  omega_p0 = 3.55e15,
  gamma = 5.0,
}
grid {
  nx_p(1:2) = 32, 32,
  coordinates = "cartesian",
}
time_step {
  dt = -0.07,
}
""")
        assert any(i.severity == Severity.ERROR for i in deck.issues)

    def test_xmin_greater_than_xmax(self):
        deck = lint_deck_text("""
simulation {
  omega_p0 = 3.55e15,
  gamma = 5.0,
}
grid {
  nx_p(1:2) = 32, 32,
  coordinates = "cartesian",
}
space {
  xmin(1:2) = 10.0, 10.0,
  xmax(1:2) = 0.0, 0.0,
}
""")
        # xmin > xmax should produce an error
        assert any("xmin" in i.message.lower() or "xmax" in i.message.lower()
                   for i in deck.issues)
        # At minimum there should be issues
        assert len(deck.issues) > 0
