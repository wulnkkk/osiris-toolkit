"""Integration tests for deck parsing — migrated from osiris-deck-parser."""

from pathlib import Path

from osiris_toolkit.deck import lint_deck_file, parse_deck_file, parse_deck_text

DECKS_DIR = Path(__file__).resolve().parents[3] / "osiris-1.0.0" / "decks" / "test"


def test_parse_base_2d() -> None:
    """Parse the base-2d test deck."""
    deck_path = DECKS_DIR / "base-2d"
    if not deck_path.exists():
        pytest.skip(f"External test deck not found: {deck_path}")
    result = parse_deck_file(str(deck_path))
    assert result["filename"] is not None
    assert len(result["sections"]) > 0


def test_parse_base_3d() -> None:
    """Parse the base-3d test deck."""
    deck_path = DECKS_DIR / "base-3d"
    if not deck_path.exists():
        pytest.skip(f"External test deck not found: {deck_path}")
    result = parse_deck_file(str(deck_path))
    assert len(result["sections"]) > 0


def test_lint_base_2d() -> None:
    """Lint a valid deck returns a report with no errors."""
    deck_path = DECKS_DIR / "base-2d"
    if not deck_path.exists():
        pytest.skip(f"External test deck not found: {deck_path}")
    report = lint_deck_file(str(deck_path))
    assert not report.has_errors()


def test_parse_text() -> None:
    """parse_deck_text works on a minimal deck."""
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
    """Parse every known test deck without crashing."""
    test_decks = [
        "base-1d", "base-2d", "base-3d",
    ]
    for name in test_decks:
        deck_path = DECKS_DIR / name
        if deck_path.exists():
            result = parse_deck_file(str(deck_path))
            assert len(result["sections"]) > 0, f"Failed to parse {name}"
