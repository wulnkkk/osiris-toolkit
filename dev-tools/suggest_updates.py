"""
suggest_updates.py — Suggest documentation updates when code changes.

Reads the current git diff (or staged changes) and maps modified files to
documentation update requirements defined in the sync matrix.

This tool is **advisory only** — it prints suggestions and always exits 0.
It does not block commits or CI pipelines.

Usage:
    python dev-tools/suggest_updates.py              # staged + unstaged changes
    python dev-tools/suggest_updates.py --since HEAD~3  # changes since 3 commits ago
    python dev-tools/suggest_updates.py --since origin/main  # branch diff
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Sync matrix: changed path pattern → suggested updates ──
# Each entry: (description, set of changed path patterns, list of suggested files)
SYNC_MATRIX = [
    (
        "CLI command changed",
        ["src/osiris_toolkit/cli.py"],
        [
            "skills/osiris-user/SKILL.md",
            "skills/osiris-user/references/task-map.md",
            "docs/manifest.json",
            "docs/user-guide/cli-reference.md",
        ],
    ),
    (
        "Python API changed",
        [
            "src/osiris_toolkit/analysis/",
            "src/osiris_toolkit/compute/",
            "src/osiris_toolkit/deck/",
            "src/osiris_toolkit/io/",
            "src/osiris_toolkit/sim/",
            "src/osiris_toolkit/units/",
            "src/osiris_toolkit/vis/",
            "src/osiris_toolkit/workflow/",
            "src/osiris_toolkit/postproc.py",
            "src/osiris_toolkit/config.py",
        ],
        [
            "skills/osiris-user/SKILL.md",
            "skills/osiris-user/references/task-map.md",
            "docs/manifest.json",
            "docs/api/",
            "docs/modules/",
        ],
    ),
    (
        "Data model changed (foundation layer)",
        [
            "src/osiris_toolkit/_models.py",
            "src/osiris_toolkit/exceptions.py",
        ],
        [
            "skills/osiris-dev/SKILL.md",
            "CONTRIBUTING.md",
            "AGENTS.md",
            "docs/architecture/",
            "docs/modules/_models.md",
            "docs/modules/exceptions.md",
        ],
    ),
    (
        "New module or layer boundary change",
        [
            "src/osiris_toolkit/resource/",
            "src/osiris_toolkit/parallel/",
            "src/osiris_toolkit/sync/",
        ],
        [
            "skills/osiris-dev/SKILL.md",
            "CONTRIBUTING.md",
            "AGENTS.md",
            "docs/architecture/dependency-hierarchy.md",
            "docs/architecture/overview.md",
        ],
    ),
    (
        "Documentation page added or removed",
        ["docs/"],
        [
            "mkdocs.yml nav",
            "docs/manifest.json",
        ],
    ),
    (
        "Dev workflow or CI changed",
        [
            "dev-tools/",
            ".github/workflows/",
            ".pre-commit-config.yaml",
            "Makefile",
        ],
        [
            "skills/osiris-dev/SKILL.md",
            "CONTRIBUTING.md",
        ],
    ),
]


def get_changed_files(since: str | None = None) -> list[str]:
    """Return list of changed file paths relative to repo root."""
    cmd = ["git", "-C", str(REPO_ROOT), "diff", "--name-only"]
    if since:
        cmd.append(since)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_staged_files() -> list[str]:
    """Return list of staged file paths."""
    cmd = ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "--cached"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Suggest documentation updates based on code changes"
    )
    parser.add_argument(
        "--since",
        metavar="REF",
        help="Compare against this git ref (e.g. HEAD~3, origin/main)",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Check staged changes only",
    )
    args = parser.parse_args()

    changed: list[str] = []
    if args.staged:
        changed = get_staged_files()
    elif args.since:
        changed = get_changed_files(since=args.since)
    else:
        # Default: both staged and unstaged
        changed = get_staged_files() + get_changed_files()

    changed = list(set(changed))  # dedup

    if not changed:
        print("No changes detected. Nothing to suggest.")
        return 0

    # ── Match changed files against sync matrix ──
    suggestions: dict[str, list[str]] = {}  # description → list of files

    for desc, patterns, files in SYNC_MATRIX:
        # Check if any changed file matches any pattern for this category
        matched = any(
            any(p.startswith(pattern.rstrip("/")) for pattern in patterns)
            for p in changed
        )
        if matched:
            suggestions[desc] = files

    # ── Report ──
    if not suggestions:
        print("No documentation updates suggested.")
        print("(Changed files don't match any sync matrix patterns.)")
        print(f"\nChanged files ({len(changed)}):")
        for f in sorted(changed)[:15]:
            print(f"  {f}")
        if len(changed) > 15:
            print(f"  ... and {len(changed) - 15} more")
        return 0

    print("=" * 50)
    print("  Documentation Sync Suggestions")
    print("=" * 50)
    print()

    all_files: set[str] = set()
    for desc, files in suggestions.items():
        print(f"  >> {desc}:")
        for f in files:
            print(f"      - {f}")
            all_files.add(f)
        print()

    print(f"  Changed files ({len(changed)}):")
    for f in sorted(changed)[:10]:
        print(f"      {f}")
    if len(changed) > 10:
        print(f"      ... and {len(changed) - 10} more")
    print()

    print(f"  Total unique docs to check: {len(all_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
