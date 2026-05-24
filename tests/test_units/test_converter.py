"""Tests for units.converter — UnitConverter."""

import numpy as np
import pytest

from osiris_toolkit.units import UnitConverter


@pytest.fixture
def converter():
    return UnitConverter(3.55e15)


class TestUnitConverterInit:
    def test_init_with_omega_p(self):
        uc = UnitConverter(1.0e15)
        assert uc is not None

    def test_init_zero_raises(self):
        with pytest.raises(ValueError):
            UnitConverter(0.0)

    def test_init_negative_raises(self):
        with pytest.raises(ValueError):
            UnitConverter(-1.0e15)


class TestUnitConverterProperties:
    def test_omega_p_stored(self, converter):
        assert converter.omega_p == 3.55e15

    def test_repr(self, converter):
        r = repr(converter)
        assert "UnitConverter" in r


class TestConvert:
    def test_convert_time(self, converter):
        result = converter.convert(1.0, "time", "s")
        assert isinstance(result, float)
        assert result > 0

    def test_convert_time_to_s(self, converter):
        norm_time = 1.0
        si_time = converter.convert(norm_time, "time", "s")
        # 1/omega_p at 3.55e15 rad/s ≈ 2.8e-16 s
        assert 1e-17 < si_time < 1e-15
        assert si_time == pytest.approx(1.0 / 3.55e15, rel=0.01)

    def test_convert_norm_is_identity(self, converter):
        result = converter.convert(42.0, "time", "norm")
        assert result == 42.0

    def test_convert_length(self, converter):
        result = converter.convert(1.0, "length", "m")
        assert result > 0

    def test_convert_velocity(self, converter):
        result = converter.convert(0.5, "velocity", "m/s")
        assert result > 0

    def test_convert_e_field(self, converter):
        result = converter.convert(0.1, "e_field", "V/m")
        assert isinstance(result, float)

    def test_convert_array(self, converter):
        arr = np.array([0.0, 1.0, 2.0])
        result = converter.convert(arr, "length", "m")
        assert isinstance(result, np.ndarray)
        assert len(result) == 3

    def test_convert_invalid_quantity(self, converter):
        with pytest.raises(KeyError):
            converter.convert(1.0, "invalid_quantity", "m")

    def test_convert_invalid_unit(self, converter):
        with pytest.raises(KeyError):
            converter.convert(1.0, "time", "invalid_unit")


class TestLabelMethods:
    def test_get_label(self, converter):
        label = converter.get_label("time", "s")
        assert isinstance(label, str)

    def test_get_length_label(self, converter):
        label = converter.get_length_label("m")
        assert isinstance(label, str)

    def test_get_time_label(self, converter):
        label = converter.get_time_label("s")
        assert isinstance(label, str)


class TestScales:
    def test_get_scale(self, converter):
        s = converter.get_scale("time", "s")
        assert s > 0

    def test_get_scale_auto(self, converter):
        s = converter.get_scale("length", "auto")
        assert s > 0

    def test_get_scale_invalid_quantity(self, converter):
        with pytest.raises(KeyError):
            converter.get_scale("invalid", "m")


class TestPhysicalConstants:
    def test_constants_positive(self):
        from osiris_toolkit.units.converter import C_LIGHT, E_CHARGE, M_ELECTRON
        assert C_LIGHT > 0
        assert E_CHARGE > 0
        assert M_ELECTRON > 0
