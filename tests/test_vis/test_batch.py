"""Unit tests for vis.batch.process_simulation."""

from pathlib import Path

import pytest


class TestProcessSimulation:
    """Test process_simulation with synthetic simulation directories."""

    def test_basic_batch_run(self, tmp_sim_dir, tmp_path):
        """Batch-process a minimal sim directory and verify output structure."""
        from osiris_toolkit.vis.batch import process_simulation

        out_root = tmp_path / "batch_output"
        process_simulation(
            sim_path=str(tmp_sim_dir),
            sim_name="test_sim",
            output_root=out_root,
        )

        sim_out = out_root / "test_sim"
        assert sim_out.is_dir()
        assert (sim_out / "fields").is_dir()
        assert (sim_out / "k_space").is_dir()
        assert (sim_out / "scattering").is_dir()
        assert (sim_out / "density").is_dir()

    def test_output_root_required(self):
        """process_simulation raises TypeError when output_root is missing."""
        from osiris_toolkit.vis.batch import process_simulation

        with pytest.raises(TypeError, match="output_root"):
            process_simulation(sim_path="/fake/path", sim_name="test")
