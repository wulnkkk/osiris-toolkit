"""K-space-only post-processing for Zmaterial cases.
Usage: python plot_kspace.py
"""

import logging
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from osiris_toolkit.parallel._cluster import detect_available_workers, limit_blas_threads
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis.parallel import _worker_plot_k_space

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

BASE = Path("/path/to/Zmaterial")  # TODO: replace with your simulation data directory
CASES = ["Au", "Au0", "Ti", "Ti0"]
QUANTITIES = ["e1", "e2", "e3"]
NUM_SAMPLES = 10


def main() -> None:
    total_jobs = 0
    completed = 0
    errors = 0

    for case in CASES:
        sim_path = BASE / case
        sim = Simulation(str(sim_path))
        available = sim.list_fields()
        logger.info("[%s] Fields available: %s", case, available)

        tasks: list[tuple[str, int]] = []
        selected: list[int] = []
        for qty in QUANTITIES:
            if qty not in available:
                continue
            iters = sim.list_iterations(qty)
            if len(iters) <= NUM_SAMPLES:
                selected = iters
            else:
                step = len(iters) // NUM_SAMPLES
                selected = [iters[i] for i in range(0, len(iters), step)][:NUM_SAMPLES]
            for it in selected:
                tasks.append((qty, it))

        logger.info("[%s] %d k-space tasks (%d qty x %d iters)",
                    case, len(tasks), len(QUANTITIES), len(selected))

        if not tasks:
            logger.warning("[%s] No tasks, skipping.", case)
            continue

        kspace_dir = sim_path / "figures" / "k_space"
        kspace_dir.mkdir(parents=True, exist_ok=True)

        max_workers = min(detect_available_workers(), 16)
        ctx = multiprocessing.get_context("spawn")
        t0 = time.perf_counter()

        with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as ex:
            futmap: dict = {}
            for qty, it in tasks:
                out = str(kspace_dir / f"{qty}_{it:06d}.png")
                fut = ex.submit(_worker_plot_k_space, sim, it, qty, out)
                futmap[fut] = f"kspace {qty} it={it}"

            total_jobs += len(futmap)

            for fut in as_completed(futmap):
                desc = futmap[fut]
                try:
                    fut.result()
                    completed += 1
                    if completed % 10 == 0:
                        logger.info("  progress: %d/%d", completed, total_jobs)
                except Exception as exc:
                    errors += 1
                    logger.error("  FAIL %s: %s", desc, exc)

        elapsed = time.perf_counter() - t0
        logger.info("[%s] done: %d tasks in %.0fs", case, len(futmap), elapsed)

    logger.info("=== ALL DONE ===")
    logger.info("Total: %d, completed: %d, errors: %d", total_jobs, completed, errors)


if __name__ == "__main__":
    main()
