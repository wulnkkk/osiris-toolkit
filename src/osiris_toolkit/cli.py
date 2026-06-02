"""Unified CLI for osiris-toolkit."""

from __future__ import annotations

import json
from pathlib import Path

import click

from osiris_toolkit import __version__


@click.group()
@click.version_option(__version__, prog_name="osiris-toolkit")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging (DEBUG level).")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output (ERROR level).")
def main(verbose: bool, quiet: bool) -> None:
    """osiris-toolkit — comprehensive toolkit for OSIRIS PIC simulations.

    Covers input deck parsing, simulation data extraction, unit conversion,
    analysis, and visualization.
    """
    import logging

    from osiris_toolkit._logging import configure

    if verbose:
        configure(logging.DEBUG)
    elif quiet:
        configure(logging.ERROR)


# ---------------------------------------------------------------------------
# deck subcommands
# ---------------------------------------------------------------------------


@main.group()
def deck() -> None:
    """Parse and validate OSIRIS input decks."""


@deck.command("parse")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output", "-o",
    type=click.Choice(["json", "python"]),
    default="json",
    help="Output format.",
)
def deck_parse(file: Path, output: str) -> None:
    """Parse an OSIRIS input deck and print the result."""
    from osiris_toolkit.deck import parse_deck_file

    result = parse_deck_file(str(file))

    if output == "json":
        # Convert to JSON-serializable form
        out: dict = {
            "filename": result.get("filename", str(file)),
            "sections": [],
        }
        for sec in result.get("sections", []):
            sec_out: dict = {"name": sec["name"], "line": sec.get("line", 0), "params": {}}
            for key, val in sec.get("params", {}).items():
                if hasattr(val, "__iter__") and not isinstance(val, (str, dict)):
                    sec_out["params"][key] = list(val) if not isinstance(val, (str, dict)) else val
                else:
                    sec_out["params"][key] = val
            out["sections"].append(sec_out)
        click.echo(json.dumps(out, indent=2, default=str))
    else:
        click.echo(str(result))


@deck.command("lint")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def deck_lint(file: Path) -> None:
    """Validate an input deck and print issues."""
    from osiris_toolkit.deck import lint_deck_file
    from osiris_toolkit.deck.reporter import Severity

    report = lint_deck_file(str(file))

    if not report.issues:
        click.echo("No issues found.")
        return

    for issue in report.issues:
        prefix = {
            Severity.ERROR: "ERROR",
            Severity.WARNING: "WARNING",
            Severity.INFO: "INFO",
        }.get(issue.severity, "?")

        click.echo(
            f"{prefix}: [{issue.rule_id}] {issue.message} "
            f"(section={issue.section}, line={issue.line})"
        )

    click.echo(f"\n{report.summary()}")


@deck.command("validate")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def deck_validate(file: Path) -> None:
    """Validate an input deck; exit with non-zero if errors found."""
    from osiris_toolkit.deck import lint_deck_file

    report = lint_deck_file(str(file))
    if report.has_errors():
        for issue in report.errors():
            click.echo(
                f"ERROR: [{issue.rule_id}] {issue.message} "
                f"(section={issue.section}, line={issue.line})"
            )
        raise SystemExit(1)
    click.echo("Deck is valid.")


@deck.command("estimate")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--cores-per-node", "-c",
    type=int, default=None,
    help="CPU cores per compute node (default: auto-detect from node_conf × n_threads).",
)
@click.option(
    "--efficiency", "-e",
    type=float, default=0.15,
    help="Sustained FLOP/s fraction of peak (default: 0.15).",
)
def deck_estimate(file: Path, cores_per_node: int | None, efficiency: float) -> None:
    """Estimate computational resources for a simulation input deck.

    Predicts per-node memory usage, wall-clock runtime (order-of-magnitude),
    and total disk space based on grid size, particle count, and diagnostic
    output frequencies.
    """
    from osiris_toolkit.deck import parse_deck_file
    from osiris_toolkit.resource import estimate_resources, format_report

    deck = parse_deck_file(str(file))
    report = estimate_resources(deck, efficiency=efficiency)
    click.echo(format_report(report))


# ---------------------------------------------------------------------------
# sim subcommands
# ---------------------------------------------------------------------------


@main.group()
def sim() -> None:
    """Explore simulation output directories."""


@sim.command("info")
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
def sim_info(directory: Path) -> None:
    """Print summary information about a simulation output directory."""
    from osiris_toolkit.sim import Simulation
    from osiris_toolkit.sim.catalog import OSIRIS_DIAGNOSTICS

    sim_obj = Simulation(str(directory))

    click.echo(f"Simulation: {directory}")
    click.echo(f"Run info: {sim_obj.run_info}")

    click.echo("\nAvailable diagnostics:")
    for name, kind in OSIRIS_DIAGNOSTICS.items():
        if kind.is_per_species and hasattr(sim_obj, "_fields"):
            continue  # handled below
        click.echo(f"  {name}: {kind.data_class.__name__}")

    click.echo("\nField quantities:")
    for q in sim_obj.list_fields():
        iters = sim_obj.list_iterations(q)
        click.echo(f"  {q}: iterations {min(iters)}..{max(iters)} ({len(iters)} frames)")

    if sim_obj.list_species():
        click.echo(f"\nSpecies: {', '.join(sim_obj.list_species())}")

    phases = sim_obj.list_phasespaces()
    if phases:
        click.echo(f"\nPhasespaces: {len(phases)} available")

    if sim_obj.list_tracks():
        click.echo(f"\nTracks: {', '.join(sim_obj.list_tracks())}")

    if sim_obj.list_history():
        click.echo(f"\nHistory files: {', '.join(sim_obj.list_history())}")

    if sim_obj.list_timings():
        click.echo(f"\nTIMINGS files: {', '.join(sim_obj.list_timings())}")

    fmt = sim_obj.detected_format
    if fmt == "hdf5":
        click.secho(
            "\nWARNING: Detected HDF5 output format. osiris-toolkit only supports ZDF.\n"
            "  Set 'file_format = \"zdf\"' in the simulation section of your input deck.",
            fg="yellow",
        )
    elif fmt == "mixed":
        click.secho(
            "\nWARNING: Detected mixed ZDF/HDF5 output. Only ZDF files will be read.",
            fg="yellow",
        )
    else:
        click.echo(f"\nOutput format: {fmt}")


@sim.command("list")
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
@click.option("--kind", "-k", default="EMF", help="Diagnostic kind (default: EMF).")
def sim_list(directory: Path, kind: str) -> None:
    """List available data for a diagnostic kind."""
    from osiris_toolkit.sim import Simulation

    sim_obj = Simulation(str(directory))
    kind_upper = kind.upper()

    if kind_upper == "EMF":
        for q in sim_obj.list_fields():
            iters = sim_obj.list_iterations(q)
            click.echo(f"{q}: {len(iters)} frames, iter {min(iters)}..{max(iters)}")
    elif kind_upper == "DENSITY":
        for sp in sim_obj.list_species():
            click.echo(f"Species: {sp}")
    elif kind_upper == "PHASESPACE":
        for ps, sp in sim_obj.list_phasespaces():
            click.echo(f"  {ps} / {sp}")
    elif kind_upper == "TRACKS":
        for name in sim_obj.list_tracks():
            click.echo(f"  {name}")
    elif kind_upper == "HISTORY":
        for name in sim_obj.list_history():
            click.echo(f"  {name}")
    else:
        click.echo(f"Diagnostic kind '{kind}' not recognized.")
        click.echo("Known kinds: EMF, DENSITY, PHASESPACE, TRACKS, HISTORY")


# ---------------------------------------------------------------------------
# vis subcommands
# ---------------------------------------------------------------------------


@main.group()
def vis() -> None:
    """Visualize simulation data."""


@vis.command("plot")
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
@click.option("--kind", "-k", default="EMF", help="Diagnostic kind.")
@click.option("--quantity", "-q", default="e1", help="Quantity name.")
@click.option("--iteration", "-i", type=int, default=0, help="Iteration number.")
@click.option("--output", "-o", type=Path, default=None, help="Output file path.  Default: auto-generated under {sim}/figures/.")
@click.option("--overwrite", is_flag=True, help="Overwrite existing output files.")
def vis_plot(
    directory: Path, kind: str, quantity: str, iteration: int,
    output: Path | None, overwrite: bool,
) -> None:
    """Plot a single diagnostic frame."""
    from osiris_toolkit.sim import Simulation
    from osiris_toolkit.vis import VisEngine

    sim_obj = Simulation(str(directory))
    vis_eng = VisEngine(sim_obj)

    fig = vis_eng.plot(
        kind, quantity=quantity, iteration=iteration,
        output=str(output) if output else None,
    )
    if fig is None:
        click.echo(
            f"No data for {kind}/{quantity} at iteration {iteration}"
        )


@vis.command("batch")
@click.argument("sims", nargs=-1, type=str)
@click.option(
    "--output-dir", "-o",
    type=Path,
    default=None,
    help="Root directory for all output.  Default: {sim_path}/figures/.",
)
@click.option(
    "--max-workers", "-j",
    type=int,
    default=None,
    help="Number of parallel workers. Default: auto-detect (SLURM_CPUS_PER_TASK or CPU count).",
)
def vis_batch(sims: tuple[str, ...], output_dir: Path | None, max_workers: int | None) -> None:
    """Batch-process multiple simulations.

    Provide pairs of SIM_PATH SIM_NAME arguments:

    \b
        osiris-toolkit vis batch /data/Au Au
        osiris-toolkit vis batch -o /path/to/output /data/Au Au /data/Au0 Au0
    """
    from osiris_toolkit.vis.batch import process_simulation

    if len(sims) < 2 or len(sims) % 2 != 0:
        raise click.UsageError(
            "Requires at least one pair of SIM_PATH SIM_NAME arguments. "
            f"Got {len(sims)} argument(s)."
        )

    for i in range(0, len(sims), 2):
        sim_path = sims[i]
        sim_name = sims[i + 1]
        click.echo("=" * 60)
        click.echo(f"Batch processing: {sim_name}")
        click.echo("=" * 60)
        process_simulation(sim_path, sim_name, output_root=output_dir,
                           max_workers=max_workers)
        click.echo()


# ---------------------------------------------------------------------------
# analyze subcommands
# ---------------------------------------------------------------------------


@main.group()
def analyze() -> None:
    """Analyze simulation data."""


@analyze.command("describe")
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
@click.option("--quantity", "-q", default="e1", help="Quantity name.")
@click.option("--iteration", "-i", type=int, default=0, help="Iteration number.")
def analyze_describe(directory: Path, quantity: str, iteration: int) -> None:
    """Print descriptive statistics for a diagnostic quantity."""
    from osiris_toolkit.analysis.stats import describe
    from osiris_toolkit.sim import Simulation

    sim_obj = Simulation(str(directory))
    grid = sim_obj.get_field(quantity, iteration)
    if grid is None:
        click.echo(f"No data for {quantity} at iteration {iteration}")
        return

    result = describe(grid)
    click.echo(f"{quantity} @ iteration {iteration}, time={result['time']:.4f}")
    click.echo(f"  shape: {result['shape']}")
    click.echo(f"  mean: {result['mean']:.6g}")
    click.echo(f"  std:  {result['std']:.6g}")
    click.echo(f"  min:  {result['min']:.6g}")
    click.echo(f"  max:  {result['max']:.6g}")
    click.echo(f"  rms:  {result['rms']:.6g}")


# ---------------------------------------------------------------------------
# run subcommand
# ---------------------------------------------------------------------------


@main.command("run")
@click.argument("workflow_file", type=click.Path(exists=True, path_type=Path))
def run_workflow(workflow_file: Path) -> None:
    """Run a workflow from a YAML configuration file."""
    from osiris_toolkit.workflow import Pipeline

    pipe = Pipeline.from_yaml(str(workflow_file))
    click.echo(f"Running workflow: {workflow_file}")
    ctx = pipe.run()
    click.echo("Workflow complete.")
    if "analysis_results" in ctx.extra:
        click.echo(f"Analysis: {ctx.extra['analysis_results']}")
    if "figures_dir" in ctx.extra:
        click.echo(f"Figures: {ctx.extra['figures_dir']}")


# ---------------------------------------------------------------------------
# sync subcommands
# ---------------------------------------------------------------------------


@main.group()
def sync() -> None:
    """Synchronize definitions from OSIRIS Fortran source."""


@sync.command("extract")
@click.option("--osiris-path", type=click.Path(exists=True, path_type=Path), required=True)
@click.option(
    "--docs-path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to osiris/docs/reference/ for parameter descriptions.",
)
def sync_extract(osiris_path: Path, docs_path: Path | None) -> None:
    """Extract parameter and quantity definitions from OSIRIS Fortran source."""
    import osiris_toolkit.sync.diagnostics as _diag
    import osiris_toolkit.sync.namelist as _nl
    import osiris_toolkit.sync.sections as _sec

    generated_dir = (
        Path(__file__).resolve().parent / "_generated"
    )
    generated_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"Scanning Fortran source: {osiris_path}")
    _nl.generate(
        str(generated_dir / "parameters.py"),
        str(osiris_path),
        docs_path=str(docs_path) if docs_path else None,
    )
    click.echo("  → parameters.py")
    _diag.generate(str(generated_dir / "quantities.py"), str(osiris_path))
    click.echo("  → quantities.py")
    _sec.generate(str(generated_dir / "sections.py"), str(osiris_path))
    click.echo("  → sections.py")
    click.echo(f"\nWrote to: {generated_dir}")


if __name__ == "__main__":
    main()
