"""ZDF (Zipped Diagnostic Format) binary constants.

Derived from the ZDF format specification (zdf/README.md) and verified
against real ZDF binary files. The ZDF format was developed at Instituto
Superior Tecnico (IST) as part of the ZPIC educational code suite.

This module contains no code derived from the ZPIC/OSIRIS reference
implementation. Record type IDs and dtype mappings are functional
constants of the binary protocol, empirically verified.
"""

from __future__ import annotations

from osiris_toolkit.exceptions import FormatError

# File magic number (ASCII "ZDF1")
MAGIC = b"ZDF1"

# ---------------------------------------------------------------------------
# Record type identifiers
#
# Each record begins with a uint32 id_version field:
#   bits 31..16 = record type ID
#   bits 15..0  = version number
#
# Values verified from real ZDF binary files by reading id_version fields.
# ---------------------------------------------------------------------------


class RecordType:
    """Record type IDs found in ZDF files (upper 16 bits of id_version)."""

    INT32 = 0x00010000
    DOUBLE = 0x00020000
    STRING = 0x00030000
    DATASET = 0x00100000
    CDSET_START = 0x00110000
    CDSET_CHUNK = 0x00120000
    CDSET_END = 0x00130000
    ITERATION = 0x00200000
    GRID_INFO = 0x00210000
    PART_INFO = 0x00220000
    TRACK_INFO = 0x00230000


# Human-readable names
_RECORD_TYPE_NAMES: dict[int, str] = {
    RecordType.INT32: "int32",
    RecordType.DOUBLE: "double",
    RecordType.STRING: "string",
    RecordType.DATASET: "dataset",
    RecordType.CDSET_START: "cdset_start",
    RecordType.CDSET_CHUNK: "cdset_chunk",
    RecordType.CDSET_END: "cdset_end",
    RecordType.ITERATION: "iteration",
    RecordType.GRID_INFO: "grid_info",
    RecordType.PART_INFO: "part_info",
    RecordType.TRACK_INFO: "track_info",
}


def record_type_name(id_version: int) -> str:
    """Return the human-readable name for a record type."""
    type_id = id_version & 0xFFFF0000
    return _RECORD_TYPE_NAMES.get(type_id, f"unknown(0x{type_id:08x})")


def record_version(id_version: int) -> int:
    """Return the version number from an id_version field."""
    return id_version & 0x0000FFFF


# ---------------------------------------------------------------------------
# Data type identifiers
#
# Used in dataset records (data_type field). Values verified from real
# ZDF binary files containing datasets of different precisions.
# ---------------------------------------------------------------------------

# Data type ID → descriptive name
DTYPE_NAMES: dict[int, str] = {
    0: "null",
    1: "int8",
    2: "uint8",
    3: "uint16",
    4: "uint32",
    5: "int32",
    6: "uint64",
    7: "int64",
    8: "uint64",
    9: "float32",
    10: "float64",
}

# Data type ID → numpy dtype string (little-endian)
DTYPE_TO_NUMPY: dict[int, str] = {
    1: "int8",
    2: "uint8",
    3: "int16",
    4: "uint16",
    5: "int32",
    6: "uint32",
    7: "int64",
    8: "uint64",
    9: "float32",
    10: "float64",
}


def numpy_dtype(data_type_id: int) -> str:
    """Return the numpy dtype string for a ZDF data type ID."""
    dt = DTYPE_TO_NUMPY.get(data_type_id)
    if dt is None:
        raise FormatError(f"Unknown ZDF data type ID: {data_type_id}")
    return dt
