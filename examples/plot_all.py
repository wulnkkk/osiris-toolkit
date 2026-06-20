"""All-iteration field + kspace (zoom) for all 8 Zmaterial cases, skip-existing."""
import logging, multiprocessing, time, os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import matplotlib; matplotlib.use("Agg")

from osiris_toolkit.parallel._cluster import detect_available_workers, limit_blas_threads
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis.common import get_system
from osiris_toolkit.vis.parallel import _worker_plot_field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

BASE = Path("/path/to/Zmaterial")  # TODO: replace with your simulation data directory
CASES = ["Au", "Au0", "Ti", "Ti0", "CH_fixed", "CH0_fixed"]
QUANTITIES = ["e1", "e2", "e3"]


def _worker_kspace_zoom(qty, it, sim_path, output):
    limit_blas_threads(1)
    import matplotlib as _mpl; _mpl.use("Agg")
    from osiris_toolkit.vis.kspace import plot_k_space
    sim = Simulation(str(sim_path))
    system = get_system(sim)
    plot_k_space(qty, it, sim=sim, system=system, time_unit="ps",
                 output=output, xlim=(-3, 3), ylim=(-3, 3))


def gather_tasks(sim_path, sim, available, skip_existing):
    """Return list of (type, qty, it, output_path) tuples, skipping existing files."""
    tasks = []
    fd = sim_path / "figures" / "field"
    kd = sim_path / "figures" / "k_space"
    fd.mkdir(parents=True, exist_ok=True)
    kd.mkdir(parents=True, exist_ok=True)

    for qty in QUANTITIES:
        if qty not in available:
            continue
        for it in sim.list_iterations(qty):
            # Field
            fp = str(fd / f"{qty}_{it:06d}.png")
            if not (skip_existing and os.path.exists(fp)):
                tasks.append(("field", qty, it, fp))
            # K-space zoom
            kp = str(kd / f"{qty}_{it:06d}.png")
            if not (skip_existing and os.path.exists(kp)):
                tasks.append(("kspace", qty, it, kp))

    return tasks


def main():
    # Re-use existing files: only generate what's missing
    SKIP = True
    total = 0; ok = 0; skip = 0; err = 0

    for case in CASES:
        sim_path = BASE / case
        if not sim_path.is_dir():
            logger.info("[%s] not found, skip", case)
            continue
        sim = Simulation(str(sim_path))
        tasks = gather_tasks(sim_path, sim, sim.list_fields(), SKIP)
        total_all = len(tasks)
        # Count skipped
        all_possible = 0
        for qty in QUANTITIES:
            if qty in sim.list_fields():
                all_possible += len(sim.list_iterations(qty)) * 2
        already = all_possible - total_all
        skip += already
        logger.info("[%s] %d new / %d skip / %d total", case, total_all, already, all_possible)

        if not tasks:
            continue

        ctx = multiprocessing.get_context("spawn")
        nw = min(detect_available_workers(), 16)
        t0 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=nw, mp_context=ctx) as ex:
            fm = {}
            for typ, qty, it, out in tasks:
                if typ == "field":
                    fm[ex.submit(_worker_plot_field, sim, it, qty, out)] = f"field {qty} it={it}"
                else:
                    fm[ex.submit(_worker_kspace_zoom, qty, it, str(sim_path), out)] = f"kspace {qty} it={it}"
            total += len(fm)
            for f in as_completed(fm):
                d = fm[f]
                try:
                    f.result(); ok += 1
                except Exception as e:
                    err += 1; logger.error("  FAIL %s: %s", d, e)
                if ok % 50 == 0:
                    logger.info("  %d/%d", ok, total)
        logger.info("[%s] done: %d tasks in %.0fs", case, len(fm), time.perf_counter() - t0)

    logger.info("ALL DONE: %d new ok, %d skipped, %d errors", ok, skip, err)


if __name__ == "__main__":
    main()
