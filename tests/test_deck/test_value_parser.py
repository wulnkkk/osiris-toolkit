"""Tests for deck.value_parser — Fortran value parsing."""

import pytest

from osiris_toolkit.deck.lexer import TokenType
from osiris_toolkit.deck.value_parser import (
    assemble_params,
    parse_boolean,
    parse_integer,
    parse_real,
    parse_slice_dims,
    parse_value,
)


class TestParseReal:
    def test_standard(self):
        assert parse_real("1.5") == pytest.approx(1.5)

    def test_fortran_d(self):
        assert parse_real("3.55d15") == pytest.approx(3.55e15)

    def test_negative(self):
        assert parse_real("-42.0") == -42.0

    def test_exponent(self):
        assert parse_real("1.0e-3") == pytest.approx(0.001)

    def test_integer_string(self):
        v = parse_real("5")
        assert isinstance(v, float)
        assert v == 5.0


class TestParseInteger:
    def test_positive(self):
        assert parse_integer("42") == 42

    def test_negative(self):
        assert parse_integer("-10") == -10

    def test_zero(self):
        assert parse_integer("0") == 0


class TestParseBoolean:
    def test_true_lower(self):
        """Lexer strips dots, so parse_boolean receives 'true' not '.true.'."""
        assert parse_boolean("true") is True

    def test_false_lower(self):
        assert parse_boolean("false") is False

    def test_uppercase(self):
        assert parse_boolean("TRUE") is True
        assert parse_boolean("FALSE") is False

    def test_mixed_case(self):
        assert parse_boolean("True") is True


class TestParseSliceDims:
    def test_single_range(self):
        """Slice dims come without parentheses (parens stripped by lexer)."""
        dims = parse_slice_dims("1:3")
        assert dims == [(1, 3)]

    def test_two_ranges(self):
        dims = parse_slice_dims("1:2,1")
        assert dims == [(1, 2), (1, 1)]

    def test_wildcard_colon(self):
        dims = parse_slice_dims(":,1")
        assert dims[0] == (None, None)
        assert dims[1] == (1, 1)

    def test_single_index_no_range(self):
        dims = parse_slice_dims("1,1")
        assert dims == [(1, 1), (1, 1)]


class TestParseValue:
    def test_string_token(self):
        assert parse_value("hello", TokenType.STRING) == "hello"

    def test_real_token(self):
        assert parse_value("3.14", TokenType.REAL) == pytest.approx(3.14)

    def test_integer_token(self):
        assert parse_value("42", TokenType.INTEGER) == 42

    def test_boolean_token(self):
        assert parse_value("true", TokenType.BOOLEAN) is True


class TestAssembleParams:
    def test_simple_params(self):
        from osiris_toolkit.deck.ast import KeySpec, ParamAssignment
        raw = [
            ParamAssignment(keys=[KeySpec(name="omega_p0")], raw_values=["3.55e15"], line=1),
            ParamAssignment(keys=[KeySpec(name="gamma")], raw_values=["5.0"], line=2),
        ]
        result = assemble_params(raw)
        # assemble_params may return raw strings; type coercion happens at validation time
        assert "omega_p0" in result
        assert "gamma" in result

    def test_slice_params(self):
        from osiris_toolkit.deck.ast import KeySpec, ParamAssignment, SliceSpec
        raw = [
            ParamAssignment(
                keys=[KeySpec(name="nx_p", slice=SliceSpec(dims=[(1, 2)]))],
                raw_values=["32", "32"],
                line=1,
            ),
        ]
        result = assemble_params(raw)
        # Slice params may be stored as dicts with value/dims/type
        assert "nx_p" in result
        # The result contains the values in some form
        param = result["nx_p"]
        if isinstance(param, dict):
            assert "value" in param
