"""Comprehensive PIC post-processing: angular k-space + EPW spectrum + hot electrons.

Runs on HPC compute node. Output: comparison PNGs in each case's figures/analysis/
"""
import logging, time, os
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitSystem, SimulationParams
from osiris_toolkit.deck import parse_deck_file
from osiris_toolkit.compute.fft import compute_k_space
from osiris_toolkit.compute.integrate import mask_energy

BASE = Path("/path/to/Zmaterial")  # TODO: replace with your simulation data directory
CASES = ["Au", "Au0", "Ti", "Ti0", "CH_fixed", "CH0_fixed"]
CASE_LABELS = {"Au":"Au SSD", "Au0":"Au CPP", "Ti":"Ti SSD", "Ti0":"Ti CPP",
               "CH_fixed":"CH SSD", "CH0_fixed":"CH CPP"}
MATERIAL_COLORS = {"Au":"gold", "Au0":"goldenrod", "Ti":"silver", "Ti0":"gray",
                   "CH_fixed":"blue", "CH0_fixed":"navy"}
LASER_MARKER = {"SSD":"o", "CPP":"s"}


# ============================================================
# Task 1.1: Angular k-space scattering analysis
# ============================================================

def polar_mask_energy(spectrum, kx, ky, k_range, theta_range, system):
    """Integrate k-space spectrum in a polar sector: |k| in [k0,k1], θ in [θ0,θ1] degrees.

    Returns total energy in that sector (sum of |FFT|²).
    """
    kx2d, ky2d = np.meshgrid(kx, ky, indexing="ij")
    k_mag = np.sqrt(kx2d**2 + ky2d**2)
    k_conv = system.wavenumber.to(k_mag, "k0")
    theta = np.degrees(np.arctan2(ky2d, kx2d))

    mask = (k_conv >= k_range[0]) & (k_conv <= k_range[1]) & (theta >= theta_range[0]) & (theta <= theta_range[1])
    return float(np.sum(spectrum[mask]**2))


def analyze_angular_scattering(case_name, system, sim):
    """Extract SBS, SRBS, SRSS intensities vs time using polar k-space masks."""
    # Define angular sectors (in k0 units, degrees)
    sectors = {
        "SBS":    {"k": (0.8, 1.2),  "theta": (150, 210)},   # backscatter @ k~k0
        "SRBS":   {"k": (0.4, 0.9),  "theta": (150, 210)},   # backscatter @ k<k0
        "SRSS":   {"k": (0.4, 0.9),  "theta": (50, 130)},    # side-scatter
    }

    results = {name: [] for name in sectors}
    results["times"] = []
    results["total_energy"] = []

    t0 = time.perf_counter()
    for it in sim.list_iterations("e1"):
        grid = sim.get_field("e1", it)
        if grid is None:
            continue

        nx, ny = grid.data.shape
        dx = (grid.axes[0].max - grid.axes[0].min) / nx
        dy = (grid.axes[1].max - grid.axes[1].min) / ny
        kx, ky, spectrum = compute_k_space(grid.data, dx, dy)

        results["times"].append(grid.time)
        total = float(np.sum(np.abs(spectrum)**2))
        results["total_energy"].append(total if total > 0 else 1e-30)

        for name, sec in sectors.items():
            eng = polar_mask_energy(spectrum, kx, ky, sec["k"], sec["theta"], system)
            results[name].append(eng)

        if it % 9000 == 0:
            logger.info("  %s it=%d t=%.0f SBS=%.4f SRBS=%.4f SRSS=%.4f",
                        case_name, it, grid.time,
                        results["SBS"][-1] / results["total_energy"][-1],
                        results["SRBS"][-1] / results["total_energy"][-1],
                        results["SRSS"][-1] / results["total_energy"][-1])

    elapsed = time.perf_counter() - t0
    logger.info("  %s angular analysis done in %.0fs", case_name, elapsed)
    return results


def plot_angular_comparison(all_results, out_dir):
    """1x3 panel: SBS, SRBS, SRSS time evolution + final bar chart."""
    fig, axes = plt.subplots(1, 4, figsize=(22, 5))

    for idx, channel in enumerate(["SBS", "SRBS", "SRSS"]):
        ax = axes[idx]
        for case in CASES:
            r = all_results[case]
            ts = np.array(r["times"])
            vals = np.array(r[channel]) / np.array(r["total_energy"])
            ax.plot(ts, vals, label=CASE_LABELS[case], alpha=0.8, linewidth=1.2)
        ax.set_title(channel, fontsize=13)
        ax.set_xlabel("Time (1/omega_p)")
        ax.set_ylabel("Energy fraction")
        ax.legend(fontsize=7, ncol=2)
        ax.grid(True, alpha=0.3)

    # Bar chart: final-time values
    ax = axes[3]
    x = np.arange(len(CASES))
    width = 0.25
    for i, channel in enumerate(["SBS", "SRBS", "SRSS"]):
        final_vals = [all_results[c][channel][-1] / all_results[c]["total_energy"][-1] for c in CASES]
        ax.bar(x + i*width, final_vals, width, label=channel, alpha=0.85)
    ax.set_xticks(x + width)
    ax.set_xticklabels([CASE_LABELS[c] for c in CASES], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Energy fraction (final step)")
    ax.set_title("Scattering channel comparison", fontsize=13)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    fpath = out_dir / "analysis_angular_scattering.png"
    fig.savefig(fpath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("  Saved %s", fpath)


# ============================================================
# Task 1.2: EPW density spectrum (charge → 2D FFT → Δk)
# ============================================================

def analyze_epw_damping(sim, system, case_name):
    """Extract charge density k-space spectrum and estimate EPW width."""
    times_epw = []
    k_peak = []
    fwhm_k = []

    ref_iters = sim.list_iterations("e1")
    t0 = time.perf_counter()
    for it in ref_iters:
        grid = sim.get_density("electrons", quantity="charge", iteration=it)
        if grid is None:
            continue

        nx, ny = grid.data.shape
        dx = (grid.axes[0].max - grid.axes[0].min) / nx
        dy = (grid.axes[1].max - grid.axes[1].min) / ny
        kx, ky, spectrum = compute_k_space(grid.data, dx, dy)

        # 1D projection along kx (laser direction) to find EPW peak
        proj_kx = spectrum.mean(axis=1)  # average over ky
        kx_k0 = system.wavenumber.to(kx, "k0")

        # Find peak in |kx| > 0.2 k0 (exclude DC)
        mask_k = np.abs(kx_k0) > 0.2
        if mask_k.sum() > 0:
            idx_peak = np.argmax(proj_kx[mask_k])
            k_peak_val = np.abs(kx_k0[mask_k][idx_peak])

            # FWHM: find points where proj drops to half max
            half_max = proj_kx[mask_k][idx_peak] / 2
            above = np.where(proj_kx[mask_k] > half_max)[0]
            if len(above) > 1:
                dk = np.abs(kx_k0[mask_k][above[-1]] - kx_k0[mask_k][above[0]])
            else:
                dk = 0.0

            times_epw.append(grid.time)
            k_peak.append(k_peak_val)
            fwhm_k.append(dk)

    elapsed = time.perf_counter() - t0
    logger.info("  EPW analysis: %d time steps in %.0fs, mean dk=%.4f k0",
                len(k_peak), elapsed, np.mean(fwhm_k) if fwhm_k else 0)
    return {"times": times_epw, "k_peak": k_peak, "fwhm_k": fwhm_k}


def plot_epw_comparison(all_epw, out_dir):
    """Plot EPW peak wavenumber and FWHM vs time for all cases."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    for case in CASES:
        r = all_epw[case]
        ts = np.array(r["times"])
        if len(ts) == 0:
            continue
        kp = np.array(r["k_peak"])
        dk = np.array(r["fwhm_k"])
        ax1.plot(ts, kp, label=CASE_LABELS[case], linewidth=1.2)
        ax2.plot(ts, dk, label=CASE_LABELS[case], linewidth=1.2)

    ax1.set_title("EPW peak |k| vs time", fontsize=13)
    ax1.set_xlabel("Time (1/omega_p)")
    ax1.set_ylabel("|k| (k0)")
    ax1.legend(fontsize=7, ncol=2)
    ax1.grid(True, alpha=0.3)

    ax2.set_title("EPW Delta-k (FWHM) vs time", fontsize=13)
    ax2.set_xlabel("Time (1/omega_p)")
    ax2.set_ylabel("Delta-k (k0)")
    ax2.legend(fontsize=7, ncol=2)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    fpath = out_dir / "analysis_epw_damping.png"
    fig.savefig(fpath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("  Saved %s", fpath)


# ============================================================
# Task 1.3: Hot electron analysis (p1p2 → f(E) → T_hot)
# ============================================================

def analyze_hot_electrons(sim, case_name):
    """Extract electron energy spectrum from phasespace histogram and estimate T_hot."""
    times_he = []
    t_hot_vals = []
    avg_energy = []

    ref_iters = sim.list_iterations("e1")
    t0 = time.perf_counter()
    for it in ref_iters:
        ps = sim.get_phasespace("p1p2", "electrons", it)
        if ps is None or not hasattr(ps, 'data') or ps.data is None:
            continue

        data = ps.data  # 2D histogram: (np2, np1) — axes[0]=p2, axes[1]=p1
        axes = ps.axes if hasattr(ps, 'axes') else []
        if len(axes) < 2:
            continue

        ax_p2 = axes[0]; ax_p1 = axes[1]
        p2_min = float(ax_p2.get('min', -1)); p2_max = float(ax_p2.get('max', 1))
        p1_min = float(ax_p1.get('min', -1)); p1_max = float(ax_p1.get('max', 1))
        np2, np1 = data.shape
        p1_bins = np.linspace(p1_min, p1_max, np1)
        p2_bins = np.linspace(p2_min, p2_max, np2)

        p1_2d, p2_2d = np.meshgrid(p1_bins, p2_bins, indexing='ij')
        p_mag = np.sqrt(p1_2d**2 + p2_2d**2)
        E_k = np.sqrt(p_mag**2 + 1) - 1

        counts = np.abs(data)  # deposited electron charge → absolute counts
        total_counts = counts.sum()
        if total_counts < 10:
            continue

        mean_e = float(np.average(E_k.ravel(), weights=counts.ravel()))

        hot_mask = E_k > 3 * mean_e
        hot_counts = counts[hot_mask].sum()
        if hot_counts > 5:
            t_hot = float(np.average(E_k[hot_mask].ravel(), weights=counts[hot_mask].ravel()))
        else:
            t_hot = mean_e

        times_he.append(ps.time if hasattr(ps, 'time') else it)
        t_hot_vals.append(t_hot)
        avg_energy.append(mean_e)

    elapsed = time.perf_counter() - t0
    logger.info("  Hot-electron analysis: %d steps in %.0fs", len(times_he), elapsed)
    return {"times": times_he, "t_hot": t_hot_vals, "avg_energy": avg_energy}


def plot_hot_electron_comparison(all_he, out_dir):
    """Plot hot electron temperature vs time + final bar chart."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    final_t_hot = {}
    for case in CASES:
        r = all_he[case]
        ts = np.array(r["times"])
        if len(ts) == 0:
            continue
        th = np.array(r["t_hot"])
        ax1.plot(ts, th, label=CASE_LABELS[case], linewidth=1.2)
        final_t_hot[case] = th[-1] if len(th) > 0 else 0

    ax1.set_title("Hot-electron T_hot (m_e c^2) vs time", fontsize=13)
    ax1.set_xlabel("Time (1/omega_p)")
    ax1.set_ylabel("T_hot (m_e c^2)")
    ax1.legend(fontsize=7, ncol=2)
    ax1.grid(True, alpha=0.3)

    # Bar chart
    labels = [CASE_LABELS[c] for c in CASES]
    values = [final_t_hot.get(c, 0) for c in CASES]
    colors = [MATERIAL_COLORS[c] for c in CASES]
    ax2.bar(labels, values, color=colors, alpha=0.8)
    ax2.set_title("T_hot (final step)", fontsize=13)
    ax2.set_ylabel("T_hot (m_e c^2)")
    ax2.tick_params(axis="x", rotation=45, labelsize=8)
    ax2.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    fpath = out_dir / "analysis_hot_electrons.png"
    fig.savefig(fpath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("  Saved %s", fpath)


# ============================================================
# Main
# ============================================================

def main():
    # Store results for global comparison plots
    all_angular = {}
    all_epw = {}
    all_he = {}

    # Output root for global comparison plots
    out_root = BASE / "analysis_summary"
    out_root.mkdir(parents=True, exist_ok=True)

    for case in CASES:
        sim_path = BASE / case
        logger.info("=" * 60)
        logger.info("CASE: %s", case)
        logger.info("=" * 60)

        # Build UnitSystem
        in_files = sorted(sim_path.glob("*.in"))
        system = None
        if in_files:
            deck = parse_deck_file(str(in_files[0]))
            params = SimulationParams.from_deck(deck)
            system = UnitSystem.from_params(params)

        sim = Simulation(str(sim_path))

        # Per-case output
        case_out = sim_path / "figures" / "analysis"
        case_out.mkdir(parents=True, exist_ok=True)

        # Task 1.1: Angular k-space scattering
        logger.info("--- Task 1.1: Angular k-space scattering ---")
        r_angular = analyze_angular_scattering(case, system, sim)
        all_angular[case] = r_angular

        # Task 1.2: EPW damping
        logger.info("--- Task 1.2: EPW density spectrum ---")
        r_epw = analyze_epw_damping(sim, system, case)
        all_epw[case] = r_epw

        # Task 1.3: Hot electrons
        logger.info("--- Task 1.3: Hot electron analysis ---")
        r_he = analyze_hot_electrons(sim, case)
        all_he[case] = r_he

    # ---- Global comparison plots ----
    logger.info("=" * 60)
    logger.info("Generating global comparison plots...")

    plot_angular_comparison(all_angular, out_root)
    plot_epw_comparison(all_epw, out_root)
    plot_hot_electron_comparison(all_he, out_root)

    # ---- Text summary ----
    summary_path = out_root / "analysis_summary.txt"
    with open(summary_path, "w") as f:
        f.write("Scattering Channel Comparison (final time step energy fractions)\n")
        f.write(f"{'Case':<15} {'SBS':<10} {'SRBS':<10} {'SRSS':<10}\n")
        f.write("-" * 45 + "\n")
        for case in CASES:
            r = all_angular[case]
            sbs  = r["SBS"][-1] / r["total_energy"][-1]
            srbs = r["SRBS"][-1] / r["total_energy"][-1]
            srss = r["SRSS"][-1] / r["total_energy"][-1]
            f.write(f"{CASE_LABELS[case]:<15} {sbs:<10.4f} {srbs:<10.4f} {srss:<10.4f}\n")

        f.write("\nEPW Delta-k (FWHM) average\n")
        f.write(f"{'Case':<15} {'<dk>':<10}\n")
        f.write("-" * 25 + "\n")
        for case in CASES:
            dk = np.mean(all_epw[case]["fwhm_k"]) if all_epw[case]["fwhm_k"] else 0
            f.write(f"{CASE_LABELS[case]:<15} {dk:<10.4f}\n")

        f.write("\nHot-electron T_hot (final step, m_e c^2)\n")
        f.write(f"{'Case':<15} {'T_hot':<10}\n")
        f.write("-" * 25 + "\n")
        for case in CASES:
            th = all_he[case]["t_hot"][-1] if all_he[case]["t_hot"] else 0
            f.write(f"{CASE_LABELS[case]:<15} {th:<10.4f}\n")

    logger.info("Saved %s", summary_path)
    logger.info("ALL DONE")


if __name__ == "__main__":
    main()
