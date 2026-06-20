"""CH cases: CH/CH0/CH_fixed/CH0_fixed — field + k-space, e1/e2/e3, 10 sampled iters."""
import logging, multiprocessing, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import matplotlib; matplotlib.use("Agg")

from osiris_toolkit.parallel._cluster import detect_available_workers, limit_blas_threads
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis.parallel import _worker_plot_field, _worker_plot_k_space

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

BASE = Path("/path/to/Zmaterial")  # TODO: replace with your simulation data directory
CASES = ["CH", "CH0", "CH_fixed", "CH0_fixed"]
QUANTITIES = ["e1", "e2", "e3"]
NUM_SAMPLES = 10


def main():
    total = 0; ok = 0; err = 0
    for case in CASES:
        sim_path = BASE / case
        sim = Simulation(str(sim_path))
        available = sim.list_fields()
        logger.info("[%s] %s", case, available)

        tasks = []
        for qty in QUANTITIES:
            if qty not in available: continue
            iters = sim.list_iterations(qty)
            step = max(len(iters) // NUM_SAMPLES, 1)
            sel = [iters[i] for i in range(0, len(iters), step)][:NUM_SAMPLES]
            for it in sel: tasks.append((qty, it))
        logger.info("[%s] %d tasks", case, len(tasks))

        fd = sim_path / "figures" / "field"; kd = sim_path / "figures" / "k_space"
        fd.mkdir(parents=True, exist_ok=True); kd.mkdir(parents=True, exist_ok=True)

        ctx = multiprocessing.get_context("spawn")
        nw = min(detect_available_workers(), 16)
        t0 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=nw, mp_context=ctx) as ex:
            fm = {}
            for qty, it in tasks:
                fm[ex.submit(_worker_plot_field, sim, it, qty, str(fd / f"{qty}_{it:06d}.png"))] = f"field {qty} it={it}"
                fm[ex.submit(_worker_plot_k_space, sim, it, qty, str(kd / f"{qty}_{it:06d}.png"))] = f"kspace {qty} it={it}"
            total += len(fm)
            for f in as_completed(fm):
                d = fm[f]
                try: f.result(); ok += 1
                except Exception as e: err += 1; logger.error("  FAIL %s: %s", d, e)
                if ok % 20 == 0: logger.info("  %d/%d", ok, total)
        logger.info("[%s] done: %d tasks in %.0fs", case, len(fm), time.perf_counter()-t0)
    logger.info("ALL DONE: %d/%d ok, %d errors", ok, total, err)

if __name__ == "__main__": main()
