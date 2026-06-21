"""
check_docs_sync.py — Verify documentation cross-references and frontmatter compliance.

Ensures:
1. All paths in docs/manifest.json resolve to real files/directories
2. All skills/ references to docs/ paths (via GitHub URLs) point to real files
3. All doc files under docs/ have a corresponding mkdocs.yml nav entry
4. All doc files have valid frontmatter per docs/meta/documentation-standards.md
5. Devlog exists for current pyproject.toml version

Exit code 0 = all clean, 1 = issues found.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Frontmatter validation rules (mirrors docs/meta/documentation-standards.md) ──

VALID_KINDS = {"architecture", "design", "guide", "index", "reference", "tutorial"}

VALID_TOPICS = {
    "api", "architecture", "batch", "changelog", "cli", "contributing",
    "deck", "density", "design", "faq", "field", "installation",
    "kspace", "meta", "modules", "overview", "parallel", "phasespace",
    "quick-start", "simulation", "units", "workflow",
}

VALID_AUDIENCES = {r"[human]", r"[agent]", r"[human, agent]"}
VALID_ROLES = {"user", "developer", "[user, developer]"}

DIR_KIND_MAP = {
    "api/": "reference",
    "architecture/": "architecture",
    "design/": "design",
    "devlog/": "reference",
    "getting-started/": "tutorial",
    "meta/": "reference",
    "modules/": "reference",
    "user-guide/": None,  # guide or reference
}

# Files that are excluded from frontmatter checks
FM_EXCLUDE_PREFIXES = {"note/", "_build/"}


def _parse_frontmatter(text: str) -> tuple[dict | None, int]:
    """Parse YAML frontmatter. Returns (data, body_start_offset)."""
    if not text.startswith("---\n"):
        return None, 0
    end = text.find("---", 4)
    if end == -1:
        return None, 0
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError:
        return None, 0
    if not isinstance(data, dict):
        return None, 0
    return data, end + 4


def _check_frontmatter(
    rel_path: str, fm_data: dict, issues: list[str]
) -> None:
    """Validate one file's frontmatter against the standards."""
    prefix = f"  docs/{rel_path}: frontmatter"

    # Required fields
    for field in ("audience", "role", "topic", "kind", "updated"):
        if field not in fm_data:
            issues.append(f"{prefix} missing required field '{field}'")
            return  # stop: can't validate further

    aud = fm_data["audience"]
    role = fm_data["role"]
    topic = fm_data["topic"]
    kind = fm_data["kind"]
    updated = fm_data["updated"]

    # audience — YAML parses [human, agent] as list ["human", "agent"]
    if isinstance(aud, list):
        aud_set = set(aud)
        if not aud_set.issubset({"human", "agent"}):
            issues.append(f"{prefix}: invalid audience '{aud}' — must contain only human and/or agent")
    elif isinstance(aud, str):
        if aud not in ("human", "agent"):
            issues.append(f"{prefix}: invalid audience '{aud}' — must be human or agent")
    else:
        issues.append(f"{prefix}: audience must be a string or list, got {type(aud).__name__}")

    # role
    if isinstance(role, list):
        role_set = set(role)
        if not role_set.issubset({"user", "developer"}):
            issues.append(f"{prefix}: invalid role '{role}' — must contain only user and/or developer")
    elif isinstance(role, str):
        if role not in VALID_ROLES:
            issues.append(f"{prefix}: invalid role '{role}'")
    else:
        issues.append(f"{prefix}: role must be string or list")

    # topic
    if topic not in VALID_TOPICS:
        issues.append(
            f"{prefix}: invalid topic '{topic}' — "
            f"not in controlled vocabulary. Add it to docs/meta/documentation-standards.md"
        )

    # kind
    if kind not in VALID_KINDS:
        issues.append(f"{prefix}: invalid kind '{kind}' — must be {sorted(VALID_KINDS)}")

    # kind vs directory
    for dir_prefix, expected_kind in DIR_KIND_MAP.items():
        if rel_path.startswith(dir_prefix) and expected_kind is not None:
            if kind != expected_kind:
                issues.append(
                    f"{prefix}: kind '{kind}' doesn't match directory '{dir_prefix}' "
                    f"(expected '{expected_kind}')"
                )
            break

    # updated format
    if not isinstance(updated, (str, date)):
        issues.append(f"{prefix}: 'updated' must be YYYY-MM-DD")
    elif isinstance(updated, date):
        pass  # yaml parsed it as a date object, fine
    elif not re.match(r"^\d{4}-\d{2}-\d{2}$", str(updated)):
        issues.append(f"{prefix}: 'updated' '{updated}' is not YYYY-MM-DD format")


def main() -> int:
    issues: list[str] = []

    # ── Check 1: manifest.json paths ──
    manifest_path = REPO_ROOT / "docs" / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        issues.append(f"  Cannot read manifest.json: {e}")
        return 1

    manifest_paths: set[str] = set()

    def _collect(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _collect(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for v in obj:
                _collect(v)
        elif isinstance(obj, str) and "/" in obj and obj.endswith((".md", ".py", "/")):
            manifest_paths.add(obj)

    _collect(manifest)

    for mp in sorted(manifest_paths):
        target = REPO_ROOT / mp
        target_dir = REPO_ROOT / mp.rstrip("/")
        if not target.exists() and not target_dir.is_dir():
            issues.append(f"  manifest.json: path not found: {mp}")

    # ── Check 2: skills/ GitHub URL references to docs/ ──
    skills_dir = REPO_ROOT / "skills"
    if skills_dir.is_dir():
        url_pattern = re.compile(
            r"github\.com/wulnkkk/osiris-toolkit/blob/main/docs/([^\s\)\"]+)"
        )
        for skill_file in skills_dir.rglob("*.md"):
            content = skill_file.read_text(encoding="utf-8")
            for match in url_pattern.finditer(content):
                rel_path = match.group(1).split("#")[0]
                target = REPO_ROOT / "docs" / rel_path
                if not target.exists():
                    issues.append(
                        f"  {skill_file.relative_to(REPO_ROOT)}: "
                        f"URL reference to docs/{rel_path} — file not found"
                    )

    # ── Check 3: mkdocs.yml nav entries vs existing doc files ──
    mkdocs_yml = REPO_ROOT / "mkdocs.yml"
    nav_pattern = re.compile(r"^\s+-\s+.+?:\s+(\S[\S/]*\.\w+)", re.MULTILINE)
    try:
        nav_entries = set()
        for match in nav_pattern.finditer(mkdocs_yml.read_text(encoding="utf-8")):
            path = match.group(1).split("#")[0]
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
        for md_file in sorted((REPO_ROOT / "docs").rglob("*.md")):
            rel = str(md_file.relative_to(REPO_ROOT / "docs")).replace("\\", "/")
            if any(rel.startswith(e) for e in excluded):
                continue
            if rel in exempt_files or rel.startswith("_"):
                continue
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

    # ── Check 5: Frontmatter validation ──
    docs_dir = REPO_ROOT / "docs"
    for md_file in sorted(docs_dir.rglob("*.md")):
        rel = str(md_file.relative_to(docs_dir)).replace("\\", "/")
        if any(rel.startswith(p) for p in FM_EXCLUDE_PREFIXES):
            continue
        if rel.startswith("_"):
            continue

        text = md_file.read_text(encoding="utf-8")
        fm_data, _ = _parse_frontmatter(text)
        if fm_data is None:
            issues.append(f"  docs/{rel}: missing or invalid YAML frontmatter")
        else:
            _check_frontmatter(rel, fm_data, issues)

    # ── Report ──
    if issues:
        print(f"[FAIL] {len(issues)} documentation issue(s) found:\n")
        for iss in sorted(set(issues)):
            print(iss)
        return 1
    else:
        print("[PASS] Documentation checks passed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
