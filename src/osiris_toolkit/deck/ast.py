"""AST node definitions for parsed OSIRIS input decks."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SliceSpec:
    """Represents array slice notation, e.g. (1:3) or (1:2,1).

    Each dim is (start, end), with None meaning a wildcard colon (:).
    """

    dims: list[tuple[int | None, int | None]]

    def __repr__(self) -> str:
        parts = []
        for s, e in self.dims:
            s_str = str(s) if s is not None else ":"
            e_str = str(e) if e is not None else ":"
            parts.append(f"{s_str}:{e_str}")
        return "(" + ",".join(parts) + ")"


@dataclass
class KeySpec:
    """A parameter name with an optional array slice."""

    name: str
    slice: SliceSpec | None = None


@dataclass
class ParamAssignment:
    """A single key=value or key=val1,val2,val3 assignment."""

    keys: list[KeySpec]
    raw_values: list[str]  # raw string values before type conversion
    line: int

    @property
    def primary_key(self) -> str:
        """Primary parameter name (first key)."""
        return self.keys[0].name if self.keys else ""


@dataclass
class Section:
    """A named section and its parameters."""

    name: str
    params: dict[str, Any] = field(default_factory=dict)
    raw_params: list[ParamAssignment] = field(default_factory=list)
    line: int = 0


@dataclass
class Deck:
    """Top-level parsed deck."""

    sections: list[Section]
    filename: str = ""
