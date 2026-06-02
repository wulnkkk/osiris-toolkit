"""Time-evolution animation — generate GIF/MP4 from field frames."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import numpy as np

from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis.field import plot_field


def animate_field(
    quantity: str,
    sim: Simulation,
    output: Path,
    iterations: list[int] | None = None,
    fps: int = 10,
    cmap: str = "RdBu_r",
    dpi: int = 100,
    overwrite: bool = False,
) -> Path:
    """Generate an animated GIF or MP4 from field frames over time.

    Parameters
    ----------
    quantity : str
        Field quantity name.
    sim : Simulation
    output : Path
        Output file path (.gif or .mp4).
    iterations : list[int] or None
        Which iterations to include. None = all available.
    fps : int
        Frames per second.
    cmap : str
        Matplotlib colormap.
    dpi : int
        Output resolution.
    overwrite : bool
        If False, raise when output exists.

    Returns
    -------
    Path
        The generated file path.

    Notes
    -----
    Requires imageio: pip install imageio.
    """
    output = Path(output)
    if output.exists() and not overwrite:
        raise FileExistsError(f"{output} exists; use overwrite=True")

    try:
        import imageio
    except ImportError:
        raise ImportError(
            "imageio is required for animation. Install with: pip install imageio"
        )

    if iterations is None:
        iterations = sim.list_iterations(quantity)

    # Compute global vmin/vmax for consistent color scale
    vmin = float("inf")
    vmax = float("-inf")
    frames_data = []
    for it in iterations:
        grid = sim.get_field(quantity, it)
        if grid is None:
            continue
        d = grid.data
        vmin = min(vmin, np.min(d))
        vmax = max(vmax, np.max(d))
        frames_data.append((it, d))

    # Generate frames
    tmpdir = tempfile.mkdtemp(prefix="anim_")
    frame_paths = []
    try:
        for i, (it, _) in enumerate(frames_data):
            fpath = Path(tmpdir) / f"frame_{i:06d}.png"
            plot_field(
                quantity=quantity,
                iteration=it,
                sim=sim,
                output=fpath,
                cmap=cmap,
                overwrite=True,
            )
            frame_paths.append(fpath)

        # Read frames and write animation
        writer = imageio.get_writer(output, fps=fps)
        for fp in frame_paths:
            writer.append_data(imageio.imread(fp))
        writer.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return output


__all__ = ["animate_field"]
