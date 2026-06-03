"""Particle-to-grid deposition with multiple shape functions.

Provides :func:`particles_to_grid` for mapping discrete particle
quantities onto a regular grid mesh using NGP, CIC (tophat),
quadratic (triangular), or cubic (spline3) shape functions.
"""

from __future__ import annotations

import numpy as np

from osiris_toolkit._models import Field, GridAxis
from osiris_toolkit.exceptions import ValidationError

_HAS_NUMBA = False
try:
    from numba import njit as _njit
    _HAS_NUMBA = True
except ImportError:
    def _njit(*args, **kwargs):
        return lambda f: f

_SHAPE_FUNCTIONS = {"ngp", "tophat", "triangular", "spline3"}


def particles_to_grid(
    positions: np.ndarray,
    weights: np.ndarray | None = None,
    grid_shape: tuple[int, ...] = (),
    axes: list[GridAxis] | None = None,
    shape_function: str = "ngp",
    use_numba: bool = False,
) -> Field:
    """Deposit particle quantities onto a regular grid.

    Parameters
    ----------
    positions : ndarray of shape (nparts, ndim)
        Particle positions in grid-index space (0 to nx-1).
    weights : ndarray of shape (nparts,) or None
        Per-particle weights.  If None, all weights are 1.0.
    grid_shape : tuple of int
        Grid dimensions ``(nx,)`` or ``(nx, ny)``.
    axes : list of GridAxis or None
        Optional axis descriptors for the output Field.
    shape_function : str
        One of ``"ngp"``, ``"tophat"``, ``"triangular"``, ``"spline3"``.
        Default is ``"ngp"``.
    use_numba : bool
        If True and numba is available, use JIT-compiled kernels.

    Returns
    -------
    Field
        Deposited grid data.
    """
    if shape_function not in _SHAPE_FUNCTIONS:
        raise ValidationError(
            f"Unknown shape function {shape_function!r}. "
            f"Choose from: {sorted(_SHAPE_FUNCTIONS)}"
        )
    if positions.size == 0:
        return Field(
            data=np.zeros(grid_shape, dtype=np.float64),
            axes=list(axes) if axes else [],
        )

    positions = np.asarray(positions, dtype=np.float64)
    nparts, ndim = positions.shape

    if weights is None:
        weights_arr = np.ones(nparts, dtype=np.float64)
    else:
        weights_arr = np.asarray(weights, dtype=np.float64)

    if len(grid_shape) != ndim:
        raise ValidationError(
            f"grid_shape has {len(grid_shape)} dims but positions "
            f"have {ndim} dims; they must match"
        )

    grid = np.zeros(grid_shape, dtype=np.float64)

    if shape_function == "ngp":
        _deposit_ngp(positions, weights_arr, grid)
    elif shape_function == "tophat":
        _deposit_tophat(positions, weights_arr, grid)
    elif shape_function == "triangular":
        _deposit_triangular(positions, weights_arr, grid)
    elif shape_function == "spline3":
        _deposit_spline3(positions, weights_arr, grid)

    return Field(data=grid, axes=list(axes) if axes else [])


def _add_at(grid: np.ndarray, idx: tuple, value: float) -> None:
    grid[idx] += value


def _deposit_ngp(positions, weights, grid):
    """Nearest Grid Point deposition."""
    nparts = positions.shape[0]
    ndim = positions.shape[1]
    for p in range(nparts):
        idx = []
        in_bounds = True
        for d in range(ndim):
            i = int(np.round(positions[p, d]))
            if i < 0 or i >= grid.shape[d]:
                in_bounds = False
                break
            idx.append(i)
        if in_bounds:
            _add_at(grid, tuple(idx), weights[p])


def _deposit_tophat(positions, weights, grid):
    """Cloud-In-Cell (linear) deposition — 2 cells per dimension."""
    nparts = positions.shape[0]
    ndim = positions.shape[1]
    for p in range(nparts):
        offsets = [[]]
        weight_factors = [[]]
        for d in range(ndim):
            x = positions[p, d]
            i0 = int(np.floor(x))
            new_offsets = []
            new_factors = []
            for prev_off, prev_w in zip(offsets, weight_factors):
                for cell_idx in (i0, i0 + 1):
                    w_cell = 1.0 - abs(cell_idx - x)
                    new_offsets.append(prev_off + [cell_idx])
                    new_factors.append(prev_w + [w_cell])
            offsets = new_offsets
            weight_factors = new_factors
        for off_list, w_list in zip(offsets, weight_factors):
            in_bounds = all(0 <= o < grid.shape[d] for d, o in enumerate(off_list))
            if in_bounds:
                w_total = np.prod(w_list)
                _add_at(grid, tuple(off_list), w_total * weights[p])


def _deposit_triangular(positions, weights, grid):
    """Quadratic spline deposition — 3 cells per dimension."""
    nparts = positions.shape[0]
    ndim = positions.shape[1]
    for p in range(nparts):
        offsets = [[]]
        weight_factors = [[]]
        for d in range(ndim):
            x = positions[p, d]
            i0 = int(np.floor(x)) - 1
            new_offsets = []
            new_factors = []
            for prev_off, prev_w in zip(offsets, weight_factors):
                for k in range(3):
                    cell_idx = i0 + k
                    dx = abs(cell_idx - x)
                    if dx <= 1.0:
                        w_cell = 0.75 - dx * dx
                    elif dx <= 1.5:
                        w_cell = 0.5 * (1.5 - dx) ** 2
                    else:
                        w_cell = 0.0
                    new_offsets.append(prev_off + [cell_idx])
                    new_factors.append(prev_w + [w_cell])
            offsets = new_offsets
            weight_factors = new_factors
        for off_list, w_list in zip(offsets, weight_factors):
            in_bounds = all(0 <= o < grid.shape[d] for d, o in enumerate(off_list))
            if in_bounds:
                w_total = np.prod(w_list)
                _add_at(grid, tuple(off_list), w_total * weights[p])


def _deposit_spline3(positions, weights, grid):
    """Cubic spline deposition — 4 cells per dimension (M4 kernel)."""
    nparts = positions.shape[0]
    ndim = positions.shape[1]
    for p in range(nparts):
        offsets = [[]]
        weight_factors = [[]]
        for d in range(ndim):
            x = positions[p, d]
            i0 = int(np.floor(x)) - 1
            new_offsets = []
            new_factors = []
            for prev_off, prev_w in zip(offsets, weight_factors):
                for k in range(4):
                    cell_idx = i0 + k
                    dx = abs(cell_idx - x)
                    if dx <= 1.0:
                        w_cell = (2.0 / 3.0) - dx * dx + 0.5 * dx ** 3
                    elif dx <= 2.0:
                        w_cell = (1.0 / 6.0) * (2.0 - dx) ** 3
                    else:
                        w_cell = 0.0
                    new_offsets.append(prev_off + [cell_idx])
                    new_factors.append(prev_w + [w_cell])
            offsets = new_offsets
            weight_factors = new_factors
        for off_list, w_list in zip(offsets, weight_factors):
            in_bounds = all(0 <= o < grid.shape[d] for d, o in enumerate(off_list))
            if in_bounds:
                w_total = np.prod(w_list)
                _add_at(grid, tuple(off_list), w_total * weights[p])
