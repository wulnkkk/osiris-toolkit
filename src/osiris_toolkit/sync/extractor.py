"""Fortran source scanner for extracting definitions from OSIRIS source.

Parses namelist declarations, variable type/default patterns, diagnostic
quantity arrays, and get_namelist calls. Works with regex — no Fortran
compiler required.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# namelist /nl_name/ var1, var2, &
#   var3, var4
_NAMELIST_RE = re.compile(
    r"^\s*namelist\s*/\s*(\w+)\s*/\s*(.+?)$",
    re.IGNORECASE | re.MULTILINE,
)

# type declarations (Fortran free-form)
#   integer :: var
#   real(p_double) :: var1, var2
#   real(p_double), dimension(3) :: var
#   character(len=20) :: var
#   logical :: var
_TYPE_RE = re.compile(
    r"^\s*(integer|real\s*\([^)]*\)|character\s*\([^)]*\)|logical)"
    r"(?:\s*,\s*dimension\s*\(([^)]+)\))?"
    r"\s*::\s*(.+?)$",
    re.IGNORECASE | re.MULTILINE,
)

# default assignments:  var = value
_DEFAULT_RE = re.compile(
    r"^\s*(\w+)\s*=\s*(.+?)(?:\s*!.*)?$",
    re.IGNORECASE,
)

# p_report_quants character array
_QUANTS_RE = re.compile(
    r"character\s*\(\s*len\s*=\s*\d+\s*\)\s*,\s*dimension\s*\((\d+)\)\s*,"
    r"\s*(?:parameter(?:,\s*public)?\s*::|public\s*::)"
    r"\s*(?:&\s*)?\s*(\w+)\s*=\s*\(\s*/\s*(.+?)\s*/\s*\)",
    re.IGNORECASE | re.DOTALL,
)

# call get_namelist( input_file, "nl_xxx", ierr )
_GETNAMELIST_RE = re.compile(
    r'call\s+get_namelist\s*\(\s*\w+\s*,\s*"([^"]+)"',
    re.IGNORECASE,
)

# Fortran continuation: line ending with & means next line is continuation
_CONTINUATION_RE = re.compile(r"&\s*$")

# Fortran string literal extraction: '...'  or  "..."
_STRIP_QUOTES_RE = re.compile(r"""^['"](.*)['"]$""")


@dataclass
class NamelistVar:
    """A single variable in a namelist declaration."""
    name: str
    fortran_type: str = ""
    dimensions: str = ""       # e.g. "3", "p_x_dim"
    default: str | None = None


@dataclass
class NamelistEntry:
    """One namelist block."""
    name: str                      # e.g. "nl_diag_emf"
    section_name: str              # e.g. "diag_emf" (nl_ prefix stripped)
    file_path: str
    line_number: int
    variables: list[NamelistVar] = field(default_factory=list)


@dataclass
class QuantitiesEntry:
    """One report_quants array definition."""
    array_name: str                # e.g. "p_report_quants"
    count: int                     # declared dimension
    quantities: list[str]          # the quantity name strings
    file_path: str
    line_number: int


@dataclass
class SectionEntry:
    """One get_namelist call mapping."""
    section_nl: str               # e.g. "nl_diag_emf"
    section_name: str              # e.g. "diag_emf"
    file_path: str
    line_number: int


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


class FortranScanner:
    """Scans OSIRIS Fortran source for structured definitions."""

    def __init__(self, source_dir: str | Path) -> None:
        self._root = Path(source_dir)
        self._fortran_files: list[Path] = []
        self._namelists: dict[str, NamelistEntry] = {}
        self._quantities: list[QuantitiesEntry] = []
        self._sections: list[SectionEntry] = []
        self._var_types: dict[str, dict[str, str]] = {}  # file -> {var -> type}
        self._var_defaults: dict[str, dict[str, str]] = {}  # file -> {var -> default}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self) -> None:
        """Scan all Fortran files and populate all catalogs."""
        self._find_files()
        for fpath in self._fortran_files:
            self._scan_file(fpath)

    @property
    def namelists(self) -> list[NamelistEntry]:
        return list(self._namelists.values())

    @property
    def quantities(self) -> list[QuantitiesEntry]:
        return self._quantities

    @property
    def sections(self) -> list[SectionEntry]:
        return self._sections

    def get_namelist(self, name: str) -> NamelistEntry | None:
        return self._namelists.get(name)

    # ------------------------------------------------------------------
    # File discovery
    # ------------------------------------------------------------------

    def _find_files(self) -> None:
        self._fortran_files = sorted(
            p for p in self._root.rglob("*")
            if p.suffix.lower() in (".f90", ".f03", ".f", ".F90")
            and p.is_file()
        )

    # ------------------------------------------------------------------
    # Per-file scanning
    # ------------------------------------------------------------------

    def _scan_file(self, fpath: Path) -> None:
        try:
            text = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return

        lines = text.split("\n")

        # Merge continuation lines
        merged = self._merge_continuations(lines)

        # Re-join for regex scanning but keep merged lines for context
        merged_text = "\n".join(merged)

        self._scan_namelists(fpath, merged_text, lines)
        self._scan_quantities(fpath, merged_text)
        self._scan_sections(fpath, merged_text)
        self._scan_types_and_defaults(fpath, lines)

        # After scanning types/defaults, enrich namelist variables
        for entry in self._namelists.values():
            if entry.file_path != str(fpath):
                continue
            file_vtypes = self._var_types.get(str(fpath), {})
            file_vdefaults = self._var_defaults.get(str(fpath), {})
            for var in entry.variables:
                if not var.fortran_type and var.name in file_vtypes:
                    var.fortran_type = file_vtypes[var.name]
                if var.default is None and var.name in file_vdefaults:
                    var.default = file_vdefaults[var.name]

    # ------------------------------------------------------------------
    # Continuation merging
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_continuations(lines: list[str]) -> list[str]:
        merged: list[str] = []
        buf = ""
        for line in lines:
            stripped = line.rstrip()
            if _CONTINUATION_RE.search(stripped):
                buf += stripped[:-1].rstrip() + " "
            else:
                buf += stripped
                merged.append(buf)
                buf = ""
        if buf:
            merged.append(buf)
        return merged

    # ------------------------------------------------------------------
    # Namelist scanner
    # ------------------------------------------------------------------

    def _scan_namelists(
        self, fpath: Path, merged_text: str, original_lines: list[str]
    ) -> None:
        for m in _NAMELIST_RE.finditer(merged_text):
            name = m.group(1)
            var_text = m.group(2)

            # Parse variable names (comma-separated, possibly with line breaks)
            var_names = [
                v.strip() for v in var_text.replace("\n", " ").split(",") if v.strip()
            ]

            # Find line number from original text
            line_num = self._find_line_number(merged_text[: m.start()])

            entry = NamelistEntry(
                name=name,
                section_name=name[3:] if name.startswith("nl_") else name,
                file_path=str(fpath),
                line_number=line_num,
                variables=[NamelistVar(name=vn) for vn in var_names],
            )
            self._namelists[name] = entry

    # ------------------------------------------------------------------
    # Quantity array scanner
    # ------------------------------------------------------------------

    def _scan_quantities(self, fpath: Path, merged_text: str) -> None:
        for m in _QUANTS_RE.finditer(merged_text):
            count = int(m.group(1))
            array_name = m.group(2)
            raw = m.group(3)

            # Extract individual strings
            quants = self._parse_string_list(raw)
            line_num = self._find_line_number(merged_text[: m.start()])

            self._quantities.append(
                QuantitiesEntry(
                    array_name=array_name,
                    count=count,
                    quantities=quants,
                    file_path=str(fpath),
                    line_number=line_num,
                )
            )

    @staticmethod
    def _parse_string_list(raw: str) -> list[str]:
        """Parse a Fortran (/ 'str1', 'str2', ... /) list."""
        results: list[str] = []
        # Strip whitespace and newlines
        cleaned = " ".join(raw.split())
        # Find all quoted strings
        for m in re.finditer(r"['\"]([^'\"]*)['\"]", cleaned):
            results.append(m.group(1).strip())
        return results

    # ------------------------------------------------------------------
    # Section (get_namelist) scanner
    # ------------------------------------------------------------------

    def _scan_sections(self, fpath: Path, merged_text: str) -> None:
        for m in _GETNAMELIST_RE.finditer(merged_text):
            section_nl = m.group(1)
            section_name = section_nl[3:] if section_nl.startswith("nl_") else section_nl
            line_num = self._find_line_number(merged_text[: m.start()])
            self._sections.append(
                SectionEntry(
                    section_nl=section_nl,
                    section_name=section_name,
                    file_path=str(fpath),
                    line_number=line_num,
                )
            )

    # ------------------------------------------------------------------
    # Type and default scanner
    # ------------------------------------------------------------------

    def _scan_types_and_defaults(self, fpath: Path, lines: list[str]) -> None:
        file_types: dict[str, str] = {}
        file_defaults: dict[str, str] = {}

        for line in lines:
            # Try type declaration
            tm = _TYPE_RE.match(line.strip())
            if tm:
                fortran_type = tm.group(1).strip()
                _dims = tm.group(2) or ""  # parsed for future use
                names_str = tm.group(3)
                for name in names_str.split(","):
                    name = name.strip()
                    if name:
                        file_types[name] = fortran_type
                continue

            # Try default assignment
            dm = _DEFAULT_RE.match(line.strip())
            if dm:
                varname = dm.group(1)
                value = dm.group(2).strip()
                # Skip comment-only lines and obvious non-assignments
                if varname not in ("if", "do", "end", "case", "else", "then"):
                    file_defaults[varname] = value

        self._var_types[str(fpath)] = file_types
        self._var_defaults[str(fpath)] = file_defaults

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_line_number(prefix_text: str) -> int:
        return prefix_text.count("\n") + 1


# ---------------------------------------------------------------------------
# Fortran type → Python type mapping
# ---------------------------------------------------------------------------

FORTRAN_TO_PYTHON: dict[str, str] = {
    "integer": "int",
    "real": "float",
    "real(p_double)": "float",
    "real(p_k_fld)": "float",
    "real(p_k_part)": "float",
    "real(p_single)": "float",
    "real(p_diag_prec)": "float",
    "logical": "bool",
    "character": "str",
}
