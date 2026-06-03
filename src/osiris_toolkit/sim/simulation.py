"""Simulation data access layer — directory discovery and typed accessors.

Traverses an OSIRIS simulation output directory tree and provides typed
accessors for all diagnostic types (fields, density, phasespace, raw
particles, tracks, history, etc.).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from osiris_toolkit._models import (
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
)
from osiris_toolkit.exceptions import FormatError, MissingDependencyError

if TYPE_CHECKING:
    from osiris_toolkit.config import OsirisConfig

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
            return raw[:-len(suffix)], rtype
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
    if lines[0].startswith(" Iterations"):
        start_idx = 3  # skip "Iterations = N", blank line, header
    else:
        start_idx = 2  # skip header, separator line

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
        for col, val in zip(columns, values):
            data[col].append(val)

    return TimingsData(
        events=event_names,
        columns=columns,
        data={col: np.array(vals) for col, vals in data.items()},
    )


# ---------------------------------------------------------------------------
# Internal entry types
# ---------------------------------------------------------------------------


@dataclass
class _FieldEntry:
    quantity: str
    label: str
    iteration: int
    path: Path
    report_type: str = ""


@dataclass
class _SpeciesEntry:
    species: str
    quantity: str
    iteration: int
    path: Path


# ---------------------------------------------------------------------------
# Simulation class
# ---------------------------------------------------------------------------


class Simulation:
    """One OSIRIS simulation output directory.

    Parameters
    ----------
    path : str or Path
        Path to the simulation output directory (containing MS/, HIST/,
        TIMINGS/, and run-info).  Converted to an absolute path immediately.
    output_root : str, Path, or None
        Root directory for analysis/visualisation outputs.  Defaults to
        ``{path}/figures/`` (in-place).  Set this to write outputs to a
        different location (e.g. when the simulation data is read-only).
    """

    def __init__(
        self,
        path: str | Path,
        output_root: str | Path | None = None,
        config: "OsirisConfig | None" = None,
    ) -> None:
        self._path = Path(path).absolute()
        if not self._path.is_dir():
            raise NotADirectoryError(f"Not a directory: {self._path}")

        # Config: explicit param > global singleton
        from osiris_toolkit.config import OsirisConfig

        self.config = config if config is not None else OsirisConfig.get().copy_with()

        self._output_root = (
            Path(output_root).absolute()
            if output_root is not None
            else self.config.output_root
            if self.config.output_root is not None
            else self._path / "figures"
        )

        self._fields: dict[str, list[_FieldEntry]] = {}
        self._chargecons: list[_FieldEntry] = []
        self._density: dict[str, dict[str, list[_FieldEntry]]] = {}
        self._cell_avg: dict[str, dict[str, list[_FieldEntry]]] = {}
        self._udist: dict[str, dict[str, list[_FieldEntry]]] = {}
        self._phasespace: dict[str, dict[str, list[_FieldEntry]]] = {}
        self._raw: dict[str, list[_FieldEntry]] = {}
        self._tracks: dict[str, Path] = {}
        self._ion: dict[str, dict[str, list[_FieldEntry]]] = {}
        self._wall: dict[str, list[_FieldEntry]] = {}
        self._history: dict[str, Path] = {}
        self._timings: list[Path] = []

        self._discover()

    def to_dict(self) -> dict:
        """Lightweight serialization — path only. Cheap to rebuild.

        Returns a dict with the minimal information needed to reconstruct
        this Simulation. Does NOT serialize cached state, file handles,
        or catalog data — those are cheaply rebuilt by ``from_dict()``.
        """
        return {"path": str(self._path)}

    @classmethod
    def from_dict(cls, d: dict) -> "Simulation":
        """Rebuild a Simulation from the output of ``to_dict()``.

        Re-discovers the output directory, rebuilding the catalog
        from scratch. This is cheap — only file listing and parsing.
        """
        return cls(d["path"])

    # ------------------------------------------------------------------
    # Path properties
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        """Absolute path to the simulation output directory."""
        return self._path

    @property
    def output_root(self) -> Path:
        """Absolute path to the output root directory."""
        return self._output_root

    def output_dir(self, *parts: str) -> Path:
        """Construct and create an output subdirectory.

        Parameters
        ----------
        *parts : str
            Path components to join under :attr:`output_root`.

        Returns
        -------
        Path
            Absolute path to the created directory.
        """
        d = self._output_root.joinpath(*parts)
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ------------------------------------------------------------------
    # Directory auto-discovery
    # ------------------------------------------------------------------

    def _discover(self) -> None:
        ms_dir = self._path / "MS"
        if ms_dir.is_dir():
            self._discover_ms(ms_dir)

        hist_dir = self._path / "HIST"
        if hist_dir.is_dir():
            for f in hist_dir.iterdir():
                if f.is_file():
                    self._history[f.name] = f

        timings_dir = self._path / "TIMINGS"
        if timings_dir.is_dir():
            self._timings = sorted(timings_dir.glob("*.txt"))

    def _discover_ms(self, ms_dir: Path) -> None:
        for item in ms_dir.iterdir():
            name = item.name.upper()

            if name == "FLD" and item.is_dir():
                self._discover_fld(item)
            elif name == "CHARGECONS" and item.is_dir():
                self._discover_chargecons(item)
            elif name == "DENSITY" and item.is_dir():
                self._discover_species_dir(item, self._density)
            elif name == "CELL_AVG" and item.is_dir():
                self._discover_species_dir(item, self._cell_avg)
            elif name == "UDIST" and item.is_dir():
                self._discover_species_dir(item, self._udist)
            elif name == "PHA" and item.is_dir():
                self._discover_phasespace(item)
            elif name == "RAW" and item.is_dir():
                self._discover_raw(item)
            elif name == "TRACKS" and item.is_dir():
                self._discover_tracks(item)
            elif name == "ION" and item.is_dir():
                self._discover_species_dir(item, self._ion)
            elif name.startswith("FLD_WALL") and item.is_dir():
                self._discover_wall(item)

    @staticmethod
    def _zdf_files_in(dir_path: Path) -> list[Path]:
        """Return ZDF and HDF5 data files in *dir_path*."""
        flat_zdf = list(dir_path.glob("*.zdf"))
        flat_h5 = list(dir_path.glob("*.h5"))
        flat = flat_zdf + flat_h5
        if flat:
            return sorted(flat)
        nested_zdf = list(dir_path.glob("*/*.zdf"))
        nested_h5 = list(dir_path.glob("*/*.h5"))
        nested = nested_zdf + nested_h5
        return sorted(nested)

    @staticmethod
    def _zdf_files_with_quant(dir_path: Path) -> list[tuple[str, Path]]:
        """Return (quantity, file_path) pairs for ZDF and HDF5 files."""
        flat_zdf = list(dir_path.glob("*.zdf"))
        flat_h5 = list(dir_path.glob("*.h5"))
        flat = flat_zdf + flat_h5
        if flat:
            result: list[tuple[str, Path]] = []
            for f in sorted(flat):
                q, _ = _parse_iter_file(f.name)
                result.append((q, f))
            return result
        # Nested: subdirectory name is the quantity
        result = []
        for quant_dir in sorted(dir_path.iterdir()):
            if not quant_dir.is_dir():
                continue
            files = sorted(
                list(quant_dir.glob("*.zdf")) + list(quant_dir.glob("*.h5"))
            )
            for f in files:
                result.append((quant_dir.name, f))
        return result

    def _discover_fld(self, fld_dir: Path) -> None:
        for raw_quantity, zdf_file in self._zdf_files_with_quant(fld_dir):
            quantity, report_type = _parse_quantity(raw_quantity)
            _, iteration = _parse_iter_file(zdf_file.name)
            self._fields.setdefault(quantity, []).append(
                _FieldEntry(
                    quantity=quantity,
                    label="",
                    iteration=iteration,
                    path=zdf_file,
                    report_type=report_type,
                )
            )

    def _discover_chargecons(self, cc_dir: Path) -> None:
        for raw_quantity, zdf_file in self._zdf_files_with_quant(cc_dir):
            quantity, report_type = _parse_quantity(raw_quantity)
            _, iteration = _parse_iter_file(zdf_file.name)
            self._chargecons.append(
                _FieldEntry(
                    quantity=quantity,
                    label="",
                    iteration=iteration,
                    path=zdf_file,
                    report_type=report_type,
                )
            )

    def _discover_species_dir(
        self, parent: Path, target: dict[str, dict[str, list[_FieldEntry]]]
    ) -> None:
        for sp_dir in parent.iterdir():
            if not sp_dir.is_dir():
                continue
            species = sp_dir.name
            sp_entries: dict[str, list[_FieldEntry]] = {}
            for raw_quantity, zdf_file in self._zdf_files_with_quant(sp_dir):
                quantity, report_type = _parse_quantity(raw_quantity)
                _, iteration = _parse_iter_file(zdf_file.name)
                sp_entries.setdefault(quantity, []).append(
                    _FieldEntry(
                        quantity=quantity,
                        label=species,
                        iteration=iteration,
                        path=zdf_file,
                        report_type=report_type,
                    )
                )
            target[species] = sp_entries

    def _discover_phasespace(self, pha_dir: Path) -> None:
        for ps_dir in pha_dir.iterdir():
            if not ps_dir.is_dir():
                continue
            ps_name = ps_dir.name
            for sp_dir in ps_dir.iterdir():
                if not sp_dir.is_dir():
                    continue
                species = sp_dir.name
                entries: list[_FieldEntry] = []
                for zdf_file in sorted(sp_dir.glob("*.zdf")):
                    quant_label, iteration = _parse_iter_file(zdf_file.name)
                    entries.append(
                        _FieldEntry(
                            quantity=quant_label,
                            label=species,
                            iteration=iteration,
                            path=zdf_file,
                        )
                    )
                self._phasespace.setdefault(ps_name, {})[species] = entries

    def _discover_raw(self, raw_dir: Path) -> None:
        for sp_dir in raw_dir.iterdir():
            if not sp_dir.is_dir():
                continue
            species = sp_dir.name
            entries: list[_FieldEntry] = []
            for data_file in sorted(
                list(sp_dir.glob("*.zdf")) + list(sp_dir.glob("*.h5"))
            ):
                quant_label, iteration = _parse_iter_file(data_file.name)
                entries.append(
                    _FieldEntry(
                        quantity=quant_label,
                        label=species,
                        iteration=iteration,
                        path=data_file,
                    )
                )
            self._raw[species] = entries

    def _discover_tracks(self, tracks_dir: Path) -> None:
        for data_file in sorted(
            list(tracks_dir.glob("*.zdf")) + list(tracks_dir.glob("*.h5"))
        ):
            self._tracks[data_file.stem] = data_file

    def _discover_wall(self, wall_dir: Path) -> None:
        for name_dir in wall_dir.iterdir():
            if not name_dir.is_dir():
                continue
            name = name_dir.name
            entries: list[_FieldEntry] = []
            for data_file in sorted(
                list(name_dir.glob("*.zdf")) + list(name_dir.glob("*.h5"))
            ):
                quant_label, iteration = _parse_iter_file(data_file.name)
                entries.append(
                    _FieldEntry(
                        quantity=quant_label,
                        label=name,
                        iteration=iteration,
                        path=data_file,
                    )
                )
            self._wall[name] = entries

    # ------------------------------------------------------------------
    # Listing methods
    # ------------------------------------------------------------------

    def list_fields(self) -> list[str]:
        """Return available field quantity names."""
        return sorted(self._fields.keys())

    def list_species(self) -> list[str]:
        """Return species names found across density, CELL_AVG, UDIST, RAW, ION."""
        species: set[str] = set()
        for d in (self._density, self._cell_avg, self._udist, self._raw, self._ion):
            species.update(d.keys())
        return sorted(species)

    def list_phasespaces(self) -> list[tuple[str, str]]:
        """Return available (ps_name, species) pairs."""
        result: list[tuple[str, str]] = []
        for ps_name in sorted(self._phasespace):
            for sp in sorted(self._phasespace[ps_name]):
                result.append((ps_name, sp))
        return result

    def list_raw_species(self) -> list[str]:
        """Return species that have raw particle dumps."""
        return sorted(self._raw.keys())

    def list_tracks(self) -> list[str]:
        """Return available track diagnostic names."""
        return sorted(self._tracks.keys())

    def list_history(self) -> list[str]:
        """Return available history file names."""
        return sorted(self._history.keys())

    def list_timings(self) -> list[str]:
        """Return available TIMINGS file names."""
        return sorted([p.name for p in self._timings])

    def list_iterations(
        self, quantity: str, report_type: str | None = None, *, step: int = 1
    ) -> list[int]:
        """Return available iteration numbers for a given field quantity.

        Parameters
        ----------
        quantity : str
            Field quantity name.
        report_type : str or None, optional
            Report modifier to filter by. If ``None`` (default), returns
            only plain entries (no modifier). Set to a specific modifier
            string (e.g. ``"savg"``) to filter.
        step : int
            Stride. ``step=5`` returns every 5th iteration. Default 1 = all.

        Returns
        -------
        list[int]
        """
        entries = self._fields.get(quantity, [])
        if report_type is None:
            entries = [e for e in entries if e.report_type == ""]
        else:
            entries = [e for e in entries if e.report_type == report_type]
        iters = sorted({e.iteration for e in entries})
        return iters[::step]

    @property
    def run_info(self) -> dict[str, str]:
        """Parse and return the contents of the run-info file."""
        info_path = self._path / "run-info"
        if not info_path.is_file():
            return {}

        result: dict[str, str] = {}
        with open(info_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if ":" in line:
                    key, _, value = line.partition(":")
                    result[key.strip()] = value.strip()
        return result

    # ------------------------------------------------------------------
    # Data accessors
    # ------------------------------------------------------------------

    def get_field(
        self, quantity: str, iteration: int, report_type: str | None = None
    ) -> GridData | None:
        """Read field diagnostic for given quantity and iteration.

        Parameters
        ----------
        quantity : str
            Field quantity name.
        iteration : int
            Iteration number.
        report_type : str or None, optional
            Report modifier to filter by. If ``None`` (default), returns
            only plain entries (no modifier). Set to a specific modifier
            string (e.g. ``"savg"``) to filter.

        Returns
        -------
        GridData or None
        """
        entries = self._fields.get(quantity, [])
        for e in entries:
            if e.iteration == iteration:
                if report_type is None:
                    if e.report_type == "":
                        return self._read_grid(e.path)
                elif e.report_type == report_type:
                    return self._read_grid(e.path)
        return None

    def get_density(
        self,
        species: str,
        quantity: str,
        iteration: int,
        report_type: str | None = None,
    ) -> GridData | None:
        """Read density diagnostic for given species, quantity, and iteration.

        Parameters
        ----------
        species : str
            Species name.
        quantity : str
            Quantity name.
        iteration : int
            Iteration number.
        report_type : str or None, optional
            Report modifier to filter by.

        Returns
        -------
        GridData or None
        """
        sp = self._density.get(species, {})
        entries = sp.get(quantity, [])
        for e in entries:
            if e.iteration == iteration:
                if report_type is None:
                    if e.report_type == "":
                        return self._read_grid(e.path)
                elif e.report_type == report_type:
                    return self._read_grid(e.path)
        return None

    def get_cell_avg(
        self,
        species: str,
        quantity: str,
        iteration: int,
        report_type: str | None = None,
    ) -> GridData | None:
        """Read cell-average diagnostic.

        Parameters
        ----------
        species : str
            Species name.
        quantity : str
            Quantity name.
        iteration : int
            Iteration number.
        report_type : str or None, optional
            Report modifier to filter by.

        Returns
        -------
        GridData or None
        """
        sp = self._cell_avg.get(species, {})
        entries = sp.get(quantity, [])
        for e in entries:
            if e.iteration == iteration:
                if report_type is None:
                    if e.report_type == "":
                        return self._read_grid(e.path)
                elif e.report_type == report_type:
                    return self._read_grid(e.path)
        return None

    def get_udist(
        self,
        species: str,
        quantity: str,
        iteration: int,
        report_type: str | None = None,
    ) -> GridData | None:
        """Read u-distribution diagnostic.

        Parameters
        ----------
        species : str
            Species name.
        quantity : str
            Quantity name.
        iteration : int
            Iteration number.
        report_type : str or None, optional
            Report modifier to filter by.

        Returns
        -------
        GridData or None
        """
        sp = self._udist.get(species, {})
        entries = sp.get(quantity, [])
        for e in entries:
            if e.iteration == iteration:
                if report_type is None:
                    if e.report_type == "":
                        return self._read_grid(e.path)
                elif e.report_type == report_type:
                    return self._read_grid(e.path)
        return None

    def get_phasespace(
        self, ps_name: str, species: str, iteration: int
    ) -> PhasespaceData | None:
        """Read phasespace diagnostic."""
        ps = self._phasespace.get(ps_name, {})
        entries = ps.get(species, [])
        for e in entries:
            if e.iteration == iteration:
                return self._read_phasespace(e.path)
        return None

    def get_raw(self, species: str, iteration: int) -> ParticleData | None:
        """Read raw particle dump for given species and iteration."""
        entries = self._raw.get(species, [])
        for e in entries:
            if e.iteration == iteration:
                return self._read_particle(e.path)
        return None

    def get_tracks(self, name: str) -> TrackData | None:
        """Read track diagnostic by name."""
        path = self._tracks.get(name)
        if path is None:
            return None
        return self._read_tracks(path)

    def get_history(self, name: str) -> HistoryData | None:
        """Read history text file by name."""
        path = self._history.get(name)
        if path is None:
            return None
        return _parse_history_file(path)

    def get_timings(self, name: str) -> TimingsData | None:
        """Read TIMINGS profiling file by name."""
        for p in self._timings:
            if p.name == name:
                return _parse_timings_file(p)
        return None

    @property
    def detected_format(self) -> str:
        """Detect the output file format: 'zdf', 'hdf5', 'mixed', or 'unknown'."""
        ms = self._path / "MS"
        if not ms.is_dir():
            return "unknown"
        zdf_files = list(ms.rglob("*.zdf"))
        h5_files = list(ms.rglob("*.h5"))
        if zdf_files and not h5_files:
            return "zdf"
        elif h5_files and not zdf_files:
            return "hdf5"
        elif zdf_files and h5_files:
            return "mixed"
        return "unknown"

    def get_chargecons(
        self, iteration: int, report_type: str | None = None
    ) -> GridData | None:
        """Read charge conservation diagnostic.

        Parameters
        ----------
        iteration : int
            Iteration number.
        report_type : str or None, optional
            Report modifier to filter by.

        Returns
        -------
        GridData or None
        """
        for e in self._chargecons:
            if e.iteration == iteration:
                if report_type is None:
                    if e.report_type == "":
                        return self._read_grid(e.path)
                elif e.report_type == report_type:
                    return self._read_grid(e.path)
        return None

    def get_wall(
        self, name: str, iteration: int, report_type: str | None = None
    ) -> GridData | None:
        """Read wall diagnostic by name and iteration.

        Parameters
        ----------
        name : str
            Wall diagnostic name.
        iteration : int
            Iteration number.
        report_type : str or None, optional
            Report modifier to filter by.

        Returns
        -------
        GridData or None
        """
        entries = self._wall.get(name, [])
        for e in entries:
            if e.iteration == iteration:
                if report_type is None:
                    if e.report_type == "":
                        return self._read_grid(e.path)
                elif e.report_type == report_type:
                    return self._read_grid(e.path)
        return None

    def get_ion(
        self,
        species: str,
        quantity: str,
        iteration: int,
        report_type: str | None = None,
    ) -> GridData | None:
        """Read ionization diagnostic.

        Parameters
        ----------
        species : str
            Species name.
        quantity : str
            Quantity name.
        iteration : int
            Iteration number.
        report_type : str or None, optional
            Report modifier to filter by.

        Returns
        -------
        GridData or None
        """
        sp = self._ion.get(species, {})
        entries = sp.get(quantity, [])
        for e in entries:
            if e.iteration == iteration:
                if report_type is None:
                    if e.report_type == "":
                        return self._read_grid(e.path)
                elif e.report_type == report_type:
                    return self._read_grid(e.path)
        return None

    # ------------------------------------------------------------------
    # Metadata-only accessors (lightweight — no data arrays loaded)
    # ------------------------------------------------------------------

    def info_field(self, quantity: str, iteration: int) -> FieldInfo | None:
        """Read field metadata without loading the data array.

        Fast metadata-only operation. Use before :meth:`get_field` to
        check shape, axes, and units without reading the full array.

        Parameters
        ----------
        quantity : str
            Field quantity name.
        iteration : int
            Iteration number.

        Returns
        -------
        FieldInfo or None
        """
        entries = self._fields.get(quantity, [])
        for e in entries:
            if e.iteration == iteration:
                try:
                    zdf_info = self._read_info(e.path)
                except (ValueError, OSError, FormatError, MissingDependencyError):
                    return None
                if zdf_info.grid is None:
                    return None
                gi = zdf_info.grid
                it = zdf_info.iteration
                axes = []
                if gi.has_axis:
                    for i, ax in enumerate(gi.axes):
                        axes.append(GridAxis(
                            name=ax.name, type=ax.axis_type,
                            min=ax.min, max=ax.max,
                            label=ax.label, units=ax.units,
                            npoints=gi.nx[i] if i < len(gi.nx) else 0,
                        ))
                return FieldInfo(
                    quantity=quantity,
                    iteration=it.n if it else 0,
                    time=it.t if it else 0.0,
                    label=gi.label,
                    units=gi.units,
                    ndim=gi.ndims,
                    shape=tuple(gi.nx),
                    axes=axes,
                    report_type=e.report_type,
                )
        return None

    def info_raw(self, species: str, iteration: int) -> ParticleInfo | None:
        """Read particle metadata without loading data arrays.

        Parameters
        ----------
        species : str
            Species name.
        iteration : int
            Iteration number.

        Returns
        -------
        ParticleInfo or None
        """
        entries = self._raw.get(species, [])
        for e in entries:
            if e.iteration == iteration:
                try:
                    zdf_info = self._read_info(e.path)
                except (ValueError, OSError, FormatError, MissingDependencyError):
                    return None
                if zdf_info.particles is None:
                    return None
                pi = zdf_info.particles
                it = zdf_info.iteration
                return ParticleInfo(
                    species=species,
                    iteration=it.n if it else 0,
                    time=it.t if it else 0.0,
                    label=pi.label,
                    nparts=pi.nparts,
                    quants=list(pi.quants),
                )
        return None

    def info_tracks(self, name: str) -> TrackInfo | None:
        """Read track metadata without loading data arrays.

        Parameters
        ----------
        name : str
            Track diagnostic name.

        Returns
        -------
        TrackInfo or None
        """
        path = self._tracks.get(name)
        if path is None:
            return None
        try:
            zdf_info = self._read_info(path)
        except (ValueError, OSError):
            return None
        if zdf_info.tracks is None:
            return None
        ti = zdf_info.tracks
        return TrackInfo(
            name=name,
            label=ti.label,
            ntracks=ti.ntracks,
            ndump=ti.ndump,
            niter=ti.niter,
            quants=list(ti.quants),
        )

    # ------------------------------------------------------------------
    # Internal data readers (ZDF and HDF5, dispatched by file extension)
    # ------------------------------------------------------------------

    @staticmethod
    def _read_info(path: Path):
        """Read metadata from a ZDF or HDF5 file. Returns ZdfFileInfo or raises."""
        if path.suffix == ".h5":
            from osiris_toolkit.io._reader_hdf5 import read_info as _read_fn
        else:
            from osiris_toolkit.io._reader import read_info as _read_fn
        return _read_fn(str(path))

    @staticmethod
    def _read_grid(path: Path) -> GridData | None:
        """Read a grid file (ZDF or HDF5) into a GridData object."""
        try:
            if path.suffix == ".h5":
                from osiris_toolkit.io._reader_hdf5 import read_grid as _read_grid_fn
            else:
                from osiris_toolkit.io._reader import read_grid as _read_grid_fn
            data, gi, it = _read_grid_fn(str(path))
        except (ValueError, OSError):
            return None
        axes = []
        if gi.has_axis:
            for i, ax in enumerate(gi.axes):
                axes.append(
                    GridAxis(
                        name=ax.name,
                        type=ax.axis_type,
                        min=ax.min,
                        max=ax.max,
                        label=ax.label,
                        units=ax.units,
                        npoints=gi.nx[i] if i < len(gi.nx) else 0,
                    )
                )
        return GridData(
            data=data,
            axes=axes,
            iteration=it.n,
            time=it.t,
            label=gi.label,
            units=gi.units,
        )

    @staticmethod
    def _read_particle(path: Path) -> ParticleData | None:
        """Read a particle file (ZDF or HDF5) into a ParticleData object."""
        try:
            if path.suffix == ".h5":
                from osiris_toolkit.io._reader_hdf5 import read_particles as _read_fn
            else:
                from osiris_toolkit.io._reader import read_particles as _read_fn
            data, pi, it = _read_fn(str(path))
        except (ValueError, OSError):
            return None
        return ParticleData(
            data=data,
            nparts=pi.nparts,
            iteration=it.n,
            time=it.t,
            label=pi.label,
        )

    @staticmethod
    def _read_phasespace(path: Path) -> PhasespaceData | None:
        """Read a phasespace file (ZDF or HDF5) into a PhasespaceData object."""
        try:
            if path.suffix == ".h5":
                from osiris_toolkit.io._reader_hdf5 import read_grid as _read_fn
            else:
                from osiris_toolkit.io._reader import read_grid as _read_fn
            data, gi, it = _read_fn(str(path))
        except (ValueError, OSError):
            return None
        axes: list[dict[str, str]] = []
        if gi.has_axis:
            for ax in gi.axes:
                axes.append(
                    {
                        "name": ax.name,
                        "label": ax.label,
                        "units": ax.units,
                        "min": str(ax.min),
                        "max": str(ax.max),
                    }
                )
        return PhasespaceData(
            data=data,
            axes=axes,
            iteration=it.n,
            time=it.t,
            deposited_quantity=gi.label,
        )

    @staticmethod
    def _read_tracks(path: Path) -> TrackData | None:
        """Read a tracks file (ZDF or HDF5) into a TrackData object."""
        try:
            if path.suffix == ".h5":
                from osiris_toolkit.io._reader_hdf5 import read_tracks as _read_fn
            else:
                from osiris_toolkit.io._reader import read_tracks as _read_fn
            tracks, ti = _read_fn(str(path))
        except (ValueError, OSError):
            return None
        return TrackData(
            tracks=tracks,
            quants=ti.quants,
            niter=ti.niter,
        )
