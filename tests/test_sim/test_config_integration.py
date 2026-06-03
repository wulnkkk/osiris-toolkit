"""Tests for Simulation config integration."""

from pathlib import Path


def test_simulation_inherits_global_config(tmp_path):
    """Simulation without explicit config inherits from OsirisConfig."""
    from osiris_toolkit.config import OsirisConfig
    from osiris_toolkit.sim import Simulation

    sim_dir = tmp_path / "sim"
    sim_dir.mkdir()

    cfg = OsirisConfig.get()
    old_root = cfg.output_root
    cfg.set(output_root="/tmp/osiris_global_test")

    sim = Simulation(str(sim_dir))
    assert sim.config.output_root == Path("/tmp/osiris_global_test")

    cfg.set(output_root=old_root)  # restore


def test_simulation_explicit_config(tmp_path):
    """Simulation with explicit config uses it, not global."""
    from osiris_toolkit.config import OsirisConfig
    from osiris_toolkit.sim import Simulation

    sim_dir = tmp_path / "sim2"
    sim_dir.mkdir()

    custom = OsirisConfig().copy_with(output_root="/custom/root", x_unit="nm")
    sim = Simulation(str(sim_dir), config=custom)
    assert sim.config.output_root == Path("/custom/root")
    assert sim.config.x_unit == "nm"


def test_simulation_output_root_from_config(tmp_path):
    """Simulation.output_root comes from config when not overridden."""
    from osiris_toolkit.config import OsirisConfig
    from osiris_toolkit.sim import Simulation

    sim_dir = tmp_path / "sim3"
    sim_dir.mkdir()

    custom = OsirisConfig().copy_with(output_root="/explicit/output")
    sim = Simulation(str(sim_dir), config=custom)
    assert sim.output_root == Path("/explicit/output")
