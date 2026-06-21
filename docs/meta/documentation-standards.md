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
| `tasks` | List of strings | CLI task names this document covers (user-guide/) |
| `api` | List of strings | Python API names this document covers (api/) |
| `cli` | List of strings | CLI command names this document covers (api/) |
| `module` | string | Python module name this document covers (modules/, api/) |

### `kind` — Controlled Vocabulary

| Value | Meaning | Used in directories |
|-------|---------|---------------------|
| `architecture` | Architectural rule, pipeline, or constraint | `architecture/` |
| `design` | Design decision record — why something was built a certain way | `design/` |
| `guide` | Task-oriented how-to | `user-guide/`, root |
| `index` | Landing / overview page | root |
| `reference` | Exhaustive API / module / changelog reference | `api/`, `modules/`, `devlog/`, root |
| `tutorial` | Step-by-step getting-started | `getting-started/` |

### `topic` — Controlled Vocabulary

| Value | Category |
|-------|----------|
| `api` | api/ files |
| `architecture` | architecture/ files |
| `batch` | user-guide/batch-processing |
| `changelog` | Changelog and devlog files |
| `cli` | user-guide/cli-reference |
| `contributing` | docs/contributing.md |
| `deck` | user-guide/deck-parsing |
| `density` | user-guide/density-plotting |
| `design` | design/ files |
| `faq` | docs/faq.md |
| `field` | user-guide/field-plotting |
| `installation` | getting-started/installation |
| `kspace` | user-guide/kspace-analysis |
| `meta` | docs/meta/ files |
| `modules` | modules/ files |
| `overview` | docs/index.md |
| `parallel` | user-guide/parallel-execution |
| `phasespace` | user-guide/phasespace-plotting |
| `quick-start` | getting-started/quick-start |
| `simulation` | user-guide/simulation-browsing |
| `units` | user-guide/unit-conversion |
| `workflow` | user-guide and getting-started workflow docs |

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
| `api/` | `reference` | `[human, agent]` | `[user, developer]` |
| `architecture/` | `architecture` | `[human, agent]` | `[user, developer]` |
| `design/` | `design` | `[human]` | `developer` |
| `devlog/` | `reference` | `[human, agent]` | `[user, developer]` |
| `getting-started/` | `tutorial` | `[human]` or `[human, agent]` | `user` |
| `meta/` | `reference` | `[human, agent]` | `developer` |
| `modules/` | `reference` | `[human, agent]` | `developer` |
| `user-guide/` | `guide` or `reference` | `[human, agent]` | `user` or `[user, developer]` |
| Root (`index.md`, `faq.md`, etc.) | `guide`, `reference`, or `index` | `[human]` or `[human, agent]` | `user`, `developer`, or `[user, developer]` |

`check_docs_sync.py` enforces these conventions.  Violations block commits.

---

## Related

- Enforced by: `dev-tools/check_docs_sync.py`
- Referenced by: `CONTRIBUTING.md`, `skills/osiris-dev/SKILL.md`, `docs/architecture/_template.md`
- This file is part of the public documentation site (mkdocs nav entry).
