"""Integration tests for PostProcessor."""



class TestPostProcessor:
    """Test PostProcessor with synthetic simulation."""

    def test_construction(self, tmp_sim_dir):
        """PostProcessor can be constructed from a sim path."""
        from osiris_toolkit.postproc import PostProcessor
        from osiris_toolkit.sim import Simulation

        sim = Simulation(str(tmp_sim_dir))
        pp = PostProcessor(sim)
        assert pp.analyze is not None
        assert pp.vis is not None

    def test_analyze_emf_field_energy(self, tmp_sim_dir):
        """analyze.emf.field_energy returns FieldEnergyResult."""
        from osiris_toolkit.postproc import PostProcessor
        from osiris_toolkit.sim import Simulation

        sim = Simulation(str(tmp_sim_dir))
        pp = PostProcessor(sim)

        result = pp.analyze.emf.field_energy("e1", iteration=0)
        assert result.quantity == "e1"
        assert result.iteration == 0
        assert isinstance(result.total_energy, float)

    def test_analyze_emf_em_dynamics(self, tmp_sim_dir):
        """analyze.emf.em_dynamics returns EMDynamicsResult."""
        from osiris_toolkit.postproc import PostProcessor
        from osiris_toolkit.sim import Simulation

        sim = Simulation(str(tmp_sim_dir))
        pp = PostProcessor(sim)

        result = pp.analyze.emf.em_dynamics(iteration=0)
        assert result.total > 0
        assert result.e2_total > 0 or result.b2_total > 0

    def test_lazy_loading(self, tmp_sim_dir):
        """Repeated access to analyze/vis returns same instance."""
        from osiris_toolkit.postproc import PostProcessor
        from osiris_toolkit.sim import Simulation

        sim = Simulation(str(tmp_sim_dir))
        pp = PostProcessor(sim)

        a1 = pp.analyze
        a2 = pp.analyze
        assert a1 is a2

        v1 = pp.vis
        v2 = pp.vis
        assert v1 is v2

    def test_batch_runs(self, tmp_sim_dir, tmp_path):
        """pp.batch() produces expected output structure."""
        from osiris_toolkit.postproc import PostProcessor
        from osiris_toolkit.sim import Simulation

        sim = Simulation(str(tmp_sim_dir))
        pp = PostProcessor(sim)

        out_root = tmp_path / "pp_output"
        pp.batch(sim_name="test_sim", output_root=str(out_root))

        sim_out = out_root / "test_sim"
        assert sim_out.is_dir()
        assert (sim_out / "fields").is_dir()
