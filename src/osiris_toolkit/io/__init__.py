"""I/O layer — ZDF binary format reader and parallel batch I/O.

The ZDF (Zipped Diagnostic Format) was developed at Instituto
Superior Tecnico (IST) as part of the ZPIC educational code suite.
This implementation is an independent reader based on the format
specification (zdf/README.md), verified against real ZDF binary files.
It contains no code derived from the ZPIC/OSIRIS reference implementation.
"""

from osiris_toolkit.io._format import (
    DTYPE_NAMES,
    DTYPE_TO_NUMPY,
    MAGIC,
    RecordType,
    numpy_dtype,
    record_type_name,
)
from osiris_toolkit.io._parallel import read_many, read_many_map
from osiris_toolkit.io.vtk_exporter import to_vtk
from osiris_toolkit.io._reader import (
    list_records,
    read_grid,
    read_info,
    read_particles,
    read_tracks,
)
from osiris_toolkit.io._types import (
    ZdfAxis,
    ZdfFileInfo,
    ZdfGridInfo,
    ZdfIteration,
    ZdfPartInfo,
    ZdfRecord,
    ZdfTrackInfo,
)

__all__ = [
    # Reader functions
    "read_info",
    "read_grid",
    "read_particles",
    "read_tracks",
    "list_records",
    # Parallel I/O
    "read_many",
    "read_many_map",
    # VTK export
    "to_vtk",
    # Format constants
    "MAGIC",
    "RecordType",
    "DTYPE_NAMES",
    "DTYPE_TO_NUMPY",
    "numpy_dtype",
    "record_type_name",
    # Types
    "ZdfRecord",
    "ZdfIteration",
    "ZdfAxis",
    "ZdfGridInfo",
    "ZdfPartInfo",
    "ZdfTrackInfo",
    "ZdfFileInfo",
]
