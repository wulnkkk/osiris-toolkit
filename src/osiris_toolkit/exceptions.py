"""Custom exception hierarchy for osiris-toolkit.

All exceptions inherit from ``OsirisToolkitError``, allowing callers
(including AI agents) to catch a single base class or target specific
error types for fine-grained recovery strategies.
"""

from __future__ import annotations


class OsirisToolkitError(Exception):
    """Base exception for all osiris-toolkit errors."""


# -- Data availability --------------------------------------------------------

class DataNotFoundError(OsirisToolkitError):
    """Requested data, quantity, or diagnostic does not exist."""


# -- Format / file integrity --------------------------------------------------

class FormatError(OsirisToolkitError):
    """File format is invalid or unrecognised."""


class UnsupportedVersionError(FormatError):
    """ZDF or HDF5 record/dataset version is too new to read."""


# -- Validation ---------------------------------------------------------------

class ValidationError(OsirisToolkitError):
    """Parameter or input validation failed."""


class ShapeError(ValidationError):
    """Array dimensions or shape do not match the operation's requirements."""


class MissingParameterError(ValidationError):
    """Required parameter or configuration section is missing."""


# -- Pipeline -----------------------------------------------------------------

class PipelineError(OsirisToolkitError):
    """Pipeline execution failed (missing prerequisite step, etc.)."""


# -- Configuration ------------------------------------------------------------

class ConfigurationError(OsirisToolkitError):
    """Simulation or OsirisConfig is invalid or incomplete."""


# -- Units --------------------------------------------------------------------

class UnitConversionError(OsirisToolkitError):
    """Unit conversion failed (missing plasma frequency, etc.)."""


# -- Dependencies -------------------------------------------------------------

class MissingDependencyError(OsirisToolkitError):
    """Optional dependency (h5py, pyevtk, etc.) is not installed."""
