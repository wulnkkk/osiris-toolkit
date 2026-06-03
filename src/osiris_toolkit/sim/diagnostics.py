"""Backward-compatible re-exports. New code should import from ``osiris_toolkit._models`` directly.

This module exists only to avoid breaking existing imports of the form
``from osiris_toolkit.sim.diagnostics import Field``.
"""

from osiris_toolkit._models import (  # noqa: F401 — re-export
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
    _eval_particle_expr,
)

__all__ = [
    "Field",
    "FieldInfo",
    "GridAxis",
    "GridData",
    "HistoryData",
    "ParticleData",
    "ParticleInfo",
    "PhasespaceData",
    "TimingsData",
    "TrackData",
    "TrackInfo",
]
