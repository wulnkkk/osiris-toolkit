"""Metadata info accessor mixin for Simulation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from osiris_toolkit._models import (
    FieldInfo,
    GridAxis,
    ParticleInfo,
    TrackInfo,
)
from osiris_toolkit.exceptions import FormatError, MissingDependencyError


class _InfoAccessors:
    """Mixin providing metadata-only accessors (no data loaded)."""

    _fields: dict[str, Any]
    _raw: dict[str, Any]
    _tracks: dict[str, Any]

    @staticmethod
    def _read_info(path: Path):
        """Read metadata from a ZDF or HDF5 file. Returns ZdfFileInfo or raises."""
        if path.suffix == ".h5":
            from osiris_toolkit.io._reader_hdf5 import read_info as _read_fn
        else:
            from osiris_toolkit.io._reader import read_info as _read_fn
        return _read_fn(str(path))

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
