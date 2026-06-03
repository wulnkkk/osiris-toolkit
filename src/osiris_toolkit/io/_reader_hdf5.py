"""HDF5 format reader for OSIRIS diagnostic files.

Implements the same interface as _reader.py (ZDF), but reads from
HDF5 files (.h5) produced by OSIRIS when compiled with HDF5 support.

All functions are stateless — each call opens its own file handle.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from osiris_toolkit.io._types import (
    ZdfAxis,
    ZdfFileInfo,
    ZdfGridInfo,
    ZdfIteration,
    ZdfPartInfo,
    ZdfRecord,
    ZdfTrackInfo,
)


def _ensure_h5py():
    """Lazy-import h5py with a helpful error message."""
    try:
        import h5py
    except ImportError:
        raise ImportError(
            "h5py is required to read HDF5 files. "
            "Install with: pip install osiris-toolkit[hdf5]"
        )
    return h5py


# ---------------------------------------------------------------------------
# Attribute helpers
# ---------------------------------------------------------------------------


def _read_str_attr(group, name: str) -> str:
    """Read a string attribute, decoding bytes if needed."""
    val = group.attrs[name]
    if isinstance(val, (bytes, np.bytes_)):
        return val.decode("utf-8")
    return str(val)


def _read_opt_str_attr(group, name: str) -> str | None:
    """Read an optional string attribute."""
    try:
        return _read_str_attr(group, name)
    except KeyError:
        return None


# ---------------------------------------------------------------------------
# Metadata readers
# ---------------------------------------------------------------------------


def _read_grid_info_h5(grp) -> ZdfGridInfo:
    gi = ZdfGridInfo()
    gi.ndims = int(grp.attrs["NDIMS"])
    nx_data = grp["NX"][:]
    gi.nx = [int(x) for x in nx_data]
    gi.label = _read_opt_str_attr(grp, "LABEL") or ""
    gi.units = _read_opt_str_attr(grp, "UNITS") or ""

    gi.has_axis = "AXIS1" in grp
    if gi.has_axis:
        for i in range(gi.ndims):
            ax_name = f"AXIS{i+1}"
            if ax_name not in grp:
                continue
            ag = grp[ax_name]
            ax = ZdfAxis()
            ax.name = _read_opt_str_attr(ag, "NAME") or f"axis_{i}"
            ax.axis_type = int(ag.attrs.get("TYPE", 0))
            ax.min = float(ag.attrs.get("MIN", 0.0))
            ax.max = float(ag.attrs.get("MAX", 0.0))
            ax.label = _read_opt_str_attr(ag, "LABEL") or ""
            ax.units = _read_opt_str_attr(ag, "UNITS") or ""
            gi.axes.append(ax)

    return gi


def _read_iteration_h5(grp) -> ZdfIteration:
    return ZdfIteration(
        n=int(grp.attrs["N"]),
        t=float(grp.attrs["T"]),
        tunits=_read_opt_str_attr(grp, "TUNITS") or "",
    )


def _read_part_info_h5(grp) -> ZdfPartInfo:
    pi = ZdfPartInfo()
    pi.label = _read_opt_str_attr(grp, "LABEL") or ""
    pi.nparts = int(grp.attrs["NPARTS"])
    pi.nquants = int(grp.attrs["NQUANTS"])

    if "QUANTS" in grp:
        quants_grp = grp["QUANTS"]
        for qname in quants_grp:
            pi.quants.append(qname)
            qgrp = quants_grp[qname]
            pi.qlabels[qname] = _read_opt_str_attr(qgrp, "LABEL") or qname
            pi.qunits[qname] = _read_opt_str_attr(qgrp, "UNITS") or ""

    return pi


def _read_track_info_h5(grp) -> ZdfTrackInfo:
    ti = ZdfTrackInfo()
    ti.label = _read_opt_str_attr(grp, "LABEL") or ""
    ti.ntracks = int(grp.attrs["NTRACKS"])
    ti.ndump = int(grp.attrs["NDUMP"])
    ti.niter = int(grp.attrs["NITER"])
    ti.nquants = int(grp.attrs["NQUANTS"])

    if "QUANTS" in grp:
        quants_grp = grp["QUANTS"]
        for qname in quants_grp:
            ti.quants.append(qname)
            qgrp = quants_grp[qname]
            ti.qlabels.append(_read_opt_str_attr(qgrp, "LABEL") or qname)
            ti.qunits.append(_read_opt_str_attr(qgrp, "UNITS") or "")

    return ti


# ---------------------------------------------------------------------------
# High-level file readers
# ---------------------------------------------------------------------------


def read_info(path: str | Path) -> ZdfFileInfo:
    """Read metadata only from an HDF5 file.

    Returns a ``ZdfFileInfo`` with the file type, grid/particle/track
    metadata, and iteration info (as available). Does not read array data.
    """
    h5py = _ensure_h5py()
    path = Path(path)

    try:
        f = h5py.File(path, "r")
    except OSError:
        raise ValueError(f"Not a valid HDF5 file: {path}")

    with f:
        try:
            file_type = _read_str_attr(f, "TYPE")
        except KeyError:
            raise ValueError(f"Missing TYPE attribute in HDF5 file: {path}")

        sim_info = _read_opt_str_attr(f, "SIMULATION")
        info = ZdfFileInfo(file_type=file_type, simulation_info=sim_info)

        if file_type == "grid":
            if "GRID_INFO" in f:
                info.grid = _read_grid_info_h5(f["GRID_INFO"])
            if "ITERATION" in f:
                info.iteration = _read_iteration_h5(f["ITERATION"])

        elif file_type == "particles":
            if "PART_INFO" in f:
                info.particles = _read_part_info_h5(f["PART_INFO"])
            if "ITERATION" in f:
                info.iteration = _read_iteration_h5(f["ITERATION"])

        elif file_type == "tracks":
            if "TRACK_INFO" in f:
                info.tracks = _read_track_info_h5(f["TRACK_INFO"])

        else:
            raise ValueError(f"Unknown HDF5 file type: {file_type!r} in {path}")

    return info


def read_grid(path: str | Path) -> tuple[np.ndarray, ZdfGridInfo, ZdfIteration]:
    """Read an HDF5 grid file. Returns (data, grid_info, iteration)."""
    h5py = _ensure_h5py()
    path = Path(path)

    try:
        f = h5py.File(path, "r")
    except OSError:
        raise ValueError(f"Not a valid HDF5 file: {path}")

    with f:
        file_type = _read_str_attr(f, "TYPE")
        if file_type != "grid":
            raise ValueError(f"Expected 'grid' file type, got {file_type!r}")

        gi = _read_grid_info_h5(f["GRID_INFO"])
        it = _read_iteration_h5(f["ITERATION"])

        data = f["DATA"][:]
        expected_c_shape = tuple(reversed(gi.nx))
        if data.shape != expected_c_shape:
            data = data.reshape(gi.nx[::-1])

    return data, gi, it


def read_particles(path: str | Path) -> tuple[dict[str, np.ndarray], ZdfPartInfo, ZdfIteration]:
    """Read an HDF5 particles file. Returns (data_dict, part_info, iteration)."""
    h5py = _ensure_h5py()
    path = Path(path)

    try:
        f = h5py.File(path, "r")
    except OSError:
        raise ValueError(f"Not a valid HDF5 file: {path}")

    with f:
        file_type = _read_str_attr(f, "TYPE")
        if file_type != "particles":
            raise ValueError(f"Expected 'particles' file type, got {file_type!r}")

        pi = _read_part_info_h5(f["PART_INFO"])
        it = _read_iteration_h5(f["ITERATION"])

        data: dict[str, np.ndarray] = {}
        for q in pi.quants:
            if q in f:
                data[q] = f[q][:]
            else:
                data[q] = np.array([])

    return data, pi, it


def read_tracks(path: str | Path) -> tuple[list[np.ndarray], ZdfTrackInfo]:
    """Read an HDF5 tracks file. Returns (track_list, track_info)."""
    h5py = _ensure_h5py()
    path = Path(path)

    try:
        f = h5py.File(path, "r")
    except OSError:
        raise ValueError(f"Not a valid HDF5 file: {path}")

    with f:
        file_type = _read_str_attr(f, "TYPE")
        if file_type != "tracks":
            raise ValueError(f"Expected 'tracks' file type, got {file_type!r}")

        ti = _read_track_info_h5(f["TRACK_INFO"])

        itermap = f["ITERMAP"][:]
        track_data = f["DATA"][:]

        # Build per-track arrays from itermap indices
        track_sizes = np.zeros(ti.ntracks, dtype="<i8")
        for i in range(itermap.shape[0]):
            track_id = int(itermap[i, 0]) - 1
            npoints = int(itermap[i, 1])
            track_sizes[track_id] += npoints

        tracks: list[np.ndarray] = []
        for i in range(ti.ntracks):
            tracks.append(np.zeros([track_sizes[i], ti.nquants], dtype="<f4"))
            track_sizes[i] = 0

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


def list_records(path: str | Path) -> list[ZdfRecord]:
    """Return synthetic ZdfRecord list representing the HDF5 structure.

    HDF5 files do not have the ZDF record concept. This function
    synthesizes records from the HDF5 group/dataset structure for
    inspection consistency.
    """
    h5py = _ensure_h5py()
    path = Path(path)

    try:
        f = h5py.File(path, "r")
    except OSError:
        raise ValueError(f"Not a valid HDF5 file: {path}")

    records: list[ZdfRecord] = []

    with f:
        file_type = _read_opt_str_attr(f, "TYPE") or "unknown"
        records.append(ZdfRecord(pos=0, id=0, name="TYPE", length=len(file_type)))

        def _walk(name, obj):
            if isinstance(obj, h5py.Group):
                records.append(ZdfRecord(pos=0, id=0, name=name, length=len(obj)))
            elif isinstance(obj, h5py.Dataset):
                records.append(ZdfRecord(pos=0, id=0, name=name, length=obj.size))

        f.visititems(_walk)

    return records
