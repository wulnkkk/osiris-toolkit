"""Test resource estimation accuracy against completed OSIRIS simulations.

Edit SIM_DIRS below to point to your completed simulation directories.
Each directory must contain an input deck (.in file) and simulation output.
"""

import sys
from pathlib import Path

from osiris_toolkit.deck import parse_deck_file
from osiris_toolkit.resource import estimate_resources

# ── CONFIGURATION ──
# Fill in paths to your completed OSIRIS simulation directories.
# Each must contain an input deck (.in file).
SIM_DIRS: list[str] = [
    "<SIM_DIR_1>",
    "<SIM_DIR_2>",
    "<SIM_DIR_3>",
]

# ── helpers ──

pass_count = 0
fail_count = 0


def record(result: bool, name: str, detail: str = "") -> None:
    global pass_count, fail_count
    if result:
        pass_count += 1
        print(f"[PASS] {name}")
    else:
        fail_count += 1
        print(f"[FAIL] {name}: {detail}")


def find_deck_file(sim_dir: Path) -> Path | None:
    """Find the first .in file in the simulation directory."""
    for p in sim_dir.iterdir():
        if p.suffix == ".in" and p.is_file():
            return p
    # Also check parent for deck files
    for p in sim_dir.parent.iterdir():
        if p.suffix == ".in" and p.is_file():
            return p
    return None


def estimate_for_sim(sim_dir: Path) -> dict | None:
    """Extract parameters and produce estimate for one simulation."""
    deck_path = find_deck_file(sim_dir)
    if deck_path is None:
        print(f"  [WARN] No .in deck file found in or above {sim_dir}")
        return None

    try:
        deck = parse_deck_file(str(deck_path))
    except Exception as e:
        print(f"  [WARN] Failed to parse deck {deck_path}: {e}")
        return None

    try:
        report = estimate_resources(deck)
    except Exception as e:
        print(f"  [WARN] Resource estimation failed: {e}")
        return None

    return {
        "deck_path": str(deck_path),
        "total_nodes": report.params.total_nodes,
        "ngrid_total": report.params.ngrid_total,
        "n_steps": report.params.n_steps,
        "num_species": report.params.num_species,
        "memory_per_node_gb": report.memory.total_gb,
        "wall_hours": report.runtime.wall_hours_upper,
        "disk_gb": report.disk.total_gb,
    }


# ── main ──

def main() -> None:
    global pass_count, fail_count

    # Check placeholders
    unresolved = [d for d in SIM_DIRS if d.startswith("<")]
    if unresolved:
        print("[FATAL] SIM_DIRS placeholders not replaced.")
        print("  Edit test_estimate.py and fill in SIM_DIRS with paths to")
        print("  your completed OSIRIS simulation directories.")
        sys.exit(1)

    print(f"{'='*60}")
    print("Test 03: Resource Prediction Calibration")
    print(f"{'='*60}")
    print()

    estimates = {}
    for i, sim_dir in enumerate(SIM_DIRS, 1):
        p = Path(sim_dir)
        if not p.is_dir():
            print(f"[WARN] Sim {i}: {sim_dir} does not exist, skipping.")
            continue

        print(f"[INFO] Sim {i}: {sim_dir}")
        est = estimate_for_sim(p)
        if est is None:
            continue

        estimates[i] = est
        print(f"  Grid: {est['ngrid_total']} cells, {est['n_steps']} steps, "
              f"{est['num_species']} species, {est['total_nodes']} nodes")
        print(f"  Estimated memory : {est['memory_per_node_gb']:.1f} GB/node")
        print(f"  Estimated wall   : {est['wall_hours']:.1f} h")
        print(f"  Estimated disk   : {est['disk_gb']:.1f} GB")
        print()

    if len(estimates) >= 2:
        record(True, "3.1 Parameter extraction",
               f"Successfully extracted from {len(estimates)}/{len(SIM_DIRS)} sims")
    elif len(estimates) == 1:
        record(True, "3.1 Parameter extraction",
               "Extracted from 1 sim (need >=3 for proper calibration)")
    else:
        record(False, "3.1 Parameter extraction", "No simulations could be processed")

    # Print instructions for manual comparison
    print()
    print(f"{'='*60}")
    print("MANUAL STEPS: Collect actual values and compare")
    print(f"{'='*60}")
    print()
    print("For each simulation directory, run these commands to get actual values:")
    print()
    print("  # Wall time (seconds)")
    print("  sacct -j <JOBID> --format=ElapsedRaw -n -P")
    print()
    print("  # Memory (KB → divide by 1e6 for GB)")
    print("  sacct -j <JOBID> --format=MaxRSS -n -P")
    print()
    print("  # Disk usage (GB)")
    print("  du -sh <sim_output_dir>/")
    print()
    print("Then fill in the comparison table in the report template.")

    print(f"{'='*60}")
    print(f"[TOTAL] {pass_count}/{pass_count + fail_count} automated checks passed")
    print(f"{'='*60}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
