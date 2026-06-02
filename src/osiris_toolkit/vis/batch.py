"""Batch-process OSIRIS simulations: fields, k-space, density, scattering.

Generates visualisation images with physical units for all time steps.
Output is organised by simulation name under an output root directory.
"""

import logging
import time
from pathlib import Path

from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter

from .density import plot_density
from .field import plot_field
from .kspace import plot_k_space
from .scattering import analyze_scattering, plot_scattering_fraction

logger = logging.getLogger(__name__)

FIELD_QUANTS = ["e1", "e2", "e3", "b1", "b2", "b3"]


def process_simulation(
    sim_path: str | Path,
    sim_name: str,
    output_root: str | Path | None = None,
    x_unit: str = "um",
    y_unit: str = "um",
    time_unit: str = "ps",
    max_workers: int | None = None,
) -> None:
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
    """
    if max_workers is not None and max_workers > 0:
        from osiris_toolkit.vis.parallel import batch_process_parallel
        return batch_process_parallel(
            sim_path, sim_name, output_root,
            x_unit=x_unit, y_unit=y_unit, time_unit=time_unit,
            max_workers=max_workers,
        )

    t_start = time.time()

    sim = Simulation(sim_path)
    if output_root is None:
        output_root = sim.output_root
    else:
        output_root = Path(output_root)
    converter: UnitConverter | None = None
    try:
        # Try to build a converter from the simulation's omega_p0.
        # This requires that the osiris_toolkit.units params module can
        # extract omega_p0 from the run-info or an input deck.
        from osiris_toolkit.units.params import SimulationParams
        params = SimulationParams.from_sim_path(sim_path)
        if params.omega_p0 > 0:
            converter = UnitConverter(params.omega_p0)
    except Exception:
        pass

    if converter is None:
        logger.info("[%s] Warning: could not determine omega_p0;"
                    " using normalised units", sim_name)

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
        return
    if not species_list:
        logger.info("[%s] No species data found.", sim_name)

    iterations = sim.list_iterations(available_fields[0])
    n_total = len(iterations)
    logger.info(
        "[%s] %d iterations, %d fields, %d species",
        sim_name, n_total, len(available_fields), len(species_list),
    )
    logger.info("[%s] Output directory: %s", sim_name, base.resolve())

    for idx, it in enumerate(iterations):
        t_iter = time.time()

        # --- Field plots (delegate to field.py) ---
        for qty in available_fields:
            try:
                plot_field(
                    quantity=qty,
                    iteration=it,
                    sim=sim, converter=converter,
                    x_unit=x_unit,
                    y_unit=y_unit,
                    time_unit=time_unit,
                    output=str(field_dir / f"{qty}_{it:06d}.png"),
                )
            except Exception as exc:
                logger.info("  [%s] field %s iter=%s: %s", sim_name, qty, it, exc)

        # --- k-space plots (delegate to kspace.py) ---
        for qty in available_fields:
            try:
                plot_k_space(
                    quantity=qty,
                    iteration=it,
                    sim=sim, converter=converter,
                    time_unit=time_unit,
                    output=str(kspace_dir / f"kspace_{qty}_{it:06d}.png"),
                )
            except Exception as exc:
                logger.info("  [%s] k-space %s iter=%s: %s", sim_name, qty, it, exc)

        # --- Density plots (delegate to density.py) ---
        for sp in species_list:
            try:
                plot_density(
                    species=sp,
                    iteration=it,
                    sim=sim, converter=converter,
                    x_unit=x_unit,
                    y_unit=y_unit,
                    time_unit=time_unit,
                    output=str(density_dir / f"density_{sp}_{it:06d}.png"),
                )
            except Exception as exc:
                logger.info("  [%s] density %s iter=%s: %s", sim_name, sp, it, exc)

        elapsed = time.time() - t_iter
        eta = elapsed * (n_total - idx - 1)
        logger.info(
            "  [%s] iter=%06d (%d/%d) done %.1fs, ETA %.0fs",
            sim_name, it, idx + 1, n_total, elapsed, eta,
        )

    # --- Scattering analysis (delegate to scattering.py) ---
    logger.info("[%s] Scattering analysis...", sim_name)
    for qty in ["e1", "e2", "e3"]:
        if qty not in available_fields:
            continue
        try:
            result = analyze_scattering(
                quantity=qty,
                sim=sim,
                verbose=False,
            )
            plot_scattering_fraction(
                result,
                converter=converter,
                time_unit=time_unit,
                output=str(scattering_dir / f"scattering_{qty}.png"),
            )
            logger.info("  [%s] scattering %s done", sim_name, qty)
        except Exception as exc:
            logger.info("  [%s] scattering %s: %s", sim_name, qty, exc)

    total = time.time() - t_start
    logger.info("[%s] All done, elapsed %.0fs.", sim_name, total)


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
        "-o", "--output-dir",
        type=Path,
        required=True,
        help="Root directory for all output.",
    )
    parser.add_argument(
        "-j", "--max-workers",
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
        process_simulation(sim_path, sim_name, output_root=args.output_dir,
                           max_workers=args.max_workers)
        logger.info("")


if __name__ == "__main__":
    main()
