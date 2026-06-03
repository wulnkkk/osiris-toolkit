"""Data analysis — statistical and physics-domain computations."""

from __future__ import annotations

import warnings
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
from osiris_toolkit.units import UnitConverter


class PostAnalysisHub:
    """Lazy-loading hub for all diagnostic analyzers.

    Parameters
    ----------
    sim : Simulation
    converter : UnitConverter or None
    """

    def __init__(self, sim: Simulation, converter: UnitConverter | None = None) -> None:
        self._sim = sim
        self._converter = converter

    @cached_property
    def emf(self) -> EMFAnalyzer:
        return EMFAnalyzer(self._sim, self._converter)

    @cached_property
    def scattering(self) -> ScatteringAnalyzer:
        return ScatteringAnalyzer(self._sim, self._converter)

    @cached_property
    def density(self) -> DensityAnalyzer:
        return DensityAnalyzer(self._sim, self._converter)

    @cached_property
    def species(self) -> SpeciesAnalyzer:
        return SpeciesAnalyzer(self._sim, self._converter)

    @cached_property
    def phasespace(self) -> PhasespaceAnalyzer:
        return PhasespaceAnalyzer(self._sim, self._converter)

    @cached_property
    def kspace(self) -> KSpaceAnalyzer:
        return KSpaceAnalyzer(self._sim, self._converter)

    @cached_property
    def tracks(self) -> TracksAnalyzer:
        return TracksAnalyzer(self._sim, self._converter)


class Analyzer:
    """DEPRECATED: Use ``PostProcessor`` from ``osiris_toolkit.postproc`` instead.

    This class is kept for backward compatibility and will be removed in a
    future version.
    """

    def __init__(
        self,
        sim: Simulation,
        converter: UnitConverter | None = None,
    ) -> None:
        warnings.warn(
            "Analyzer is deprecated. Use PostProcessor from osiris_toolkit.postproc.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._sim = sim
        self._converter = converter

    @property
    def emf(self) -> EMFAnalyzer:
        return EMFAnalyzer(self._sim, self._converter)

    @property
    def species(self) -> SpeciesAnalyzer:
        return SpeciesAnalyzer(self._sim, self._converter)

    describe = staticmethod(describe)
    mean = staticmethod(mean)
    rms = staticmethod(rms)
    std = staticmethod(std)
    minmax = staticmethod(minmax)
    total_energy = staticmethod(total_energy)


__all__ = [
    "Analyzer",
    "EMFAnalyzer",
    "SpeciesAnalyzer",
    "DensityAnalyzer",
    "ScatteringAnalyzer",
    "KSpaceAnalyzer",
    "PhasespaceAnalyzer",
    "TracksAnalyzer",
    "PostAnalysisHub",
    "describe",
    "mean",
    "minmax",
    "rms",
    "std",
    "total_energy",
]
