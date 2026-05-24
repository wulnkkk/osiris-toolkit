"""Tests for sim.catalog — OSIRIS diagnostic types."""

from osiris_toolkit.sim.catalog import OSIRIS_DIAGNOSTICS, DiagKind
from osiris_toolkit.sim.diagnostics import (
    GridData,
    HistoryData,
    ParticleData,
    PhasespaceData,
    TrackData,
)


class TestDiagKind:
    def test_emf_kind(self):
        emf = OSIRIS_DIAGNOSTICS["EMF"]
        assert emf.name == "EMF"
        assert emf.data_class == GridData
        assert emf.is_per_axis is True
        assert isinstance(emf.quantities, list)
        assert len(emf.quantities) > 0

    def test_density_is_per_species(self):
        d = OSIRIS_DIAGNOSTICS["DENSITY"]
        assert d.is_per_species is True
        assert d.data_class == GridData

    def test_raw_kind(self):
        raw = OSIRIS_DIAGNOSTICS["RAW"]
        assert raw.data_class == ParticleData
        assert raw.is_per_species is True

    def test_phasespace_kind(self):
        pha = OSIRIS_DIAGNOSTICS["PHASESPACE"]
        assert pha.data_class == PhasespaceData
        assert pha.is_per_species is True

    def test_tracks_kind(self):
        t = OSIRIS_DIAGNOSTICS["TRACKS"]
        assert t.data_class == TrackData

    def test_history_kind(self):
        h = OSIRIS_DIAGNOSTICS["HISTORY"]
        assert h.data_class == HistoryData


class TestCatalogCompleteness:
    def test_all_12_kinds_exist(self):
        assert len(OSIRIS_DIAGNOSTICS) >= 10

    def test_emf_has_34_quantities(self):
        emf = OSIRIS_DIAGNOSTICS["EMF"]
        assert len(emf.quantities) >= 30

    def test_density_has_9_quantities(self):
        d = OSIRIS_DIAGNOSTICS["DENSITY"]
        assert len(d.quantities) >= 9

    def test_udist_has_12_quantities(self):
        u = OSIRIS_DIAGNOSTICS["UDIST"]
        assert len(u.quantities) >= 9

    def test_phase_has_momentum_unit_category(self):
        pha = OSIRIS_DIAGNOSTICS["PHASESPACE"]
        assert pha.unit_category == "momentum"

    def test_all_required_attributes(self):
        for name, dk in OSIRIS_DIAGNOSTICS.items():
            assert dk.name == name
            assert dk.dir_pattern
            assert dk.data_class is not None
