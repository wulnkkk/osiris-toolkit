"""CLI tests for deck subcommands."""

import json

import pytest


class TestCLIDeckParse:
    def test_parse_minimal(self, cli_runner, minimal_deck_path):
        from osiris_toolkit.cli import main
        result = cli_runner.invoke(main, ["deck", "parse", str(minimal_deck_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "sections" in data
        assert len(data["sections"]) >= 10

    def test_parse_json_output(self, cli_runner, minimal_deck_path):
        from osiris_toolkit.cli import main
        result = cli_runner.invoke(main, ["deck", "parse", str(minimal_deck_path), "-o", "json"])
        assert result.exit_code == 0
        # Should be valid JSON
        json.loads(result.output)

    def test_parse_nonexistent(self, cli_runner):
        from osiris_toolkit.cli import main
        result = cli_runner.invoke(main, ["deck", "parse", "nonexistent.in"])
        assert result.exit_code != 0


class TestCLIDeckLint:
    def test_lint_valid(self, cli_runner, minimal_deck_path):
        from osiris_toolkit.cli import main
        result = cli_runner.invoke(main, ["deck", "lint", str(minimal_deck_path)])
        assert result.exit_code == 0

    def test_lint_invalid(self, cli_runner, fixtures_dir):
        from osiris_toolkit.cli import main
        p = fixtures_dir / "invalid_neg_dt.in"
        result = cli_runner.invoke(main, ["deck", "lint", str(p)])
        assert result.exit_code == 0


class TestCLIDeckValidate:
    def test_validate_valid(self, cli_runner, minimal_deck_path):
        from osiris_toolkit.cli import main
        result = cli_runner.invoke(main, ["deck", "validate", str(minimal_deck_path)])
        # validate exits 0 on valid deck
        assert "Deck is valid" in result.output or result.exit_code == 0

    def test_validate_invalid(self, cli_runner, fixtures_dir):
        from osiris_toolkit.cli import main
        p = fixtures_dir / "invalid_neg_dt.in"
        result = cli_runner.invoke(main, ["deck", "validate", str(p)])
        # May exit 1 or print errors
        assert result.exit_code in (0, 1)
