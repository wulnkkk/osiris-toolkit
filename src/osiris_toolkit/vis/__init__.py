"""Visualization — plotting routines for all OSIRIS diagnostic types."""

from __future__ import annotations

import warnings
from functools import cached_property
from pathlib import Path

from osiris_toolkit.exceptions import DataNotFoundError
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter
from osiris_toolkit.vis.animation import animate_field
from osiris_toolkit.vis.batch import process_simulation
from osiris_toolkit.vis.colormap import register_cmaps, symmetrical_colormap
from osiris_toolkit.vis.comparison import plot_difference, plot_overlay
from osiris_toolkit.vis.composite import plot_composite
from osiris_toolkit.vis.density import plot_density
from osiris_toolkit.vis.energy import plot_energy_timeline, plot_poynting, plot_spectrum
from osiris_toolkit.vis.energy_summary import (
    plot_energy_timeseries,
    plot_poynting_vector,
    plot_spectrum_colormap,
)
from osiris_toolkit.vis.field import plot_all_fields, plot_field
from osiris_toolkit.vis.kspace import plot_k_space
from osiris_toolkit.vis.phasespace import plot_phasespace
from osiris_toolkit.vis.raw import (
    plot_raw_energy_spectrum,
    plot_raw_momentum,
    plot_raw_phasespace,
    plot_raw_scatter,
)
from osiris_toolkit.vis.scattering import plot_scattering_fraction
from osiris_toolkit.vis.tracks import (
    plot_tracks_energy,
    plot_tracks_field,
    plot_tracks_orbit,
)


class PostVisHub:
    """Lazy-loading hub for all visualization sub-modules.

    Parameters
    ----------
    sim : Simulation
    converter : UnitConverter or None
    """

    def __init__(self, sim: Simulation, converter: UnitConverter | None = None) -> None:
        self._sim = sim
        self._converter = converter

    def invalidate_cache(self) -> None:
        """Clear all cached namespace properties.

        Call this after changing the simulation or converter so that
        the next access to ``.field``, ``.energy``, ``.raw``, or
        ``.tracks`` builds fresh objects.
        """
        for attr in ("field", "energy", "raw", "tracks"):
            self.__dict__.pop(attr, None)

    def set_converter(self, converter: UnitConverter) -> None:
        """Replace the unit converter and invalidate all cached namespaces."""
        self._converter = converter
        self.invalidate_cache()

    # -- field -----------------------------------------------------------

    def plot_field(self, quantity: str, iteration: int, **kwargs) -> Path | None:
        return plot_field(
            sim=self._sim, converter=self._converter,
            quantity=quantity, iteration=iteration, **kwargs,
        )

    def plot_all_fields(self, iteration: int, **kwargs) -> None:
        return plot_all_fields(
            sim=self._sim, converter=self._converter,
            iteration=iteration, **kwargs,
        )

    @cached_property
    def field(self):
        """Convenience namespace for field plotting."""
        return _FieldVis(self)

    # -- energy ----------------------------------------------------------

    plot_energy_timeline = staticmethod(plot_energy_timeline)
    plot_spectrum = staticmethod(plot_spectrum)
    plot_poynting = staticmethod(plot_poynting)

    @cached_property
    def energy(self):
        """Convenience namespace for energy/spectrum plotting."""
        return _EnergyVis(self)

    # -- raw particles ----------------------------------------------------

    @cached_property
    def raw(self):
        """Convenience namespace for RAW particle plotting."""
        return _RawVis(self)

    # -- tracks -----------------------------------------------------------

    @cached_property
    def tracks(self):
        """Convenience namespace for TRACKS trajectory plotting."""
        return _TracksVis(self)

    # -- density, phasespace, kspace -------------------------------------

    def plot_density(self, species: str, iteration: int, quantity: str = "charge", **kwargs) -> Path | None:
        return plot_density(
            sim=self._sim, converter=self._converter,
            species=species, iteration=iteration, quantity=quantity, **kwargs,
        )

    def plot_phasespace(self, ps_name: str, species: str, iteration: int, **kwargs) -> Path | None:
        return plot_phasespace(
            sim=self._sim, converter=self._converter,
            ps_name=ps_name, species=species, iteration=iteration, **kwargs,
        )

    def plot_k_space(self, quantity: str, iteration: int, **kwargs) -> Path | None:
        return plot_k_space(
            sim=self._sim, converter=self._converter,
            quantity=quantity, iteration=iteration, **kwargs,
        )

    def plot(self, kind: str, **kwargs) -> Path | None:
        """Generic plot by diagnostic kind name."""
        kind = kind.upper()
        if kind == "EMF":
            return plot_field(sim=self._sim, converter=self._converter, **kwargs)
        elif kind == "DENSITY":
            return plot_density(sim=self._sim, converter=self._converter, **kwargs)
        elif kind == "PHASESPACE":
            return plot_phasespace(sim=self._sim, converter=self._converter, **kwargs)
        elif kind == "KSPACE":
            return plot_k_space(sim=self._sim, converter=self._converter, **kwargs)
        else:
            quantity = kwargs.get("quantity")
            iteration = kwargs.get("iteration")
            if quantity and iteration is not None:
                return plot_field(
                    sim=self._sim, converter=self._converter,
                    quantity=quantity, iteration=iteration,
                    **{k: v for k, v in kwargs.items() if k not in ("quantity", "iteration")},
                )
            raise DataNotFoundError(f"Unknown diagnostic kind {kind!r}")


class _FieldVis:
    def __init__(self, hub: PostVisHub) -> None:
        self._hub = hub

    def plot(self, quantity: str, iteration: int, **kwargs) -> Path | None:
        return self._hub.plot_field(quantity=quantity, iteration=iteration, **kwargs)

    def plot_all(self, iteration: int, **kwargs) -> None:
        return self._hub.plot_all_fields(iteration=iteration, **kwargs)


class _EnergyVis:
    def __init__(self, hub: PostVisHub) -> None:
        self._hub = hub

    def timeline(self, results, **kwargs) -> Path | None:
        return plot_energy_timeline(results, **kwargs)

    def spectrum(self, result, **kwargs) -> Path | None:
        return plot_spectrum(result, **kwargs)

    def poynting(self, result, component="s1", **kwargs) -> Path | None:
        return plot_poynting(result, component=component, **kwargs)


class _RawVis:
    """RAW particle visualization namespace."""

    def __init__(self, hub: PostVisHub) -> None:
        self._hub = hub

    def scatter(self, species: str, iteration: int, **kwargs) -> Path | None:
        raw = self._hub._sim.get_raw(species, iteration)
        if raw is None:
            raise DataNotFoundError(
                f"No raw particle data for species '{species}' at iteration {iteration}"
            )
        return plot_raw_scatter(raw, **kwargs)

    def momentum(self, species: str, iteration: int, **kwargs) -> Path | None:
        raw = self._hub._sim.get_raw(species, iteration)
        if raw is None:
            raise DataNotFoundError(
                f"No raw particle data for species '{species}' at iteration {iteration}"
            )
        return plot_raw_momentum(raw, **kwargs)

    def phasespace(self, species: str, iteration: int, **kwargs) -> Path | None:
        raw = self._hub._sim.get_raw(species, iteration)
        if raw is None:
            raise DataNotFoundError(
                f"No raw particle data for species '{species}' at iteration {iteration}"
            )
        return plot_raw_phasespace(raw, **kwargs)

    def energy_spectrum(self, species: str, iteration: int, **kwargs) -> Path | None:
        raw = self._hub._sim.get_raw(species, iteration)
        if raw is None:
            raise DataNotFoundError(
                f"No raw particle data for species '{species}' at iteration {iteration}"
            )
        return plot_raw_energy_spectrum(raw, **kwargs)


class _TracksVis:
    """TRACKS trajectory visualization namespace."""

    def __init__(self, hub: PostVisHub) -> None:
        self._hub = hub

    def orbit(self, name: str, **kwargs) -> Path | None:
        td = self._hub._sim.get_tracks(name)
        if td is None:
            raise DataNotFoundError(f"No track data for '{name}'")
        return plot_tracks_orbit(td, **kwargs)

    def energy(self, name: str, **kwargs) -> Path | None:
        td = self._hub._sim.get_tracks(name)
        if td is None:
            raise DataNotFoundError(f"No track data for '{name}'")
        return plot_tracks_energy(td, **kwargs)

    def field(self, name: str, field_component: str, **kwargs) -> Path | None:
        td = self._hub._sim.get_tracks(name)
        if td is None:
            raise DataNotFoundError(f"No track data for '{name}'")
        return plot_tracks_field(td, field_component, **kwargs)


class VisEngine:
    """DEPRECATED: Use ``PostProcessor`` from ``osiris_toolkit.postproc``.

    Kept for backward compatibility. Will be removed in a future version.
    """

    def __init__(
        self,
        sim: Simulation,
        converter: UnitConverter | None = None,
    ) -> None:
        warnings.warn(
            "VisEngine is deprecated. Use PostProcessor from osiris_toolkit.postproc.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._sim = sim
        self._converter = converter
        self._hub = PostVisHub(sim, converter)

    @property
    def converter(self) -> UnitConverter | None:
        return self._converter

    def plot(self, kind: str, **kwargs) -> Path | None:
        return self._hub.plot(kind, **kwargs)

    def plot_field(self, quantity: str, iteration: int, **kwargs) -> Path | None:
        return self._hub.plot_field(quantity=quantity, iteration=iteration, **kwargs)

    def plot_density(self, species: str, iteration: int, quantity: str = "charge", **kwargs) -> Path | None:
        return self._hub.plot_density(species=species, iteration=iteration, quantity=quantity, **kwargs)

    def plot_phasespace(self, ps_name: str, species: str, iteration: int, **kwargs) -> Path | None:
        return self._hub.plot_phasespace(ps_name=ps_name, species=species, iteration=iteration, **kwargs)

    def plot_k_space(self, quantity: str, iteration: int, **kwargs) -> Path | None:
        return self._hub.plot_k_space(quantity=quantity, iteration=iteration, **kwargs)

    def plot_composite(self, iteration: int, **kwargs) -> Path | None:
        return plot_composite(
            sim=self._sim, converter=self._converter,
            iteration=iteration, **kwargs,
        )

    def batch(
        self, sim_name: str, output_root=None, x_unit="um", y_unit="um",
        time_unit="ps", max_workers=None,
    ) -> None:
        return process_simulation(
            sim_path=str(self._sim.path),
            sim_name=sim_name,
            output_root=output_root,
            x_unit=x_unit,
            y_unit=y_unit,
            time_unit=time_unit,
            max_workers=max_workers,
        )


__all__ = [
    "VisEngine",
    "PostVisHub",
    "animate_field",
    "plot_field",
    "plot_all_fields",
    "plot_density",
    "plot_phasespace",
    "plot_composite",
    "plot_k_space",
    "plot_scattering_fraction",
    "plot_difference",
    "plot_overlay",
    "plot_energy_timeline",
    "plot_energy_timeseries",
    "plot_spectrum",
    "plot_spectrum_colormap",
    "plot_poynting",
    "plot_poynting_vector",
    "plot_raw_energy_spectrum",
    "plot_raw_momentum",
    "plot_raw_phasespace",
    "plot_raw_scatter",
    "plot_tracks_energy",
    "plot_tracks_field",
    "plot_tracks_orbit",
    "process_simulation",
    "register_cmaps",
    "symmetrical_colormap",
]
