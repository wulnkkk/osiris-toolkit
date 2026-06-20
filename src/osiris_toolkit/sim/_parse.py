"""Filename and text-file parsing helpers for OSIRIS simulation output."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from osiris_toolkit._models import HistoryData, TimingsData
from osiris_toolkit.exceptions import FormatError

# ---------------------------------------------------------------------------
# Naming convention: {quant}[-{label}]-{iter:06d}.zdf
# ---------------------------------------------------------------------------
_ITER_FILE_RE = re.compile(r"^(.+)-(\d{6})\.(?:zdf|h5)$")


def _parse_iter_file(filename: str) -> tuple[str, int]:
    """Parse quantity/label and iteration number from a ZDF filename.

    Returns (quant_label, iteration). quant_label may include species
    or phasespace names separated by '-'.
    """
    m = _ITER_FILE_RE.match(filename)
    if m is None:
        raise FormatError(f"Unexpected ZDF filename format: {filename}")
    return m.group(1), int(m.group(2))


# Known OSIRIS report type suffixes (detected from filename)
_REPORT_SUFFIXES = {
    "_savg": "savg",
    "_senv": "senv",
    "_line": "line",
    "_slice": "slice",
    "_tavg": "tavg",
}


def _parse_quantity(raw: str) -> tuple[str, str]:
    """Parse a raw quantity string into (base_quantity, report_type).

    OSIRIS report modifiers appear as suffixes on quantity names in
    ZDF filenames (e.g. ``e1_savg-000100.zdf``).

    Parameters
    ----------
    raw : str
        Raw quantity string from filename parsing.

    Returns
    -------
    tuple[str, str]
        (base_quantity, report_type). report_type is "" if no modifier.
    """
    raw_lower = raw.lower()
    for suffix, rtype in _REPORT_SUFFIXES.items():
        if raw_lower.endswith(suffix):
            return raw[: -len(suffix)], rtype
    return raw, ""


# ---------------------------------------------------------------------------
# History file parser
# ---------------------------------------------------------------------------


def _parse_history_file(filepath: Path) -> HistoryData:
    """Parse an OSIRIS history text file.

    Format:
        # col1  col2  col3 ...
        0.0  1.0  2.0  ...
        0.1  1.1  2.1  ...
    """
    with open(filepath, encoding="utf-8", errors="replace") as fh:
        lines = [ln.strip() for ln in fh if ln.strip()]

    if not lines:
        return HistoryData()

    # Header line: strip leading '#' and split
    header = lines[0].lstrip("#").strip()
    columns = header.split()

    # Data rows
    rows = []
    for ln in lines[1:]:
        if ln.startswith("#"):
            continue
        try:
            rows.append([float(v) for v in ln.split()])
        except ValueError:
            continue

    if not rows:
        return HistoryData(columns=columns, data={})

    arr = np.array(rows)
    data = {}
    for i, col in enumerate(columns):
        if i < arr.shape[1]:
            data[col] = arr[:, i]

    return HistoryData(columns=columns, data=data)


def _parse_timings_file(filepath: Path) -> TimingsData:
    """Parse an OSIRIS TIMINGS profiling text file.

    Serial format::

                                         Event            Total [s]
    -----------------------------------------------------------
    push_particles                          1.234E+02
    deposit_current                         5.678E+01

    Parallel format::

     Iterations = 1000

                                        Event            Avg [s]            Min [s]            Max [s]
    ------------------------------------------------------------------------------------------------------
    push_particles                       1.234E+02          1.200E+02          1.300E+02
    """
    with open(filepath, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip() for ln in fh if ln.strip()]

    if not lines:
        return TimingsData()

    # Detect serial vs parallel
    start_idx: int
    start_idx = 3 if lines[0].startswith(" Iterations") else 2

    if start_idx >= len(lines):
        return TimingsData()

    # Header line is the line just before the separator
    header_line = lines[start_idx - 1]
    col_parts = header_line.strip().split("  ")
    columns = [c.strip() for c in col_parts if c.strip()]

    event_names: list[str] = []
    data: dict[str, list[float]] = {col: [] for col in columns}

    for ln in lines[start_idx:]:
        # Event name is left-aligned in the first 40 columns
        if len(ln) < 40:
            continue
        event_name = ln[:40].strip()
        rest = ln[40:].strip()
        try:
            values = [float(v) for v in rest.split()]
        except ValueError:
            continue
        if len(values) != len(columns):
            continue
        event_names.append(event_name)
        for col, val in zip(columns, values, strict=True):
            data[col].append(val)

    return TimingsData(
        events=event_names,
        columns=columns,
        data={col: np.array(vals) for col, vals in data.items()},
    )
