"""Tests for sim._parse — filename and text parsing helpers."""

import pytest

from osiris_toolkit.sim._parse import _parse_iter_file, _parse_quantity


class TestParseIterFile:
    def test_zdf_file(self):
        q, label, it = _parse_iter_file("e1-000050.zdf")
        assert q == "e1"
        assert label == ""
        assert it == 50

    def test_h5_file(self):
        q, label, it = _parse_iter_file("charge-000100.h5")
        assert q == "charge"
        assert label == ""
        assert it == 100

    def test_with_label(self):
        q, label, it = _parse_iter_file("x1x2-electrons-000000.zdf")
        assert q == "x1x2"
        assert label == "electrons"
        assert it == 0

    def test_flat_density(self):
        """Flat DENSITY format: charge-electrons-000100.zdf."""
        q, label, it = _parse_iter_file("charge-electrons-000100.zdf")
        assert q == "charge"
        assert label == "electrons"
        assert it == 100

    def test_invalid_format(self):
        from osiris_toolkit.exceptions import FormatError

        with pytest.raises(FormatError):
            _parse_iter_file("not-a-valid-filename.txt")


class TestParseQuantity:
    def test_plain(self):
        q, rt = _parse_quantity("e1")
        assert q == "e1"
        assert rt == ""

    def test_savg(self):
        q, rt = _parse_quantity("e1_savg")
        assert q == "e1"
        assert rt == "savg"

    def test_tavg(self):
        q, rt = _parse_quantity("charge_tavg")
        assert q == "charge"
        assert rt == "tavg"

    def test_no_false_match(self):
        q, rt = _parse_quantity("something_else")
        assert q == "something_else"
        assert rt == ""
