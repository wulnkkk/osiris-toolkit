"""Public API for osiris-toolkit deck parsing."""

from pathlib import Path

from .lexer import tokenize
from .parser import parse_tokens
from .reporter import IssueReport
from .validator import validate_deck


def parse_deck_text(text: str, filename: str = "<input>") -> dict:
    """Parse OSIRIS input deck text into a flat parameter dictionary.

    Returns a dictionary structured as::

        {
            "sections": [
                {"name": "node_conf", "params": {...}, "line": 1},
                ...
            ]
        }
    """
    deck = parse_tokens(tokenize(text, filename), filename)
    return {
        "filename": deck.filename,
        "sections": [
            {"name": s.name, "params": s.params, "line": s.line}
            for s in deck.sections
        ],
    }


def parse_deck_file(path: str) -> dict:
    """Parse an OSIRIS input deck file into a flat parameter dictionary."""
    text = Path(path).read_text(encoding="utf-8")
    return parse_deck_text(text, str(path))


def lint_deck_text(text: str, filename: str = "<input>") -> IssueReport:
    """Lint OSIRIS input deck text and return a validation report."""
    deck = parse_tokens(tokenize(text, filename), filename)
    return validate_deck(deck)


def lint_deck_file(path: str) -> IssueReport:
    """Lint an OSIRIS input deck file and return a validation report."""
    text = Path(path).read_text(encoding="utf-8")
    return lint_deck_text(text, str(path))
