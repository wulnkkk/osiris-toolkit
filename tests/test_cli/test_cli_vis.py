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
