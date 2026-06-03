"""Tests for OsirisConfig singleton."""

import logging
from pathlib import Path


class TestOsirisConfig:
    """Test OsirisConfig singleton behavior."""

    def test_get_returns_same_instance(self):
        """OsirisConfig.get() returns the same instance."""
        from osiris_toolkit.config import OsirisConfig

        a = OsirisConfig.get()
        b = OsirisConfig.get()
        assert a is b

    def test_default_values(self):
        """Default field values match specification."""
        from osiris_toolkit.config import OsirisConfig

        cfg = OsirisConfig.get()
        assert cfg.output_root is None
        assert cfg.log_level == logging.WARNING
        assert cfg.parallel_workers == 1
        assert cfg.overwrite is False
        assert cfg.x_unit == "um"
        assert cfg.y_unit == "um"
        assert cfg.time_unit == "ps"
        assert cfg.log_json is False

    def test_set_updates_fields(self):
        """set() updates multiple fields at once."""
        from osiris_toolkit.config import OsirisConfig

        cfg = OsirisConfig.get()
        original_root = cfg.output_root
        original_workers = cfg.parallel_workers

        cfg.set(output_root="/tmp/test", parallel_workers=4)
        assert cfg.output_root == Path("/tmp/test")
        assert cfg.parallel_workers == 4

        # restore original values to not pollute other tests
        cfg.output_root = original_root
        cfg.parallel_workers = original_workers

    def test_copy_with_returns_independent_copy(self):
        """copy_with() returns a new instance that doesn't affect original."""
        from osiris_toolkit.config import OsirisConfig

        cfg = OsirisConfig.get()
        copy = cfg.copy_with(output_root="/different")
        assert copy.output_root == Path("/different")
        assert copy.parallel_workers == cfg.parallel_workers
        # modify copy, verify original unchanged
        copy.parallel_workers = 99
        assert cfg.parallel_workers == 1

    def test_copy_with_partial_override(self):
        """copy_with keeps unspecified fields from parent."""
        from osiris_toolkit.config import OsirisConfig

        cfg = OsirisConfig.get()
        copy = cfg.copy_with(x_unit="nm")
        assert copy.x_unit == "nm"
        assert copy.y_unit == "um"
        assert copy.time_unit == "ps"


class TestSaveOrShowConfig:
    """Test save_or_show respects OsirisConfig.overwrite."""

    def test_overwrite_from_config(self, tmp_path):
        """save_or_show uses config.overwrite when not explicitly passed."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import pytest

        from osiris_toolkit.config import OsirisConfig
        from osiris_toolkit.vis.common import save_or_show

        fpath = tmp_path / "test.png"
        fig, _ = plt.subplots()
        save_or_show(fig, fpath)
        plt.close(fig)

        fig2, _ = plt.subplots()
        cfg = OsirisConfig.get()
        old = cfg.overwrite
        cfg.overwrite = False
        with pytest.raises(FileExistsError):
            save_or_show(fig2, fpath)
        cfg.overwrite = True
        save_or_show(fig2, fpath)
        cfg.overwrite = old
        plt.close(fig2)
