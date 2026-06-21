---
audience: [human, agent]
role: developer
topic: meta
kind: reference
updated: 2026-06-21
---

# Documentation Standards

This file defines the frontmatter specification and document conventions for
all files under `docs/`. It is **self-describing**: the rules below apply to
this file itself, and `dev-tools/check_docs_sync.py` reads this file to validate
the rest of the repository.

When a rule changes here, CI automatically re-validates all documents against
the new rule.

---

## Frontmatter Specification

Every `.md` file under `docs/` must have YAML frontmatter delimited by `---`.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `audience` | `[human]`, `[agent]`, or `[human, agent]` | Who this document is written for |
| `role` | `user`, `developer`, or `[user, developer]` | What the reader needs to know to use this document |
| `topic` | Controlled vocabulary (see below) | What this document is about |
| `kind` | Controlled vocabulary (see below) | What type of document this is |
| `updated` | `YYYY-MM-DD` | Date of last meaningful content change |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `tasks` | List of strings | CLI task names this document covers (how-to/) |
| `api` | List of strings | Python API names this document covers (reference/api/) |
| `cli` | List of strings | CLI command names this document covers (reference/api/) |
| `module` | string | Python module name this document covers (reference/modules/, reference/api/) |

### `kind` — Controlled Vocabulary

| Value | Meaning | Used in directories |
|-------|---------|---------------------|
| `how-to` | Task-oriented how-to guide | `how-to/` |
| `index` | Landing / overview page | root |
| `reference` | Exhaustive API / module / changelog reference | `reference/api/`, `reference/modules/`, `devlog/`, root |
| `tutorial` | Step-by-step getting-started | `tutorials/` |
| `explanation` | Architectural rules, design decisions, pipelines | `explanation/` |

### `topic` — Controlled Vocabulary

| Value | Category |
|-------|----------|
| `api` | reference/api/ files |
| `architecture` | explanation/architecture/ files |
| `batch` | how-to/batch-processing |
| `changelog` | Changelog and devlog files |
| `cli` | how-to/cli-reference |
| `contributing` | docs/contributing.md |
| `deck` | how-to/deck-parsing |
| `density` | how-to/density-plotting |
| `design` | explanation/design/ files |
| `faq` | docs/faq.md |
| `field` | how-to/field-plotting |
| `installation` | tutorials/installation |
| `kspace` | how-to/kspace-analysis |
| `meta` | docs/meta/ files |
| `modules` | reference/modules/ files |
| `overview` | docs/index.md |
| `parallel` | how-to/parallel-execution |
| `phasespace` | how-to/phasespace-plotting |
| `quick-start` | tutorials/quick-start |
| `simulation` | how-to/simulation-browsing |
| `units` | how-to/unit-conversion |
| `workflow` | how-to and tutorials workflow docs |

To add a new topic: add it to this table, then update this file's `updated` date.
CI will validate the new vocabulary against all documents on the next run.

### `role` — Controlled Vocabulary

| Value | For documents that assume the reader can... |
|-------|---------------------------------------------|
| `user` | Use CLI / Python API (no source code knowledge needed) |
| `developer` | Read and modify source code |
| `[user, developer]` | Either role |

---

## Directory Conventions

| Directory | Expected `kind` | Expected `audience` | Expected `role` |
|-----------|----------------|---------------------|-----------------|
| `how-to/` | `how-to` | `[human, agent]` | `user` or `[user, developer]` |
| `reference/api/` | `reference` | `[human, agent]` | `[user, developer]` |
| `reference/modules/` | `reference` | `[human, agent]` | `developer` |
| `explanation/` | `explanation` | `[human, agent]` | `[user, developer]` or `developer` |
| `devlog/` | `reference` | `[human, agent]` | `[user, developer]` |
| `tutorials/` | `tutorial` | `[human]` or `[human, agent]` | `user` |
| `meta/` | `reference` or `explanation` | `[human, agent]` | `developer` |
| Root (`index.md`, `faq.md`, etc.) | `how-to`, `reference`, or `index` | `[human]` or `[human, agent]` | `user`, `developer`, or `[user, developer]` |

`check_docs_sync.py` enforces these conventions.  Violations block commits.

---

## Related

- Enforced by: `dev-tools/check_docs_sync.py`
- Referenced by: `CONTRIBUTING.md`, `skills/osiris-dev/SKILL.md`, `docs/explanation/architecture/_template.md`
- This file is part of the public documentation site (mkdocs nav entry).
