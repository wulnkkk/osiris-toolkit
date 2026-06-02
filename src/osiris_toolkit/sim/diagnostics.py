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

    def __getitem__(self, key: Any) -> Field:
        """Slice by array indices. Returns a new Field with sliced data and axes.

        Supports standard numpy slicing: ``field[0:10, 0:5]``.
        Named-axis slicing is planned for a future release.
        """
        sliced_data = self.data[key]

        if not isinstance(key, tuple):
            key = (key,)

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
