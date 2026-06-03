"""Tests for Simulation path ownership and output_root."""


from osiris_toolkit.sim import Simulation


def test_sim_path_is_absolute(tmp_path):
    """Simulation.path returns an absolute path."""
    sim = Simulation(str(tmp_path))
    assert sim.path.is_absolute()
    assert sim.path == tmp_path.resolve()


def test_sim_path_from_relative(tmp_path, monkeypatch):
    """Relative path passed to Simulation becomes absolute."""
    monkeypatch.chdir(str(tmp_path.parent))
    rel = tmp_path.name
    sim = Simulation(rel)
    assert sim.path.is_absolute()
    assert sim.path == tmp_path.resolve()


def test_sim_default_output_root(tmp_path):
    """Default output_root is {sim_path}/figures/."""
    sim = Simulation(str(tmp_path))
    assert sim.output_root == tmp_path.resolve() / "figures"


def test_sim_custom_output_root(tmp_path):
    """Explicit output_root overrides the default."""
    custom = tmp_path / "custom_output"
    sim = Simulation(str(tmp_path), output_root=str(custom))
    assert sim.output_root == custom.resolve()


def test_sim_output_dir_creates_and_returns(tmp_path):
    """output_dir() creates the directory and returns its Path."""
    sim = Simulation(str(tmp_path))
    d = sim.output_dir("fields")
    assert d.is_dir()
    assert d == tmp_path.resolve() / "figures" / "fields"


def test_sim_output_dir_nested(tmp_path):
    """output_dir() with multiple parts creates nested directories."""
    sim = Simulation(str(tmp_path))
    d = sim.output_dir("analysis", "emf")
    assert d.is_dir()
    assert d == tmp_path.resolve() / "figures" / "analysis" / "emf"
