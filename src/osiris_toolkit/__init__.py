"""osiris-toolkit: Comprehensive toolkit for OSIRIS PIC simulation."""

__version__ = "0.9.0"

from osiris_toolkit.analysis.tracks import TracksAnalyzer
from osiris_toolkit.compute import (
    compute_k_space,
    line_integrate,
    mask_energy,
    particles_to_grid,
    spectral_power,
    trapz_2d,
)
from osiris_toolkit.io import (
    list_records,
    read_grid,
    read_info,
    read_particles,
    read_tracks,
)
from osiris_toolkit.postproc import PostProcessor
from osiris_toolkit.sim import (
    OSIRIS_DIAGNOSTICS,
    DiagKind,
    Field,
    FieldInfo,
    GridAxis,
    GridData,
    HistoryData,
    ParticleData,
    ParticleInfo,
    PhasespaceData,
    Simulation,
    TimingsData,
    TrackData,
    TrackInfo,
)
from osiris_toolkit.units import UnitConverter

__all__ = [
    "__version__",
    "DiagKind",
    "Field",
    "FieldInfo",
    "GridAxis",
    "GridData",
    "HistoryData",
    "OSIRIS_DIAGNOSTICS",
    "ParticleData",
    "ParticleInfo",
    "PhasespaceData",
    "PostProcessor",
    "Simulation",
    "TimingsData",
    "TrackData",
    "TrackInfo",
    "TracksAnalyzer",
    "UnitConverter",
    "compute_k_space",
    "line_integrate",
    "list_records",
    "mask_energy",
    "particles_to_grid",
    "read_grid",
    "read_info",
    "read_particles",
    "read_tracks",
    "spectral_power",
    "trapz_2d",
]
