"""Lightweight dataclasses for ZDF metadata.

These are pure data containers with no dependency on other osiris_toolkit
modules. They represent the metadata structure defined by the ZDF format
specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ZdfRecord:
    """Header of a single ZDF record within a file."""

    pos: int  # byte offset of the record
    id: int  # id_version field (type + version)
    name: str  # record name
    length: int  # data length in bytes


@dataclass
class ZdfIteration:
    """Iteration metadata record."""

    n: int  # iteration number
    t: float  # simulation time
    tunits: str  # time units


@dataclass
class ZdfAxis:
    """Single grid axis descriptor."""

    name: str = ""
    axis_type: int = 0
    min: float = 0.0
    max: float = 0.0
    label: str = ""
    units: str = ""


@dataclass
class ZdfGridInfo:
    """Grid metadata record."""

    ndims: int = 0
    nx: list[int] = field(default_factory=list)
    label: str = ""
    units: str = ""
    has_axis: bool = False
    axes: list[ZdfAxis] = field(default_factory=list)


@dataclass
class ZdfPartInfo:
    """Particle metadata record."""

    name: str = ""
    label: str = ""
    nparts: int = 0
    nquants: int = 0
    quants: list[str] = field(default_factory=list)
    qlabels: dict[str, str] = field(default_factory=dict)
    qunits: dict[str, str] = field(default_factory=dict)


@dataclass
class ZdfTrackInfo:
    """Track metadata record."""

    name: str = ""
    label: str = ""
    ntracks: int = 0
    ndump: int = 0
    niter: int = 0
    nquants: int = 0
    quants: list[str] = field(default_factory=list)
    qlabels: list[str] = field(default_factory=list)
    qunits: list[str] = field(default_factory=list)


@dataclass
class ZdfFileInfo:
    """Complete metadata for a ZDF or HDF5 file."""

    file_type: str = ""  # "grid", "particles", "tracks-2"
    grid: ZdfGridInfo | None = None
    particles: ZdfPartInfo | None = None
    tracks: ZdfTrackInfo | None = None
    iteration: ZdfIteration | None = None
    simulation_info: str | None = None  # HDF5-only: git version, compile time, input file
