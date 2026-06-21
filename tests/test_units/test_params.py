"""Tests for SimulationParams and UnitSystem."""

import pytest

from osiris_toolkit.exceptions import MissingParameterError, UnitConversionError
from osiris_toolkit.units import SimulationParams
from osiris_toolkit.units.converter import UnitSystem


class TestSimulationParams:
    def test_from_deck_basic(self) -> None:
        deck = {
            "sections": [
                {
                    "name": "simulation",
                    "params": {"omega_p0": 3.55e15, "n0": 1.0, "gamma": 5.0},
                }
            ]
        }
        params = SimulationParams.from_deck(deck)
        assert params.omega_p0 == 3.55e15
        assert params.n0 == 1.0
        assert params.gamma == 5.0

    def test_from_deck_missing_section(self) -> None:
        with pytest.raises(MissingParameterError, match="Missing 'simulation' section"):
            SimulationParams.from_deck({"sections": []})

    def test_from_deck_missing_omega_p0(self) -> None:
        with pytest.raises(MissingParameterError, match="omega_p0"):
            SimulationParams.from_deck({"sections": [{"name": "simulation", "params": {}}]})

    def test_from_omega_p0(self) -> None:
        params = SimulationParams.from_omega_p0(1.0e15)
        assert params.omega_p0 == 1.0e15
        assert params.n0 is None


class TestUnitSystem:
    def test_construction(self) -> None:
        us = UnitSystem(3.55e15)
        assert us.omega_p > 0

    def test_convert_length_um(self) -> None:
        us = UnitSystem(3.55e15)
        result = us.length.to(1.0, "um")
        assert isinstance(result, float)
        assert result > 0

    def test_convert_efield_gvpm(self) -> None:
        us = UnitSystem(3.55e15)
        result = us.e_field.to(1.0, "GV/m")
        assert result > 0

    def test_from_params(self) -> None:
        params = SimulationParams.from_omega_p0(1.0e15)
        us = UnitSystem.from_params(params)
        assert us.omega_p == 1.0e15

    def test_auto_units(self) -> None:
        us = UnitSystem(3.55e15)
        assert us.time.to(1.0, "auto") > 0
        assert us.length.to(1.0, "auto") > 0

    def test_negative_omega_p_raises(self) -> None:
        with pytest.raises(UnitConversionError, match="omega_p"):
            UnitSystem(-1.0)

    def test_unknown_quantity_raises(self) -> None:
        us = UnitSystem(1.0e15)
        with pytest.raises(UnitConversionError):
            us["nonexistent"]
