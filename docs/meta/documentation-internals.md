---
audience: [human, agent]
role: developer
topic: meta
kind: explanation
updated: 2026-06-21
---

# Documentation Internals — How the System Works

This document explains the internal design of the osiris-toolkit documentation
and compliance system. It covers **how** things work, not just **what** they do.
For the what and where, see [Project Anatomy](project-anatomy.md) and
[Documentation Standards](documentation-standards.md).

---

## 1. Architecture Overview

```
                    ┌──────────────────────────────┐
                    │  docs/meta/standards.md       │  ← SSOT: defines all rules
                    │  (frontmatter spec, vocab,    │
                    │   kind x directory mapping)    │
                    └──────────────┬───────────────┘
                                   │ read by
                                   ▼
                    ┌──────────────────────────────┐
                    │  check_docs_sync.py           │  ← Validator engine
                    │  - parses YAML frontmatter   │
                    │  - validates against rules    │
                    │  - checks manifest, nav, URLs │
                    └──────────────┬───────────────┘
                                   │ invoked by
                    ┌──────────────┼───────────────┐
                    │              │               │
                    ▼              ▼               ▼
              pre-commit       CI checks        make check-docs
              (per commit)    (per push)        (manual)
                    │              │
                    ▼              ▼
              Block commit    Block merge
              
                                   │
                    ┌──────────────┼───────────────┐
                    │  (other checks run in parallel)
                    │  check_arch.py     ← imports
                    │  check_english.py  ← CJK scan
                    └─────────────────────────────────┘
```

**Key invariant:** `standards.md` defines rules in prose. `check_docs_sync.py` encodes the same rules in Python. When the rules change, both must be updated. The script validates `standards.md` itself against the rules — if you add a new topic but forget the script, the script won't catch violations because the new topic isn't in `VALID_TOPICS`.

---

## 2. Frontmatter Validation Engine

### 2.1 Parsing

```
File content:
  ---\n
  audience: [human, agent]\n
  kind: how-to\n
  ...\n
  ---\n
  # Title\n

Parser:
  1. Check first 4 bytes == "---\n"           → yes? has frontmatter
  2. Find next "---" after offset 4           → end of frontmatter
  3. yaml.safe_load(text[4:end])              → Python dict
  4. Return (dict, body_start_offset)
```

If step 1 fails, the file has **no frontmatter** — hard error.
If step 3 throws YAMLError, **invalid frontmatter** — hard error.

### 2.2 Validation Flow

```
For each .md file under docs/ (excluding note/, _build/):
  1. Parse frontmatter → dict
  2. Check required keys: audience, role, topic, kind, updated
     → missing any? FAIL, stop further checks for this file
  3. Check audience: is list of {human, agent} OR string human/agent
     → invalid? FAIL
  4. Check role: is list of {user, developer} OR string user/developer
     → invalid? FAIL
  5. Check topic: in VALID_TOPICS set?
     → no? FAIL, suggest adding to standards.md
  6. Check kind: in VALID_KINDS set?
     → no? FAIL
  7. Check kind vs directory: does DIR_KIND_MAP[directory_prefix] match?
     → None = skip check (wildcard directory)
     → mismatch? FAIL
  8. Check updated: YYYY-MM-DD format?
     → no? FAIL

Any FAIL → exit code 1, commit blocked
All PASS → exit code 0
```

### 2.3 Why the Script Mirrors the Spec

`VALID_KINDS` in `check_docs_sync.py` is a hardcoded copy of the `kind` table in
`standards.md`. This is intentional — the script is the **executable specification**.
When you add a new kind or topic:

1. Add it to `standards.md` (prose)
2. Add it to `check_docs_sync.py` (code)
3. CI validates both: the new value in the script, and the prose in standards.md
4. Both must be committed together

If we made the script parse standards.md at runtime, a typo in standards.md would
silently break validation. The duplication is the price of reliability.

---

## 3. The Self-Describing Loop

```
standards.md defines:
  kind: explanation  ← legal?
  topic: meta        ← in controlled vocabulary?
  audience: [human, agent]

check_docs_sync.py validates standards.md against the same rules.
If standards.md violates its own rules, CI fails.

Example failure:
  standards.md: topic: made-up-topic
  → check_docs_sync: "topic 'made-up-topic' not in controlled vocabulary"
  → CI red → must fix standards.md

This is "eating your own dogfood" — the meta document is checked by
the same validator it defines the rules for.
```

---

## 4. Compliance Pipeline — End to End

### 4.1 When You Commit

```
git commit
  │
  ├── pre-commit hooks (in order):
  │   trailing-whitespace, end-of-file-fixer, check-yaml, check-toml,
  │   check-added-large-files, check-merge-conflict, debug-statements,
  │   detect-private-key, ruff, ruff-format, mypy, commitizen
  │
  ├── check-arch      (if src/ changed)
  ├── check-english   (always)
  └── check-docs-sync (if docs/ or skills/ or mkdocs.yml changed)
       │
       └── exit 1 → commit blocked, message printed to terminal
```

### 4.2 When You Push

```
git push
  │
  ├── pre-push hook: make check-all
  │   = lint + format-check + typecheck + test-quick + docs-build
  │     + check-arch + check-docs + check-english
  │
  └── GitHub Actions CI:
      ├── test job (3.10, 3.11, 3.12):
      │   ruff check → ruff format check → mypy → pytest
      │
      └── checks job (3.12):
          check_arch.py → check_docs_sync.py → check_english.py
          → mkdocs build --strict
```

### 4.3 When You Release (manual)

```
1. git checkout main, ensure CI green
2. uv run cz bump                    ← auto version + git tag
3. Verify ADR: every arch change has Issue [ADR]
4. Update CHANGELOG.md               ← Unreleased → [vX.Y.Z]
5. git push --follow-tags
6. GitHub Release
   └── triggers deploy-docs.yml → mkdocs build + deploy to Pages
```

---

## 5. Sync Matrix — Change Propagation

When code changes, the sync matrix defines what docs must be reviewed:

```
Trigger                       → Must Review
─────────────────────────────────────────────────────
CLI command added/changed     skills/osiris-user/SKILL.md
                              skills/osiris-user/references/task-map.md
                              docs/manifest.json
                              docs/how-to/cli-reference.md

Python API added/changed      skills/osiris-user/SKILL.md
                              skills/osiris-user/references/task-map.md
                              docs/manifest.json
                              docs/reference/api/<module>.md
                              docs/reference/modules/<module>.md

Data model changed            skills/osiris-dev/SKILL.md
(exceptions, _models)         CONTRIBUTING.md, AGENTS.md
                              docs/explanation/architecture/
                              docs/reference/modules/_models.md

New module / new dependency   skills/osiris-dev/SKILL.md
                              CONTRIBUTING.md, AGENTS.md
                              docs/explanation/architecture/
                              GitHub Issue [ADR]

File added/removed in docs/   mkdocs.yml nav
                              docs/manifest.json
```

**Enforcement:** `dev-tools/suggest_updates.py` reads `git diff` and maps changed
files against this matrix. It prints suggestions but never blocks. The actual
enforcement is via pre-commit `check-docs-sync` (path existence) + human review
(PR checklist + release checklist).

---

## 6. Agent Integration

```
Agent loads project
  │
  ├── AGENTS.md auto-discovered → directs to skills/
  │
  ├── skills/osiris-user/SKILL.md
  │     - CLI quick reference
  │     - Python API entry points
  │     - Decision trees for common tasks
  │     - Links to docs/how-to/ via GitHub URLs
  │
  └── skills/osiris-dev/SKILL.md
        - Architecture rules (linked from docs/explanation/)
        - Submit Checklist (16 items)
        - Decision Records policy
        - Release Process
        - Links to docs/reference/modules/ via GitHub URLs

skills/ → docs/ links use absolute GitHub URLs:
  https://github.com/wulnkkk/osiris-toolkit/blob/main/docs/...

Why absolute? skills/ is outside the mkdocs build tree. Relative paths
would break. check_docs_sync.py validates that every such URL resolves
to an actual file in the repo.

Known risk: if the default branch is renamed (main → master), all URLs break.
This is documented but accepted as low probability.
```

---

## 7. Key Implementation Details

### 7.1 Why YAML Frontmatter + Python, Not JSON Schema

- YAML frontmatter is native to mkdocs/Jekyll/Hugo — zero tooling overhead
- Python validation runs in CI without npm/pip install of schema validators
- The rules are simple enough (6 kinds, 20 topics, 5 required fields) that a
  full schema language would be over-engineering

### 7.2 Why `note/` Is Excluded From Everything

```
.gitignore          → never committed
mkdocs.yml          → never published
check_english.py    → allowed to contain Chinese
check_docs_sync.py  → not validated for frontmatter
```

Purpose: developer-local workspace. Chinese analysis, draft designs, raw test
reports. The exclusion is by design, not oversight.

### 7.3 Why `_template.md` Is in arch, Not Meta

`docs/explanation/architecture/_template.md` is the template for new architecture
documents. It's in architecture/ because it describes architecture document format.
It references `docs/meta/documentation-standards.md` for the full spec — the
template is a quick start, the standards file is the authority.

---

## 8. Current Gaps

| Gap | Why | Plan |
|-----|-----|------|
| `suggest_updates.py` is advisory only | Semantic sync is inherently non-automatable | Accept as known limitation |
| `check_docs_sync.py` hardcodes rules from standards.md | See §2.3 | Accept as reliability trade-off |
| No CI check for ADR existence | Deciding what's "architectural" requires human judgment | Covered by Release Process step 3 (manual) |
| `blob/main/` URLs brittle to branch rename | GitHub convention, low risk | Monitor, fix if main is ever renamed |

---

## Related

- [Documentation Standards](documentation-standards.md) — frontmatter spec and vocabularies
- [Project Anatomy](project-anatomy.md) — directory map and tool reference
- [Doc System Architecture Design](../explanation/design/doc-system-architecture.md) — original design decisions
