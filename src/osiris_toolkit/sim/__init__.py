"""Simulation data access layer — directory discovery and typed diagnostic containers."""

from osiris_toolkit.sim.catalog import OSIRIS_DIAGNOSTICS, DiagKind
from osiris_toolkit.sim.diagnostics import (
    GridAxis,
    GridData,
    HistoryData,
    ParticleData,
    PhasespaceData,
    TrackData,
)
from osiris_toolkit.sim.simulation import Simulation

__all__ = [
    "Simulation",
    "GridData",
    "GridAxis",
    "ParticleData",
    "PhasespaceData",
    "TrackData",
    "HistoryData",
    "OSIRIS_DIAGNOSTICS",
    "DiagKind",
]
