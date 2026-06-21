"""Parallel batch visualization — fan out (quantity, iteration) pairs across processes.

Each worker creates its own Simulation, renders one matplotlib figure,
saves PNG, and closes.  File writes target deterministic paths:
``{output_dir}/{qty}_{iter:06d}.png`` — no locking needed.
"""

import logging
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import matplotlib

from osiris_toolkit.vis.batch import BatchResult

matplotlib.use("Agg")

from osiris_toolkit.parallel._cluster import (
    detect_available_workers,
    detect_job_array,
    detect_mpi_rank,
    limit_blas_threads,
    split_iterations,
)
from osiris_toolkit.sim import Simulation

logger = logging.getLogger(__name__)

# ── Worker functions (module-level, pickle-safe) ──────────────────────


def _worker_plot_field(
    sim: Simulation,
    iteration: int,
    quantity: str,
    output: str,
    x_unit: str = "um",
    y_unit: str = "um",
    time_unit: str = "ps",
) -> str:
    """Worker: plot one field frame.  Returns output path."""
    limit_blas_threads(1)
    import matplotlib as _mpl

    _mpl.use("Agg")
    from osiris_toolkit.vis.common import get_system
    from osiris_toolkit.vis.field import plot_field

    system = get_system(sim)
    plot_field(
        quantity=quantity,
        iteration=iteration,
        sim=sim,
        system=system,
        x_unit=x_unit,
        y_unit=y_unit,
        time_unit=time_unit,
        output=output,
    )
    import matplotlib.pyplot as _plt

    _plt.close("all")
    return output


def _worker_plot_k_space(
    sim: Simulation,
    iteration: int,
    quantity: str,
    output: str,
    time_unit: str = "ps",
) -> str:
    """Worker: plot one k-space frame.  Returns output path."""
    limit_blas_threads(1)
    import matplotlib as _mpl

    _mpl.use("Agg")
    from osiris_toolkit.vis.common import get_system
    from osiris_toolkit.vis.kspace import plot_k_space

    system = get_system(sim)
    plot_k_space(
        quantity=quantity,
        iteration=iteration,
        sim=sim,
        system=system,
        time_unit=time_unit,
        output=output,
    )
    import matplotlib.pyplot as _plt

    _plt.close("all")
    return output


def _worker_plot_density(
    sim: Simulation,
    iteration: int,
    species: str,
    output: str,
    quantity: str = "charge",  # noqa: ARG001
    x_unit: str = "um",
    y_unit: str = "um",
    time_unit: str = "ps",
) -> str:
    """Worker: plot one density frame.  Returns output path."""
    limit_blas_threads(1)
    import matplotlib as _mpl

    _mpl.use("Agg")
    from osiris_toolkit.vis.common import get_system
    from osiris_toolkit.vis.density import plot_density

    system = get_system(sim)
    plot_density(
        species=species,
        iteration=iteration,
        sim=sim,
        system=system,
        x_unit=x_unit,
        y_unit=y_unit,
        time_unit=time_unit,
        output=output,
    )
    import matplotlib.pyplot as _plt

    _plt.close("all")
    return output


# ── Public API ─────────────────────────────────────────────────────────


def batch_process_parallel(
    sim_path: str | Path,
    sim_name: str,
    output_root: str | Path | None = None,
    x_unit: str = "um",
    y_unit: str = "um",
    time_unit: str = "ps",
    max_workers: int | None = None,
) -> BatchResult:
    """Parallel version of ``process_simulation``.

    Fans out all (quantity, iteration) pairs for fields, k-space, and
    density across worker processes.  Scattering analysis (which has a
    cross-iteration dependency) runs sequentially after all workers finish.

    .. versionchanged:: 0.17.0
        Now returns ``BatchResult`` instead of ``None``.
    """
    sim_path = str(sim_path)
    sim = Simulation(sim_path)
    output_root = sim.output_root if output_root is None else Path(output_root)

    sim = Simulation(sim_path)  # discover ONCE, pickle to workers

    available_fields = sim.list_fields()
    species_list = sim.list_species()
    if not available_fields:
        logger.info("[%s] No field data found.", sim_name)
        return BatchResult(sim_name=sim_name, files=[], elapsed=0.0, errors=["No field data found."])

    iterations = sim.list_iterations(available_fields[0])
    base = output_root / sim_name
    field_dir = base / "fields"
    kspace_dir = base / "k_space"
    density_dir = base / "density"
    scattering_dir = base / "scattering"
    for d in [field_dir, kspace_dir, density_dir, scattering_dir]:
        d.mkdir(parents=True, exist_ok=True)

    n_total = len(iterations)
    logger.info(
        "[%s] %d iterations, %d fields, %d species (parallel)",
        sim_name,
        n_total,
        len(available_fields),
        len(species_list),
    )

    # Cluster sharding
    mpi = detect_mpi_rank()
    if mpi:
        my_iters = split_iterations(iterations, *mpi)
    else:
        arr = detect_job_array()
        my_iters = split_iterations(iterations, *arr) if arr else iterations

    if max_workers is None:
        max_workers = detect_available_workers()
    ctx = multiprocessing.get_context("spawn")
    t_start = time.time()

    base_kwargs: dict = {
        "x_unit": x_unit,
        "y_unit": y_unit,
        "time_unit": time_unit,
    }

    all_files: list[Path] = []
    all_errors: list[str] = []

    with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as ex:
        futures: dict = {}

        for it in my_iters:
            for qty in available_fields:
                out = str(field_dir / f"{qty}_{it:06d}.png")
                futures[
                    ex.submit(
                        _worker_plot_field,
                        sim,
                        it,
                        qty,
                        out,
                        **base_kwargs,
                    )
                ] = f"field {qty} it={it}"

        for it in my_iters:
            for qty in available_fields:
                out = str(kspace_dir / f"kspace_{qty}_{it:06d}.png")
                futures[
                    ex.submit(
                        _worker_plot_k_space,
                        sim,
                        it,
                        qty,
                        out,
                        time_unit=time_unit,
                    )
                ] = f"kspace {qty} it={it}"

        for it in my_iters:
            for sp in species_list:
                out = str(density_dir / f"density_{sp}_{it:06d}.png")
                futures[
                    ex.submit(
                        _worker_plot_density,
                        sim,
                        it,
                        sp,
                        out,
                        **base_kwargs,
                    )
                ] = f"density {sp} it={it}"

        for done, future in enumerate(as_completed(futures), start=1):
            label = futures[future]
            try:
                fpath = future.result()
                if fpath:
                    all_files.append(Path(fpath))
            except Exception as exc:
                logger.info("  [%s] %s: %s", sim_name, label, exc)
                all_errors.append(f"{label}: {exc}")
            if done % 50 == 0:
                logger.info("  [%s] %d/%d tasks done", sim_name, done, len(futures))

    total = time.time() - t_start
    logger.info("[%s] Parallel phase done, elapsed %.0fs.", sim_name, total)

    # ── Scattering analysis (cross-iteration, runs sequentially) ──
    logger.info("[%s] Scattering analysis...", sim_name)
    from osiris_toolkit.analysis.scattering import ScatteringAnalyzer
    from osiris_toolkit.vis.common import get_system
    from osiris_toolkit.vis.scattering import plot_scattering_fraction

    system = get_system(sim)
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
                all_files.append(Path(fpath))
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
