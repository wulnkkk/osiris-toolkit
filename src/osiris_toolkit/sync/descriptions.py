"""Extract parameter descriptions from OSIRIS reference documentation.

Parses ``docs/reference/*.md`` markdown files to build a mapping of
section → parameter → description that can be injected into
``_generated/parameters.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

from osiris_toolkit.sync.sections import DOC_TO_SECTION

# Matches: - **param_name**, type, default = value
_PARAM_DEF_RE = re.compile(r"^\s*-\s*\*{2}(\w+)\*{2},")

# Matches: **param_name** description text
_PARAM_DESC_RE = re.compile(r"^\s*\*{2}(\w+)\*{2}\s+(.+)")


def parse_docs(docs_dir: str | Path) -> dict[str, dict[str, str]]:
    """Parse all OSIRIS reference docs and extract parameter descriptions.

    Returns ``{section_name: {param_name: description}}``.
    """
    docs_path = Path(docs_dir)
    if not docs_path.is_dir():
        return {}

    result: dict[str, dict[str, str]] = {}

    for md_file in sorted(docs_path.glob("*.md")):
        if md_file.name == "index.md":
            continue

        doc_name = md_file.stem  # filename without .md
        section_name = DOC_TO_SECTION.get(doc_name)
        if section_name is None:
            # Try case-insensitive fallback
            for dn, sn in DOC_TO_SECTION.items():
                if dn.lower() == doc_name.lower():
                    section_name = sn
                    break
        if section_name is None:
            continue

        text = md_file.read_text(encoding="utf-8", errors="replace")
        descriptions = _extract_param_descriptions(text)
        if descriptions:
            result[section_name] = descriptions

    return result


def _extract_param_descriptions(text: str) -> dict[str, str]:
    """Extract parameter descriptions from a single reference doc.

    Scans for bullet-point parameter definitions and subsequent
    ``**param_name** description text`` paragraphs.
    """
    lines = text.split("\n")
    descriptions: dict[str, str] = {}
    current_param: str | None = None

    for line in lines:
        # Check if this line starts a parameter description paragraph
        desc_m = _PARAM_DESC_RE.match(line)
        if desc_m:
            param = desc_m.group(1).lower()
            desc_text = desc_m.group(2)
            # Track as the current parameter being described
            current_param = param
            descriptions[param] = desc_text
            continue

        # Check if this line is a bullet param definition
        def_m = _PARAM_DEF_RE.match(line)
        if def_m:
            current_param = def_m.group(1).lower()
            continue

        # If continuing a multi-line description
        if current_param and current_param in descriptions and line.strip():
            # Append continuation line
            descriptions[current_param] += " " + line.strip()
        else:
            current_param = None

    return descriptions
