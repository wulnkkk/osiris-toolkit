"""Tests for the custom exception hierarchy."""

import pytest

from osiris_toolkit.exceptions import (
    ConfigurationError,
    DataNotFoundError,
    FormatError,
    MissingDependencyError,
    MissingParameterError,
    OsirisToolkitError,
    PipelineError,
    ShapeError,
    UnitConversionError,
    UnsupportedVersionError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Verify inheritance chain."""

    def test_all_inherit_from_base(self):
        for cls in [
            DataNotFoundError,
            FormatError,
            ValidationError,
            PipelineError,
            ConfigurationError,
            UnitConversionError,
            MissingDependencyError,
        ]:
            assert issubclass(cls, OsirisToolkitError)

    def test_unsupported_version_is_format_error(self):
        assert issubclass(UnsupportedVersionError, FormatError)
        assert issubclass(UnsupportedVersionError, OsirisToolkitError)

    def test_shape_error_is_validation_error(self):
        assert issubclass(ShapeError, ValidationError)
        assert issubclass(ShapeError, OsirisToolkitError)

    def test_missing_parameter_is_validation_error(self):
        assert issubclass(MissingParameterError, ValidationError)
        assert issubclass(MissingParameterError, OsirisToolkitError)


class TestExceptionMessages:
    """Verify exceptions carry messages correctly."""

    def test_data_not_found_carries_message(self):
        exc = DataNotFoundError("No data for e1 at iteration 50")
        assert "e1" in str(exc)
        assert "50" in str(exc)

    def test_format_error_carries_message(self):
        exc = FormatError("Not a valid ZDF file: bad magic")
        assert "ZDF" in str(exc)

    def test_can_catch_by_base(self):
        """AI can catch OsirisToolkitError to handle all toolkit errors."""
        try:
            raise ShapeError("Expected 2-D, got 1-D")
        except OsirisToolkitError:
            pass
        else:
            pytest.fail("Should have been caught by OsirisToolkitError")

    def test_can_catch_specifically(self):
        """AI can catch DataNotFoundError to skip missing data gracefully."""
        try:
            raise DataNotFoundError("missing")
        except DataNotFoundError:
            pass
        else:
            pytest.fail("Should have been caught by DataNotFoundError")
