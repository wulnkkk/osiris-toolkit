"""Simulation data access layer — directory discovery and typed diagnostic containers."""

from osiris_toolkit.sim.catalog import OSIRIS_DIAGNOSTICS, DiagKind
from osiris_toolkit.sim.diagnostics import (
    Field,
    FieldInfo,
    GridAxis,
    GridData,
    HistoryData,
    ParticleData,
    ParticleInfo,
    PhasespaceData,
    TimingsData,
    TrackData,
    TrackInfo,
)
from osiris_toolkit.sim.simulation import Simulation

__all__ = [
    "Simulation",
    "Field",
    "FieldInfo",
    "GridData",
    "GridAxis",
    "ParticleData",
    "ParticleInfo",
    "PhasespaceData",
    "TimingsData",
    "TrackData",
    "TrackInfo",
    "HistoryData",
    "OSIRIS_DIAGNOSTICS",
    "DiagKind",
]
