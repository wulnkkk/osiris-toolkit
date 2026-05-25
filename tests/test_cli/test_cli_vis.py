"""CLI tests for vis subcommands."""


class TestCLIVisPlot:
    def test_plot_valid(self, cli_runner, tmp_sim_dir, tmp_path):
        from osiris_toolkit.cli import main
        output = tmp_path / "output.png"
        result = cli_runner.invoke(main, ["vis", "plot", str(tmp_sim_dir),
                                          "-k", "EMF", "-q", "e1", "-i", "0",
                                          "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()

    def test_plot_missing_data(self, cli_runner, tmp_sim_dir_empty):
        from osiris_toolkit.cli import main
        result = cli_runner.invoke(main, ["vis", "plot", str(tmp_sim_dir_empty),
                                          "-k", "EMF", "-q", "e1", "-i", "0"])
        # May exit 0 or with message about no data
        assert result.exit_code in (0, 1)


class TestCLIVisBatch:
    def test_batch_valid(self, cli_runner, tmp_sim_dir, tmp_path):
        from osiris_toolkit.cli import main
        out_dir = tmp_path / "cli_batch_output"
        result = cli_runner.invoke(main, [
            "vis", "batch",
            "-o", str(out_dir),
            str(tmp_sim_dir), "test_sim",
        ])
        assert result.exit_code == 0
        assert (out_dir / "test_sim" / "fields").is_dir()
        assert (out_dir / "test_sim" / "k_space").is_dir()

    def test_batch_output_dir_defaults_to_sim_figures(self, cli_runner, tmp_sim_dir):
        """vis batch without -o defaults to {sim_path}/figures/."""
        from osiris_toolkit.cli import main
        result = cli_runner.invoke(main, [
            "vis", "batch",
            str(tmp_sim_dir), "test_sim",
        ])
        assert result.exit_code == 0
        assert (tmp_sim_dir / "figures" / "test_sim" / "fields").is_dir()

    def test_batch_odd_args(self, cli_runner, tmp_path):
        from osiris_toolkit.cli import main
        out_dir = tmp_path / "out"
        result = cli_runner.invoke(main, [
            "vis", "batch",
            "-o", str(out_dir),
            "/data/Au",
        ])
        assert result.exit_code != 0
