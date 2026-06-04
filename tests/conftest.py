"""Shared test fixtures for osiris-toolkit."""

import sys
from pathlib import Path

# Use Agg backend for all vis tests (no window popups)
import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

# Ensure tests/ is importable for helpers module
_tests_dir = Path(__file__).resolve().parent
if str(_tests_dir) not in sys.path:
    sys.path.insert(0, str(_tests_dir))

ROOT = Path(__file__).resolve().parents[1]
DECKS_DIR = ROOT.parent / "osiris-1.0.0" / "decks" / "test"


# ---------------------------------------------------------------------------
# Data path fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def data_path():
    """Root of real simulation data, or None if not configured."""
    from data_path import get_data_path
    return get_data_path()


@pytest.fixture(scope="session")
def case1_path(data_path):
    """Path to case1/ simulation (minimal: 1 ZDF, has run-info)."""
    if data_path is None:
        return None
    p = data_path / "case1"
    return p if p.is_dir() else None


@pytest.fixture(scope="session")
def srs_path(data_path):
    """Path to SRS/ simulation (60 ZDF files, FLD/e1,e2,e3)."""
    if data_path is None:
        return None
    p = data_path / "SRS"
    return p if p.is_dir() else None


@pytest.fixture(scope="session")
def laser_path(data_path):
    """Path to laser/ simulation (9232 ZDF files, DENSITY+FLD)."""
    if data_path is None:
        return None
    p = data_path / "laser"
    return p if p.is_dir() else None


# ---------------------------------------------------------------------------
# Mock GridData fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def grid_2d():
    from osiris_toolkit.sim.diagnostics import GridData
    data = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
    return GridData(data=data, iteration=5, time=1.0, label="test")


@pytest.fixture
def grid_1d():
    from osiris_toolkit.sim.diagnostics import GridData
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float64)
    return GridData(data=data, iteration=10, time=2.0, label="1d")


@pytest.fixture
def grid_32x32():
    from osiris_toolkit.sim.diagnostics import GridData
    rng = np.random.default_rng(42)
    data = rng.random((32, 32)).astype(np.float64)
    return GridData(data=data, iteration=0, time=0.0, label="random")


@pytest.fixture
def grid_zeros():
    from osiris_toolkit.sim.diagnostics import GridData
    return GridData(data=np.zeros((8, 8)), iteration=0, time=0.0, label="zeros")


@pytest.fixture
def grid_nan():
    from osiris_toolkit.sim.diagnostics import GridData
    data = np.full((4, 4), np.nan)
    return GridData(data=data, iteration=0, time=0.0, label="nan")


# ---------------------------------------------------------------------------
# Deck fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fixtures_dir():
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def minimal_deck_path(fixtures_dir):
    return fixtures_dir / "minimal.in"


@pytest.fixture
def base_2d_path():
    return DECKS_DIR / "base-2d"


# ---------------------------------------------------------------------------
# Synthetic ZDF file fixtures (via zdf_builder)
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_zdf_grid(tmp_path):
    """Create a minimal valid ZDF grid file (4x4 float32)."""
    from helpers.zdf_builder import write_minimal_grid_zdf
    p = tmp_path / "test-000000.zdf"
    data = np.arange(16, dtype=np.float32).reshape(4, 4)
    write_minimal_grid_zdf(p, data, iteration=0, time=0.0, label="test_grid")
    return p


@pytest.fixture
def tmp_zdf_grid_with_axes(tmp_path):
    """Create a minimal valid ZDF grid file with axis metadata."""
    from helpers.zdf_builder import write_minimal_grid_zdf
    p = tmp_path / "grid_axes-000000.zdf"
    data = np.ones((4, 8), dtype=np.float32)
    axes = [
        {"name": "x1", "type": 0, "min": 0.0, "max": 10.0, "label": "x1", "units": "c/\\omega_p"},
        {"name": "x2", "type": 1, "min": -5.0, "max": 5.0, "label": "x2", "units": "c/\\omega_p"},
    ]
    write_minimal_grid_zdf(p, data, iteration=42, time=1.5, axes=axes, label="e1", units="sim")
    return p


@pytest.fixture
def tmp_zdf_grid_1d(tmp_path):
    """Create a 1D ZDF grid file."""
    from helpers.zdf_builder import write_minimal_grid_zdf
    p = tmp_path / "1d-000000.zdf"
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    write_minimal_grid_zdf(p, data, iteration=0, time=0.0, label="1d_test")
    return p


@pytest.fixture
def tmp_zdf_particles(tmp_path):
    """Create a minimal valid ZDF particles file."""
    from helpers.zdf_builder import write_minimal_particles_zdf
    p = tmp_path / "particles-000000.zdf"
    parts = {
        "name": np.array([1.0, 2.0, 3.0], dtype=np.float32),
        "x1": np.array([0.1, 0.2, 0.3], dtype=np.float32),
        "x2": np.array([0.5, 0.6, 0.7], dtype=np.float32),
        "p1": np.array([1.0, 2.0, 3.0], dtype=np.float32),
        "p2": np.array([4.0, 5.0, 6.0], dtype=np.float32),
        "p3": np.array([7.0, 8.0, 9.0], dtype=np.float32),
    }
    write_minimal_particles_zdf(p, parts, iteration=10, time=0.5, label="electrons")
    return p


@pytest.fixture
def tmp_zdf_tracks(tmp_path):
    """Create a minimal valid ZDF tracks file."""
    from helpers.zdf_builder import write_minimal_tracks_zdf
    p = tmp_path / "tracks-000000.zdf"
    t1 = np.random.default_rng(123).normal(size=(50, 3)).astype(np.float32)
    t2 = np.random.default_rng(456).normal(size=(30, 3)).astype(np.float32)
    write_minimal_tracks_zdf(p, [t1, t2], quants=["itermap", "x1", "p1", "ene"],
                             niter=100, label="test_tracks")
    return p


# ---------------------------------------------------------------------------
# Robustness: corrupt ZDF files
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_zdf_truncated(tmp_path):
    """A ZDF file truncated after the magic bytes."""
    from helpers.zdf_builder import write_invalid_zdf
    p = tmp_path / "truncated.zdf"
    write_invalid_zdf(p, truncated=True)
    return p


@pytest.fixture
def tmp_zdf_corrupt_magic(tmp_path):
    """A file with corrupt magic bytes."""
    from helpers.zdf_builder import write_invalid_zdf
    p = tmp_path / "corrupt.zdf"
    write_invalid_zdf(p, magic_corrupt=True)
    return p


@pytest.fixture
def tmp_zdf_empty(tmp_path):
    """An empty (zero-byte) file."""
    from helpers.zdf_builder import write_zero_byte_file
    p = tmp_path / "empty.zdf"
    write_zero_byte_file(p)
    return p


# ---------------------------------------------------------------------------
# Synthetic simulation directories
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_sim_dir(tmp_path):
    """Create a minimal simulation directory with synthetic FLD files."""
    from helpers.zdf_builder import write_minimal_grid_zdf
    ms_fld = tmp_path / "MS" / "FLD"
    ms_fld.mkdir(parents=True)
    for i in range(3):
        data = np.ones((8, 8), dtype=np.float32) * (i + 1)
        write_minimal_grid_zdf(ms_fld / f"e1-{i*10:06d}.zdf", data, iteration=i * 10, time=i * 0.5)
    # run-info
    (tmp_path / "run-info").write_text("omega_p0: 3.55e15\ngamma: 5.0\nnx_p: 32 32\n")
    return tmp_path


@pytest.fixture
def tmp_sim_dir_density(tmp_path):
    """Create a simulation directory with DENSITY species subdirectories."""
    from helpers.zdf_builder import write_minimal_grid_zdf
    for sp in ("electrons", "protons"):
        sp_dir = tmp_path / "MS" / "DENSITY" / sp / "charge"
        sp_dir.mkdir(parents=True)
        data = np.ones((4, 4), dtype=np.float32) * (1.0 if sp == "electrons" else 2.0)
        write_minimal_grid_zdf(sp_dir / "charge-000000.zdf", data, iteration=0, time=0.0, label=sp)
    (tmp_path / "run-info").write_text("omega_p0: 3.55e15\n")
    return tmp_path


@pytest.fixture
def tmp_sim_dir_empty(tmp_path):
    """An empty simulation directory (no MS/, no HIST/)."""
    return tmp_path


# ---------------------------------------------------------------------------
# CLI fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cli_runner():
    """Click CliRunner for CLI testing."""
    from click.testing import CliRunner
    return CliRunner()


# ---------------------------------------------------------------------------
# Unit system fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def unit_system():
    from osiris_toolkit.units.converter import UnitSystem
    return UnitSystem(3.55e15)
