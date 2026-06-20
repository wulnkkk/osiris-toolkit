"""Data accessor mixin for Simulation."""

from __future__ import annotations

from pathlib import Path

from osiris_toolkit._models import (
    GridAxis,
    GridData,
    HistoryData,
    ParticleData,
    PhasespaceData,
    TimingsData,
    TrackData,
)
from osiris_toolkit.sim._parse import (
    _parse_history_file,
    _parse_timings_file,
)


class _DataAccessors:
    """Mixin providing typed data accessors for all OSIRIS diagnostic types."""

    # -- Listing methods ----------------------------------------------------

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

    def list_iterations(self, quantity: str, report_type: str | None = None, *, step: int = 1) -> list[int]:
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

    # -- Field accessors ----------------------------------------------------

    def get_field(self, quantity: str, iteration: int, report_type: str | None = None) -> GridData | None:
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

    def get_phasespace(self, ps_name: str, species: str, iteration: int) -> PhasespaceData | None:
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

    def get_chargecons(self, iteration: int, report_type: str | None = None) -> GridData | None:
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

    def get_wall(self, name: str, iteration: int, report_type: str | None = None) -> GridData | None:
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

    # -- Internal readers ----------------------------------------------------

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
