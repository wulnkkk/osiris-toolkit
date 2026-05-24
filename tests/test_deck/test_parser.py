"""Tests for deck.parser — token-to-AST parser."""

import pytest

from osiris_toolkit.deck.ast import Deck, Section
from osiris_toolkit.deck.lexer import TokenType, tokenize
from osiris_toolkit.deck.parser import ParseError, parse_tokens


class TestParseTokens:
    def test_single_section(self):
        text = "simulation { omega_p0 = 3.55e15 }"
        deck = parse_tokens(tokenize(text))
        assert len(deck.sections) == 1
        assert deck.sections[0].name == "simulation"
        assert "omega_p0" in deck.sections[0].params

    def test_multiple_sections(self):
        text = "simulation { omega_p0 = 3.55e15 }\ngrid { nx_p(1:2) = 32, 32 }"
        deck = parse_tokens(tokenize(text))
        assert len(deck.sections) == 2
        assert deck.sections[0].name == "simulation"
        assert deck.sections[1].name == "grid"

    def test_section_with_string_param(self):
        text = 'grid { coordinates = "cartesian" }'
        deck = parse_tokens(tokenize(text))
        assert deck.sections[0].params["coordinates"] == "cartesian"

    def test_section_with_bool_param(self):
        text = "node_conf { if_periodic(1:2) = .true., .true. }"
        deck = parse_tokens(tokenize(text))
        param = deck.sections[0].params["if_periodic"]
        # Slice params are stored as dicts with value/dims/type
        if isinstance(param, dict):
            assert param["value"] == [True, True]
        else:
            assert param == [True, True]

    def test_section_with_slice_param_1d(self):
        text = "grid { nx_p(1:2) = 32, 32 }"
        deck = parse_tokens(tokenize(text))
        param = deck.sections[0].params["nx_p"]
        if isinstance(param, dict):
            assert param["value"] == [32, 32]
        else:
            assert param == [32, 32]

    def test_section_with_slice_param_2d(self):
        text = "emf_bound { type(1:2,1) = \"conducting\", \"conducting\" }"
        deck = parse_tokens(tokenize(text))
        assert "type" in deck.sections[0].params

    def test_empty_input(self):
        deck = parse_tokens(tokenize(""))
        assert len(deck.sections) == 0

    def test_deck_has_filename(self):
        deck = parse_tokens(tokenize("simulation { }"), filename="test.in")
        assert deck.filename == "test.in"


class TestParseErrors:
    def test_missing_rbrace(self):
        with pytest.raises(ParseError):
            parse_tokens(tokenize("simulation { omega_p0 = 3.55e15"))

    def test_missing_lbrace(self):
        with pytest.raises(ParseError):
            parse_tokens(tokenize("simulation omega_p0 = 3.55e15 }"))

    def test_unexpected_eof(self):
        with pytest.raises(ParseError):
            parse_tokens(tokenize("simulation {\n"))

    def test_parse_error_has_line_col(self):
        try:
            parse_tokens(tokenize("simulation {"))
        except ParseError as e:
            assert e.line >= 1
