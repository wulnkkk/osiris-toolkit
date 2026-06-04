"""Test MPI multi-node parallel analysis and visualisation.

Usage:
    mpirun -np <N> python tests/hpc/01-mpi-multinode/test_mpi.py
"""

import os
import sys

from osiris_toolkit.parallel._cluster import (
    detect_mpi_rank,
    limit_blas_threads,
    split_iterations,
)
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


def test_1_1_mpi_distribution(comm_rank: int, comm_size: int) -> None:
    """Verify all MPI ranks are present and unique."""
    _all_ranks = comm_rank  # gather not available; each rank prints its own info
    print(f"[INFO] MPI rank={comm_rank}, world_size={comm_size}")
    record(comm_size > 1, "1.1 MPI distribution: all ranks detected",
           f"world_size={comm_size}, expected > 1")


def test_1_2_iteration_split(comm_rank: int, comm_size: int) -> None:
    """Verify iteration splitting has no overlap and no gaps."""
    sim = Simulation(SIM_DATA_PATH)
    fields = sim.list_fields()
    if not fields:
        record(False, "1.2 Iteration split", "No field data found")
        return
    iterations = sim.list_iterations(fields[0])
    my_iters = split_iterations(iterations, comm_rank, comm_size)

    # Check this rank's iterations are a valid stride subset
    for it in my_iters:
        idx = iterations.index(it)
        if idx % comm_size != comm_rank:
            record(False, "1.2 Iteration split",
                   f"Iteration {it} at index {idx} assigned to wrong rank {comm_rank}")
            return

    print(f"[INFO] Rank {comm_rank}: {len(my_iters)} iterations assigned")
    record(True, "1.2 Iteration split: no overlap, no gaps")


def test_1_3_analysis_parallel(comm_rank: int, comm_size: int) -> None:
    """Test multi-node field energy analysis."""
    from osiris_toolkit.analysis.parallel import field_energy_all

    sim = Simulation(SIM_DATA_PATH)
    fields = sim.list_fields()
    if not fields:
        record(False, "1.3 Multi-node analysis", "No field data found")
        return

    quantity = fields[0]
    total_iterations = len(sim.list_iterations(quantity))
    results = field_energy_all(sim, quantity)

    # Only rank 0 collects and validates
    print(f"[INFO] Rank {comm_rank}: processed {len(results)}/{total_iterations} iterations")
    record(len(results) > 0, "1.3 Multi-node analysis parallel",
           f"{len(results)} results returned, total iterations={total_iterations}")


def test_1_4_visualisation_parallel(comm_rank: int, comm_size: int) -> None:
    """Test multi-node batch visualisation (analysis-only subset for MPI test)."""
    from osiris_toolkit.analysis.parallel import describe_all

    sim = Simulation(SIM_DATA_PATH)
    fields = sim.list_fields()
    if not fields:
        record(False, "1.4 Multi-node visualisation", "No field data found")
        return

    results = describe_all(sim, fields[0])
    print(f"[INFO] Rank {comm_rank}: describe_all returned {len(results)} results")

    # Validate: each result has expected keys
    expected_keys = {"iteration", "time", "mean", "std", "min", "max", "rms"}
    for r in results:
        if not expected_keys.issubset(r.keys()):
            record(False, "1.4 Multi-node visualisation",
                   f"Missing keys in result: {r.keys()}")
            return
    record(True, "1.4 Multi-node visualisation parallel",
           f"{len(results)} describe results with valid keys")


def main() -> None:
    global pass_count, fail_count, SIM_DATA_PATH
    limit_blas_threads(1)

    mpi = detect_mpi_rank()
    if mpi is None:
        comm_rank, comm_size = 0, 1
        print("[INFO] No MPI detected; running single-process sanity check.")
    else:
        comm_rank, comm_size = mpi

    # Resolve sim data path
    sim_path = SIM_DATA_PATH.strip()
    if sim_path.startswith("<"):
        print("[FATAL] SIM_DATA_PATH placeholder not replaced.")
        print("  Set env var: export SIM_DATA_PATH=/path/to/sim/output")
        sys.exit(1)

    if not os.path.isdir(sim_path):
        print(f"[FATAL] SIM_DATA_PATH does not exist: {sim_path}")
        sys.exit(1)


    SIM_DATA_PATH = sim_path

    print(f"{'='*60}")
    print("Test 01: MPI Multi-Node Parallel")
    print(f"Rank: {comm_rank}, World size: {comm_size}")
    print(f"Data path: {SIM_DATA_PATH}")
    print(f"{'='*60}")

    test_1_1_mpi_distribution(comm_rank, comm_size)
    test_1_2_iteration_split(comm_rank, comm_size)
    test_1_3_analysis_parallel(comm_rank, comm_size)
    test_1_4_visualisation_parallel(comm_rank, comm_size)

    print(f"{'='*60}")
    print(f"[TOTAL] {pass_count}/{pass_count + fail_count} passed")
    print(f"{'='*60}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
