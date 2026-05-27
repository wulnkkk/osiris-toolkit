"""PostProcessor — unified entry point for analysis and visualization."""

from __future__ import annotations

from functools import cached_property

from osiris_toolkit.analysis import PostAnalysisHub
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units import UnitConverter
from osiris_toolkit.vis import PostVisHub


class PostProcessor:
    """Unified post-processing entry point bound to a Simulation.

    Provides ``.analyze`` for numerical analysis and ``.vis`` for plotting.

    Parameters
    ----------
    sim : Simulation
        The loaded simulation output.
    converter : UnitConverter or None
        Unit converter. Auto-created from sim if available.

    Examples
    --------
    >>> from osiris_toolkit import Simulation
    >>> from osiris_toolkit.postproc import PostProcessor
    >>> sim = Simulation("/path/to/output")
    >>> pp = PostProcessor(sim)

    >>> # Analysis
    >>> result = pp.analyze.emf.field_energy("e1", iteration=50)
    >>> print(result.total_energy)

    >>> # Visualization
    >>> pp.vis.field.plot("e1", iteration=50, x_unit="um")

    >>> # Batch
    >>> pp.batch(sim_name="run_01")
    """

    def __init__(
        self,
        sim: Simulation,
        converter: UnitConverter | None = None,
    ) -> None:
        self._sim = sim
        self._converter = converter

    @cached_property
    def analyze(self) -> PostAnalysisHub:
        """Numerical analysis hub — all diagnostic analyzers."""
        return PostAnalysisHub(self._sim, self._converter)

    @cached_property
    def vis(self) -> PostVisHub:
        """Visualization hub — all plotting functions."""
        return PostVisHub(self._sim, self._converter)

    def batch(
        self,
        sim_name: str,
        output_root: str | None = None,
        x_unit: str = "um",
        y_unit: str = "um",
        time_unit: str = "ps",
        max_workers: int | None = None,
    ) -> None:
        """Batch-process all diagnostic types (fields, k-space, density, scattering).

        Parameters
        ----------
        sim_name : str
            Human-readable name for the output subdirectory.
        output_root : str or None
            Root directory for all output. Defaults to sim's figures dir.
        x_unit, y_unit : str
            Spatial axis units.
        time_unit : str
            Time unit for titles.
        max_workers : int or None
            Number of parallel workers.
        """
        from osiris_toolkit.vis.batch import process_simulation

        process_simulation(
            sim_path=str(self._sim.path),
            sim_name=sim_name,
            output_root=output_root,
            x_unit=x_unit,
            y_unit=y_unit,
            time_unit=time_unit,
            max_workers=max_workers,
        )
