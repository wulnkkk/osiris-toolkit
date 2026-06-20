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
from osiris_toolkit.io.vtk_exporter import to_vtk

__all__ = [
    "DTYPE_NAMES",
    "DTYPE_TO_NUMPY",
    "MAGIC",
    "RecordType",
    "ZdfAxis",
    "ZdfFileInfo",
    "ZdfGridInfo",
    "ZdfIteration",
    "ZdfPartInfo",
    "ZdfRecord",
    "ZdfTrackInfo",
    "list_records",
    "numpy_dtype",
    "read_grid",
    "read_info",
    "read_many",
    "read_many_map",
    "read_particles",
    "read_tracks",
    "record_type_name",
    "to_vtk",
]
