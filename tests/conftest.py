"""Shared test fixtures for osiris-toolkit."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DECKS_DIR = ROOT.parent / "osiris-1.0.0" / "decks" / "test"


@pytest.fixture
def base_2d_path() -> Path:
    return DECKS_DIR / "base-2d"
