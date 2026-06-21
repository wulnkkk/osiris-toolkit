"""CLI tests for sim subcommands."""


class TestCLISimInfo:
    def test_info_valid_dir(self, cli_runner, tmp_sim_dir):
        from osiris_toolkit.cli import main

        result = cli_runner.invoke(main, ["sim", "info", str(tmp_sim_dir)])
        assert result.exit_code == 0
        assert "Simulation:" in result.output

    def test_info_empty_dir(self, cli_runner, tmp_sim_dir_empty):
        from osiris_toolkit.cli import main

        result = cli_runner.invoke(main, ["sim", "info", str(tmp_sim_dir_empty)])
        assert result.exit_code == 0

    def test_info_nonexistent(self, cli_runner):
        from osiris_toolkit.cli import main

        result = cli_runner.invoke(main, ["sim", "info", "nonexistent_dir"])
        assert result.exit_code != 0


class TestCLISimList:
    def test_list_emf(self, cli_runner, tmp_sim_dir):
        from osiris_toolkit.cli import main

        result = cli_runner.invoke(main, ["sim", "list", str(tmp_sim_dir), "-k", "EMF"])
        assert result.exit_code == 0
        assert "e1" in result.output

    def test_list_unknown_kind(self, cli_runner, tmp_sim_dir):
        from osiris_toolkit.cli import main

        result = cli_runner.invoke(main, ["sim", "list", str(tmp_sim_dir), "-k", "UNKNOWN"])
        assert result.exit_code == 0
        assert "not recognized" in result.output.lower() or "Known" in result.output
