"""Tests for vis — common utilities."""

import numpy as np
import pytest


# Check if safe_log_norm exists; if not, skip tests
try:
    from osiris_toolkit.vis.common import safe_log_norm
    HAS_SAFE_LOG_NORM = True
except ImportError:
    HAS_SAFE_LOG_NORM = False


@pytest.mark.skipif(not HAS_SAFE_LOG_NORM, reason="safe_log_norm not available")
class TestSafeLogNorm:
    def test_all_positive(self):
        norm = safe_log_norm(np.array([1.0, 10.0, 100.0]))
        assert norm is not None

    def test_contains_zero(self):
        norm = safe_log_norm(np.array([0.0, 10.0, 100.0]))
        assert norm is not None

    def test_contains_negative(self):
        norm = safe_log_norm(np.array([-5.0, 0.0, 10.0]))
        assert norm is not None

    def test_all_zeros(self):
        norm = safe_log_norm(np.array([0.0, 0.0, 0.0]))
        assert norm is not None

