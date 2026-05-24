"""Tests for io._parallel — parallel batch I/O."""

from pathlib import Path

import numpy as np
import pytest

from osiris_toolkit.io._reader import read_grid, read_info
from osiris_toolkit.io._parallel import read_many, read_many_map


class TestReadMany:
    def test_read_many_sequential(self, tmp_path):
        """Read multiple synthetic grid files."""
        from helpers.zdf_builder import write_minimal_grid_zdf

        paths = []
        for i in range(3):
            p = tmp_path / f"test-{i:06d}.zdf"
            write_minimal_grid_zdf(p, np.ones((4, 4), dtype=np.float32) * i, iteration=i, time=i * 0.5)
            paths.append(p)

        results = read_many(paths, read_grid, max_workers=1)
        assert len(results) == 3
        for i, (data, gi, it) in enumerate(results):
            assert it.n == i

    def test_read_many_parallel(self, tmp_path):
        """Read with multiple workers — verifies no deadlocks and correct results."""
        from helpers.zdf_builder import write_minimal_grid_zdf

        paths = []
        for i in range(6):
            p = tmp_path / f"test-{i:06d}.zdf"
            write_minimal_grid_zdf(p, np.ones((4, 4), dtype=np.float32), iteration=i, time=0.0)
            paths.append(p)

        results = read_many(paths, read_grid, max_workers=2)
        assert len(results) == 6
        iterations = sorted(it.n for _, _, it in results)
        assert iterations == list(range(6))

    def test_read_many_preserves_order(self, tmp_path):
        """Results must be in the same order as input paths."""
        from helpers.zdf_builder import write_minimal_grid_zdf

        paths = []
        for i in range(5):
            p = tmp_path / f"test-{i:06d}.zdf"
            write_minimal_grid_zdf(p, np.ones((2, 2), dtype=np.float32), iteration=i, time=0.0)
            paths.append(p)

        results = read_many(paths, read_grid, max_workers=4)
        for i, (_, _, it) in enumerate(results):
            assert it.n == i, f"Order mismatch at index {i}"

    def test_read_many_on_error_raise(self, tmp_path):
        """on_error='raise' should propagate the first exception."""
        from helpers.zdf_builder import write_invalid_zdf, write_minimal_grid_zdf

        write_minimal_grid_zdf(tmp_path / "good.zdf", np.ones((2, 2), dtype=np.float32))
        write_invalid_zdf(tmp_path / "bad.zdf", magic_corrupt=True)

        paths = [tmp_path / "good.zdf", tmp_path / "bad.zdf"]
        with pytest.raises(ValueError, match="Not a valid ZDF file"):
            read_many(paths, read_grid, max_workers=1)

    def test_read_many_on_error_return(self, tmp_path):
        """on_error='return' should store exceptions in result list."""
        from helpers.zdf_builder import write_invalid_zdf, write_minimal_grid_zdf

        write_minimal_grid_zdf(tmp_path / "good.zdf", np.ones((2, 2), dtype=np.float32))
        write_invalid_zdf(tmp_path / "bad.zdf", magic_corrupt=True)

        paths = [tmp_path / "good.zdf", tmp_path / "bad.zdf"]
        results = read_many(paths, read_grid, max_workers=1, on_error="return")
        assert len(results) == 2
        assert isinstance(results[0], tuple)  # success
        assert isinstance(results[1], Exception)  # error stored

    def test_read_many_empty_list(self):
        result = read_many([], read_grid)
        assert result == []

    def test_read_many_with_info(self, tmp_path):
        """read_info works with read_many too."""
        from helpers.zdf_builder import write_minimal_grid_zdf

        paths = []
        for i in range(3):
            p = tmp_path / f"test-{i:06d}.zdf"
            write_minimal_grid_zdf(p, np.ones((4, 4), dtype=np.float32), iteration=i, time=0.0)
            paths.append(p)

        results = read_many(paths, read_info, max_workers=2)
        assert len(results) == 3
        for r in results:
            assert r.file_type == "grid"


class TestReadManyMap:
    def test_with_post_function(self, tmp_path):
        """Post-processing function is applied to each result."""
        from helpers.zdf_builder import write_minimal_grid_zdf

        paths = []
        for i in range(3):
            p = tmp_path / f"test-{i:06d}.zdf"
            write_minimal_grid_zdf(p, np.ones((4, 4), dtype=np.float32) * i, iteration=i, time=0.0)
            paths.append(p)

        # Post function extracts just the iteration number
        def extract_iter(result):
            _, _, it = result
            return it.n

        iterations = read_many_map(paths, read_grid, post_fn=extract_iter, max_workers=2)
        assert iterations == [0, 1, 2]

    def test_without_post_function(self, tmp_path):
        """No post-function should work like read_many."""
        from helpers.zdf_builder import write_minimal_grid_zdf

        p = tmp_path / "test-000000.zdf"
        write_minimal_grid_zdf(p, np.ones((2, 2), dtype=np.float32))
        results = read_many_map([p], read_grid, post_fn=None)
        assert len(results) == 1
        assert isinstance(results[0], tuple)
