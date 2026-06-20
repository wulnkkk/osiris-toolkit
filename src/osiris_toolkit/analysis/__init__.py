"""Data analysis — statistical and physics-domain computations."""

from __future__ import annotations

from functools import cached_property

from osiris_toolkit.analysis.density import DensityAnalyzer
from osiris_toolkit.analysis.emf import EMFAnalyzer
from osiris_toolkit.analysis.kspace import KSpaceAnalyzer
from osiris_toolkit.analysis.phasespace import PhasespaceAnalyzer
from osiris_toolkit.analysis.scattering import ScatteringAnalyzer
from osiris_toolkit.analysis.species import SpeciesAnalyzer
from osiris_toolkit.analysis.stats import (
    describe,
    mean,
    minmax,
    rms,
    std,
    total_energy,
)
from osiris_toolkit.analysis.tracks import TracksAnalyzer
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units.converter import UnitSystem


class PostAnalysisHub:
    """Lazy-loading hub for all diagnostic analyzers.

    Parameters
    ----------
    sim : Simulation
    system : UnitSystem or None
    """

    def __init__(self, sim: Simulation, system: UnitSystem | None = None) -> None:
        self._sim = sim
        self._system = system

    @cached_property
    def emf(self) -> EMFAnalyzer:
        return EMFAnalyzer(self._sim, self._system)

    @cached_property
    def scattering(self) -> ScatteringAnalyzer:
        return ScatteringAnalyzer(self._sim, self._system)

    @cached_property
    def density(self) -> DensityAnalyzer:
        return DensityAnalyzer(self._sim, self._system)

    @cached_property
    def species(self) -> SpeciesAnalyzer:
        return SpeciesAnalyzer(self._sim, self._system)

    @cached_property
    def phasespace(self) -> PhasespaceAnalyzer:
        return PhasespaceAnalyzer(self._sim, self._system)

    @cached_property
    def kspace(self) -> KSpaceAnalyzer:
        return KSpaceAnalyzer(self._sim, self._system)

    @cached_property
    def tracks(self) -> TracksAnalyzer:
        return TracksAnalyzer(self._sim, self._system)


__all__ = [
    "DensityAnalyzer",
    "EMFAnalyzer",
    "KSpaceAnalyzer",
    "PhasespaceAnalyzer",
    "PostAnalysisHub",
    "ScatteringAnalyzer",
    "SpeciesAnalyzer",
    "TracksAnalyzer",
    "describe",
    "mean",
    "minmax",
    "rms",
    "std",
    "total_energy",
]
