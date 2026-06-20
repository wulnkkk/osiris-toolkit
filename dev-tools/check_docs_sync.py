"""
check_docs_sync.py — Verify documentation and skill cross-references.

Ensures:
1. All paths in docs/manifest.json resolve to real files/directories
2. All skills/ references to docs/ paths (via GitHub URLs) point to real files
3. All doc files under docs/ have a corresponding mkdocs.yml nav entry

Exit code 0 = all clean, 1 = issues found.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    issues: list[str] = []

    # ── Check 1: manifest.json paths ──
    manifest_path = REPO_ROOT / "docs" / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        issues.append(f"  Cannot read manifest.json: {e}")
        return 1

    # Collect all path-like values from manifest
    manifest_paths: set[str] = set()
    def _collect(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _collect(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _collect(v)
        elif isinstance(obj, str) and ("/" in obj and obj.endswith((".md", ".py", "/"))):
            manifest_paths.add(obj)
    _collect(manifest)

    for mp in sorted(manifest_paths):
        target = REPO_ROOT / mp
        target_dir = REPO_ROOT / mp.rstrip("/")  # directory entries
        if not target.exists() and not target_dir.is_dir():
            issues.append(f"  manifest.json: path not found: {mp}")

    # ── Check 2: skills/ GitHub URL references to docs/ ──
    skills_dir = REPO_ROOT / "skills"
    if skills_dir.is_dir():
        # Pattern: blob/main/docs/...path...
        url_pattern = re.compile(r"github\.com/wulnkkk/osiris-toolkit/blob/main/docs/([^\s\)\"]+)")
        for skill_file in skills_dir.rglob("*.md"):
            content = skill_file.read_text(encoding="utf-8")
            for match in url_pattern.finditer(content):
                rel_path = match.group(1)
                # Strip anchor (#section) for file existence check
                rel_path = rel_path.split("#")[0]
                target = REPO_ROOT / "docs" / rel_path
                if not target.exists():
                    issues.append(
                        f"  {skill_file.relative_to(REPO_ROOT)}: URL reference to docs/{rel_path} — file not found"
                    )

    # ── Check 3: mkdocs.yml nav entries vs existing doc files ──
    mkdocs_yml = REPO_ROOT / "mkdocs.yml"
    # Match: `- Title: path.md` — handles multi-word titles
    nav_pattern = re.compile(r"^\s+-\s+.+?:\s+(\S[\S/]*\.\w+)", re.MULTILINE)
    try:
        nav_entries = set()
        for match in nav_pattern.finditer(mkdocs_yml.read_text(encoding="utf-8")):
            path = match.group(1)
            # Strip anchors if any
            path = path.split("#")[0]
            nav_entries.add(path)
    except FileNotFoundError:
        issues.append("  mkdocs.yml not found")
        nav_entries = set()

    for entry in sorted(nav_entries):
        target = REPO_ROOT / "docs" / entry
        if not target.exists() and not target.is_dir():
            issues.append(f"  mkdocs.yml nav: {entry} -> docs/{entry} not found")

    # Check for orphaned doc files (no nav entry)
    if nav_entries:
        excluded = {"note/", "_build/"}
        exempt_files = {"CHANGELOG.md", "manifest.json"}
        for md_file in (REPO_ROOT / "docs").rglob("*.md"):
            rel = str(md_file.relative_to(REPO_ROOT / "docs")).replace("\\", "/")
            if any(rel.startswith(e) for e in excluded):
                continue
            if rel in exempt_files or rel.startswith("_"):
                continue
            # mkdocs can reference index files as directories
            alt = rel.removesuffix("/index.md")
            if rel not in nav_entries and alt not in nav_entries:
                issues.append(f"  docs/{rel}: no mkdocs.yml nav entry (orphan?)")

    # ── Check 4: devlog exists for current version ──
    pyproject = REPO_ROOT / "pyproject.toml"
    try:
        content = pyproject.read_text(encoding="utf-8")
        m = re.search(r'^version = "(\d+\.\d+\.\d+)"', content, re.MULTILINE)
        if m:
            ver = m.group(1)
            devlog = REPO_ROOT / "docs" / "devlog" / f"{ver}.md"
            if not devlog.exists():
                issues.append(
                    f"  docs/devlog/{ver}.md not found — "
                    f"each version bump requires a corresponding devlog "
                    f"(see CONTRIBUTING.md Before Release checklist)"
                )
    except FileNotFoundError:
        issues.append("  pyproject.toml not found — cannot verify devlog")

    # ── Report ──
    if issues:
        print(f"[FAIL] {len(issues)} documentation sync issue(s) found:\n")
        for iss in sorted(set(issues)):
            print(iss)
        return 1
    else:
        print("[PASS] Documentation sync checks passed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
