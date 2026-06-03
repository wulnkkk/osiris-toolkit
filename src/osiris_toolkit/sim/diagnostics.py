"""Data container dataclasses for OSIRIS diagnostic data."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class GridAxis:
    """Descriptor for a single grid axis."""

    name: str = ""
    type: int = 0
    min: float = 0.0
    max: float = 0.0
    label: str = ""
    units: str = ""
    npoints: int = 0

    def value_to_index(self, value: float) -> float:
        """Convert a physical coordinate to a fractional grid index.

        Parameters
        ----------
        value : float
            Physical coordinate along this axis.

        Returns
        -------
        float
            Fractional grid index (0 to npoints-1).
        """
        if self.npoints <= 0:
            raise ValueError(
                f"GridAxis.npoints not set for axis {self.name!r}; "
                "cannot convert coordinates"
            )
        span = self.max - self.min
        if span == 0:
            return 0.0
        return (value - self.min) / span * (self.npoints - 1)

    def index_to_value(self, idx: float) -> float:
        """Convert a grid index to a physical coordinate.

        Parameters
        ----------
        idx : float
            Grid index (fractional or integer).

        Returns
        -------
        float
            Physical coordinate.
        """
        if self.npoints <= 0:
            raise ValueError(
                f"GridAxis.npoints not set for axis {self.name!r}; "
                "cannot convert coordinates"
            )
        if self.npoints == 1:
            return self.min
        return self.min + (idx / (self.npoints - 1)) * (self.max - self.min)


@dataclass
class Field:
    """Grid-based diagnostic data with operator overloading and physical slicing.

    This replaces ``GridData`` (kept as an alias for backward compatibility).
    Supports element-wise arithmetic operators (+, -, *, /, **) and
    physical-coordinate slicing via ``__getitem__``.
    """

    data: np.ndarray
    axes: list[GridAxis] = field(default_factory=list)
    iteration: int = 0
    time: float = 0.0
    label: str = ""
    units: str = ""

    # --- Operator overloading (element-wise on .data) ---

    def _copy_meta(self, data: np.ndarray) -> Field:
        """Return a new Field with the same metadata but different data."""
        return Field(
            data=data,
            axes=copy.deepcopy(self.axes),
            iteration=self.iteration,
            time=self.time,
            label=self.label,
            units=self.units,
        )

    def __add__(self, other: Field | float | np.ndarray) -> Field:
        if isinstance(other, Field):
            if self.data.shape != other.data.shape:
                raise ValueError(
                    f"Shape mismatch: {self.data.shape} vs {other.data.shape}"
                )
            return self._copy_meta(self.data + other.data)
        return self._copy_meta(self.data + other)

    def __radd__(self, other: float | np.ndarray) -> Field:
        return self._copy_meta(other + self.data)

    def __sub__(self, other: Field | float | np.ndarray) -> Field:
        if isinstance(other, Field):
            if self.data.shape != other.data.shape:
                raise ValueError(
                    f"Shape mismatch: {self.data.shape} vs {other.data.shape}"
                )
            return self._copy_meta(self.data - other.data)
        return self._copy_meta(self.data - other)

    def __rsub__(self, other: float | np.ndarray) -> Field:
        return self._copy_meta(other - self.data)

    def __mul__(self, other: Field | float | np.ndarray) -> Field:
        if isinstance(other, Field):
            if self.data.shape != other.data.shape:
                raise ValueError(
                    f"Shape mismatch: {self.data.shape} vs {other.data.shape}"
                )
            return self._copy_meta(self.data * other.data)
        return self._copy_meta(self.data * other)

    def __rmul__(self, other: float | np.ndarray) -> Field:
        return self._copy_meta(other * self.data)

    def __truediv__(self, other: Field | float | np.ndarray) -> Field:
        if isinstance(other, Field):
            if self.data.shape != other.data.shape:
                raise ValueError(
                    f"Shape mismatch: {self.data.shape} vs {other.data.shape}"
                )
            return self._copy_meta(self.data / other.data)
        return self._copy_meta(self.data / other)

    def __rtruediv__(self, other: float | np.ndarray) -> Field:
        return self._copy_meta(other / self.data)

    def __pow__(self, exponent: float) -> Field:
        return self._copy_meta(self.data ** exponent)

    def __neg__(self) -> Field:
        return self._copy_meta(-self.data)

    def __abs__(self) -> Field:
        return self._copy_meta(np.abs(self.data))

    # --- Physical slicing ---

    def __getitem__(self, key: Any) -> "Field | float":
        """Slice by array indices, with optional bilinear interpolation.

        Integer indices use nearest-grid-point. Float indices trigger
        bilinear interpolation. Supports mixed int/float/slice keys.

        Examples
        --------
        >>> field[0:10, 0:5]       # integer slice (existing behavior)
        >>> field[2000.5, 1800.3]  # bilinear interpolation at float coords
        >>> field[:, 1800.5]       # mixed: slice x1, interpolate at x2=1800.5
        """
        if not isinstance(key, tuple):
            key = (key,)

        # Detect float indices → use bilinear interpolation
        has_float = any(isinstance(k, float) for k in key)
        if has_float:
            return self._interpolate(key)

        sliced_data = self.data[key]

        new_axes: list[GridAxis] = []
        # Track which dimension of sliced_data corresponds to which original axis
        sliced_dim = 0
        for i, k in enumerate(key):
            if i >= len(self.axes):
                break
            if isinstance(k, slice):
                # This axis is preserved in sliced_data
                ax = self.axes[i]
                # Clamp slice bounds to valid axis range
                npoints_ax = ax.npoints if ax.npoints > 0 else self.data.shape[i]
                start = k.start if k.start is not None else 0
                stop_val = k.stop if k.stop is not None else npoints_ax
                # Clamp to valid range
                start = max(0, min(start, npoints_ax))
                stop_val = max(0, min(stop_val, npoints_ax))

                new_npoints = sliced_data.shape[sliced_dim] if sliced_dim < sliced_data.ndim else 0

                if new_npoints > 0 and ax.npoints > 0:
                    new_min = ax.index_to_value(float(start))
                    end_idx = float(max(start, stop_val - 1))
                    new_max = ax.index_to_value(end_idx)
                else:
                    new_min = float(start) if ax.npoints <= 0 else ax.min
                    new_max = float(stop_val) if ax.npoints <= 0 else ax.max

                new_axes.append(GridAxis(
                    name=ax.name, type=ax.type,
                    min=new_min, max=new_max,
                    label=ax.label, units=ax.units,
                    npoints=new_npoints,
                ))
                sliced_dim += 1
            # scalar index: axis is removed (skip)

        return Field(
            data=sliced_data,
            axes=new_axes,
            iteration=self.iteration,
            time=self.time,
            label=self.label,
            units=self.units,
        )

    def _interpolate(self, key: tuple) -> "Field | float":
        """Bilinear interpolation at float coordinates along requested axes.

        Parameters
        ----------
        key : tuple
            Index tuple possibly containing float values for interpolation.

        Returns
        -------
        Field or float
            If all axes are scalar (int or float), returns a single float.
            Otherwise returns a Field with the interpolated data.
        """
        result = self.data.astype(np.float64)
        scalar_out = True
        current_dim = 0  # axis index within *result*, which shrinks as axes collapse

        for axis_idx, k in enumerate(key):
            if isinstance(k, slice):
                scalar_out = False
                current_dim += 1
                continue
            n = self.data.shape[axis_idx]
            if isinstance(k, (int, np.integer)):
                # Integer index: extract that slice, axis collapses
                result = result.take(k, axis=current_dim)
                # current_dim stays — subsequent axes shift left
                continue
            # Float index: bilinear interpolation along this axis
            k = max(0.0, min(float(k), n - 1))
            i0 = int(np.floor(k))
            i1 = min(i0 + 1, n - 1)
            w1 = k - i0
            w0 = 1.0 - w1

            sl0 = [slice(None)] * result.ndim
            sl1 = [slice(None)] * result.ndim
            sl0[current_dim] = i0
            sl1[current_dim] = i1
            result = w0 * result[tuple(sl0)] + w1 * result[tuple(sl1)]
            # current_dim stays — float interp also collapses the axis

        if scalar_out:
            return float(result)
        # Build Field with remaining axes
        kept_axes = []
        kept_dim = 0
        for i, k in enumerate(key):
            if i >= len(self.axes):
                break
            if isinstance(k, (slice, float)):
                if kept_dim < result.ndim:
                    ax = self.axes[i]
                    npoints = result.shape[kept_dim]
                    kept_axes.append(GridAxis(
                        name=ax.name, type=ax.type,
                        min=ax.min, max=ax.max,
                        label=ax.label, units=ax.units,
                        npoints=npoints,
                    ))
                    kept_dim += 1

        return Field(
            data=result.astype(self.data.dtype),
            axes=kept_axes,
            iteration=self.iteration, time=self.time,
            label=self.label, units=self.units,
        )

    # --- Properties ---

    @property
    def ndim(self) -> int:
        """Number of dimensions of the data array."""
        return self.data.ndim

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the data array."""
        return self.data.shape

    # --- Convenience ---

    def mean(self, **kwargs: Any) -> float | np.ndarray:
        """Mean of the data array."""
        result = self.data.mean(**kwargs)
        return float(result) if result.ndim == 0 else result

    def std(self, **kwargs: Any) -> float | np.ndarray:
        """Standard deviation of the data array."""
        result = self.data.std(**kwargs)
        return float(result) if result.ndim == 0 else result


# Backward compatibility alias
GridData = Field


@dataclass
class ParticleData:
    """Per-particle diagnostic data (raw particle dumps)."""

    data: dict[str, np.ndarray] = field(default_factory=dict)
    nparts: int = 0
    iteration: int = 0
    time: float = 0.0
    label: str = ""

    def filter(self, expr: str) -> "ParticleData":
        """Return a new ParticleData with particles matching *expr*.

        Parameters
        ----------
        expr : str
            A filter expression using keys from ``self.data``,
            e.g. ``'p1 > 0 and ene < 10'``.

        Returns
        -------
        ParticleData
            A filtered view.  Arrays share memory with the original.
            Call ``.compress()`` to get a memory-independent copy.
        """
        mask = _eval_particle_expr(expr, self.data)
        new_nparts = int(mask.sum())
        new_data = {}
        for k, v in self.data.items():
            new_data[k] = v[mask]
        return ParticleData(
            data=new_data,
            nparts=new_nparts,
            iteration=self.iteration,
            time=self.time,
            label=self.label,
        )

    def compress(self) -> "ParticleData":
        """Return a copy with contiguous arrays (independent of source).

        Returns
        -------
        ParticleData
        """
        new_data = {}
        for k, v in self.data.items():
            new_data[k] = np.ascontiguousarray(v) if not v.flags["C_CONTIGUOUS"] else v.copy()
        return ParticleData(
            data=new_data,
            nparts=self.nparts,
            iteration=self.iteration,
            time=self.time,
            label=self.label,
        )

    def __len__(self) -> int:
        return self.nparts


@dataclass
class PhasespaceData:
    """Phasespace diagnostic data."""

    data: np.ndarray
    axes: list[dict[str, str]] = field(default_factory=list)
    iteration: int = 0
    time: float = 0.0
    deposited_quantity: str = ""


@dataclass
class TrackData:
    """Particle track diagnostic data."""

    tracks: list[np.ndarray] = field(default_factory=list)
    quants: list[str] = field(default_factory=list)
    niter: int = 0


@dataclass
class HistoryData:
    """Time-series history data from text files."""

    columns: list[str] = field(default_factory=list)
    data: dict[str, np.ndarray] = field(default_factory=dict)


@dataclass
class TimingsData:
    """Timing profile data from TIMINGS/ text files.

    Events are the profiling event names (e.g. push_particles, solve_emf).
    Columns are the metric names (e.g. 'Total [s]' for serial,
    'Avg [s]', 'Min [s]', 'Max [s]' for parallel).
    Data maps metric name to array of per-event values.
    """

    events: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    data: dict[str, np.ndarray] = field(default_factory=dict)


@dataclass
class FieldInfo:
    """Lightweight field metadata — no data array loaded.

    Read via :meth:`Simulation.info_field`.
    """

    quantity: str = ""
    iteration: int = 0
    time: float = 0.0
    label: str = ""
    units: str = ""
    ndim: int = 0
    shape: tuple[int, ...] = ()
    axes: list[GridAxis] = field(default_factory=list)
    report_type: str = ""


@dataclass
class ParticleInfo:
    """Lightweight particle metadata — no data arrays loaded.

    Read via :meth:`Simulation.info_raw`.
    """

    species: str = ""
    iteration: int = 0
    time: float = 0.0
    label: str = ""
    nparts: int = 0
    quants: list[str] = field(default_factory=list)


@dataclass
class TrackInfo:
    """Lightweight track metadata — no data arrays loaded.

    Read via :meth:`Simulation.info_tracks`.
    """

    name: str = ""
    label: str = ""
    ntracks: int = 0
    ndump: int = 0
    niter: int = 0
    quants: list[str] = field(default_factory=list)


def _eval_particle_expr(expr: str, data: dict[str, np.ndarray]) -> np.ndarray:
    """Evaluate a filter expression against particle data.

    Tries numexpr first; falls back to eval with restricted namespace.
    Returns a boolean mask array.

    Parameters
    ----------
    expr : str
        Filter expression, e.g. ``'p1 > 0 and ene < 10'``.
    data : dict
        Particle data dict with array values.

    Returns
    -------
    np.ndarray
        Boolean mask array.

    Raises
    ------
    ValueError
        If the expression cannot be evaluated.
    """
    try:
        import numexpr

        mask = numexpr.evaluate(expr, local_dict=data)
        return np.asarray(mask, dtype=bool)
    except ImportError:
        pass
    except Exception as e:
        raise ValueError(
            f"Failed to evaluate filter expression {expr!r}: {e}"
        ) from e

    # Fallback: use Python eval with restricted namespace
    try:
        safe_locals = {k: v for k, v in data.items()}
        mask = eval(expr, {"__builtins__": {}}, safe_locals)
        return np.asarray(mask, dtype=bool)
    except Exception as e:
        raise ValueError(
            f"Failed to evaluate filter expression {expr!r}: {e}"
        ) from e
