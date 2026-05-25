"""Batch-process OSIRIS simulations: fields, k-space, density, scattering.

Generates visualisation images with physical units for all time steps.
Output is organised by simulation name under an output root directory.
"""

import time
from pathlib import Path

from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter

from .density import plot_density
from .field import plot_field
from .kspace import plot_k_space
from .scattering import analyze_scattering, plot_scattering_fraction

FIELD_QUANTS = ["e1", "e2", "e3", "b1", "b2", "b3"]


def process_simulation(
    sim_path: str | Path,
    sim_name: str,
    output_root: str | Path,
    x_unit: str = "um",
    y_unit: str = "um",
    time_unit: str = "ps",
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
    output_root : str or Path
        Root directory for all output.
    x_unit, y_unit : str
        Spatial axis units.
    time_unit : str
        Time unit for titles.
    """
    t_start = time.time()

    output_root = Path(output_root)

    sim = Simulation(sim_path)
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
        print(f"[{sim_name}] Warning: could not determine omega_p0;"
              f" using normalised units")

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
        print(f"[{sim_name}] No field data found.")
        return
    if not species_list:
        print(f"[{sim_name}] No species data found.")

    iterations = sim.list_iterations(available_fields[0])
    n_total = len(iterations)
    print(
        f"[{sim_name}] {n_total} iterations, {len(available_fields)} fields,"
        f" {len(species_list)} species"
    )
    print(f"[{sim_name}] Output directory: {base.resolve()}")

    for idx, it in enumerate(iterations):
        t_iter = time.time()

        # --- Field plots (delegate to field.py) ---
        for qty in available_fields:
            try:
                plot_field(
                    quantity=qty,
                    iteration=it,
                    sim_path=str(sim_path),
                    converter=converter,
                    x_unit=x_unit,
                    y_unit=y_unit,
                    time_unit=time_unit,
                    output=str(field_dir / f"{qty}_{it:06d}.png"),
                )
            except Exception as exc:
                print(f"  [{sim_name}] field {qty} iter={it}: {exc}")

        # --- k-space plots (delegate to kspace.py) ---
        for qty in available_fields:
            try:
                plot_k_space(
                    quantity=qty,
                    iteration=it,
                    sim_path=str(sim_path),
                    converter=converter,
                    time_unit=time_unit,
                    output=str(kspace_dir / f"kspace_{qty}_{it:06d}.png"),
                )
            except Exception as exc:
                print(f"  [{sim_name}] k-space {qty} iter={it}: {exc}")

        # --- Density plots (delegate to density.py) ---
        for sp in species_list:
            try:
                plot_density(
                    species=sp,
                    iteration=it,
                    sim_path=str(sim_path),
                    converter=converter,
                    x_unit=x_unit,
                    y_unit=y_unit,
                    time_unit=time_unit,
                    output=str(density_dir / f"density_{sp}_{it:06d}.png"),
                )
            except Exception as exc:
                print(f"  [{sim_name}] density {sp} iter={it}: {exc}")

        elapsed = time.time() - t_iter
        eta = elapsed * (n_total - idx - 1)
        print(
            f"  [{sim_name}] iter={it:06d} ({idx + 1}/{n_total})"
            f" done {elapsed:.1f}s, ETA {eta:.0f}s"
        )

    # --- Scattering analysis (delegate to scattering.py) ---
    print(f"[{sim_name}] Scattering analysis...")
    for qty in ["e1", "e2", "e3"]:
        if qty not in available_fields:
            continue
        try:
            result = analyze_scattering(
                quantity=qty,
                sim_path=str(sim_path),
                verbose=False,
            )
            plot_scattering_fraction(
                result,
                converter=converter,
                time_unit=time_unit,
                output=str(scattering_dir / f"scattering_{qty}.png"),
            )
            print(f"  [{sim_name}] scattering {qty} done")
        except Exception as exc:
            print(f"  [{sim_name}] scattering {qty}: {exc}")

    total = time.time() - t_start
    print(f"[{sim_name}] All done, elapsed {total:.0f}s.")


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
        print("=" * 60)
        print(f"Batch processing: {sim_name}")
        print("=" * 60)
        process_simulation(sim_path, sim_name, output_root=args.output_dir)
        print()


if __name__ == "__main__":
    main()
