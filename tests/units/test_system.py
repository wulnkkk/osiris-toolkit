"""Tests for UnitSystem."""

import pytest

from osiris_toolkit.exceptions import UnitConversionError
from osiris_toolkit.units.converter import UnitSystem
from osiris_toolkit.units.params import SimulationParams


class TestUnitSystem:
    def test_construction(self):
        s = UnitSystem(3.55e15)
        assert s.omega_p == 3.55e15
        assert s.length.name == "length"

    def test_length_conversion(self):
        s = UnitSystem(3.55e15)
        l_um = s.length.to(1.0, "um")
        assert l_um > 0

    def test_length_roundtrip(self):
        s = UnitSystem(3.55e15)
        val_norm = 1.0
        val_um = s.length.to(val_norm, "um")
        val_back = val_um / s.length.scales["um"]
        assert val_back == pytest.approx(val_norm)

    def test_wavenumber_without_omega0(self):
        s = UnitSystem(3.55e15)
        assert "k0" not in s.wavenumber.scales
        assert "rad/um" in s.wavenumber.scales
        with pytest.raises(UnitConversionError):
            s.wavenumber.to(1.0, "k0")

    def test_wavenumber_with_omega0(self):
        pytest.skip("Requires Task 4: SimulationParams omega0_norm extension")
        # params = SimulationParams(omega_p0=3.55e15, omega0_norm=10.0)
        # s = UnitSystem(3.55e15, params=params)
        # assert "k0" in s.wavenumber.scales
        # result = s.wavenumber.to(100.0, "k0")
        # expected = 100.0 / 10.0
        # assert result == pytest.approx(expected)

    def test_getitem(self):
        s = UnitSystem(3.55e15)
        assert s["length"] is s.length
        assert s["e_field"] is s.e_field

    def test_getitem_unknown(self):
        s = UnitSystem(3.55e15)
        with pytest.raises(UnitConversionError, match="Unknown"):
            s["not_a_quantity"]

    def test_label_norm(self):
        s = UnitSystem(3.55e15)
        assert s.length.label("norm") == "[c/omega_p]"

    def test_label_physical(self):
        s = UnitSystem(3.55e15)
        lbl = s.time.label("ps")
        assert "ps" in lbl

    def test_latex(self):
        s = UnitSystem(3.55e15)
        latex = s.e_field.latex("GV/m")
        assert "GV/m" in latex
        assert "$" in latex

    def test_from_params(self):
        params = SimulationParams(omega_p0=3.55e15, n0=1.0, gamma=2.0)
        s = UnitSystem.from_params(params)
        assert s.omega_p == 3.55e15
        assert s.params is params

    def test_omega_p_must_be_positive(self):
        with pytest.raises(UnitConversionError, match="omega_p"):
            UnitSystem(0)
        with pytest.raises(UnitConversionError, match="omega_p"):
            UnitSystem(-1.0)
