"""
check_english.py — Verify all project content is in English.

Scans .py and .md files for non-ASCII characters that indicate
non-English text. Excludes:
- docs/note/ (personal workspace)
- Test data exercising Unicode parsing
- Auto-generated files (_generated/)
- .gitignored files

Exit code 0 = all clean, 1 = non-English content found.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories to exclude entirely
EXCLUDE_DIRS = {
    "docs/note",
    "docs/_build",
    "site",
    "output",
    "data",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".reasonix",
    ".github",
}

# File patterns to exclude
EXCLUDE_PATTERNS: list[re.Pattern] = [
    re.compile(r"src/osiris_toolkit/_generated/"),
    re.compile(r"tests/hpc/"),
]

# CJK character ranges (Chinese, Japanese, Korean)
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]")

# Cyrillic ranges
CYRILLIC_RE = re.compile(r"[\u0400-\u04ff]")

# Other non-Latin ranges to flag
OTHER_NON_LATIN_RE = re.compile(r"[\u0600-\u06ff\u0e00-\u0e7f\u0e80-\u0eff]")

# Known false positives — files that intentionally contain non-English test data
ALLOWED_NON_ENGLISH = {
    # Test data files with Unicode parsing tests
    "tests/test_deck/test_lexer.py",
    "tests/test_deck/test_parser.py",
}


def should_skip(file_path: Path) -> bool:
    """Check if a file should be skipped."""
    rel = str(file_path.relative_to(REPO_ROOT)).replace("\\", "/")

    for exclude_dir in EXCLUDE_DIRS:
        if rel.startswith(exclude_dir):
            return True
    for pattern in EXCLUDE_PATTERNS:
        if pattern.search(rel):
            return True
    return False


def has_non_english(text: str) -> bool:
    """Check for non-English characters."""
    if CJK_RE.search(text):
        return True
    if CYRILLIC_RE.search(text):
        return True
    if OTHER_NON_LATIN_RE.search(text):
        return True
    return False


def main() -> int:
    violations: list[str] = []
    extensions = (".py", ".md")

    for ext in extensions:
        for file_path in sorted(REPO_ROOT.rglob(f"*{ext}")):
            if should_skip(file_path):
                continue

            rel = str(file_path.relative_to(REPO_ROOT)).replace("\\", "/")
            if rel in ALLOWED_NON_ENGLISH:
                continue

            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, Exception):
                continue

            for lineno, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                # Skip comment lines that list valid examples (e.g., regex test data)
                if has_non_english(stripped):
                    violations.append(f"  {rel}:{lineno}: {stripped[:120]}")

    if violations:
        print(f"[FAIL] {len(violations)} non-English line(s) found:\n")
        for v in sorted(violations):
            print(v)
        print("\n💡 All project content must be in English (see CONTRIBUTING.md).")
        print("   Exceptions: docs/note/, test data exercising Unicode parsing.")
        return 1
    else:
        print("[PASS] English language check passed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
