"""Pipeline orchestration for automated simulation workflows.

Provides a lightweight pipeline framework where each step is a callable
that transforms a shared context. Pipelines can be configured via YAML
files or constructed programmatically.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from osiris_toolkit.deck.main import lint_deck_file, parse_deck_file
from osiris_toolkit.exceptions import MissingParameterError, PipelineError
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import SimulationParams, UnitConverter

# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------


@dataclass
class PipelineContext:
    """Shared state passed between pipeline steps.

    Steps read from and write to this context. Keys that are None
    indicate data not yet available.

    Attributes
    ----------
    deck_path : Path | None
        Path to the input deck file.
    sim_path : Path | None
        Path to the simulation output directory.
    deck : dict | None
        Parsed deck dictionary (from ``parse_deck_file``).
    params : SimulationParams | None
        Physical parameters extracted from the deck.
    sim : Simulation | None
        Loaded Simulation object.
    converter : UnitConverter | None
        Unit converter built from params.
    extra : dict
        Arbitrary user-defined key-value storage.
    """

    deck_path: Path | None = None
    sim_path: Path | None = None
    deck: dict | None = None
    params: SimulationParams | None = None
    sim: Simulation | None = None
    converter: UnitConverter | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False

    def require_deck(self) -> dict:
        """Return deck or raise."""
        if self.deck is None:
            raise PipelineError("Pipeline: deck not loaded. Run DeckParseStep first.")
        return self.deck

    def require_sim(self) -> Simulation:
        """Return sim or raise."""
        if self.sim is None:
            raise PipelineError("Pipeline: Simulation not loaded. Run SimLoadStep first.")
        return self.sim

    def require_converter(self) -> UnitConverter:
        """Return converter or raise."""
        if self.converter is None:
            raise PipelineError("Pipeline: UnitConverter not built. Ensure deck is loaded.")
        return self.converter

    def save_snapshot(self, path: str | Path) -> Path:
        """Save non-runtime state to a JSON file.

        Saves deck_path, sim_path, dry_run, and extra. Does NOT save
        deck, sim, params, or converter objects — those are rebuilt
        from paths when the snapshot is loaded.
        """
        data: dict[str, Any] = {
            "deck_path": str(self.deck_path) if self.deck_path else None,
            "sim_path": str(self.sim_path) if self.sim_path else None,
            "dry_run": self.dry_run,
            "extra": self.extra,
        }
        path = Path(path)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return path

    @classmethod
    def load_snapshot(cls, path: str | Path) -> PipelineContext:
        """Restore context from a snapshot file.

        Rebuilds deck and sim from saved paths. Returns a fully
        functional PipelineContext ready for resumed execution.
        """
        from osiris_toolkit.deck.parser import parse_deck_file
        from osiris_toolkit.sim import Simulation
        from osiris_toolkit.units.converter import UnitConverter
        from osiris_toolkit.units.params import SimulationParams

        data = json.loads(Path(path).read_text())
        ctx = cls(dry_run=data.get("dry_run", False))
        ctx.extra = data.get("extra", {})

        if data.get("deck_path"):
            ctx.deck_path = Path(data["deck_path"])
            ctx.deck = parse_deck_file(str(ctx.deck_path))
            ctx.params = SimulationParams.from_deck(ctx.deck)
            ctx.converter = UnitConverter.from_params(ctx.params)

        if data.get("sim_path"):
            ctx.sim_path = Path(data["sim_path"])
            ctx.sim = Simulation(str(ctx.sim_path))

        return ctx


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------


class PipelineStep(ABC):
    """Abstract base for a pipeline step.

    Subclasses implement ``run(ctx) -> PipelineContext``.
    """

    name: str = "step"

    @abstractmethod
    def run(self, ctx: PipelineContext) -> PipelineContext:
        ...

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {self.name}>"


class DeckParseStep(PipelineStep):
    """Parse an OSIRIS input deck into a dictionary."""

    name = "deck_parse"

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.deck_path = self._path
        ctx.deck = parse_deck_file(str(self._path))
        try:
            ctx.params = SimulationParams.from_deck(ctx.deck)
        except (ValueError, MissingParameterError):
            # omega_p0 not found — unit conversion will be unavailable
            ctx.params = None
        if ctx.params:
            ctx.converter = UnitConverter.from_params(ctx.params)
        return ctx


class DeckValidateStep(PipelineStep):
    """Lint and validate an input deck."""

    name = "deck_validate"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.require_deck()  # ensure deck is loaded
        # Lint requires a file path; re-read from disk
        if ctx.deck_path is None:
            raise PipelineError("DeckValidateStep requires deck_path in context.")
        report = lint_deck_file(str(ctx.deck_path))
        if report.has_errors():
            issues = [f"[{i.rule_id}] {i.message}" for i in report.errors()]
            raise PipelineError(
                f"Deck validation failed with {len(issues)} error(s):\n  "
                + "\n  ".join(issues)
            )
        return ctx


class SimLoadStep(PipelineStep):
    """Load a simulation output directory."""

    name = "sim_load"

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.sim_path = self._path
        ctx.sim = Simulation(str(self._path))
        # If we didn't get a converter from the deck, try to find a deck
        # in the simulation directory
        if ctx.converter is None:
            in_files = sorted(self._path.glob("*.in"))
            if in_files:
                try:
                    deck = parse_deck_file(str(in_files[0]))
                    ctx.params = SimulationParams.from_deck(deck)
                    ctx.converter = UnitConverter.from_params(ctx.params)
                except (ValueError, OSError, MissingParameterError):
                    pass
        return ctx


@dataclass
class AnalyzeStep(PipelineStep):
    """Run statistical analysis on a set of quantities."""

    name = "analyze"

    quantities: list[str] = field(default_factory=lambda: ["e1"])
    iterations: list[int] | str = "all"
    kind: str = "EMF"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        sim = ctx.require_sim()
        results: dict[str, Any] = {}

        for qty in self.quantities:
            grid = sim.get_field(qty, 0)
            if grid is not None:
                results[qty] = {
                    "mean": float(grid.data.mean()),
                    "std": float(grid.data.std()),
                    "min": float(grid.data.min()),
                    "max": float(grid.data.max()),
                    "shape": list(grid.data.shape),
                }

        ctx.extra.setdefault("analysis_results", {})[self.kind] = results
        return ctx


@dataclass
class VisualizeStep(PipelineStep):
    """Generate plots for specified diagnostic kinds."""

    name = "visualize"

    kinds: list[str] = field(default_factory=lambda: ["EMF"])
    iteration: int = 0
    output_dir: str = "./figures"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        sim = ctx.require_sim()
        output = Path(self.output_dir)
        output.mkdir(parents=True, exist_ok=True)

        from osiris_toolkit.postproc import PostProcessor

        pp = PostProcessor(sim, converter=ctx.converter)

        for kind in self.kinds:
            kind_lower = kind.lower()
            if kind_lower == "emf":
                pp.vis.plot(
                    "EMF",
                    quantity="e1",
                    iteration=self.iteration,
                    output=str(output / f"e1_{self.iteration:06d}.png"),
                )

        ctx.extra["figures_dir"] = str(output)
        return ctx


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class Pipeline:
    """An ordered sequence of pipeline steps.

    Parameters
    ----------
    steps : list[PipelineStep]
        Steps to execute in order.
    """

    def __init__(self, steps: list[PipelineStep]) -> None:
        self._steps = steps

    def run(self, ctx: PipelineContext | None = None) -> PipelineContext:
        """Execute all steps in order, returning the final context.

        Parameters
        ----------
        ctx : PipelineContext | None
            Initial context. A fresh context is created if None.

        Returns
        -------
        PipelineContext
            The context after all steps have run.

        Raises
        ------
        RuntimeError
            If any step fails.
        """
        import logging
        _log = logging.getLogger(__name__)

        if ctx is None:
            ctx = PipelineContext()

        for step in self._steps:
            if ctx.dry_run:
                _log.info("[DRY RUN] Would execute: %s", step.name)
            else:
                ctx = step.run(ctx)

        return ctx

    @classmethod
    def from_yaml(cls, path: str | Path) -> Pipeline:
        """Build a pipeline from a YAML configuration file.

        Parameters
        ----------
        path : str or Path
            Path to the YAML file.

        Returns
        -------
        Pipeline

        YAML format::

            pipeline:
              - deck_parse:
                  path: "./input/simulation.in"
              - deck_validate:
              - sim_load:
                  path: "./output/"
              - analyze:
                  quantities: ["e1", "charge"]
              - visualize:
                  kinds: ["EMF", "DENSITY"]
                  iteration: 100
                  output_dir: "./figures/"
        """
        with open(path, encoding="utf-8") as fh:
            config = yaml.safe_load(fh)

        steps: list[PipelineStep] = []
        for entry in config.get("pipeline", []):
            for step_name, step_args in entry.items():
                step_args = step_args or {}
                if step_name == "deck_parse":
                    steps.append(DeckParseStep(path=step_args.get("path", ".")))
                elif step_name == "deck_validate":
                    steps.append(DeckValidateStep())
                elif step_name == "sim_load":
                    steps.append(SimLoadStep(path=step_args.get("path", ".")))
                elif step_name == "analyze":
                    steps.append(
                        AnalyzeStep(
                            quantities=step_args.get("quantities", ["e1"]),
                            kind=step_args.get("kind", "EMF"),
                        )
                    )
                elif step_name == "visualize":
                    steps.append(
                        VisualizeStep(
                            kinds=step_args.get("kinds", ["EMF"]),
                            iteration=step_args.get("iteration", 0),
                            output_dir=step_args.get("output_dir", "./figures"),
                        )
                    )
                else:
                    raise PipelineError(
                        f"Unknown pipeline step: {step_name!r}. "
                        "Known: deck_parse, deck_validate, sim_load, analyze, visualize"
                    )

        return cls(steps)


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def quick_pipeline(deck_path: str | Path, sim_path: str | Path) -> Pipeline:
    """Build a minimal pipeline: parse deck → load sim.

    This is the most common setup for interactive analysis.
    """
    return Pipeline(
        [
            DeckParseStep(path=deck_path),
            SimLoadStep(path=sim_path),
        ]
    )
