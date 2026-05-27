"""Parallel batch visualization — fan out (quantity, iteration) pairs across processes.

Each worker creates its own Simulation, renders one matplotlib figure,
saves PNG, and closes.  File writes target deterministic paths:
``{output_dir}/{qty}_{iter:06d}.png`` — no locking needed.
"""

import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from osiris_toolkit.parallel._cluster import (
    detect_available_workers,
    detect_job_array,
    detect_mpi_rank,
    limit_blas_threads,
    split_iterations,
)
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter

# ── Worker functions (module-level, pickle-safe) ──────────────────────

def _worker_plot_field(
    sim_path: str,
    iteration: int,
    quantity: str,
    output: str,
    x_unit: str = "um",
    y_unit: str = "um",
    time_unit: str = "ps",
    converter_omega_p0: float | None = None,
) -> str:
    """Worker: plot one field frame.  Returns output path."""
    limit_blas_threads(1)
    import matplotlib as _mpl
    _mpl.use("Agg")
    from osiris_toolkit.vis.field import plot_field

    converter = UnitConverter(converter_omega_p0) if converter_omega_p0 else None
    sim = Simulation(sim_path)
    plot_field(
        quantity=quantity, iteration=iteration, sim=sim,
        converter=converter, x_unit=x_unit, y_unit=y_unit,
        time_unit=time_unit, output=output,
    )
    return output


def _worker_plot_k_space(
    sim_path: str,
    iteration: int,
    quantity: str,
    output: str,
    time_unit: str = "ps",
    converter_omega_p0: float | None = None,
) -> str:
    """Worker: plot one k-space frame.  Returns output path."""
    limit_blas_threads(1)
    import matplotlib as _mpl
    _mpl.use("Agg")
    from osiris_toolkit.vis.kspace import plot_k_space

    converter = UnitConverter(converter_omega_p0) if converter_omega_p0 else None
    sim = Simulation(sim_path)
    plot_k_space(
        quantity=quantity, iteration=iteration, sim=sim,
        converter=converter, time_unit=time_unit, output=output,
    )
    return output


def _worker_plot_density(
    sim_path: str,
    iteration: int,
    species: str,
    output: str,
    quantity: str = "charge",
    x_unit: str = "um",
    y_unit: str = "um",
    time_unit: str = "ps",
    converter_omega_p0: float | None = None,
) -> str:
    """Worker: plot one density frame.  Returns output path."""
    limit_blas_threads(1)
    import matplotlib as _mpl
    _mpl.use("Agg")
    from osiris_toolkit.vis.density import plot_density

    converter = UnitConverter(converter_omega_p0) if converter_omega_p0 else None
    sim = Simulation(sim_path)
    plot_density(
        species=species, iteration=iteration, sim=sim,
        converter=converter, x_unit=x_unit, y_unit=y_unit,
        time_unit=time_unit, output=output,
    )
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
) -> None:
    """Parallel version of ``process_simulation``.

    Fans out all (quantity, iteration) pairs for fields, k-space, and
    density across worker processes.  Scattering analysis (which has a
    cross-iteration dependency) runs sequentially after all workers finish.
    """
    sim_path = str(sim_path)
    sim = Simulation(sim_path)
    if output_root is None:
        output_root = sim.output_root
    else:
        output_root = Path(output_root)

    converter_omega_p0: float | None = None
    try:
        from osiris_toolkit.units.params import SimulationParams

        params = SimulationParams.from_sim_path(sim_path)
        if params.omega_p0 > 0:
            converter_omega_p0 = params.omega_p0
    except Exception:
        pass

    available_fields = sim.list_fields()
    species_list = sim.list_species()
    if not available_fields:
        print(f"[{sim_name}] No field data found.")
        return

    iterations = sim.list_iterations(available_fields[0])
    base = output_root / sim_name
    field_dir = base / "fields"
    kspace_dir = base / "k_space"
    density_dir = base / "density"
    scattering_dir = base / "scattering"
    for d in [field_dir, kspace_dir, density_dir, scattering_dir]:
        d.mkdir(parents=True, exist_ok=True)

    n_total = len(iterations)
    print(
        f"[{sim_name}] {n_total} iterations, {len(available_fields)} fields,"
        f" {len(species_list)} species (parallel)"
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
        "converter_omega_p0": converter_omega_p0,
    }

    with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as ex:
        futures: dict = {}

        for it in my_iters:
            for qty in available_fields:
                out = str(field_dir / f"{qty}_{it:06d}.png")
                futures[
                    ex.submit(
                        _worker_plot_field, sim_path, it, qty, out,
                        **base_kwargs,
                    )
                ] = f"field {qty} it={it}"

        for it in my_iters:
            for qty in available_fields:
                out = str(kspace_dir / f"kspace_{qty}_{it:06d}.png")
                futures[
                    ex.submit(
                        _worker_plot_k_space, sim_path, it, qty, out,
                        time_unit=time_unit,
                        converter_omega_p0=converter_omega_p0,
                    )
                ] = f"kspace {qty} it={it}"

        for it in my_iters:
            for sp in species_list:
                out = str(density_dir / f"density_{sp}_{it:06d}.png")
                futures[
                    ex.submit(
                        _worker_plot_density, sim_path, it, sp, out,
                        **base_kwargs,
                    )
                ] = f"density {sp} it={it}"

        done = 0
        for future in as_completed(futures):
            label = futures[future]
            try:
                future.result()
            except Exception as exc:
                print(f"  [{sim_name}] {label}: {exc}")
            done += 1
            if done % 50 == 0:
                print(f"  [{sim_name}] {done}/{len(futures)} tasks done")

    total = time.time() - t_start
    print(f"[{sim_name}] Parallel phase done, elapsed {total:.0f}s.")

    # ── Scattering analysis (cross-iteration, runs sequentially) ──
    print(f"[{sim_name}] Scattering analysis...")
    for qty in ["e1", "e2", "e3"]:
        if qty not in available_fields:
            continue
        try:
            from osiris_toolkit.vis.scattering import (
                analyze_scattering,
                plot_scattering_fraction,
            )

            result = analyze_scattering(
                quantity=qty, sim=sim, verbose=False,
            )
            plot_scattering_fraction(
                result,
                converter=(
                    UnitConverter(converter_omega_p0)
                    if converter_omega_p0
                    else None
                ),
                time_unit=time_unit,
                output=str(scattering_dir / f"scattering_{qty}.png"),
            )
            print(f"  [{sim_name}] scattering {qty} done")
        except Exception as exc:
            print(f"  [{sim_name}] scattering {qty}: {exc}")

    print(f"[{sim_name}] All done, elapsed {time.time() - t_start:.0f}s.")
