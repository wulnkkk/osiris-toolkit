"""LazySimulation — iteration-subsampling wrapper for Simulation."""

from __future__ import annotations


class LazySimulation:
    """Wrapper that subsamples iterations of a Simulation.

    Parameters
    ----------
    sim : Simulation
        The underlying Simulation.
    step : int
        Iteration stride. ``step=5`` → every 5th iteration.
    """

    def __init__(self, sim, step: int = 1):
        self._sim = sim
        self.step = step

    def list_iterations(self, quantity: str) -> list[int]:
        """Return subsampled iteration list using ``self.step``."""
        return self._sim.list_iterations(quantity, step=self.step)

    def __getattr__(self, name: str):
        return getattr(self._sim, name)
