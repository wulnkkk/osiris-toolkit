"""Simulation data access layer — directory discovery and simulation model.

Traverses an OSIRIS simulation output directory tree and provides typed
accessors for all diagnostic types via :class:`_DataAccessors` and
:class:`_InfoAccessors` mixins.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from osiris_toolkit.config import OsirisConfig

from osiris_toolkit.sim._accessors import _DataAccessors
from osiris_toolkit.sim._info import _InfoAccessors
from osiris_toolkit.sim._parse import (
    _parse_iter_file,
    _parse_quantity,
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


class Simulation(_DataAccessors, _InfoAccessors):
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

