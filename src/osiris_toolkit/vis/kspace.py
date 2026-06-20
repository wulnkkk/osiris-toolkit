"""FFT k-space visualisation of OSIRIS field data.

Converted from the MATLAB scripts ``Filter_scattered_wave.m`` and
``plotex.m``.  Computes a 2-D FFT of a field component and plots it in
k-space with unit-aware axes.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osiris_toolkit.compute.fft import compute_k_space as _compute_k_space
from osiris_toolkit.exceptions import DataNotFoundError
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units._quantity import QuantityKind
from osiris_toolkit.units.converter import UnitSystem
from osiris_toolkit.vis._quantified import QuantifiedSpectrum

from .common import get_system, load_sim, save_or_show

logger = logging.getLogger(__name__)


def _auto_k_range(
    k_norm: np.ndarray,
    spectrum: np.ndarray,
    unit: str,
    quantity: QuantityKind,
    threshold_frac: float = 0.01,
    margin: float = 0.1,
) -> tuple[float, float]:
    """Auto-determine k-space plot range from signal extent.

    Parameters
    ----------
    k_norm : ndarray
        1-D array of k values in normalized angular wavenumber.
    spectrum : ndarray
        2-D |FFT| amplitude.
    unit : str
        Target k-space unit.
    quantity : QuantityKind
        Wavenumber quantity for conversion.
    threshold_frac : float
        Fraction of the spectrum maximum used as the cutoff threshold.
    margin : float
        Fraction of the active span to add as padding on each side.

    Returns
    -------
    tuple[float, float]
        (k_min, k_max) in the target unit.
    """
    threshold = spectrum.max() * threshold_frac
    k_conv = quantity.to(k_norm, unit)
    # Determine which spectrum axis corresponds to this k-axis
    if len(k_norm) == spectrum.shape[0]:
        projection = spectrum.max(axis=1)  # project axis 0 → rows → length nx
    elif len(k_norm) == spectrum.shape[1]:
        projection = spectrum.max(axis=0)  # project axis 1 → cols → length ny
    else:
        from osiris_toolkit.exceptions import ShapeError

        raise ShapeError(f"k_norm length {len(k_norm)} does not match spectrum shape {spectrum.shape}")
    mask = projection > threshold
    if not mask.any():
        return (float(k_conv.min()), float(k_conv.max()))
    k_active = k_conv[mask]
    span = float(k_active.max() - k_active.min())
    return (float(k_active.min()) - span * margin, float(k_active.max()) + span * margin)


def plot_k_space(
    quantity: str,
    iteration: int,
    sim_path: str | Path | None = None,
    *,
    sim: Simulation | None = None,
    system: UnitSystem | None = None,
    k_unit: str = "k0",
    time_unit: str = "auto",
    log_scale: bool = True,
    clim: tuple[float, float] | None = None,
    cmap: str = "jet",
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    white_low: float = 0.05,
    output: str | Path | None = None,
) -> Path | None:
    """Plot the 2-D FFT of a field component in k-space.

    Parameters
    ----------
    quantity : str
        Field component name (e.g. ``'e1'``, ``'e3'``).
    iteration : int
        Iteration number to read.
    sim_path : str or Path
        Path to the simulation output directory.
    system : UnitSystem or None
        Unit system for k-space axis conversion.
    k_unit : str
        Target unit for k-space axes (default ``'k0'``).
    time_unit : str
        Unit for the time shown in the title.
    log_scale : bool
        If True, take the natural log of the FFT amplitude.
    clim : (vmin, vmax) or None
        Colour limits for ``imshow``.  If None, auto-scaled.
    cmap : str
        Colormap name.
    xlim, ylim : (float, float) or None
        k-axis ranges.  If None, auto-determined via :func:`_auto_k_range`.
    white_low : float
        Fraction of the colormap low end to fade to white.
    output : Path or None
        File path to save the figure.
    """
    sim_obj = load_sim(sim_path, sim=sim)
    if system is None:
        system = get_system(sim_obj)

    if output is None and sim_obj is not None:
        d = sim_obj.output_dir("k_space")
        output = d / f"{quantity}_{iteration:06d}.png"

    grid = sim_obj.get_field(quantity, iteration)
    if grid is None:
        raise DataNotFoundError(f"Field {quantity!r} not found at iteration {iteration}")

    # Compute FFT
    nx, ny = grid.data.shape
    dx = (grid.axes[0].max - grid.axes[0].min) / nx
    dy = (grid.axes[1].max - grid.axes[1].min) / ny
    kx, ky, spectrum = _compute_k_space(grid.data, dx, dy)

    if log_scale:
        display = np.log(np.maximum(spectrum, 1e-30))
    else:
        display = spectrum

    fig, ax = plt.subplots(figsize=(10, 8))

    base_cmap = plt.get_cmap(cmap)
    n_colors = 256
    n_white = int(white_low * n_colors)
    colors = base_cmap(np.linspace(0, 1, n_colors - n_white))
    white_fade = np.column_stack(
        [
            np.linspace(1, colors[0, 0], n_white),
            np.linspace(1, colors[0, 1], n_white),
            np.linspace(1, colors[0, 2], n_white),
            np.ones(n_white),
        ]
    )
    custom_cmap = plt.cm.colors.ListedColormap(np.vstack([white_fade, colors]))

    if system is not None:
        qspec = QuantifiedSpectrum(
            kx_norm=kx,
            ky_norm=ky,
            spectrum=spectrum,
            quantity=grid.label,
            iteration=grid.iteration,
            time=grid.time,
            system=system,
        )
        extent = [
            qspec.kx.to(k_unit).min(),
            qspec.kx.to(k_unit).max(),
            qspec.ky.to(k_unit).min(),
            qspec.ky.to(k_unit).max(),
        ]
        xlabel = qspec.kx.latex(k_unit)
        ylabel = qspec.ky.latex(k_unit)
    else:
        extent = [
            kx.min() / (2 * np.pi),
            kx.max() / (2 * np.pi),
            ky.min() / (2 * np.pi),
            ky.max() / (2 * np.pi),
        ]
        xlabel = r"$k_x\ [k_0]$"
        ylabel = r"$k_y\ [k_0]$"

    im = ax.imshow(
        display,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap=custom_cmap,
    )

    if clim:
        im.set_clim(*clim)

    cbar = fig.colorbar(im, ax=ax)
    cbar_label = f"{'ln|' if log_scale else '|'}FFT({quantity.upper()})|"
    cbar.set_label(cbar_label)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if system is not None:
        t_disp = system.time.to(grid.time, time_unit)
        ax.set_title(f"{quantity.upper()} k-space  |  iteration={iteration}  |  t={t_disp:.1f}")
    else:
        ax.set_title(f"{quantity.upper()} k-space  |  iteration={iteration}  |  t={grid.time:.1f}")

    if xlim is None and system is not None:
        xlim = _auto_k_range(kx, spectrum, k_unit, system.wavenumber)
    if ylim is None and system is not None:
        ylim = _auto_k_range(ky, spectrum, k_unit, system.wavenumber)
    if xlim is not None:
        ax.set_xlim(*xlim)
    if ylim is not None:
        ax.set_ylim(*ylim)

    fig.tight_layout()
    save_or_show(fig, output)
    return Path(output) if output else None


def batch_k_space(
    quantity: str,
    iterations: list[int],
    sim_path: str | Path,
    system: UnitSystem | None = None,
    output_dir: str | Path = "k_space_output",
    **kwargs,
) -> None:
    """Generate k-space JPEG images for multiple iterations.

    Parameters
    ----------
    quantity : str
        Field component name.
    iterations : list of int
        Iteration numbers to process.
    sim_path : str or Path
        Path to the simulation output directory.
    system : UnitSystem or None
        Unit system for k-space axis conversion.
    output_dir : str or Path
        Directory for output images.
    **kwargs
        Passed through to ``plot_k_space``.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sim = load_sim(sim_path)
    if system is None:
        system = get_system(sim)

    for it in iterations:
        grid = sim.get_field(quantity, it)
        if grid is None:
            logger.info("  skipping %s iteration=%s -- not found", quantity, it)
            continue
        out = output_dir / f"k_{quantity}_{it:06d}.jpg"
        plot_k_space(
            quantity,
            it,
            sim_path=sim_path,
            system=system,
            output=out,
            **kwargs,
        )
        logger.info("  saved %s", out)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.info("Usage: python -m osiris_toolkit.vis.kspace SIM_PATH [ITERATION]")
        sys.exit(1)

    sim_path = sys.argv[1]
    iteration = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    sim = load_sim(sim_path)
    system = get_system(sim)
    iters = sim.list_iterations("e1")
    if iters:
        it = iters[iteration] if iteration < len(iters) else iters[-1]
        plot_k_space(
            "e1",
            it,
            sim_path=sim_path,
            system=system,
            time_unit="ps",
            output="k_space_e1.png",
        )
        logger.info("Done -- see k_space_e1.png")
