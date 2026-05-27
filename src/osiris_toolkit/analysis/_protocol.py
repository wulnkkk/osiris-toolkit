"""Diagnostic analyzer protocol — abstract base for all OSIRIS diagnostic types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from osiris_toolkit.sim import Simulation
    from osiris_toolkit.units import UnitConverter


class DiagnosticAnalyzer(ABC):
    """Abstract base class for all diagnostic-type analyzers.

    Each subclass corresponds to one OSIRIS diagnostic kind (EMF, DENSITY,
    RAW, TRACKS, etc.).  The ABC enforces:

    * ``diagnostic_kind`` — the OSIRIS diagnostic name string
    * ``list_available`` — discover what quantities/species are available

    Subclasses are free to define their own analysis methods with
    diagnostic-specific signatures (e.g. ``field_energy(quantity, iteration)``
    vs ``density_profile(species, quantity, iteration, axis)``).
    """

    def __init__(self, sim: Simulation, converter: UnitConverter | None = None) -> None:
        self._sim = sim
        self._converter = converter

    @property
    @abstractmethod
    def diagnostic_kind(self) -> str:
        """OSIRIS diagnostic kind name, e.g. ``'EMF'``, ``'DENSITY'``."""
        ...

    @abstractmethod
    def list_available(self) -> list[str]:
        """Return names of quantities/species available for this diagnostic."""
        ...

    @property
    def sim(self) -> Simulation:
        """The bound Simulation object."""
        return self._sim

    @property
    def converter(self) -> UnitConverter | None:
        """The bound UnitConverter, if any."""
        return self._converter
