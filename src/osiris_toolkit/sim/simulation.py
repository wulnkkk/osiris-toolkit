"""Simulation data access layer — directory discovery and typed accessors.

Traverses an OSIRIS simulation output directory tree and provides typed
accessors for all diagnostic types (fields, density, phasespace, raw
particles, tracks, history, etc.).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from osiris_toolkit.io._reader import read_grid, read_particles, read_tracks
from osiris_toolkit.sim.diagnostics import (
    GridAxis,
    GridData,
    HistoryData,
    ParticleData,
    PhasespaceData,
    TrackData,
)

# ---------------------------------------------------------------------------
# Naming convention: {quant}[-{label}]-{iter:06d}.zdf
# ---------------------------------------------------------------------------
_ITER_FILE_RE = re.compile(r"^(.+)-(\d{6})\.zdf$")


def _parse_iter_file(filename: str) -> tuple[str, int]:
    """Parse quantity/label and iteration number from a ZDF filename.

    Returns (quant_label, iteration). quant_label may include species
    or phasespace names separated by '-'.
    """
    m = _ITER_FILE_RE.match(filename)
    if m is None:
        raise ValueError(f"Unexpected ZDF filename format: {filename}")
    return m.group(1), int(m.group(2))


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


# ---------------------------------------------------------------------------
# Internal entry types
# ---------------------------------------------------------------------------


@dataclass
class _FieldEntry:
    quantity: str
    label: str
    iteration: int
    path: Path


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
    """Access OSIRIS simulation output by diagnostic type.

    Parameters
    ----------
    path : str or Path
        Path to the simulation output directory (containing MS/, HIST/,
        TIMINGS/, and run-info).
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        if not self._path.is_dir():
            raise NotADirectoryError(f"Not a directory: {self._path}")

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
        """Return .zdf files in *dir_path*, supporting flat and nested layouts.

        Flat:   dir/*-000000.zdf
        Nested: dir/<quant>/*-000000.zdf
        """
        flat = list(dir_path.glob("*.zdf"))
        if flat:
            return sorted(flat)
        return sorted(dir_path.glob("*/*.zdf"))

    @staticmethod
    def _zdf_files_with_quant(dir_path: Path) -> list[tuple[str, Path]]:
        """Return (quantity, file_path) pairs.

        Discovers quantity from subdirectory name (nested layout)
        or filename prefix (flat layout).
        """
        flat = list(dir_path.glob("*.zdf"))
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
            for f in sorted(quant_dir.glob("*.zdf")):
                result.append((quant_dir.name, f))
        return result

    def _discover_fld(self, fld_dir: Path) -> None:
        for quantity, zdf_file in self._zdf_files_with_quant(fld_dir):
            _, iteration = _parse_iter_file(zdf_file.name)
            self._fields.setdefault(quantity, []).append(
                _FieldEntry(
                    quantity=quantity,
                    label="",
                    iteration=iteration,
                    path=zdf_file,
                )
            )

    def _discover_chargecons(self, cc_dir: Path) -> None:
        for quantity, zdf_file in self._zdf_files_with_quant(cc_dir):
            _, iteration = _parse_iter_file(zdf_file.name)
            self._chargecons.append(
                _FieldEntry(
                    quantity=quantity,
                    label="",
                    iteration=iteration,
                    path=zdf_file,
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
            for quantity, zdf_file in self._zdf_files_with_quant(sp_dir):
                _, iteration = _parse_iter_file(zdf_file.name)
                sp_entries.setdefault(quantity, []).append(
                    _FieldEntry(
                        quantity=quantity,
                        label=species,
                        iteration=iteration,
                        path=zdf_file,
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
            self._raw[species] = entries

    def _discover_tracks(self, tracks_dir: Path) -> None:
        for zdf_file in sorted(tracks_dir.glob("*.zdf")):
            self._tracks[zdf_file.stem] = zdf_file

    def _discover_wall(self, wall_dir: Path) -> None:
        for name_dir in wall_dir.iterdir():
            if not name_dir.is_dir():
                continue
            name = name_dir.name
            entries: list[_FieldEntry] = []
            for zdf_file in sorted(name_dir.glob("*.zdf")):
                quant_label, iteration = _parse_iter_file(zdf_file.name)
                entries.append(
                    _FieldEntry(
                        quantity=quant_label,
                        label=name,
                        iteration=iteration,
                        path=zdf_file,
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

    def list_iterations(self, quantity: str) -> list[int]:
        """Return available iteration numbers for a given field quantity."""
        entries = self._fields.get(quantity, [])
        return [e.iteration for e in entries]

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

    def get_field(self, quantity: str, iteration: int) -> GridData | None:
        """Read field diagnostic for given quantity and iteration."""
        entries = self._fields.get(quantity, [])
        for e in entries:
            if e.iteration == iteration:
                return self._read_grid_zdf(e.path)
        return None

    def get_density(
        self, species: str, quantity: str, iteration: int
    ) -> GridData | None:
        """Read density diagnostic for given species, quantity, and iteration."""
        sp = self._density.get(species, {})
        entries = sp.get(quantity, [])
        for e in entries:
            if e.iteration == iteration:
                return self._read_grid_zdf(e.path)
        return None

    def get_cell_avg(
        self, species: str, quantity: str, iteration: int
    ) -> GridData | None:
        """Read cell-average diagnostic."""
        sp = self._cell_avg.get(species, {})
        entries = sp.get(quantity, [])
        for e in entries:
            if e.iteration == iteration:
                return self._read_grid_zdf(e.path)
        return None

    def get_udist(
        self, species: str, quantity: str, iteration: int
    ) -> GridData | None:
        """Read u-distribution diagnostic."""
        sp = self._udist.get(species, {})
        entries = sp.get(quantity, [])
        for e in entries:
            if e.iteration == iteration:
                return self._read_grid_zdf(e.path)
        return None

    def get_phasespace(
        self, ps_name: str, species: str, iteration: int
    ) -> PhasespaceData | None:
        """Read phasespace diagnostic."""
        ps = self._phasespace.get(ps_name, {})
        entries = ps.get(species, [])
        for e in entries:
            if e.iteration == iteration:
                return self._read_phasespace_zdf(e.path)
        return None

    def get_raw(self, species: str, iteration: int) -> ParticleData | None:
        """Read raw particle dump for given species and iteration."""
        entries = self._raw.get(species, [])
        for e in entries:
            if e.iteration == iteration:
                return self._read_particle_zdf(e.path)
        return None

    def get_tracks(self, name: str) -> TrackData | None:
        """Read track diagnostic by name."""
        path = self._tracks.get(name)
        if path is None:
            return None
        return self._read_tracks_zdf(path)

    def get_history(self, name: str) -> HistoryData | None:
        """Read history text file by name."""
        path = self._history.get(name)
        if path is None:
            return None
        return _parse_history_file(path)

    def get_chargecons(self, iteration: int) -> GridData | None:
        """Read charge conservation diagnostic."""
        for e in self._chargecons:
            if e.iteration == iteration:
                return self._read_grid_zdf(e.path)
        return None

    def get_wall(self, name: str, iteration: int) -> GridData | None:
        """Read wall diagnostic by name and iteration."""
        entries = self._wall.get(name, [])
        for e in entries:
            if e.iteration == iteration:
                return self._read_grid_zdf(e.path)
        return None

    def get_ion(
        self, species: str, quantity: str, iteration: int
    ) -> GridData | None:
        """Read ionization diagnostic."""
        sp = self._ion.get(species, {})
        entries = sp.get(quantity, [])
        for e in entries:
            if e.iteration == iteration:
                return self._read_grid_zdf(e.path)
        return None

    # ------------------------------------------------------------------
    # Internal ZDF readers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_grid_zdf(path: Path) -> GridData | None:
        try:
            data, gi, it = read_grid(str(path))
        except (ValueError, OSError):
            return None
        axes = []
        if gi.has_axis:
            for ax in gi.axes:
                axes.append(
                    GridAxis(
                        name=ax.name,
                        type=ax.axis_type,
                        min=ax.min,
                        max=ax.max,
                        label=ax.label,
                        units=ax.units,
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
    def _read_particle_zdf(path: Path) -> ParticleData | None:
        try:
            data, pi, it = read_particles(str(path))
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
    def _read_phasespace_zdf(path: Path) -> PhasespaceData | None:
        try:
            data, gi, it = read_grid(str(path))
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
    def _read_tracks_zdf(path: Path) -> TrackData | None:
        try:
            tracks, ti = read_tracks(str(path))
        except (ValueError, OSError):
            return None
        return TrackData(
            tracks=tracks,
            quants=ti.quants,
            niter=ti.niter,
        )
