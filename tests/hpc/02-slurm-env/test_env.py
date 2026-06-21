"""Test SLURM environment variable detection.

Usage:
    python tests/hpc/02-slurm-env/test_env.py
"""

import os
import sys

from osiris_toolkit.parallel._cluster import (
    detect_available_workers,
    detect_job_array,
    limit_blas_threads,
    split_iterations,
)

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


# ── tests ──


def test_2_1_cpu_detection() -> None:
    """detect_available_workers() should read SLURM_CPUS_PER_TASK."""
    slurm_cpus = os.environ.get("SLURM_CPUS_PER_TASK")
    workers = detect_available_workers()

    print(f"[INFO] SLURM_CPUS_PER_TASK={slurm_cpus}")
    print(f"[INFO] detect_available_workers()={workers}")

    if slurm_cpus is None:
        record(True, "2.1 CPU detection", f"SLURM_CPUS_PER_TASK not set (not a SLURM job?), workers={workers}")
    else:
        record(workers == int(slurm_cpus), "2.1 CPU detection", f"workers={workers}, expected={slurm_cpus}")


def test_2_2_job_array_detection() -> None:
    """detect_job_array() should read SLURM_ARRAY_TASK_ID / SLURM_ARRAY_TASK_COUNT."""
    arr = detect_job_array()
    slurm_tid = os.environ.get("SLURM_ARRAY_TASK_ID")
    slurm_cnt = os.environ.get("SLURM_ARRAY_TASK_COUNT")

    print(f"[INFO] SLURM_ARRAY_TASK_ID={slurm_tid}, SLURM_ARRAY_TASK_COUNT={slurm_cnt}")
    print(f"[INFO] detect_job_array()={arr}")

    if slurm_tid is None or slurm_cnt is None:
        record(True, "2.2 Job array detection", "Not in a job array; detect_job_array() should return None")
        if arr is not None:
            record(False, "2.2 Job array detection", f"Expected None but got {arr}")
    else:
        expected = (int(slurm_tid), int(slurm_cnt))
        record(arr == expected, "2.2 Job array detection", f"got {arr}, expected {expected}")


def test_2_3_job_array_iteration_split() -> None:
    """Verify job array tasks get non-overlapping iteration slices."""
    arr = detect_job_array()
    if arr is None:
        print("[INFO] 2.3 skipped: not in a job array")
        return

    task_id, task_count = arr
    # Use a fixed 20-element list to test splitting
    all_iterations = list(range(20))
    my_slice = split_iterations(all_iterations, task_id, task_count)

    # Verify: each item's index mod task_count equals task_id
    for item in my_slice:
        if item % task_count != task_id:
            record(False, "2.3 Job array split", f"Item {item} assigned to task {task_id} (mod {task_count})")
            return

    print(f"[INFO] Task {task_id}/{task_count}: slice = {my_slice}")
    record(True, "2.3 Job array iteration split", f"Task {task_id}/{task_count}: {len(my_slice)} items, no overlap")


def test_2_4_blas_thread_limiting() -> None:
    """limit_blas_threads() should set OMP_NUM_THREADS etc. to 1."""
    # Clear first
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ.pop(v, None)

    limit_blas_threads(1)

    ok = True
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        val = os.environ.get(v)
        print(f"[INFO] {v}={val}")
        if val != "1":
            ok = False

    record(ok, "2.4 BLAS thread limiting", "All thread variables should be set to '1'")


# ── main ──


def main() -> None:
    global pass_count, fail_count

    print(f"{'=' * 60}")
    print("Test 02: SLURM Environment Variable Integration")
    print(f"{'=' * 60}")

    test_2_1_cpu_detection()
    test_2_2_job_array_detection()
    test_2_3_job_array_iteration_split()
    test_2_4_blas_thread_limiting()

    print(f"{'=' * 60}")
    print(f"[TOTAL] {pass_count}/{pass_count + fail_count} passed")
    print(f"{'=' * 60}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
