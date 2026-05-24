"""Synthetic ZDF binary file builder for testing.

Generates minimal valid ZDF files (grid, particles, tracks) without
external dependencies. Also supports generating intentionally corrupt
files for robustness testing.
"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np

# -- ZDF constants (copied from io._format to keep builder zero-dependency) --
MAGIC = b"ZDF1"
STRING = 0x00030000
DATASET = 0x00100000
CDSET_START = 0x00110000
CDSET_CHUNK = 0x00120000
CDSET_END = 0x00130000
ITERATION = 0x00200000
GRID_INFO = 0x00210000
PART_INFO = 0x00220000
TRACK_INFO = 0x00230000

# Data type IDs
DT_FLOAT32 = 9
DT_FLOAT64 = 10


def _encode_string(s: str) -> bytes:
    """Encode a ZDF string: uint32 length + ASCII data + 4-byte padding."""
    data = s.encode("ascii")
    length = len(data)
    buf = struct.pack("<I", length) + data
    pad = ((length + 3) // 4) * 4 - length
    if pad:
        buf += b"\x00" * pad
    return buf


def _make_record(record_type: int, version: int, name: str, data: bytes) -> bytes:
    """Build a complete ZDF record."""
    id_ver = record_type | (version & 0xFFFF)
    name_enc = _encode_string(name)
    length = len(data)
    return struct.pack("<I", id_ver) + name_enc + struct.pack("<Q", length) + data


def _make_grid_info(nx: list[int], label: str = "", units: str = "",
                    axes: list[dict] | None = None) -> bytes:
    """Build a GRID_INFO v1 record body."""
    ndims = len(nx)
    buf = struct.pack("<I", ndims)
    for n in nx:
        buf += struct.pack("<Q", n)
    buf += _encode_string(label)
    buf += _encode_string(units)
    has_axis = 1 if axes else 0
    buf += struct.pack("<i", has_axis)
    if axes:
        for i in range(ndims):
            if i < len(axes):
                ax = axes[i]
                buf += _encode_string(ax.get("name", f"axis_{i}"))
                buf += struct.pack("<i", ax.get("type", 0))
                buf += struct.pack("<d", ax.get("min", 0.0))
                buf += struct.pack("<d", ax.get("max", 1.0))
                buf += _encode_string(ax.get("label", ""))
                buf += _encode_string(ax.get("units", ""))
            else:
                # Pad missing axes with defaults
                buf += _encode_string(f"axis_{i}")
                buf += struct.pack("<i", 0)
                buf += struct.pack("<d", 0.0)
                buf += struct.pack("<d", 1.0)
                buf += _encode_string("")
                buf += _encode_string("")
    return buf


def _make_iteration(n: int, t: float, tunits: str = "1/\\omega_p") -> bytes:
    """Build an ITERATION v0 record body."""
    buf = struct.pack("<i", n)
    buf += struct.pack("<d", t)
    buf += _encode_string(tunits)
    return buf


def _make_part_info(label: str, nparts: int,
                    quants: list[str], qlabels: dict[str, str] | None = None,
                    qunits: dict[str, str] | None = None) -> bytes:
    """Build a PART_INFO v1 record body."""
    buf = _encode_string(label)
    buf += struct.pack("<Q", nparts)
    buf += struct.pack("<I", len(quants))
    for q in quants:
        buf += _encode_string(q)
    for q in quants:
        buf += _encode_string(qlabels.get(q, q) if qlabels else q)
    for q in quants:
        buf += _encode_string(qunits.get(q, "") if qunits else "")
    return buf


def _make_track_info(label: str, ntracks: int, ndump: int, niter: int,
                     quants: list[str], qlabels: list[str] | None = None,
                     qunits: list[str] | None = None) -> bytes:
    """Build a TRACK_INFO v1 record body."""
    buf = _encode_string(label)
    buf += struct.pack("<I", ntracks)
    buf += struct.pack("<I", ndump)
    buf += struct.pack("<I", niter)
    buf += struct.pack("<I", len(quants))
    for q in quants:
        buf += _encode_string(q)
    for q in quants:
        buf += _encode_string(qlabels[quants.index(q)] if qlabels else q)
    for q in quants:
        buf += _encode_string(qunits[quants.index(q)] if qunits else "")
    return buf


def _make_dataset(data_type_id: int, ndims: int, nx: list[int],
                  data: np.ndarray) -> bytes:
    """Build a DATASET v1 record body. Data is written in Fortran order."""
    buf = struct.pack("<I", 0)  # dataset ID
    buf += struct.pack("<i", data_type_id)
    buf += struct.pack("<I", ndims)
    for n in nx:
        buf += struct.pack("<Q", n)
    # Write data in Fortran (column-major) order — reverse numpy axes
    fortran_order = np.asfortranarray(data)
    buf += fortran_order.tobytes()
    return buf


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def write_minimal_grid_zdf(
    path: str | Path,
    data: np.ndarray,
    iteration: int = 0,
    time: float = 0.0,
    label: str = "",
    units: str = "",
    axes: list[dict] | None = None,
) -> None:
    """Write a minimal valid ZDF grid file.

    Parameters
    ----------
    path : str or Path
        Output file path.
    data : np.ndarray
        Grid data. Shape determines nx.
    iteration : int
        Iteration number.
    time : float
        Simulation time.
    label : str
        Data label.
    units : str
        Data units.
    axes : list of dict, optional
        Axis descriptors with keys: name, type, min, max, label, units.
    """
    if data.dtype == np.float32:
        dtype_id = DT_FLOAT32
    elif data.dtype == np.float64:
        dtype_id = DT_FLOAT64
    else:
        data = data.astype(np.float32)
        dtype_id = DT_FLOAT32

    shape = list(data.shape)
    ndims = len(shape)
    nx = list(reversed(shape))  # C-order shape -> Fortran dimensions

    buf = MAGIC
    buf += _make_record(STRING, 0, "TYPE", _encode_string("grid"))
    buf += _make_record(GRID_INFO, 1, "", _make_grid_info(nx, label, units, axes))
    buf += _make_record(ITERATION, 0, "", _make_iteration(iteration, time))
    buf += _make_record(DATASET, 1, "", _make_dataset(dtype_id, ndims, nx, data))

    Path(path).write_bytes(buf)


def write_minimal_particles_zdf(
    path: str | Path,
    parts: dict[str, np.ndarray],
    iteration: int = 0,
    time: float = 0.0,
    label: str = "",
) -> None:
    """Write a minimal valid ZDF particles file.

    Parameters
    ----------
    path : str or Path
    parts : dict mapping quantity name -> 1D numpy array
        Typical keys: "name", "x1", "x2", "p1", "p2", "p3".
    iteration : int
    time : float
    label : str
    """
    quants = list(parts.keys())
    nparts = len(next(iter(parts.values()))) if parts else 0

    buf = MAGIC
    buf += _make_record(STRING, 0, "TYPE", _encode_string("particles"))
    buf += _make_record(PART_INFO, 1, "", _make_part_info(label, nparts, quants))
    buf += _make_record(ITERATION, 0, "", _make_iteration(iteration, time))

    for q in quants:
        arr = parts[q]
        if arr.dtype != np.float32:
            arr = arr.astype(np.float32)
        n = len(arr)
        dataset_body = _make_dataset(DT_FLOAT32, 1, [n], arr)
        buf += _make_record(DATASET, 1, q, dataset_body)

    Path(path).write_bytes(buf)


def _make_cdset(data_type_id: int, ndims: int, nx: list[int],
                 data: np.ndarray, dsid: int = 0, record_name: str = "") -> bytes:
    """Build CDSET_START + CDSET_CHUNK + CDSET_END records as one chunk.

    Writes the entire array as a single chunk covering the full extent.
    """
    buf = b""
    chunk_name = f"{dsid:08x}-chunk"
    end_name = f"{dsid:08x}-end"

    # CDSET_START
    start_body = struct.pack("<I", dsid)
    start_body += struct.pack("<i", data_type_id)
    start_body += struct.pack("<I", ndims)
    for n in nx:
        start_body += struct.pack("<Q", n)
    buf += _make_record(CDSET_START, 1, record_name, start_body)

    # CDSET_CHUNK — full array, one chunk
    # count/start/stride are in Fortran order (same as nx).
    # Data is written as raw bytes; the reader handles Fortran↔C conversion.
    arr = np.asarray(data)  # ensure ndarray
    chunk_data_bytes = arr.tobytes()
    chunk_body = b""
    for c in nx:
        chunk_body += struct.pack("<q", c)       # count (Fortran dims)
    for _ in range(ndims):
        chunk_body += struct.pack("<q", 0)       # start
    for _ in range(ndims):
        chunk_body += struct.pack("<q", 1)       # stride
    chunk_body += chunk_data_bytes
    buf += _make_record(CDSET_CHUNK, 1, chunk_name, chunk_body)

    # CDSET_END
    buf += _make_record(CDSET_END, 1, end_name, b"")

    return buf


def write_minimal_tracks_zdf(
    path: str | Path,
    tracks: list[np.ndarray],
    quants: list[str] | None = None,
    niter: int = 100,
    label: str = "",
) -> None:
    """Write a minimal valid ZDF tracks file.

    Parameters
    ----------
    path : str or Path
    tracks : list of (npoints, nquants) np.ndarray (float32)
        Each entry is one track's data.
    quants : list of str, optional
        Quantity names. Defaults to "q0", "q1", ...
    niter : int
        Total iterations simulated.
    label : str
    """
    ntracks = len(tracks)
    ndump = tracks[0].shape[0] if tracks else 0
    nquants = (tracks[0].shape[1] + 1) if tracks else 1  # +1 for itermap index quant

    if quants is None:
        quants = [f"q{i}" for i in range(nquants)]

    buf = MAGIC
    buf += _make_record(STRING, 0, "TYPE", _encode_string("tracks-2"))
    buf += _make_record(TRACK_INFO, 1, "", _make_track_info(label, ntracks, ndump, niter, quants))

    # Build itermap: for each track, list (track_id, npoints)
    # Fortran dims: [2, nentries]; C-order result will be (nentries, 2).
    itermap_rows = []
    for tid, t in enumerate(tracks, start=1):
        itermap_rows.append([tid, t.shape[0]])
    itermap_data = np.array(itermap_rows, dtype=np.int32)  # shape (ntracks, 2)
    buf += _make_cdset(5, 2, [2, len(tracks)], itermap_data, record_name="itermap")

    # Build data: concatenate all tracks
    # Fortran dims: [nquants, total_points]; C-order result will be (total_points, nquants).
    all_data = np.concatenate(tracks, axis=0) if tracks else np.zeros((0, 0), dtype=np.float32)
    if all_data.size > 0:
        buf += _make_cdset(DT_FLOAT32, 2, [all_data.shape[1], all_data.shape[0]], all_data, record_name="data")
    else:
        buf += _make_cdset(DT_FLOAT32, 2, [0, 0], all_data, record_name="data")

    Path(path).write_bytes(buf)


def write_invalid_zdf(path: str | Path, *, magic_corrupt: bool = False,
                      truncated: bool = False) -> None:
    """Write an intentionally invalid ZDF file for robustness testing.

    Parameters
    ----------
    path : str or Path
    magic_corrupt : bool
        Replace "ZDF1" magic with "XXXX".
    truncated : bool
        Cut off file right after the magic.
    """
    buf = b"XXXX" if magic_corrupt else MAGIC
    if truncated:
        Path(path).write_bytes(buf)
        return

    buf += _make_record(STRING, 0, "TYPE", _encode_string("grid"))
    if truncated:
        Path(path).write_bytes(buf[:16])
        return

    Path(path).write_bytes(buf)


def write_zero_byte_file(path: str | Path) -> None:
    """Write an empty file."""
    Path(path).write_bytes(b"")
