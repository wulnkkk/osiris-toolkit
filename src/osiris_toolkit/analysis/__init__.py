"""Data analysis — statistical and physics-domain computations."""

from osiris_toolkit.analysis.emf import EMFAnalyzer
from osiris_toolkit.analysis.species import SpeciesAnalyzer
from osiris_toolkit.analysis.stats import (
    describe,
    mean,
    minmax,
    rms,
    std,
    total_energy,
)
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter


class Analyzer:
    """Unified analysis entry point bound to a Simulation.

    Provides sub-analyzers for each diagnostic type with auto-discovery
    of available data.

    Parameters
    ----------
    sim : Simulation
        The loaded simulation output directory.
    converter : UnitConverter | None
        Unit converter. If None and sim has a bound deck, one is
        auto-created.

    Examples
    --------
    >>> from osiris_toolkit import Simulation, Analyzer
    >>> sim = Simulation("/path/to/output")
    >>> ana = Analyzer(sim)
    >>> ana.emf.total_em_energy(iteration=50)
    >>> ana.species.density_profile("electrons", "charge", iteration=50)
    """

    def __init__(
        self,
        sim: Simulation,
        converter: UnitConverter | None = None,
    ) -> None:
        self._sim = sim
        self._converter = converter

    @property
    def emf(self) -> EMFAnalyzer:
        """EMF-specific analysis."""
        return EMFAnalyzer(self._sim, self._converter)

    @property
    def species(self) -> SpeciesAnalyzer:
        """Species and density analysis."""
        return SpeciesAnalyzer(self._sim, self._converter)

    # Convenience statics (no converter needed)
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
    "describe",
    "mean",
    "minmax",
    "rms",
    "std",
    "total_energy",
]
