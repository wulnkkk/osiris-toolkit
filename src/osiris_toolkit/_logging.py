"""Central logging configuration for osiris-toolkit."""

from __future__ import annotations

import logging
import sys
from typing import Any


_logger: logging.Logger | None = None


def get_logger(name: str = "osiris_toolkit") -> logging.Logger:
    """Get or create the osiris-toolkit logger.

    Parameters
    ----------
    name : str
        Logger name. Defaults to the package root logger.

    Returns
    -------
    logging.Logger
    """
    global _logger
    if _logger is not None and name == "osiris_toolkit":
        return _logger
    if _logger is not None:
        suffix = name.split(".", 1)[1] if "." in name else name
        return _logger.getChild(suffix)
    _logger = logging.getLogger("osiris_toolkit")
    _logger.setLevel(logging.WARNING)
    if not _logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            "[%(levelname)s] %(name)s: %(message)s"
        ))
        _logger.addHandler(handler)
    return _logger


def configure(level: int, json_output: bool = False) -> None:
    """Configure logging level and format.

    Parameters
    ----------
    level : int
        Logging level (e.g. logging.DEBUG, logging.INFO).
    json_output : bool
        If True, emit JSON-formatted log records.
    """
    logger = get_logger()
    logger.setLevel(level)
    if json_output:
        logger.handlers.clear()
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_JSONFormatter())
        logger.addHandler(handler)


class _JSONFormatter(logging.Formatter):
    """JSON log formatter for machine-readable output."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        return json.dumps({
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        })
