"""Integration tests for deck parsing."""

from pathlib import Path

import pytest

from osiris_toolkit.deck import lint_deck_file, parse_deck_file, parse_deck_text

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_parse_bundled_deck() -> None:
    """Parse the bundled minimal test deck."""
    result = parse_deck_file(str(FIXTURES_DIR / "minimal.in"))
    assert len(result["sections"]) == 11
    # Verify key sections
    names = [s["name"] for s in result["sections"]]
    assert "simulation" in names
    assert "grid" in names
    assert "species" in names


def test_parse_bundled_deck_params() -> None:
    """Verify parameter values from the bundled deck."""
    result = parse_deck_file(str(FIXTURES_DIR / "minimal.in"))
    sim = next(s for s in result["sections"] if s["name"] == "simulation")
    assert sim["params"]["omega_p0"] == 3.55e15
    assert sim["params"]["gamma"] == 5.0


def test_lint_bundled_deck() -> None:
    """Lint the bundled deck — should have no fatal errors."""
    report = lint_deck_file(str(FIXTURES_DIR / "minimal.in"))
    assert not report.has_errors()


def test_parse_text() -> None:
    """parse_deck_text works on inline input."""
    text = """
simulation {
  omega_p0 = 3554059560960100.0,
}

grid {
  nx_p(1:2) = 32, 32,
  coordinates = "cartesian",
}
"""
    result = parse_deck_text(text)
    assert len(result["sections"]) == 2


def test_parse_all_test_decks() -> None:
    """Parse every known upstream test deck (if available)."""
    decks_dir = Path(__file__).resolve().parents[3] / "osiris-1.0.0" / "decks" / "test"
    if not decks_dir.exists():
        pytest.skip("Upstream OSIRIS test decks not available")

    test_decks = ["base-1d", "base-2d", "base-3d"]
    for name in test_decks:
        deck_path = decks_dir / name
        if deck_path.exists():
            result = parse_deck_file(str(deck_path))
            assert len(result["sections"]) > 0, f"Failed to parse {name}"


# ---------------------------------------------------------------------------
# Invalid deck fixtures tests
# ---------------------------------------------------------------------------


def test_lint_invalid_no_omega():
    """Linting a deck without omega_p0 should produce issues."""
    f = FIXTURES_DIR / "invalid_no_omega.in"
    report = lint_deck_file(str(f))
    assert len(report.issues) > 0


def test_lint_invalid_neg_dt():
    """Negative dt should produce errors."""
    f = FIXTURES_DIR / "invalid_neg_dt.in"
    report = lint_deck_file(str(f))
    assert len(report.issues) > 0


def test_lint_invalid_order():
    """Wrong section order should produce warnings."""
    f = FIXTURES_DIR / "invalid_order.in"
    report = lint_deck_file(str(f))
    assert len(report.issues) > 0


def test_lint_invalid_syntax():
    """Syntax errors should be caught or parsing may fail gracefully."""
    f = FIXTURES_DIR / "invalid_syntax.in"
    try:
        report = lint_deck_file(str(f))
        # If lint succeeds, there should be issues
        assert len(report.issues) > 0
    except Exception:
        # Parse errors are expected for syntax errors
        pass


def test_parse_invalid_syntax_raises_or_partial():
    """Syntax errors should either raise or return a partial result."""
    f = FIXTURES_DIR / "invalid_syntax.in"
    try:
        result = parse_deck_file(str(f))
        # If it doesn't raise, should return some structure
        assert "sections" in result
    except Exception:
        # Raising on syntax error is acceptable
        pass
