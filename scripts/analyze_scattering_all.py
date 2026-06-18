"""Scattering fraction analysis for all 6 Zmaterial cases."""
import logging, time
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitSystem, SimulationParams
from osiris_toolkit.deck import parse_deck_file
from osiris_toolkit.analysis.scattering import ScatteringAnalyzer
from osiris_toolkit.vis.scattering import plot_scattering_fraction

BASE = Path("/path/to/Zmaterial")
CASES = ["Au", "Au0", "Ti", "Ti0", "CH_fixed", "CH0_fixed"]
QUANTITIES = ["e1", "e2", "e3"]


def main():
    for case in CASES:
        sim_path = BASE / case
        logger.info("=== %s ===", case)

        # UnitSystem from deck
        in_files = sorted(sim_path.glob("*.in"))
        system = None
        if in_files:
            try:
                deck = parse_deck_file(str(in_files[0]))
                params = SimulationParams.from_deck(deck)
                system = UnitSystem.from_params(params)
                logger.info("  UnitSystem OK, omega_p=%.3g", system.omega_p)
            except Exception as e:
                logger.warning("  No UnitSystem: %s", e)

        sim = Simulation(str(sim_path))
        available = sim.list_fields()
        logger.info("  Fields: %s", available)

        # Output dir
        out_dir = sim_path / "figures" / "scattering"
        out_dir.mkdir(parents=True, exist_ok=True)

        analyzer = ScatteringAnalyzer(sim, system)
        t0 = time.perf_counter()

        for qty in QUANTITIES:
            if qty not in available:
                logger.info("  skip %s (not available)", qty)
                continue
            try:
                logger.info("  analyzing %s ...", qty)
                result = analyzer.analyze(quantity=qty, verbose=True)
                fpath = plot_scattering_fraction(
                    result,
                    system=system,
                    time_unit="ps",
                    output=str(out_dir / f"scattering_{qty}.png"),
                )
                if fpath:
                    logger.info("  saved %s", fpath)
            except Exception as e:
                logger.error("  FAIL %s: %s", qty, e)

        logger.info("  done in %.0fs", time.perf_counter() - t0)

    logger.info("ALL DONE")


if __name__ == "__main__":
    main()
