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

    def test_output_root_defaults_to_sim_figures(self, tmp_sim_dir):
        """When output_root is None, defaults to {sim_path}/figures/."""
        from osiris_toolkit.vis.batch import process_simulation

        process_simulation(
            sim_path=str(tmp_sim_dir),
            sim_name="test_sim",
        )

        sim_out = tmp_sim_dir / "figures" / "test_sim"
        assert sim_out.is_dir()
        assert (sim_out / "fields").is_dir()


class TestBatchResult:
    """Test process_simulation returns BatchResult."""

    def test_returns_batch_result(self, tmp_path, monkeypatch):
        """process_simulation returns BatchResult with files and errors."""
        from unittest.mock import MagicMock, patch
        from osiris_toolkit.vis.batch import process_simulation

        sim_dir = tmp_path / "sim"
        sim_dir.mkdir()
        ms_dir = sim_dir / "MS" / "FLD"
        ms_dir.mkdir(parents=True)

        fake_fld = MagicMock()
        fake_fld.data.shape = (2, 2)
        fake_fld.axes = []
        fake_fld.time = 0.0
        fake_fld.label = "e1"

        with patch(
            "osiris_toolkit.vis.batch.Simulation",
            autospec=True,
        ) as mock_sim_cls:
            mock_sim = mock_sim_cls.return_value
            mock_sim.list_fields.return_value = ["e1"]
            mock_sim.list_species.return_value = []
            mock_sim.list_iterations.return_value = [0]
            mock_sim.get_field.return_value = fake_fld
            mock_sim.output_root = tmp_path

            result = process_simulation(str(sim_dir), "test_sim")
            assert result.sim_name == "test_sim"
            assert isinstance(result.files, list)
            assert isinstance(result.errors, list)
            assert result.elapsed > 0


class TestProgressCallback:
    """Test progress_callback integration."""

    def test_callback_called_per_iteration(self, tmp_path):
        """progress_callback is called once per iteration."""
        from unittest.mock import MagicMock, patch
        from osiris_toolkit.vis.batch import process_simulation

        sim_dir = tmp_path / "sim"
        sim_dir.mkdir()
        ms_dir = sim_dir / "MS" / "FLD"
        ms_dir.mkdir(parents=True)

        fake_fld = MagicMock()
        fake_fld.data.shape = (2, 2)
        fake_fld.axes = []
        fake_fld.time = 0.0
        fake_fld.label = "e1"

        with patch(
            "osiris_toolkit.vis.batch.Simulation",
            autospec=True,
        ) as mock_sim_cls:
            mock_sim = mock_sim_cls.return_value
            mock_sim.list_fields.return_value = ["e1"]
            mock_sim.list_species.return_value = []
            mock_sim.list_iterations.return_value = [0, 10, 20]
            mock_sim.get_field.return_value = fake_fld
            mock_sim.output_root = tmp_path

            cb = MagicMock()
            process_simulation(str(sim_dir), "test_sim", progress_callback=cb)
            assert cb.call_count == 3
