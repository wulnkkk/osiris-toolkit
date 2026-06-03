"""Tests for PostVisHub cache management."""


class TestPostVisHubCache:
    def test_invalidate_cache_clears_namespaces(self):
        from osiris_toolkit.sim import Simulation
        from osiris_toolkit.vis import PostVisHub

        sim = Simulation.__new__(Simulation)
        hub = PostVisHub(sim)

        _ = hub.field
        assert "field" in hub.__dict__

        hub.invalidate_cache()
        assert "field" not in hub.__dict__
        assert "energy" not in hub.__dict__

    def test_set_converter_invalidates_cache(self):
        from osiris_toolkit.sim import Simulation
        from osiris_toolkit.units import UnitConverter
        from osiris_toolkit.vis import PostVisHub

        sim = Simulation.__new__(Simulation)
        hub = PostVisHub(sim)

        _ = hub.field
        assert "field" in hub.__dict__

        uc = UnitConverter.__new__(UnitConverter)
        hub.set_converter(uc)
        assert hub._converter is uc
        assert "field" not in hub.__dict__
