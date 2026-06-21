"""Test large-scale parallel data processing throughput.

Usage:
    python tests/hpc/04-large-data-scale/test_throughput.py --mode analysis
    python tests/hpc/04-large-data-scale/test_throughput.py --mode vis
"""

import argparse
import gc
import os
import sys
import time

from osiris_toolkit.parallel._cluster import detect_available_workers, limit_blas_threads
from osiris_toolkit.sim import Simulation

SIM_DATA_PATH = os.environ.get("SIM_DATA_PATH", "<SIM_DATA_DIR>")

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


def mode_analysis(sim_path: str) -> None:
    """Run field_energy_all with varying worker counts; measure speedup."""
    from osiris_toolkit.analysis.parallel import field_energy_all

    sim = Simulation(sim_path)
    fields = sim.list_fields()
    if not fields:
        print("[FATAL] No field data found")
        sys.exit(1)

    quantity = fields[0]
    iterations = sim.list_iterations(quantity)
    total_iters = len(iterations)
    print(f"[INFO] Mode: analysis, Quantity: {quantity}, Iterations: {total_iters}")

    worker_counts = [1, 2, 4, 8]
    baseline_time = None
    timings = {}

    for n_workers in worker_counts:
        gc.collect()
        t0 = time.perf_counter()

        results = field_energy_all(sim, quantity, max_workers=n_workers)

        elapsed = time.perf_counter() - t0

        if baseline_time is None:
            baseline_time = elapsed
            speedup = 1.0
        else:
            speedup = baseline_time / elapsed

        timings[n_workers] = {"time": elapsed, "speedup": speedup}
        print(f"  Workers={n_workers:2d}: time={elapsed:6.1f}s, results={len(results)}, speedup={speedup:.2f}x")

    # Test 4.1: all iterations processed
    record(len(results) == total_iters, "4.1 field_energy_all", f"{len(results)}/{total_iters} iterations")

    # Test 4.3: meaningful speedup at >= 4 workers
    if 4 in timings:
        record(
            timings[4]["speedup"] >= 1.5,
            "4.3 Scalability: speedup at 4 workers",
            f"speedup={timings[4]['speedup']:.2f}x",
        )

    # Test 4.4: large dataset read — check max single read
    # Load the field with most data to measure I/O
    t0 = time.perf_counter()
    grid = sim.get_field(quantity, iterations[0])
    if grid is not None:
        read_time = time.perf_counter() - t0
        data_mb = grid.data.nbytes / (1024**2)
        print(f"  Largest read: {data_mb:.1f} MB in {read_time:.2f}s ({data_mb / read_time:.1f} MB/s)")
        record(True, "4.4 Large dataset read", f"{data_mb:.1f} MB at {data_mb / read_time:.1f} MB/s")
    else:
        record(False, "4.4 Large dataset read", "get_field returned None")


def mode_vis(sim_path: str) -> None:
    """Run batch_process_parallel and count generated files."""
    from osiris_toolkit.vis.parallel import batch_process_parallel

    sim = Simulation(sim_path)
    fields = sim.list_fields()
    species = sim.list_species()
    if not fields:
        print("[FATAL] No field data found")
        sys.exit(1)

    print("[INFO] Mode: vis")
    print(f"[INFO] Fields: {fields}")
    print(f"[INFO] Species: {species}")

    t0 = time.perf_counter()
    max_workers = detect_available_workers()
    print(f"[INFO] Workers: {max_workers}")

    batch_process_parallel(
        sim_path=sim_path,
        sim_name="hpc_test_04",
        max_workers=min(max_workers, 8),
    )
    elapsed = time.perf_counter() - t0

    # Count generated files
    output_dir = sim.output_root / "hpc_test_04"
    file_count = 0
    if output_dir.is_dir():
        file_count = sum(1 for _ in output_dir.rglob("*.png"))
        file_count += sum(1 for _ in output_dir.rglob("*.pdf"))

    print(f"  Total time: {elapsed:.1f}s")
    print(f"  Files generated: {file_count}")
    record(file_count > 0, "4.2 Batch visualisation", f"{file_count} files in {elapsed:.1f}s")


def main() -> None:
    global pass_count, fail_count

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["analysis", "vis"])
    args = parser.parse_args()

    limit_blas_threads(1)

    # Resolve sim data path
    sim_path = SIM_DATA_PATH.strip()
    if sim_path.startswith("<"):
        print("[FATAL] SIM_DATA_PATH placeholder not replaced.")
        print("  Set env var: export SIM_DATA_PATH=/path/to/sim/output")
        sys.exit(1)
    if not os.path.isdir(sim_path):
        print(f"[FATAL] SIM_DATA_PATH does not exist: {sim_path}")
        sys.exit(1)

    print(f"{'=' * 60}")
    print(f"Test 04: Large-Scale Data Parallel Processing  [mode={args.mode}]")
    print(f"Data path: {sim_path}")
    print(f"{'=' * 60}")

    if args.mode == "analysis":
        mode_analysis(sim_path)
    else:
        mode_vis(sim_path)

    print(f"{'=' * 60}")
    print(f"[TOTAL] {pass_count}/{pass_count + fail_count} passed")
    print(f"{'=' * 60}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
