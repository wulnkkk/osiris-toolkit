"""Batch-process OSIRIS simulations: fields, k-space, density, scattering.

Generates visualisation images with physical units for all time steps.
Output is organised by simulation name under an output root directory.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from osiris_toolkit.sim import Simulation

from .common import get_system
from .density import plot_density
from .field import plot_field
from .kspace import plot_k_space
from .scattering import plot_scattering_fraction

logger = logging.getLogger(__name__)

FIELD_QUANTS = ["e1", "e2", "e3", "b1", "b2", "b3"]


@dataclass
class ProgressEvent:
    """Emitted by process_simulation() after each iteration.

    Attributes
    ----------
    iteration : int
        Current iteration number.
    total : int
        Total number of iterations.
    elapsed : float
        Time spent on the current iteration (seconds).
    eta : float
        Estimated remaining time (seconds).
    """

    iteration: int
    total: int
    elapsed: float
    eta: float


@dataclass
class BatchResult:
    """Returned by process_simulation() after completion.

    Attributes
    ----------
    sim_name : str
        Human-readable simulation name.
    files : list of Path
        All generated output file paths.
    elapsed : float
        Total wall-clock time (seconds).
    errors : list of str
        Non-fatal error messages collected during processing.
    """

    sim_name: str
    files: list[Path]
    elapsed: float
    errors: list[str]


def process_simulation(
    sim_path: str | Path,
    sim_name: str,
    output_root: str | Path | None = None,
    x_unit: str = "um",
    y_unit: str = "um",
    time_unit: str = "ps",
    max_workers: int | None = None,
    overwrite: bool = False,  # noqa: ARG001
    *,
    progress_callback: Callable[[ProgressEvent], None] | None = None,
) -> BatchResult:
    """Run all visualisation and analysis pipelines on a single simulation.

    Creates the following directory structure under *output_root*/*sim_name*::

        fields/        field component images
        k_space/       FFT k-space images
        density/       species density images
        scattering/    scattering fraction plots

    Parameters
    ----------
    sim_path : str or Path
        Path to the simulation output directory.
    sim_name : str
        Human-readable name used for the output subdirectory.
    output_root : str, Path, or None
        Root directory for all output.  If None, defaults to
        ``Simulation(sim_path).output_root`` (in-place under the sim
        directory).  Set this to write outputs elsewhere.
    x_unit, y_unit : str
        Spatial axis units.
    time_unit : str
        Time unit for titles.
    max_workers : int or None
        Number of parallel workers.  If positive, delegates to the parallel
        implementation.  ``None`` (default) runs sequentially.
    progress_callback : callable or None
        Optional callback invoked after each iteration with a
        :class:`ProgressEvent`.
    """
    if max_workers is not None and max_workers > 0:
        from osiris_toolkit.vis.parallel import batch_process_parallel

        batch_process_parallel(
            sim_path,
            sim_name,
            output_root,
            x_unit=x_unit,
            y_unit=y_unit,
            time_unit=time_unit,
            max_workers=max_workers,
        )
        return BatchResult(
            sim_name=sim_name,
            files=[],
            elapsed=0.0,
            errors=["Parallel path does not yet support BatchResult details"],
        )

    t_start = time.time()

    all_files: list[Path] = []
    all_errors: list[str] = []

    sim = Simulation(sim_path)
    output_root = sim.output_root if output_root is None else Path(output_root)
    system = get_system(sim)
    if system is None:
        logger.info("[%s] Warning: no unit system available; using normalised units", sim_name)

    base = output_root / sim_name
    field_dir = base / "fields"
    kspace_dir = base / "k_space"
    density_dir = base / "density"
    scattering_dir = base / "scattering"
    for d in [field_dir, kspace_dir, density_dir, scattering_dir]:
        d.mkdir(parents=True, exist_ok=True)

    available_fields = sim.list_fields()
    species_list = sim.list_species()
    if not available_fields:
        logger.info("[%s] No field data found.", sim_name)
        return BatchResult(sim_name=sim_name, files=[], elapsed=time.time() - t_start, errors=[])
    if not species_list:
        logger.info("[%s] No species data found.", sim_name)

    iterations = sim.list_iterations(available_fields[0])
    n_total = len(iterations)
    logger.info(
        "[%s] %d iterations, %d fields, %d species",
        sim_name,
        n_total,
        len(available_fields),
        len(species_list),
    )
    logger.info("[%s] Output directory: %s", sim_name, base.resolve())

    for idx, it in enumerate(iterations):
        t_iter = time.time()

        # --- Field plots (delegate to field.py) ---
        for qty in available_fields:
            try:
                fpath = plot_field(
                    quantity=qty,
                    iteration=it,
                    sim=sim,
                    system=system,
                    x_unit=x_unit,
                    y_unit=y_unit,
                    time_unit=time_unit,
                    output=str(field_dir / f"{qty}_{it:06d}.png"),
                )
                if fpath is not None:
                    all_files.append(fpath)
            except Exception as exc:
                logger.info("  [%s] field %s iter=%s: %s", sim_name, qty, it, exc)
                all_errors.append(f"field {qty} iter={it}: {exc}")

        # --- k-space plots (delegate to kspace.py) ---
        for qty in available_fields:
            try:
                fpath = plot_k_space(
                    quantity=qty,
                    iteration=it,
                    sim=sim,
                    system=system,
                    time_unit=time_unit,
                    output=str(kspace_dir / f"kspace_{qty}_{it:06d}.png"),
                )
                if fpath is not None:
                    all_files.append(fpath)
            except Exception as exc:
                logger.info("  [%s] k-space %s iter=%s: %s", sim_name, qty, it, exc)
                all_errors.append(f"k-space {qty} iter={it}: {exc}")

        # --- Density plots (delegate to density.py) ---
        for sp in species_list:
            try:
                fpath = plot_density(
                    species=sp,
                    iteration=it,
                    sim=sim,
                    system=system,
                    x_unit=x_unit,
                    y_unit=y_unit,
                    time_unit=time_unit,
                    output=str(density_dir / f"density_{sp}_{it:06d}.png"),
                )
                if fpath is not None:
                    all_files.append(fpath)
            except Exception as exc:
                logger.info("  [%s] density %s iter=%s: %s", sim_name, sp, it, exc)
                all_errors.append(f"density {sp} iter={it}: {exc}")

        elapsed = time.time() - t_iter
        eta = elapsed * (n_total - idx - 1)
        logger.info(
            "  [%s] iter=%06d (%d/%d) done %.1fs, ETA %.0fs",
            sim_name,
            it,
            idx + 1,
            n_total,
            elapsed,
            eta,
        )

        if progress_callback is not None:
            progress_callback(
                ProgressEvent(
                    iteration=it,
                    total=n_total,
                    elapsed=elapsed,
                    eta=elapsed * (n_total - idx - 1),
                )
            )

    # --- Scattering analysis (delegate to scattering.py) ---
    logger.info("[%s] Scattering analysis...", sim_name)
    from osiris_toolkit.analysis.scattering import ScatteringAnalyzer

    scattering_analyzer = ScatteringAnalyzer(sim, system)
    for qty in ["e1", "e2", "e3"]:
        if qty not in available_fields:
            continue
        try:
            result = scattering_analyzer.analyze(
                quantity=qty,
                verbose=False,
            )
            fpath = plot_scattering_fraction(
                result,
                system=system,
                time_unit=time_unit,
                output=str(scattering_dir / f"scattering_{qty}.png"),
            )
            if fpath is not None:
                all_files.append(fpath)
            logger.info("  [%s] scattering %s done", sim_name, qty)
        except Exception as exc:
            logger.info("  [%s] scattering %s: %s", sim_name, qty, exc)
            all_errors.append(f"scattering {qty}: {exc}")

    total = time.time() - t_start
    logger.info("[%s] All done, elapsed %.0fs.", sim_name, total)
    return BatchResult(
        sim_name=sim_name,
        files=all_files,
        elapsed=total,
        errors=all_errors,
    )


def main() -> None:
    """Entry point for batch processing.

    Usage::

        python -m osiris_toolkit.vis.batch -o /path/to/output \\
            /data/Au Au /data/Au0 Au0
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Batch-process OSIRIS simulations: fields, k-space, density, scattering.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        required=True,
        help="Root directory for all output.",
    )
    parser.add_argument(
        "-j",
        "--max-workers",
        type=int,
        default=None,
        help="Number of parallel workers (default: sequential).",
    )
    parser.add_argument(
        "sims",
        nargs="*",
        help="Pairs of SIM_PATH SIM_NAME (e.g. /data/Au Au /data/Au0 Au0).",
    )
    args = parser.parse_args()

    if len(args.sims) < 2 or len(args.sims) % 2 != 0:
        parser.error(
            "At least one pair of SIM_PATH SIM_NAME is required. "
            "Got: %s" % (" ".join(args.sims) if args.sims else "(none)")
        )

    for i in range(0, len(args.sims), 2):
        sim_path = args.sims[i]
        sim_name = args.sims[i + 1]
        logger.info("=" * 60)
        logger.info("Batch processing: %s", sim_name)
        logger.info("=" * 60)
        process_simulation(sim_path, sim_name, output_root=args.output_dir, max_workers=args.max_workers)
        logger.info("")


if __name__ == "__main__":
    main()
