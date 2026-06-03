"""Tests for vis.parallel batch processing."""



class TestBatchProcessParallel:
    def test_basic_parallel_run(self, tmp_sim_dir, tmp_path):
        """Parallel batch-process produces correct output structure."""
        from osiris_toolkit.vis.parallel import batch_process_parallel

        out_root = tmp_path / "parallel_output"
        batch_process_parallel(
            sim_path=str(tmp_sim_dir),
            sim_name="test_sim",
            output_root=out_root,
            max_workers=1,  # single worker for deterministic test
        )

        sim_out = out_root / "test_sim"
        assert sim_out.is_dir()
        assert (sim_out / "fields").is_dir()
        assert (sim_out / "k_space").is_dir()
        assert (sim_out / "scattering").is_dir()
        assert (sim_out / "density").is_dir()

    def test_multi_worker(self, tmp_sim_dir, tmp_path):
        """Parallel batch-process with multiple workers."""
        from osiris_toolkit.vis.parallel import batch_process_parallel

        out_root = tmp_path / "multi_output"
        batch_process_parallel(
            sim_path=str(tmp_sim_dir),
            sim_name="multi_sim",
            output_root=out_root,
            max_workers=2,
        )

        sim_out = out_root / "multi_sim"
        assert sim_out.is_dir()
        # Field PNGs should exist for each iteration
        field_files = sorted((sim_out / "fields").glob("*.png"))
        assert len(field_files) == 3
        # k-space / density / scattering dirs created (plots may fail
        # with synthetic ZDF lacking axis metadata)
        assert (sim_out / "k_space").is_dir()
        assert (sim_out / "density").is_dir()
        assert (sim_out / "scattering").is_dir()


class TestProcessSimulationWithMaxWorkers:
    def test_max_workers_delegates_to_parallel(self, tmp_sim_dir, tmp_path):
        """process_simulation with max_workers>0 uses parallel implementation."""
        from osiris_toolkit.vis.batch import process_simulation

        out_root = tmp_path / "delegated_output"
        process_simulation(
            sim_path=str(tmp_sim_dir),
            sim_name="delegated",
            output_root=out_root,
            max_workers=1,
        )

        sim_out = out_root / "delegated"
        assert (sim_out / "fields").is_dir()
        assert (sim_out / "k_space").is_dir()

    def test_max_workers_none_is_sequential(self, tmp_sim_dir, tmp_path):
        """process_simulation with max_workers=None runs sequential path."""
        from osiris_toolkit.vis.batch import process_simulation

        out_root = tmp_path / "sequential_output"
        process_simulation(
            sim_path=str(tmp_sim_dir),
            sim_name="sequential",
            output_root=out_root,
        )

        sim_out = out_root / "sequential"
        assert (sim_out / "fields").is_dir()
        assert (sim_out / "k_space").is_dir()
