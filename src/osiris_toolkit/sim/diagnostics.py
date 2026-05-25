"""Data container dataclasses for OSIRIS diagnostic data."""

from __future__ import annotations

from dataclasses import dataclass, field

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


@dataclass
class GridData:
    """Grid-based diagnostic data (fields, density, current, etc.)."""

    data: np.ndarray
    axes: list[GridAxis] = field(default_factory=list)
    iteration: int = 0
    time: float = 0.0
    label: str = ""
    units: str = ""


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
