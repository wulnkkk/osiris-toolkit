"""FFT k-space visualisation of OSIRIS field data.

Converted from the MATLAB scripts ``Filter_scattered_wave.m`` and
``plotex.m``.  Computes a 2-D FFT of a field component and plots it in
dimensionless k/k0 space (no unit conversion needed for the axes).
"""

import logging
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osiris_toolkit.compute.fft import compute_k_space as _compute_k_space
from osiris_toolkit.sim import GridData, Simulation
from osiris_toolkit.units import UnitConverter

from .common import get_converter, load_sim, save_or_show

logger = logging.getLogger(__name__)


def compute_k_space(
    grid: GridData, omega0_norm: float = 1.0
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the 2-D FFT k-space spectrum from a grid dataset.

    .. deprecated::
        Use ``osiris_toolkit.compute.fft.compute_k_space`` instead.
        The new function accepts raw ``(data, dx, dy)`` arrays rather than
        a ``GridData`` object.

    Parameters
    ----------
    grid : GridData
        Field or density grid data.
    omega0_norm : float
        Laser frequency in normalised units (default 1.0).

    Returns
    -------
    kx_k0 : 1-D array
        kx/k0 values, fftshifted.
    ky_k0 : 1-D array
        ky/k0 values, fftshifted.
    spectrum : 2-D array
        |FFT| amplitude, fftshifted.
    """
    warnings.warn(
        "vis.kspace.compute_k_space is deprecated. "
        "Use osiris_toolkit.compute.fft.compute_k_space instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    data = grid.data
    if data.ndim != 2:
        raise ValueError(f"Expected 2-D data, got shape {data.shape}")
    nx, ny = data.shape
    dx = (grid.axes[0].max - grid.axes[0].min) / nx
    dy = (grid.axes[1].max - grid.axes[1].min) / ny
    return _compute_k_space(data, dx, dy, omega0_norm)


def plot_k_space(
    quantity: str,
    iteration: int,
    sim_path: str | Path | None = None,
    *,
    sim: Simulation | None = None,
    converter: UnitConverter | None = None,
    time_unit: str = "auto",
    log_scale: bool = True,
    clim: tuple[float, float] | None = None,
    cmap: str = "jet",
    omega0_norm: float = 1.0,
    xlim: tuple[float, float] = (-2.0, 2.0),
    ylim: tuple[float, float] = (-2.0, 2.0),
    white_low: float = 0.05,
    output: str | Path | None = None,
) -> Path | None:
    """Plot the 2-D FFT of a field component in k/k0 space.

    Parameters
    ----------
    quantity : str
        Field component name (e.g. ``'e1'``, ``'e3'``).
    iteration : int
        Iteration number to read.
    sim_path : str or Path
        Path to the simulation output directory.
    converter : UnitConverter or None
        Used only for the time display in the title (k-space axes are
        dimensionless).
    time_unit : str
        Unit for the time shown in the title.
    log_scale : bool
        If True, take the natural log of the FFT amplitude.
    clim : (vmin, vmax) or None
        Colour limits for ``imshow``.  If None, auto-scaled.
    cmap : str
        Colormap name.
    omega0_norm : float
        Laser frequency in normalised units.
    xlim, ylim : (float, float)
        k/k0 axis ranges.
    white_low : float
        Fraction of the colormap low end to fade to white.
    output : Path or None
        File path to save the figure.
    """
    sim_obj = load_sim(sim_path, sim=sim)
    if converter is None:
        converter = get_converter(sim_obj)

    if output is None and sim_obj is not None:
        d = sim_obj.output_dir("k_space")
        output = d / f"{quantity}_{iteration:06d}.png"

    grid = sim_obj.get_field(quantity, iteration)
    if grid is None:
        raise ValueError(
            f"Field {quantity!r} not found at iteration {iteration}"
        )

    nx, ny = grid.data.shape
    dx = (grid.axes[0].max - grid.axes[0].min) / nx
    dy = (grid.axes[1].max - grid.axes[1].min) / ny
    kx_k0, ky_k0, spectrum = _compute_k_space(grid.data, dx, dy, omega0_norm)

    if log_scale:
        spectrum = np.log(np.maximum(spectrum, 1e-30))

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
    custom_cmap = plt.cm.colors.ListedColormap(
        np.vstack([white_fade, colors])
    )

    im = ax.imshow(
        spectrum,
        origin="lower",
        aspect="auto",
        extent=[
            kx_k0.min() / (2 * np.pi),
            kx_k0.max() / (2 * np.pi),
            ky_k0.min() / (2 * np.pi),
            ky_k0.max() / (2 * np.pi),
        ],
        cmap=custom_cmap,
    )

    if clim:
        im.set_clim(*clim)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("ln|FFT(E)|" if log_scale else "|FFT(E)|")

    ax.set_xlabel(r"$k_x\ [k_0]$", fontsize=14)
    ax.set_ylabel(r"$k_y\ [k_0]$", fontsize=14)

    if converter is not None:
        t_disp = converter.convert(grid.time, "time", time_unit)
        ax.set_title(
            f"{quantity.upper()} k-space  |  iteration={iteration}"
            f"  |  t={t_disp:.1f}"
        )
    else:
        ax.set_title(
            f"{quantity.upper()} k-space  |  iteration={iteration}"
            f"  |  t={grid.time:.1f}"
        )

    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)

    fig.tight_layout()
    save_or_show(fig, output)
    return Path(output) if output else None


def batch_k_space(
    quantity: str,
    iterations: list[int],
    sim_path: str | Path,
    converter: UnitConverter | None = None,
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
    converter : UnitConverter or None
        Unit converter (only used for time display).
    output_dir : str or Path
        Directory for output images.
    **kwargs
        Passed through to ``plot_k_space``.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sim = load_sim(sim_path)
    if converter is None:
        converter = get_converter(sim)

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
            converter=converter,
            output=out,
            **kwargs,
        )
        logger.info("  saved %s", out)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.info(
            "Usage: python -m osiris_toolkit.vis.kspace SIM_PATH [ITERATION]"
        )
        sys.exit(1)

    sim_path = sys.argv[1]
    iteration = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    sim = load_sim(sim_path)
    converter = get_converter(sim)
    iters = sim.list_iterations("e1")
    if iters:
        it = iters[iteration] if iteration < len(iters) else iters[-1]
        plot_k_space(
            "e1", it, sim_path=sim_path, converter=converter,
            time_unit="ps", output="k_space_e1.png",
        )
        logger.info("Done -- see k_space_e1.png")
