"""Visualization — plotting routines for all OSIRIS diagnostic types."""

from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure

from osiris_toolkit.sim import Simulation
from osiris_toolkit.sim.catalog import OSIRIS_DIAGNOSTICS
from osiris_toolkit.units import UnitConverter
from osiris_toolkit.vis.batch import process_simulation
from osiris_toolkit.vis.composite import plot_composite
from osiris_toolkit.vis.density import plot_density
from osiris_toolkit.vis.field import plot_all_fields, plot_field
from osiris_toolkit.vis.kspace import plot_k_space
from osiris_toolkit.vis.phasespace import plot_phasespace
from osiris_toolkit.vis.scattering import analyze_scattering, plot_scattering_fraction


class VisEngine:
    """Unified visualization entry point bound to a Simulation.

    Provides sub-plotters for each diagnostic type and a generic
    ``plot()`` method for agent-friendly access.

    Parameters
    ----------
    sim : Simulation
        The loaded simulation output.
    converter : UnitConverter | None
        Unit converter. Auto-created from sim's bound deck if available.

    Examples
    --------
    >>> from osiris_toolkit import Simulation
    >>> from osiris_toolkit.vis import VisEngine
    >>> sim = Simulation("/path/to/output")
    >>> vis = VisEngine(sim)
    >>> vis.plot("EMF", quantity="e1", iteration=50, x_unit="um")
    """

    def __init__(
        self,
        sim: Simulation,
        converter: UnitConverter | None = None,
    ) -> None:
        self._sim = sim
        self._converter = converter

    @property
    def converter(self) -> UnitConverter | None:
        return self._converter

    # -- generic agent-friendly interface -------------------------------

    def plot(self, kind: str, **kwargs) -> Figure | None:
        """Plot a diagnostic type with keyword arguments.

        Parameters
        ----------
        kind : str
            Diagnostic kind name (e.g. "EMF", "DENSITY", "PHASESPACE").
        **kwargs
            Passed to the specific plotting function. Common keys:
            quantity, iteration, species, x_unit, y_unit, output.
        """
        kind = kind.upper()
        if kind == "EMF":
            return plot_field(sim_path=str(self._sim._path), **kwargs)
        elif kind == "DENSITY":
            return plot_density(sim_path=str(self._sim._path), **kwargs)
        elif kind == "PHASESPACE":
            return plot_phasespace(sim_path=str(self._sim._path), **kwargs)
        elif kind == "KSPACE":
            return plot_k_space(sim_path=str(self._sim._path), **kwargs)
        else:
            # Generic: try to read the diagnostic kind directly
            diag_kind = OSIRIS_DIAGNOSTICS.get(kind)
            if diag_kind is None:
                raise ValueError(
                    f"Unknown diagnostic kind {kind!r}. "
                    f"Known: {sorted(OSIRIS_DIAGNOSTICS)}"
                )
            # Fallback to field plot for grid-based diagnostics
            quantity = kwargs.get("quantity")
            iteration = kwargs.get("iteration")
            if quantity and iteration is not None:
                return plot_field(
                    sim_path=str(self._sim._path),
                    quantity=quantity,
                    iteration=iteration,
                    **{k: v for k, v in kwargs.items() if k not in ("quantity", "iteration")},
                )
            raise ValueError(
                "quantity and iteration are required for generic plot"
            )

    # -- convenience shortcuts ------------------------------------------

    def plot_field(self, quantity: str, iteration: int, **kwargs) -> Figure | None:
        return plot_field(
            sim_path=str(self._sim._path),
            quantity=quantity,
            iteration=iteration,
            **kwargs,
        )

    def plot_density(
        self, species: str, iteration: int, quantity: str = "charge", **kwargs
    ) -> Figure | None:
        return plot_density(
            sim_path=str(self._sim._path),
            species=species,
            iteration=iteration,
            quantity=quantity,
            **kwargs,
        )

    def plot_phasespace(
        self, ps_name: str, species: str, iteration: int, **kwargs
    ) -> Figure | None:
        return plot_phasespace(
            sim_path=str(self._sim._path),
            ps_name=ps_name,
            species=species,
            iteration=iteration,
            **kwargs,
        )

    def plot_k_space(
        self, quantity: str, iteration: int, **kwargs
    ) -> Figure | None:
        return plot_k_space(
            sim_path=str(self._sim._path),
            quantity=quantity,
            iteration=iteration,
            **kwargs,
        )

    def plot_composite(self, iteration: int, **kwargs) -> Figure | None:
        return plot_composite(
            sim_path=str(self._sim._path),
            iteration=iteration,
            **kwargs,
        )

    def batch(
        self,
        sim_name: str,
        output_root: str | Path,
        x_unit: str = "um",
        y_unit: str = "um",
        time_unit: str = "ps",
    ) -> None:
        """Batch-process all diagnostic types.

        Parameters
        ----------
        sim_name : str
            Human-readable name used for the output subdirectory.
        output_root : str or Path
            Root directory for all output.
        x_unit, y_unit : str
            Spatial axis units.
        time_unit : str
            Time unit for titles.
        """
        return process_simulation(
            sim_path=str(self._sim._path),
            sim_name=sim_name,
            output_root=output_root,
            x_unit=x_unit,
            y_unit=y_unit,
            time_unit=time_unit,
        )


__all__ = [
    "VisEngine",
    "plot_field",
    "plot_all_fields",
    "plot_density",
    "plot_phasespace",
    "plot_composite",
    "plot_k_space",
    "analyze_scattering",
    "plot_scattering_fraction",
    "process_simulation",
]
