---
audience: [human]
role: [developer, user]
topic: design
kind: design
updated: 2026-06-20
---

# Documentation System Architecture — Agent Skills & Compliance Design

This document records the architectural decisions, design rationale, and
migration history of the osiris-toolkit documentation system, including
the separation of agent skills from human docs and the compliance
enforcement system.

---

## Context

osiris-toolkit serves two audiences (users + developers) across two
channels (human readers + AI agents). This creates four distinct personas:

| Persona | Role | Entry point | Format |
|---------|------|-------------|--------|
| Human-User | Uses CLI/Python API for data processing | `README.md` → mkdocs site | HTML website |
| Agent-User | AI assistant helping process data | `AGENTS.md` → `skills/osiris-user/SKILL.md` | Markdown |
| Human-Dev | Contributes code to the project | `CONTRIBUTING.md` → mkdocs site | HTML website |
| Agent-Dev | AI assistant helping write code | `AGENTS.md` → `skills/osiris-dev/SKILL.md` | Markdown |

Initially, both sets of content lived under `docs/agent-user/` and
`docs/agent-dev/`. This had several problems (see Problem below).

---

## Problem

1. **Semantic mismatch**: Files under `docs/` are published on the mkdocs
   website (audience: human). But agent-skill content has `audience: agent`
   frontmatter — it was never meant for human readers.

2. **Cross-platform lock-in**: The initial implementation used `.claude/skills/`
   (Claude Code convention). This tied the canonical skill source to a
   single AI platform, contradicting the project's platform-neutral stance.

3. **Build dependency**: Wrapper files in `docs/agent-*/` used
   `mkdocs-include-markdown-plugin` to include from `.claude/skills/`.
   This required a non-standard plugin dependency that failed silently on
   path resolution issues.

4. **No compliance enforcement**: Architecture rules (no reverse deps,
   layer hierarchy, English-only) were documented but never automated.
   Both human developers and AI agents could unknowingly violate them.

5. **No sync mechanism**: When CLI or API changed, there was no automated
   reminder to update the corresponding agent skill files.

---

## Decision 1: Separate Skills from Docs

### Decision

Move all agent-facing content out of `docs/` into a top-level `skills/`
directory. The `docs/` directory becomes a **pure human documentation**
space, published exclusively via mkdocs.

### Rationale

- Aligns with the [Agent Skills open standard](https://agentskills.io/)
  (directory `skill-name/SKILL.md` with YAML frontmatter)
- Removes the semantic ambiguity of `docs/agent-*/`
- Eliminates the need for `mkdocs-include-markdown-plugin`
- Makes the canonical source discoverable at a consistent path
  (`skills/osiris-dev/SKILL.md`) regardless of AI platform

### Directory layout

```
osiris-toolkit/
├── skills/
│   ├── osiris-dev/                     # Developer skill
│   │   ├── SKILL.md                    # Frontmatter: name, description
│   │   └── references/
│   │       └── task-map.md             # Auxiliary reference
│   └── osiris-user/                    # User skill
│       ├── SKILL.md
│       └── references/
│           ├── task-map.md
│           └── recipes/                # Step-by-step walkthroughs
├── docs/                               # Human documentation only
├── AGENTS.md                           # Cross-platform entry point
└── CONTRIBUTING.md                     # Human contributor guide
```

### Rejected alternatives

| Alternative | Why rejected |
|-------------|-------------|
| Keep in `.claude/skills/` | Platform-specific (Claude Code only) |
| Keep in `docs/agent-*/` with include plugin | Build dependency + semantic mismatch |
| Symlink `docs/agent-*/` → `.claude/skills/` | Windows git core.symlinks=false |

---

## Decision 2: Cross-Reference Strategy

### Decision

Use two link styles depending on the target:

| Source → Target | Link style | Example |
|-----------------|-----------|---------|
| `AGENTS.md` → `skills/` | **Local** relative | `skills/osiris-dev/SKILL.md` |
| `docs/*.md` → `AGENTS.md` | **Local** relative | `AGENTS.md` |
| `skills/*/SKILL.md` → `docs/` | **Absolute** GitHub URL | `https://github.com/.../docs/...` |
| `skills/*/SKILL.md` → `skills/` | **Local** relative | `references/task-map.md` |
| `docs/*.md` → `docs/` | **Local** relative | `user-guide/cli-reference.md` |

### Rationale

- Links within `docs/` must be local/relative for mkdocs to resolve them
  correctly during `mkdocs build --strict`.
- Links from `skills/` to `docs/` must be absolute GitHub URLs because
  skills live outside the mkdocs build tree. Relative paths would either
  break mkdocs (file not found) or resolve to wrong targets.
- Links within `skills/` use local relative paths as recommended by the
  Agent Skills spec (progressive disclosure).
- All local links are verified by `dev-tools/check_docs_sync.py` in CI.

---

## Decision 3: Cross-Platform Entry Point

### Decision

Place `AGENTS.md` at the project root as the single cross-platform entry
point for all AI tools.

### Rationale

- Recognized by Claude Code, Cursor, GitHub Copilot, and Reasonix
  (see [GitHub docs on AGENTS.md](https://docs.github.com/en/copilot/...))
- Auto-loaded every session — gives any AI tool immediate project context
- Contains platform-specific configuration guides for Claude Code, Cursor,
  Copilot, and Reasonix
- Avoids needing separate `CLAUDE.md`, `.cursorrules`, etc.

---

## Decision 4: Five-Layer Compliance System

### Decision

Enforce project norms through five complementary layers:

| Layer | Mechanism | What it catches | Applies to |
|-------|-----------|----------------|------------|
| 1. Agent guide | `skills/osiris-dev/SKILL.md` Submit Checklist | Architecture rules, sync matrix, pre-submit verification | Agents |
| 2. Pre-commit | 13 git hooks | Format, types, arch deps, English, doc sync, private keys | Both |
| 3. CI | `checks` job (parallel to `test`) | Arch deps, doc sync, English (on push/PR) | Both |
| 4. Sync matrix | `CONTRIBUTING.md` maintenance checklist | CLI/API/architecture change → corresponding skill files | Both |
| 5. PR checklist | `CONTRIBUTING.md` + GitHub PR template | Human verification before merge | Humans |

### Compliance scripts

| Script | What it checks |
|--------|----------------|
| `dev-tools/check_arch.py` | AST-based import scan: no reverse dependency across layers, no `UnitConverter` usage |
| `dev-tools/check_docs_sync.py` | All `manifest.json` paths exist; all `skills/` URL refs to `docs/` resolve; mkdocs nav entries match files on disk |
| `dev-tools/check_english.py` | CJK/Cyrillic/non-Latin character scan, excluding `docs/note/` and test data |

### Makefile targets

```makefile
make check-all      # Lint + format-check + typecheck + test-quick + docs-build + arch + doc-sync + english
make check-arch     # Architecture dependency check only
make check-docs     # Documentation sync check only
make check-english  # English language check only
```

---

## Decision 5: Change Synchronization Matrix

### Decision

Define the set of files that must be updated together for each type
of change, documented in `CONTRIBUTING.md` §When Adding/Changing Public
API.

| Change type | Files to update |
|-------------|----------------|
| **CLI command** changed/added | `skills/osiris-user/SKILL.md` + `references/task-map.md` + `docs/manifest.json` |
| **Python API** changed/added | `skills/osiris-user/SKILL.md` + `references/task-map.md` + `docs/manifest.json` |
| **Architecture rule** changed | `skills/osiris-dev/SKILL.md` + `CONTRIBUTING.md` + `AGENTS.md` |
| **Dev workflow** changed | `CONTRIBUTING.md` + `docs/contributing.md` + `skills/osiris-dev/SKILL.md` + `AGENTS.md` |
| **File** added/removed | `mkdocs.yml` nav + `docs/manifest.json` |

The `check-all` target and CI `checks` job verify that all referenced
paths are valid, but they cannot verify semantic accuracy of the sync.
That requires human (or agent) diligence via the PR/Submit checklist.

## Versioning Policy

This project follows [Semantic Versioning 2.0.0](https://semver.org/). During
the **0.y.z** initial development phase:

| Change type | Bump | Example |
|-------------|------|---------|
| Breaking API change | MINOR | `0.15.0` → `0.16.0` |
| Backward compatible feature | MINOR | `0.15.0` → `0.16.0` |
| Bug fix | PATCH | `0.15.0` → `0.15.1` |

Both `BREAKING CHANGE` and `feat` increment MINOR while version is 0.x.
When the project graduates to 1.0.0, `BREAKING CHANGE` will revert to
incrementing MAJOR. See `[tool.commitizen.bump_map]` in `pyproject.toml`
for the current mapping.

---

## Migration History

| Step | What changed | Files affected |
|------|-------------|----------------|
| 1 | Created `AGENTS.md` as cross-platform entry point | +1 |
| 2 | Moved skills from `.claude/skills/` to `skills/` | ~6 |
| 3 | Replaced `docs/agent-*/` wrappers with direct `skills/` files | ~5 |
| 4 | Removed `mkdocs-include-markdown-plugin` dependency | ~2 |
| 5 | Updated all cross-references to use GitHub URLs where needed | ~5 |
| 6 | Added `dev-tools/check_*.py` compliance scripts | +3 |
| 7 | Added pre-commit hooks and CI checks job | ~3 |
| 8 | Added Agent Submit Checklist to `skills/osiris-dev/SKILL.md` | ~1 |

---

## Consequences

### Positive

- **Single source of truth**: `skills/*/SKILL.md` is the canonical skill
  content; nothing is duplicated.
- **Platform-neutral**: `skills/` works with any AI tool without configuration.
- **No build dependency**: mkdocs builds without plugins.
- **Automated enforcement**: 3 new CI checks catch architecture, doc-sync,
  and language violations before merge.
- **Agent-guarded**: Agents loading `osiris-dev` skill get the Submit
  Checklist before making changes.

### Negative

- **GitHub URL brittleness**: URLs in skill files contain `blob/main/`.
  If the default branch is renamed, all URLs break.
- **No automated semantic sync**: The sync matrix is documented but not
  enforced — a CLI change could be merged without updating the user skill
  if the developer skips the checklist.
- **Pre-commit scripts are Python**: `check_arch.py` etc. are Python
  scripts, adding a small overhead compared to native pre-commit hooks.

### Mitigations

- URLs use `blob/main/` consistently. Branch rename is a project-level
  decision that would trigger a bulk URL update.
- CI `checks` job verifies path existence but not semantic accuracy.
  This is a fundamental limitation of static analysis; semantic review
  remains the responsibility of the PR/submit checklist.
- Scripts run only on staged/changed files via pre-commit's `files:` filter,
  so overhead is negligible in practice.

---

## Future Considerations

1. **Auto-generation**: Consider a script that extracts CLI definitions
   from `click` decorators and auto-updates `skills/osiris-user/SKILL.md`
   and `docs/user-guide/cli-reference.md`.

2. **Skill validation**: Use `skills-ref validate` (from the Agent Skills
   reference implementation) to validate `skills/*/SKILL.md` frontmatter
   in CI.

3. **Version pinning**: Consider adding a `compatibility` field to skill
   frontmatter indicating the minimum osiris-toolkit version required.

---

## Related

- Devlog: `docs/devlog/0.16.0.md` — release implementing this design
- ADR: This design doc was created before the ADR Issue system was established.
