"""CLI tests for analyze subcommands."""


class TestCLIAnalyzeDescribe:
    def test_describe_valid(self, cli_runner, tmp_sim_dir):
        from osiris_toolkit.cli import main

        result = cli_runner.invoke(main, ["analyze", "describe", str(tmp_sim_dir), "-q", "e1", "-i", "0"])
        assert result.exit_code == 0
        assert "mean" in result.output

    def test_describe_missing_data(self, cli_runner, tmp_sim_dir_empty):
        from osiris_toolkit.cli import main

        result = cli_runner.invoke(main, ["analyze", "describe", str(tmp_sim_dir_empty), "-q", "e1", "-i", "0"])
        assert result.exit_code == 0
        assert "No data" in result.output
