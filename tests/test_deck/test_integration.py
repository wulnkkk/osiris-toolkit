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
