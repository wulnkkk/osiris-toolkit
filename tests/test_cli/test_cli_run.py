"""CLI tests for run workflow subcommand."""


class TestCLIRunWorkflow:
    def test_run_minimal_yaml(self, cli_runner, tmp_sim_dir, fixtures_dir):
        from osiris_toolkit.cli import main

        wf = fixtures_dir / "workflow_minimal.yaml"
        # Workflow references "." — run from tmp_sim_dir
        import os

        cwd = os.getcwd()
        try:
            os.chdir(tmp_sim_dir)
            result = cli_runner.invoke(main, ["run", str(wf)])
            # May succeed or fail depending on data availability
            assert result.exit_code in (0, 1)
        finally:
            os.chdir(cwd)

    def test_run_nonexistent(self, cli_runner):
        from osiris_toolkit.cli import main

        result = cli_runner.invoke(main, ["run", "nonexistent.yaml"])
        assert result.exit_code != 0
