"""Tests for analysis result dataclass construction."""

import numpy as np

from osiris_toolkit.analysis._result_types import (
    DensityProfileResult,
    EMDynamicsResult,
    EMSpectrumResult,
    FieldEnergyResult,
    ParticleSpectrumResult,
    PoyntingResult,
    ScatteringResult,
    TemperatureResult,
)


class TestResultTypes:
    """Verify all result dataclasses can be constructed."""

    def test_field_energy_result(self):
        r = FieldEnergyResult(quantity="e1", iteration=50, time=10.0, total_energy=42.0)
        assert r.quantity == "e1"
        assert r.total_energy == 42.0

    def test_em_dynamics_result(self):
        r = EMDynamicsResult(iteration=50, time=10.0, e2_total=1.0, b2_total=2.0, total=3.0)
        assert r.total == 3.0

    def test_em_spectrum_result(self):
        kx = np.array([-1.0, 0.0, 1.0])
        ky = np.array([-1.0, 0.0, 1.0])
        spec = np.ones((3, 3))
        r = EMSpectrumResult(
            quantity="e1",
            iteration=50,
            time=10.0,
            kx_k0=kx,
            ky_k0=ky,
            spectrum=spec,
        )
        assert r.spectrum.shape == (3, 3)

    def test_poynting_result(self):
        arr = np.ones((10, 10))
        r = PoyntingResult(iteration=50, time=10.0, s1=arr, s2=arr, s3=arr)
        assert r.s1.shape == (10, 10)

    def test_scattering_result(self):
        r = ScatteringResult(
            quantity="e3",
            iterations=[0, 10, 20],
            times=[0.0, 1.0, 2.0],
            scattered_fraction=[0.0, 0.1, 0.2],
        )
        assert len(r.scattered_fraction) == 3

    def test_density_profile_result(self):
        r = DensityProfileResult(
            species="electrons",
            quantity="charge",
            iteration=50,
            time=10.0,
            axis=0,
            coord=np.arange(10),
            profile=np.ones(10),
        )
        assert r.profile.shape == (10,)

    def test_particle_spectrum_result(self):
        r = ParticleSpectrumResult(
            species="electrons",
            iteration=50,
            time=10.0,
            bin_centers=np.arange(100),
            counts=np.ones(100),
        )
        assert len(r.counts) == 100

    def test_temperature_result(self):
        r = TemperatureResult(
            species="electrons",
            iteration=50,
            time=10.0,
            components={"T11": 1.0, "T22": 2.0, "T33": 3.0},
        )
        assert r.components["T11"] == 1.0
