"""osiris-toolkit: Comprehensive toolkit for OSIRIS PIC simulation."""

__version__ = "0.15.0"

from osiris_toolkit.analysis.tracks import TracksAnalyzer
from osiris_toolkit.compute import (
    compute_k_space,
    line_integrate,
    mask_energy,
    particles_to_grid,
    spectral_power,
    trapz_2d,
)
from osiris_toolkit.config import OsirisConfig
from osiris_toolkit.exceptions import (
    ConfigurationError,
    DataNotFoundError,
    FormatError,
    MissingDependencyError,
    MissingParameterError,
    OsirisToolkitError,
    PipelineError,
    ShapeError,
    UnitConversionError,
    UnsupportedVersionError,
    ValidationError,
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
from osiris_toolkit.sim._lazy import LazySimulation
from osiris_toolkit.units import UnitConverter, UnitSystem
from osiris_toolkit.vis.batch import BatchResult, ProgressEvent

__all__ = [
    "__version__",
    "BatchResult",
    "ConfigurationError",
    "DataNotFoundError",
    "DataNotFoundError",
    "DiagKind",
    "Field",
    "FieldInfo",
    "FormatError",
    "GridAxis",
    "GridData",
    "HistoryData",
    "LazySimulation",
    "MissingDependencyError",
    "MissingParameterError",
    "OSIRIS_DIAGNOSTICS",
    "OsirisConfig",
    "OsirisToolkitError",
    "ParticleData",
    "ParticleInfo",
    "PhasespaceData",
    "PipelineError",
    "PostProcessor",
    "ProgressEvent",
    "ShapeError",
    "Simulation",
    "TimingsData",
    "TrackData",
    "TrackInfo",
    "TracksAnalyzer",
    "UnitConverter",
    "UnitConversionError",
    "UnsupportedVersionError",
    "ValidationError",
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
