"""Tests for units.converter — UnitSystem."""

import numpy as np
import pytest

from osiris_toolkit.exceptions import UnitConversionError
from osiris_toolkit.units.converter import UnitSystem


@pytest.fixture
def system():
    return UnitSystem(3.55e15)


class TestUnitSystemInit:
    def test_init_with_omega_p(self):
        us = UnitSystem(1.0e15)
        assert us is not None

    def test_init_zero_raises(self):
        with pytest.raises(UnitConversionError):
            UnitSystem(0.0)

    def test_init_negative_raises(self):
        with pytest.raises(UnitConversionError):
            UnitSystem(-1.0e15)


class TestUnitSystemProperties:
    def test_omega_p_stored(self, system):
        assert system.omega_p == 3.55e15

    def test_repr(self, system):
        r = repr(system)
        assert "UnitSystem" in r


class TestConvert:
    def test_convert_time(self, system):
        result = system.time.to(1.0, "s")
        assert isinstance(result, float)
        assert result > 0

    def test_convert_time_to_s(self, system):
        norm_time = 1.0
        si_time = system.time.to(norm_time, "s")
        # 1/omega_p at 3.55e15 rad/s ≈ 2.8e-16 s
        assert 1e-17 < si_time < 1e-15
        assert si_time == pytest.approx(1.0 / 3.55e15, rel=0.01)

    def test_convert_norm_is_identity(self, system):
        result = system.time.to(42.0, "norm")
        assert result == 42.0

    def test_convert_length(self, system):
        result = system.length.to(1.0, "m")
        assert result > 0

    def test_convert_velocity(self, system):
        result = system.velocity.to(0.5, "m/s")
        assert result > 0

    def test_convert_e_field(self, system):
        result = system.e_field.to(0.1, "V/m")
        assert isinstance(result, float)

    def test_convert_array(self, system):
        arr = np.array([0.0, 1.0, 2.0])
        result = system.length.to(arr, "m")
        assert isinstance(result, np.ndarray)
        assert len(result) == 3

    def test_convert_invalid_quantity(self, system):
        with pytest.raises(UnitConversionError):
            system["invalid_quantity"]

    def test_convert_invalid_unit(self, system):
        with pytest.raises(UnitConversionError):
            system.time.to(1.0, "invalid_unit")


class TestLabelMethods:
    def test_get_label(self, system):
        label = system.time.label("s")
        assert isinstance(label, str)

    def test_get_length_label(self, system):
        label = system.length.label("m")
        assert isinstance(label, str)

    def test_get_time_label(self, system):
        label = system.time.label("s")
        assert isinstance(label, str)


class TestScales:
    def test_get_scale(self, system):
        s = system.time.scales["s"]
        assert s > 0

    def test_get_scale_auto(self, system):
        s = system.length.scales["um"]  # auto unit for length
        assert s > 0

    def test_get_scale_invalid_quantity(self, system):
        with pytest.raises(UnitConversionError):
            system["invalid"]


class TestPhysicalConstants:
    def test_constants_positive(self):
        from osiris_toolkit.units.converter import C_LIGHT, E_CHARGE, M_ELECTRON

        assert C_LIGHT > 0
        assert E_CHARGE > 0
        assert M_ELECTRON > 0
