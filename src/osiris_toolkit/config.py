"""Global configuration for osiris-toolkit.

Provides an :class:`OsirisConfig` singleton for managing global defaults
(output root, logging level, parallel workers, units, etc.).

Usage::

    from osiris_toolkit.config import OsirisConfig

    # Global setup
    OsirisConfig.get().set(output_root="/data/figures", parallel_workers=4)

    # Read a setting
    root = OsirisConfig.get().output_root

    # Create a per-simulation override
    sim_cfg = OsirisConfig.get().copy_with(output_root="/other")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OsirisConfig:
    """Layered configuration for osiris-toolkit.

    Fields not set (None for optional, or factory default) cascade:
    explicit kwarg > sim.config > global OsirisConfig > hardcoded default.

    Attributes
    ----------
    output_root : Path or None
        Root directory for analysis/visualisation output.
    log_level : int
        Logging level (e.g. ``logging.DEBUG``).
    log_json : bool
        If True, emit JSON-formatted log records.
    parallel_workers : int
        Default number of parallel workers.
    overwrite : bool
        If True, overwrite existing output files by default.
    x_unit : str
        Default spatial x-axis unit.
    y_unit : str
        Default spatial y-axis unit.
    time_unit : str
        Default time unit.
    """

    output_root: Path | None = None
    log_level: int = logging.WARNING
    log_json: bool = False
    parallel_workers: int = 1
    overwrite: bool = False
    x_unit: str = "um"
    y_unit: str = "um"
    time_unit: str = "ps"

    def __post_init__(self) -> None:
        """Coerce field types after construction."""
        if isinstance(self.output_root, str):
            object.__setattr__(self, "output_root", Path(self.output_root))

    def set(self, **kwargs) -> None:
        """Update multiple fields at once.

        Parameters
        ----------
        **kwargs
            Field names and values to set.
        """
        for k, v in kwargs.items():
            if hasattr(self, k):
                if k == "output_root" and isinstance(v, str):
                    v = Path(v)
                setattr(self, k, v)

    def copy_with(self, **overrides) -> OsirisConfig:
        """Return a new OsirisConfig inheriting current values, with overrides.

        Parameters
        ----------
        **overrides
            Fields to override in the copy.

        Returns
        -------
        OsirisConfig
            A new independent instance.
        """
        new = OsirisConfig()
        for fld in _FIELDS:
            setattr(new, fld, getattr(self, fld))
        for k, v in overrides.items():
            if hasattr(new, k):
                if k == "output_root" and isinstance(v, str):
                    v = Path(v)
                setattr(new, k, v)
        return new

    @classmethod
    def get(cls) -> OsirisConfig:
        """Return the global singleton instance.

        Returns
        -------
        OsirisConfig
            The module-level singleton.
        """
        global _config
        return _config


# Module-level fields for copy iteration
_FIELDS = [
    "output_root",
    "log_level",
    "log_json",
    "parallel_workers",
    "overwrite",
    "x_unit",
    "y_unit",
    "time_unit",
]

# Global singleton
_config = OsirisConfig()
