"""Tests for workflow.pipeline module."""

import json
import tempfile
from pathlib import Path

import pytest

from osiris_toolkit.exceptions import PipelineError
from osiris_toolkit.workflow.pipeline import (
    DeckParseStep,
    DeckValidateStep,
    Pipeline,
    PipelineContext,
    PipelineStep,
)


class _TestStep(PipelineStep):
    """A step that records it was called."""

    name = "test_step"

    def __init__(self) -> None:
        self.called = False

    def run(self, ctx: PipelineContext) -> PipelineContext:
        self.called = True
        ctx.extra["test_ran"] = True
        return ctx


class TestPipelineContext:
    def test_default(self) -> None:
        ctx = PipelineContext()
        assert ctx.deck is None
        assert ctx.sim is None

    def test_require_deck_raises(self) -> None:
        ctx = PipelineContext()
        with pytest.raises(PipelineError, match="deck not loaded"):
            ctx.require_deck()

    def test_require_sim_raises(self) -> None:
        ctx = PipelineContext()
        with pytest.raises(PipelineError, match="Simulation not loaded"):
            ctx.require_sim()


class TestPipeline:
    def test_empty_pipeline(self) -> None:
        pipe = Pipeline([])
        ctx = pipe.run()
        assert isinstance(ctx, PipelineContext)

    def test_single_step(self) -> None:
        step = _TestStep()
        pipe = Pipeline([step])
        ctx = pipe.run()
        assert step.called
        assert ctx.extra["test_ran"] is True

    def test_chain_steps(self) -> None:
        step1 = _TestStep()
        step2 = _TestStep()
        pipe = Pipeline([step1, step2])
        pipe.run()
        assert step1.called
        assert step2.called


class TestDeckParseStep:
    def test_parse_au_deck(self) -> None:
        deck_path = Path(__file__).resolve().parents[3] / "osiris-deck-parser" / "inputtest" / "Au.in"
        if not deck_path.exists():
            pytest.skip("Test deck not found")

        ctx = PipelineContext()
        step = DeckParseStep(path=deck_path)
        ctx = step.run(ctx)

        assert ctx.deck is not None
        assert len(ctx.deck["sections"]) > 0
        assert ctx.params is not None
        assert ctx.params.omega_p0 > 0
        assert ctx.converter is not None
        assert ctx.deck_path == deck_path

    def test_validate_valid_deck(self) -> None:
        deck_path = Path(__file__).resolve().parents[3] / "osiris-1.0.0" / "decks" / "test" / "base-2d"
        if not deck_path.exists():
            pytest.skip("Test deck not found")

        ctx = PipelineContext()
        ctx = DeckParseStep(path=deck_path).run(ctx)
        ctx = DeckValidateStep().run(ctx)
        # Should not raise — base-2d has no errors


class TestPipelineYaml:
    def test_from_yaml(self) -> None:
        import os

        # Write a minimal deck to a temp file for the YAML to reference
        deck_fd, deck_path = tempfile.mkstemp(suffix=".in")
        os.write(deck_fd, b"simulation { omega_p0 = 3.55e15, }\n")
        os.close(deck_fd)

        # Use forward slashes to avoid YAML escape-sequence issues on Windows
        yaml_path = deck_path.replace("\\", "/")
        yaml_content = f"""pipeline:
  - deck_parse:
      path: \"{yaml_path}\"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            tmp = f.name

        try:
            pipe = Pipeline.from_yaml(tmp)
            assert len(pipe._steps) == 1
            assert isinstance(pipe._steps[0], DeckParseStep)
            ctx = pipe.run()
            assert ctx.params is not None
            assert ctx.params.omega_p0 == 3.55e15
        finally:
            Path(tmp).unlink()
            Path(deck_path).unlink()


class TestPipelineDryRun:
    """Test Pipeline dry_run mode."""

    def test_dry_run_does_not_execute_steps(self):
        """dry_run=True skips step execution."""
        from osiris_toolkit.workflow.pipeline import (
            Pipeline,
            PipelineContext,
            PipelineStep,
        )

        executed = []

        class CounterStep(PipelineStep):
            name = "counter"

            def run(self, ctx):
                executed.append(1)
                return ctx

        ctx = PipelineContext(dry_run=True)
        pipe = Pipeline([CounterStep()])
        pipe.run(ctx)
        assert len(executed) == 0

    def test_dry_run_logs_step_name(self, caplog):
        """dry_run=True logs step names."""
        import logging

        from osiris_toolkit.workflow.pipeline import (
            Pipeline,
            PipelineContext,
            PipelineStep,
        )

        # Ensure the pipeline module logger propagates INFO to caplog
        logging.getLogger("osiris_toolkit.workflow.pipeline").setLevel(logging.INFO)

        class DummyStep(PipelineStep):
            name = "dummy"

            def run(self, ctx):
                return ctx

        ctx = PipelineContext(dry_run=True)
        pipe = Pipeline([DummyStep()])
        with caplog.at_level(logging.INFO):
            pipe.run(ctx)
        assert any("DRY RUN" in m for m in caplog.messages)
        assert any("dummy" in m for m in caplog.messages)

    def test_normal_run_still_works(self):
        """dry_run=False (default) executes steps as before."""
        from osiris_toolkit.workflow.pipeline import (
            Pipeline,
            PipelineContext,
            PipelineStep,
        )

        executed = []

        class CounterStep(PipelineStep):
            name = "counter"

            def run(self, ctx):
                executed.append(1)
                return ctx

        pipe = Pipeline([CounterStep()])
        pipe.run(PipelineContext())
        assert len(executed) == 1


class TestPipelineSnapshot:
    def test_save_snapshot_writes_json(self, tmp_path):
        ctx = PipelineContext(
            deck_path=Path("/fake/deck.in"),
            sim_path=Path("/fake/sim"),
            dry_run=True,
        )
        ctx.extra = {"key": "value"}

        snap_path = tmp_path / "snapshot.json"
        result = ctx.save_snapshot(snap_path)
        assert result.exists()

        raw = json.loads(snap_path.read_text())
        assert raw["deck_path"] == str(Path("/fake/deck.in"))
        assert raw["sim_path"] == str(Path("/fake/sim"))
        assert raw["dry_run"] is True
        assert raw["extra"] == {"key": "value"}
