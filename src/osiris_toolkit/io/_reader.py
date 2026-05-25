"""Clean-room ZDF binary format reader.

Implements the ZDF format as described in the format specification
(zdf/README.md) and verified against real ZDF binary files. This
implementation contains no code derived from the ZPIC/OSIRIS reference
implementation.

All functions are stateless — each call opens its own file handle,
reads the requested data, and closes. This design is inherently
thread-safe and pickle-safe, enabling parallel batch reads.
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import BinaryIO

import numpy as np

from osiris_toolkit.io._format import (
    MAGIC,
    RecordType,
    numpy_dtype,
    record_type_name,
    record_version,
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

# ---------------------------------------------------------------------------
# Low-level: scalar readers (all little-endian, per format spec)
# ---------------------------------------------------------------------------


def _read_int32(fh: BinaryIO) -> int:
    return struct.unpack("<i", fh.read(4))[0]


def _read_uint32(fh: BinaryIO) -> int:
    return struct.unpack("<I", fh.read(4))[0]


def _read_int64(fh: BinaryIO) -> int:
    return struct.unpack("<q", fh.read(8))[0]


def _read_uint64(fh: BinaryIO) -> int:
    return struct.unpack("<Q", fh.read(8))[0]


def _read_float32(fh: BinaryIO) -> float:
    return struct.unpack("<f", fh.read(4))[0]


def _read_float64(fh: BinaryIO) -> float:
    return struct.unpack("<d", fh.read(8))[0]


def _read_string(fh: BinaryIO) -> str:
    """Read a ZDF string: uint32 length + ASCII data + 4-byte alignment."""
    length = _read_uint32(fh)
    if length == 0:
        return ""
    raw = fh.read(length)
    # Skip 4-byte alignment padding
    pad = ((length + 3) // 4) * 4 - length
    if pad:
        fh.read(pad)
    return raw.decode("ascii")


# ---------------------------------------------------------------------------
# Record-level operations
# ---------------------------------------------------------------------------


def _read_record(fh: BinaryIO) -> ZdfRecord | None:
    """Read one record header. Returns None at EOF."""
    pos = fh.tell()
    try:
        id_ver_raw = fh.read(4)
    except Exception:
        return None
    if len(id_ver_raw) < 4:
        return None
    id_ver = struct.unpack("<I", id_ver_raw)[0]
    name = _read_string(fh)
    try:
        rec_len = _read_uint64(fh)
    except Exception:
        return None
    return ZdfRecord(pos=pos, id=id_ver, name=name, length=rec_len)


def _skip_record(fh: BinaryIO, rec: ZdfRecord) -> None:
    """Seek past a record's data."""
    fh.seek(rec.pos + 4 + _encoded_string_size(rec.name) + 8 + rec.length)


def _encoded_string_size(s: str) -> int:
    """Size of a ZDF-encoded string on disk: length(uint32) + data + padding."""
    data_len = len(s)
    return 4 + ((data_len + 3) // 4) * 4


# ---------------------------------------------------------------------------
# Metadata record readers
# ---------------------------------------------------------------------------


def _read_iteration(fh: BinaryIO, rec: ZdfRecord) -> ZdfIteration:
    n = _read_int32(fh)
    t = _read_float64(fh)
    tunits = _read_string(fh)
    return ZdfIteration(n=n, t=t, tunits=tunits)


def _read_grid_info(fh: BinaryIO, rec: ZdfRecord) -> ZdfGridInfo:
    ver = record_version(rec.id)
    if ver > 1:
        raise ValueError(f"Unsupported grid_info version: {ver}")

    gi = ZdfGridInfo()
    gi.ndims = _read_uint32(fh)
    gi.nx = [int(x) for x in np.fromfile(fh, dtype="<u8", count=gi.ndims)]
    gi.label = _read_string(fh)
    gi.units = _read_string(fh)
    gi.has_axis = bool(_read_int32(fh))

    if gi.has_axis:
        for i in range(gi.ndims):
            ax = ZdfAxis()
            ax.name = _read_string(fh) if ver > 0 else f"axis_{i}"
            ax.axis_type = _read_int32(fh)
            ax.min = _read_float64(fh)
            ax.max = _read_float64(fh)
            ax.label = _read_string(fh)
            ax.units = _read_string(fh)
            gi.axes.append(ax)

    return gi


def _read_part_info(fh: BinaryIO, rec: ZdfRecord) -> ZdfPartInfo:
    ver = record_version(rec.id)
    if ver > 2:
        raise ValueError(f"Unsupported part_info version: {ver}")

    pi = ZdfPartInfo()
    pi.label = _read_string(fh)

    if ver >= 1:
        pi.nparts = int(_read_uint64(fh))
        pi.nquants = _read_uint32(fh)
        for _ in range(pi.nquants):
            pi.quants.append(_read_string(fh))
        for q in pi.quants:
            pi.qlabels[q] = _read_string(fh)
        for q in pi.quants:
            pi.qunits[q] = _read_string(fh)
    else:
        # Legacy v0 format: nquants first, then quants, then nparts
        pi.nquants = _read_uint32(fh)
        for _ in range(pi.nquants):
            pi.quants.append(_read_string(fh))
        for q in pi.quants:
            pi.qlabels[q] = q
        for q in pi.quants:
            pi.qunits[q] = _read_string(fh)
        pi.nparts = int(_read_uint64(fh))

    return pi


def _read_track_info(fh: BinaryIO, rec: ZdfRecord) -> ZdfTrackInfo:
    ver = record_version(rec.id)
    if ver > 1:
        raise ValueError(f"Unsupported track_info version: {ver}")

    ti = ZdfTrackInfo()
    ti.label = _read_string(fh)
    ti.ntracks = _read_uint32(fh)
    ti.ndump = _read_uint32(fh)
    ti.niter = _read_uint32(fh)
    ti.nquants = _read_uint32(fh)

    for _ in range(ti.nquants):
        ti.quants.append(_read_string(fh))
    for _ in range(ti.nquants):
        ti.qlabels.append(_read_string(fh))
    for _ in range(ti.nquants):
        ti.qunits.append(_read_string(fh))

    # First quantity is iteration data (not stored in track arrays)
    ti.nquants -= 1
    ti.quants.pop(0)
    ti.qlabels.pop(0)
    ti.qunits.pop(0)

    return ti


# ---------------------------------------------------------------------------
# Array reader
# ---------------------------------------------------------------------------


def _read_array(fh: BinaryIO, dtype_id: int, shape: tuple[int, ...]) -> np.ndarray:
    """Read a data array in the given dtype and shape.

    Data is stored in Fortran (column-major) order. The shape must be
    reversed to produce a C-order (row-major) numpy array.
    """
    dt = numpy_dtype(dtype_id)
    size = int(np.prod(shape))
    data = np.fromfile(fh, dtype=dt, count=size)
    # Reverse dimensions: Fortran (file) → C (numpy)
    return data.reshape(tuple(reversed(shape)))


# ---------------------------------------------------------------------------
# Dataset readers
# ---------------------------------------------------------------------------


def _read_data_header(fh: BinaryIO) -> tuple[int, int, list[int]]:
    """Read the common data header: data_type_id, ndims, nx.

    Shared by regular and chunked dataset readers.
    """
    data_type_id = _read_int32(fh)
    ndims = _read_uint32(fh)
    nx = [int(x) for x in np.fromfile(fh, dtype="<u8", count=ndims)]
    return data_type_id, ndims, nx


def _read_dataset(fh: BinaryIO, rec: ZdfRecord) -> np.ndarray | None:
    """Read a regular (non-chunked) dataset."""
    type_id = rec.id & 0xFFFF0000
    if type_id != RecordType.DATASET:
        raise ValueError(f"Expected DATASET record, got {record_type_name(rec.id)}")

    ver = record_version(rec.id)
    if ver > 2:
        raise ValueError(f"Unsupported dataset version: {ver}")

    if ver >= 1:
        _id = _read_uint32(fh)  # dataset ID (not needed)

    data_type_id, ndims, nx = _read_data_header(fh)

    return _read_array(fh, data_type_id, tuple(nx))


def _read_cdset(fh: BinaryIO, rec: ZdfRecord, rewind: bool = False) -> np.ndarray | None:
    """Read a chunked dataset (CDSET_START → CDSET_CHUNK* → CDSET_END)."""
    type_id = rec.id & 0xFFFF0000
    if type_id != RecordType.CDSET_START:
        raise ValueError(f"Expected CDSET_START record, got {record_type_name(rec.id)}")

    ver = record_version(rec.id)
    if ver > 1:
        raise ValueError(f"Unsupported cdset version: {ver}")

    _id = _read_uint32(fh)
    data_type_id, ndims, nx = _read_data_header(fh)

    # Allocate empty array (C-order shape)
    dt = numpy_dtype(data_type_id)
    c_shape = tuple(reversed(nx))
    data = np.zeros(c_shape, dtype=dt)

    # Chunk name: 8 hex digits + "-chunk" (empirically verified from real files)
    chunk_name = f"{_id:08x}-chunk"
    end_name = f"{_id:08x}-end"

    if rewind:
        save_pos = fh.tell()

    while True:
        chunk_rec = _read_record(fh)
        if chunk_rec is None:
            break

        if chunk_rec.name == chunk_name:
            _ = _read_uint32(fh)  # dataset_id (uint32, verified against OSIRIS zdf.c)
            count = [int(x) for x in np.fromfile(fh, dtype="<i8", count=ndims)]
            start = [int(x) for x in np.fromfile(fh, dtype="<i8", count=ndims)]
            stride = [int(x) for x in np.fromfile(fh, dtype="<i8", count=ndims)]
            # Read chunk data: pass count as-is (Fortran dims).
            # _read_array reverses internally, producing C-order shape that
            # matches the slice target built from reversed count below.
            chunk = _read_array(fh, data_type_id, tuple(count))

            # Map chunk into full array using C-order slices
            slices: list[slice] = []
            for d in range(ndims):
                s = start[ndims - 1 - d]
                c = count[ndims - 1 - d]
                st = stride[ndims - 1 - d]
                slices.append(slice(s, s + c, st))
            data[tuple(slices)] = chunk

        elif chunk_rec.name == end_name:
            break
        else:
            _skip_record(fh, chunk_rec)

    if rewind:
        fh.seek(save_pos)

    return data


# ---------------------------------------------------------------------------
# File type reader (first record in every ZDF file)
# ---------------------------------------------------------------------------


def _read_file_type(fh: BinaryIO) -> str:
    """Read the file type from the first (TYPE) record.

    The first record in every ZDF file is a STRING record named "TYPE"
    whose data encodes the file type (e.g. "grid", "particles", "tracks-2").
    """
    rec = _read_record(fh)
    if rec is None:
        raise ValueError("Unexpected EOF: missing TYPE record")
    type_id = rec.id & 0xFFFF0000
    if type_id != RecordType.STRING:
        raise ValueError(f"Expected TYPE (STRING) record, got {record_type_name(rec.id)}")
    return _read_string(fh)


# ---------------------------------------------------------------------------
# High-level file readers
# ---------------------------------------------------------------------------


def read_info(path: str | Path) -> ZdfFileInfo:
    """Read metadata only from a ZDF file.

    Returns a ``ZdfFileInfo`` with the file type, grid/particle/track
    metadata, and iteration info (as available). Does not read array data.
    """
    with open(path, "rb") as fh:
        _check_magic(fh)
        file_type = _read_file_type(fh)
        info = ZdfFileInfo(file_type=file_type)

        if file_type == "grid":
            rec = _read_record(fh)
            if rec is None:
                raise ValueError("Unexpected EOF reading grid info")
            info.grid = _read_grid_info(fh, rec)
            rec = _read_record(fh)
            if rec is None:
                raise ValueError("Unexpected EOF reading iteration")
            info.iteration = _read_iteration(fh, rec)

        elif file_type == "particles":
            rec = _read_record(fh)
            if rec is None:
                raise ValueError("Unexpected EOF reading particle info")
            info.particles = _read_part_info(fh, rec)
            rec = _read_record(fh)
            if rec is None:
                raise ValueError("Unexpected EOF reading iteration")
            info.iteration = _read_iteration(fh, rec)

        elif file_type == "tracks-2":
            rec = _read_record(fh)
            if rec is None:
                raise ValueError("Unexpected EOF reading track info")
            info.tracks = _read_track_info(fh, rec)

        else:
            raise ValueError(f"Unknown ZDF file type: {file_type!r}")

    return info


def read_grid(path: str | Path) -> tuple[np.ndarray, ZdfGridInfo, ZdfIteration]:
    """Read a ZDF grid file. Returns (data, grid_info, iteration)."""
    with open(path, "rb") as fh:
        _check_magic(fh)
        _read_file_type(fh)  # consume TYPE record

        rec = _read_record(fh)
        if rec is None:
            raise ValueError("Unexpected EOF reading grid info")
        gi = _read_grid_info(fh, rec)

        rec = _read_record(fh)
        if rec is None:
            raise ValueError("Unexpected EOF reading iteration")
        it = _read_iteration(fh, rec)

        rec = _read_record(fh)
        if rec is None:
            raise ValueError("Unexpected EOF reading dataset")
        type_id = rec.id & 0xFFFF0000
        if type_id == RecordType.DATASET:
            data = _read_dataset(fh, rec)
        elif type_id == RecordType.CDSET_START:
            data = _read_cdset(fh, rec)
        else:
            raise ValueError(f"Expected dataset, got {record_type_name(rec.id)}")

        if data is None:
            raise ValueError("Failed to read grid dataset")

    return data, gi, it


def read_particles(path: str | Path) -> tuple[dict[str, np.ndarray], ZdfPartInfo, ZdfIteration]:
    """Read a ZDF particles file. Returns (data_dict, part_info, iteration)."""
    with open(path, "rb") as fh:
        _check_magic(fh)
        _read_file_type(fh)  # consume TYPE record

        rec = _read_record(fh)
        if rec is None:
            raise ValueError("Unexpected EOF reading particle info")
        pi = _read_part_info(fh, rec)

        rec = _read_record(fh)
        if rec is None:
            raise ValueError("Unexpected EOF reading iteration")
        it = _read_iteration(fh, rec)

        data: dict[str, np.ndarray] = {}
        for q in pi.quants:
            rec = _read_record(fh)
            if rec is None:
                break
            type_id = rec.id & 0xFFFF0000
            if type_id == RecordType.DATASET:
                arr = _read_dataset(fh, rec)
            elif type_id == RecordType.CDSET_START:
                arr = _read_cdset(fh, rec, rewind=True)
            else:
                arr = None
            data[q] = arr if arr is not None else np.array([])

    return data, pi, it


def read_tracks(path: str | Path) -> tuple[list[np.ndarray], ZdfTrackInfo]:
    """Read a ZDF tracks file. Returns (track_list, track_info)."""
    with open(path, "rb") as fh:
        _check_magic(fh)
        _read_file_type(fh)  # consume TYPE record

        rec = _read_record(fh)
        if rec is None:
            raise ValueError("Unexpected EOF reading track info")
        ti = _read_track_info(fh, rec)

        # Read itermap
        rec = _read_record(fh)
        if rec is None or rec.name != "itermap":
            raise ValueError("Expected itermap record")
        itermap = _read_cdset(fh, rec)
        if itermap is None:
            return [], ti

        # Read data (position is now after itermap CDSET_END)
        rec = _read_record(fh)
        if rec is None or rec.name != "data":
            raise ValueError("Expected data record")
        track_data = _read_cdset(fh, rec)
        if track_data is None:
            return [], ti

        # Build per-track arrays from itermap indices
        track_sizes = np.zeros(ti.ntracks, dtype="<i8")
        for i in range(itermap.shape[0]):
            track_id = int(itermap[i, 0]) - 1
            npoints = int(itermap[i, 1])
            track_sizes[track_id] += npoints

        tracks: list[np.ndarray] = []
        for i in range(ti.ntracks):
            tracks.append(np.zeros([track_sizes[i], ti.nquants], dtype="<f4"))
            track_sizes[i] = 0  # reset for use as write cursor

        idx = 0
        for i in range(itermap.shape[0]):
            track_id = int(itermap[i, 0]) - 1
            npoints = int(itermap[i, 1])
            tracks[track_id][track_sizes[track_id]:track_sizes[track_id] + npoints, :] = (
                track_data[idx:idx + npoints, :]
            )
            track_sizes[track_id] += npoints
            idx += npoints

    return tracks, ti


# ---------------------------------------------------------------------------
# Record listing (for inspection)
# ---------------------------------------------------------------------------


def list_records(path: str | Path) -> list[ZdfRecord]:
    """Return all record headers in a ZDF file without reading data."""
    records: list[ZdfRecord] = []
    with open(path, "rb") as fh:
        _check_magic(fh)
        while True:
            rec = _read_record(fh)
            if rec is None:
                break
            records.append(rec)
            _skip_record(fh, rec)
    return records


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_magic(fh: BinaryIO) -> None:
    """Verify the ZDF magic number at the current file position."""
    magic = fh.read(4)
    if magic != MAGIC:
        raise ValueError(
            f"Not a valid ZDF file: expected magic {MAGIC!r}, got {magic!r}"
        )
