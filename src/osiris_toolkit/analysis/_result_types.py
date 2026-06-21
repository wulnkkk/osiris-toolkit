"""Analysis result dataclasses — strongly-typed return values for all analyzers."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from osiris_toolkit._models import GridData


@dataclass
class FieldEnergyResult:
    """Single field-component energy at one iteration."""

    quantity: str
    iteration: int
    time: float
    total_energy: float
    grid: GridData | None = None


@dataclass
class EMDynamicsResult:
    """Total electromagnetic energy decomposition at one iteration."""

    iteration: int
    time: float
    e2_total: float
    b2_total: float
    total: float


@dataclass
class EMSpectrumResult:
    """2-D FFT spectrum of a field component at one iteration."""

    quantity: str
    iteration: int
    time: float
    kx_k0: np.ndarray
    ky_k0: np.ndarray
    spectrum: np.ndarray


@dataclass
class PoyntingResult:
    """Poynting vector S = E x B at one iteration."""

    iteration: int
    time: float
    s1: np.ndarray
    s2: np.ndarray
    s3: np.ndarray


@dataclass
class ScatteringResult:
    """K-space scattering energy fractions over time."""

    quantity: str
    iterations: list[int] = field(default_factory=list)
    times: list[float] = field(default_factory=list)
    scattered_fraction: list[float] = field(default_factory=list)
    side_scatter_fraction: list[float] = field(default_factory=list)
    back_scatter_fraction: list[float] = field(default_factory=list)
    mask_info: dict = field(default_factory=dict)


@dataclass
class DensityProfileResult:
    """Line-integrated density profile along one axis."""

    species: str
    quantity: str
    iteration: int
    time: float
    axis: int
    coord: np.ndarray
    profile: np.ndarray


@dataclass
class DensityIntegralResult:
    """Integrated density quantity (e.g. total charge)."""

    species: str
    quantity: str
    iteration: int
    time: float
    total: float


@dataclass
class ParticleSpectrumResult:
    """Energy histogram from raw particle data."""

    species: str
    iteration: int
    time: float
    bin_centers: np.ndarray
    counts: np.ndarray


@dataclass
class TemperatureResult:
    """Temperature tensor diagonal components."""

    species: str
    iteration: int
    time: float
    components: dict[str, float] = field(default_factory=dict)


@dataclass
class MomentumStatsResult:
    """Per-axis momentum statistics from raw particle data."""

    species: str
    iteration: int
    time: float
    p1_mean: float
    p1_std: float
    p2_mean: float
    p2_std: float
    p3_mean: float
    p3_std: float
    anisotropy: float  # p1_std / p2_std for transverse directions
    nparts: int


@dataclass
class HistoryResult:
    """Single-column timeseries extracted from a HISTORY file."""

    name: str
    column: str
    time: np.ndarray
    values: np.ndarray
