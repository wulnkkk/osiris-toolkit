"""Tests for LazySimulation and list_iterations step parameter."""

from unittest.mock import MagicMock


class TestListIterationsStep:
    """Test Simulation.list_iterations(step=...)"""

    def test_step_returns_subset(self):
        """step=3 returns every 3rd iteration."""
        from osiris_toolkit.sim.simulation import Simulation

        mock_sim = MagicMock(spec=Simulation)
        entries = [MagicMock(iteration=i, report_type="") for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]
        mock_sim._fields = {"e1": entries}

        from osiris_toolkit.sim import simulation as sim_mod

        orig = sim_mod.Simulation.list_iterations
        result = orig(mock_sim, "e1", step=3)
        assert result == [0, 3, 6, 9]

    def test_step_default_is_1(self):
        """step=1 (default) returns all iterations."""
        from osiris_toolkit.sim.simulation import Simulation

        mock_sim = MagicMock(spec=Simulation)
        entries = [MagicMock(iteration=i, report_type="") for i in [0, 1, 2]]
        mock_sim._fields = {"e1": entries}

        from osiris_toolkit.sim import simulation as sim_mod

        orig = sim_mod.Simulation.list_iterations
        result = orig(mock_sim, "e1")
        assert result == [0, 1, 2]


class TestLazySimulation:
    """Test LazySimulation wrapper."""

    def test_list_iterations_with_step(self):
        """LazySimulation.list_iterations returns step-subsampled list."""
        from osiris_toolkit.sim._lazy import LazySimulation

        mock_sim = MagicMock()
        mock_sim.list_iterations.side_effect = lambda quantity, step=1: [0, 1, 2, 3, 4, 5][::step]

        lazy = LazySimulation(mock_sim, step=2)
        result = lazy.list_iterations("e1")
        assert result == [0, 2, 4]
        mock_sim.list_iterations.assert_called_once_with("e1", step=2)

    def test_delegates_other_methods(self):
        """LazySimulation delegates get_field etc. to underlying sim."""
        from osiris_toolkit.sim._lazy import LazySimulation

        mock_sim = MagicMock()
        lazy = LazySimulation(mock_sim, step=3)

        lazy.get_field("e1", 0)
        mock_sim.get_field.assert_called_once_with("e1", 0)

    def test_step_property(self):
        """LazySimulation.step returns the stride."""
        from osiris_toolkit.sim._lazy import LazySimulation

        mock_sim = MagicMock()
        lazy = LazySimulation(mock_sim, step=5)
        assert lazy.step == 5
