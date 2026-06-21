"""Tests for deck.lexer — tokenizer."""

from osiris_toolkit.deck.lexer import TokenType, tokenize


def _collect(source):
    return list(tokenize(source))


def _filter_types(source):
    return [t.type for t in _collect(source)]


class TestTokenizeBasics:
    def test_empty_input(self):
        tokens = _filter_types("")
        assert tokens == [TokenType.EOF]

    def test_whitespace_only(self):
        tokens = _filter_types("  \n\t  ")
        assert tokens == [TokenType.EOF]

    def test_comment_only(self):
        tokens = _filter_types("! this is a comment")
        assert tokens == [TokenType.EOF]

    def test_simple_section(self):
        tokens = _filter_types("simulation { }")
        assert tokens == [
            TokenType.SECTION_NAME,
            TokenType.LBRACE,
            TokenType.RBRACE,
            TokenType.EOF,
        ]

    def test_section_with_params(self):
        tokens = _filter_types("simulation {\n  omega_p0 = 3.55e15,\n}")
        expected = [
            TokenType.SECTION_NAME,
            TokenType.LBRACE,
            TokenType.NAME,
            TokenType.EQUALS,
            TokenType.REAL,
            TokenType.COMMA,
            TokenType.RBRACE,
            TokenType.EOF,
        ]
        assert tokens == expected

    def test_multiple_sections(self):
        source = "simulation { omega_p0 = 3.55e15 }\ngrid { nx_p(1:2) = 32, 32 }"
        tokens = _filter_types(source)
        assert tokens.count(TokenType.SECTION_NAME) == 2


class TestTokenizeValues:
    def test_string_value(self):
        tokens = _collect('coordinates = "cartesian"')
        types = [t.type for t in tokens]
        assert TokenType.STRING in types

    def test_boolean_true(self):
        tokens = _collect("flag = .true.")
        types = [t.type for t in tokens]
        assert TokenType.BOOLEAN in types

    def test_boolean_false(self):
        tokens = _collect("flag = .false.")
        types = [t.type for t in tokens]
        assert TokenType.BOOLEAN in types

    def test_integer_value(self):
        tokens = _collect("n = 42")
        types = [t.type for t in tokens]
        assert TokenType.INTEGER in types

    def test_float_value(self):
        tokens = _collect("dt = 0.07")
        types = [t.type for t in tokens]
        assert TokenType.REAL in types

    def test_fortran_d_exponent(self):
        tokens = _collect("omega_p0 = 3.55d15")
        types = [t.type for t in tokens]
        assert TokenType.REAL in types

    def test_negative_number(self):
        tokens = _collect("rqm = -1.0")
        types = [t.type for t in tokens]
        assert TokenType.REAL in types

    def test_slice_notation_1d(self):
        tokens = _collect("nx_p(1:2) = 32")
        types = [t.type for t in tokens]
        assert TokenType.SLICE in types

    def test_slice_notation_2d(self):
        tokens = _collect("type(1:2,1) = 0")
        types = [t.type for t in tokens]
        assert TokenType.SLICE in types


class TestTokenizeComments:
    def test_full_line_comment(self):
        tokens = _collect("! comment\nsimulation { }")
        assert len(tokens) >= 4

    def test_inline_comment(self):
        tokens = _collect("dt = 0.07 ! timestep")
        types = [t.type for t in tokens]
        assert TokenType.REAL in types


class TestTokenPositions:
    def test_token_has_line_col(self):
        tokens = _collect("dt = 0.07")
        real_token = next(t for t in tokens if t.type == TokenType.REAL)
        assert real_token.line >= 1
        assert real_token.col >= 1


class TestTokenizeEdgeCases:
    def test_unicode_in_comments(self):
        tokens = _collect("! 中文注释\ndt = 0.07")
        types = [t.type for t in tokens]
        assert TokenType.NAME in types

    def test_section_name_with_underscore(self):
        tokens = _filter_types("time_step { }")
        assert tokens[0] == TokenType.SECTION_NAME

    def test_no_comma_before_rbrace(self):
        tokens = _filter_types("simulation { omega_p0 = 3.55e15 }")
        assert TokenType.COMMA not in tokens  # no comma before }
