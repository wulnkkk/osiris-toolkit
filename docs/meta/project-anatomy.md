---
audience: [human, agent]
role: [user, developer]
topic: meta
kind: reference
updated: 2026-06-21
---

# Project Anatomy

A map of every directory, config file, and tool in this repository — so you can
find what you need without guessing.

---

## Entry Points by Persona

| I am a… | Start here | Then go to… |
|----------|-----------|-------------|
| **User** (want to process data) | [README.md](https://github.com/wulnkkk/osiris-toolkit#readme) | `tutorials/` → `how-to/` → `reference/api/` |
| **Contributor** (want to change code) | [CONTRIBUTING.md](https://github.com/wulnkkk/osiris-toolkit/blob/main/CONTRIBUTING.md) | `explanation/architecture/` → `explanation/design/` → `reference/modules/` |
| **AI Agent** (helping a user/contributor) | [AGENTS.md](https://github.com/wulnkkk/osiris-toolkit/blob/main/AGENTS.md) | `skills/osiris-user/` or `skills/osiris-dev/` |
| **Lost** (want to understand the repo) | This file | Keep reading ↓ |

---

## Directory Map

```
osiris-toolkit/
│
├── src/osiris_toolkit/     ← Core library (Python package)
│   ├── deck/               │  Input deck parser (lexer + recursive-descent)
│   ├── io/                 │  ZDF / HDF5 binary readers (stateless, thread-safe)
│   ├── sim/                │  Simulation directory discovery + data accessors
│   ├── units/              │  UnitSystem + QuantityKind (13 physical dimensions)
│   ├── compute/            │  Pure math: FFT, integration, deposition
│   ├── analysis/           │  Diagnostic-specific analysis (EMF, scattering, k-space,…)
│   ├── vis/                │  Visualization (field, density, raw, tracks, k-space,…)
│   ├── resource/           │  HPC resource estimator (memory, runtime, disk)
│   ├── parallel/           │  Multi-worker detection + task splitting
│   ├── workflow/           │  YAML pipeline + post-processing workflow
│   ├── sync/               │  Version sync utility
│   ├── _models.py          │  Foundation data model dataclasses (GridData, ParticleData,…)
│   ├── _generated/         │  Auto-generated parameter definitions (do not edit)
│   ├── exceptions.py       │  12-class exception hierarchy
│   ├── config.py           │  OsirisConfig global singleton
│   ├── cli.py              │  Click CLI (6 command groups)
│   ├── postproc.py         │  PostProcessor unified entry point
│   └── _logging.py         │  Internal logging configuration
│
├── docs/                   ← Human documentation (published via mkdocs)
│   ├── meta/               │  Documentation about the documentation
│   ├── getting-started/    │  Tutorials: install, quick-start, basic workflow
│   ├── user-guide/         │  Task-oriented how-to guides
│   ├── api/                │  Auto-generated API reference (mkdocstrings)
│   ├── modules/            │  Per-module internals and design notes
│   ├── architecture/       │  Architecture rules, data flow, dependency hierarchy
│   ├── design/             │  Design decision records (why things are built a certain way)
│   ├── devlog/             │  Per-version technical release logs (v0.1.0 – v0.16.0)
│   ├── note/               │  Developer-local workspace (gitignored, not published)
│   ├── index.md            │  Documentation home page
│   ├── faq.md              │  Frequently asked questions
│   ├── contributing.md     │  Quick-reference contributor guide
│   ├── CHANGELOG.md        │  Version changelog summary
│   └── manifest.json       │  Agent entry-point registry
│
├── skills/                 ← AI agent skills (Agent Skills open standard)
│   ├── osiris-dev/         │  Developer skill: architecture rules, workflow, testing
│   └── osiris-user/        │  User skill: CLI/Python API, decision trees, recipes
│
├── dev-tools/              ← Development automation scripts
│   ├── check_arch.py       │  Blocking: verify module dependency hierarchy
│   ├── check_docs_sync.py  │  Blocking: verify manifest, nav, URL, and frontmatter
│   ├── check_english.py    │  Blocking: scan for non-English (CJK/Cyrillic) content
│   ├── extract_definitions.py │  Generate: create _generated/ from OSIRIS Fortran source
│   └── suggest_updates.py  │  Advisory: suggest doc updates based on git diff
│
├── .github/                ← GitHub-specific configuration
│   ├── workflows/          │  CI/CD: ci.yml (test+checks), deploy-docs.yml (mkdocs deploy)
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/     │  bug_report, feature_request, adr templates
│
├── tests/                  ← pytest test suite
│   ├── test_deck/          │  Deck parser tests
│   ├── test_io/            │  ZDF/HDF5 reader tests
│   ├── test_sim/           │  Simulation discovery tests
│   ├── test_units/         │  UnitSystem/QuantityKind tests
│   ├── test_compute/       │  FFT/integration/deposition tests
│   ├── test_vis/           │  Visualization tests (skipped without real data)
│   ├── test_analysis/      │  Analysis tests
│   └── hpc/                │  HPC cluster integration tests (manual, not CI)
│
├── examples/               ← Usage example scripts
│
├── pyproject.toml           ← Build config, dependencies, ruff/mypy/pytest/commitizen settings
├── Makefile                 ← One-command dev automation (lint, test, check-all, bump…)
├── .pre-commit-config.yaml  ← 13 git hooks (format, typecheck, arch, english, doc-sync…)
├── mkdocs.yml               ← Documentation site config + full navigation tree
├── AGENTS.md                ← Cross-platform entry point for all AI tools
├── README.md                ← User-facing project overview + quick start
├── CONTRIBUTING.md          ← Full contributor guide (rules, workflow, release process)
├── CHANGELOG.md             ← Root-level changelog (mirrored in docs/CHANGELOG.md)
├── LICENSE                  ← MIT
├── CODE_OF_CONDUCT.md       ← Contributor Code of Conduct
├── SECURITY.md              ← Security policy
├── .gitignore               ← Git ignore rules (excludes docs/note/, _build/, .ipynb…)
└── .python-version          ← Python version pin (>=3.10)
```

---

## Configuration Files — Who Owns What

| File | Owns | Must Not Be Edited By Hand |
|------|------|---------------------------|
| `pyproject.toml` | Build system + ruff/mypy/pytest/commitizen config | `[project] name/version` via `cz bump` only |
| `.pre-commit-config.yaml` | Git hooks (what runs on every commit/push) | — |
| `mkdocs.yml` | Documentation site structure and nav | — |
| `.gitignore` | What files are excluded from version control | — |
| `.python-version` | Target Python version for `uv` | — |

---

## dev-tools Scripts

| Script | Type | Called by | What it checks |
|--------|------|-----------|----------------|
| `check_arch.py` | **Blocking** | pre-commit + CI | AST scan: no reverse dependencies across layers, no deprecated `UnitConverter` usage |
| `check_docs_sync.py` | **Blocking** | pre-commit + CI | `manifest.json` paths, `skills/` URL references, `mkdocs.yml` nav entries, frontmatter compliance |
| `check_english.py` | **Blocking** | pre-commit + CI | CJK/Cyrillic/non-Latin characters in `.py` and `.md` files (excludes `docs/note/`) |
| `extract_definitions.py` | **Manual** | Developer | Re-generates `src/osiris_toolkit/_generated/` from OSIRIS Fortran source |
| `suggest_updates.py` | **Advisory** | `make suggest-updates` | Reads `git diff`, maps changed files to docs that may need updating |

### How They Are Wired

```
git commit  →  .pre-commit-config.yaml
                 ├── check-arch       (if src/ changed)
                 ├── check-docs-sync  (if docs/skills/mkdocs changed)
                 └── check-english    (always)

git push    →  .pre-commit-config.yaml (pre-push stage)
                 └── check-all  (lint + typecheck + test + docs-build + all 3 checks)

CI on PR   →  .github/workflows/ci.yml
                 ├── test job     (ruff + mypy + pytest, 3 Python versions)
                 └── checks job   (check_arch + check_docs_sync + check_english + mkdocs build)
```

---

## CI/CD Pipelines

### `ci.yml` — Runs on every push and PR to `main`

| Job | Steps | Purpose |
|-----|-------|---------|
| **test** (matrix: 3.10, 3.11, 3.12) | ruff lint → ruff format check → mypy → pytest (fast) | Code quality + tests across Python versions |
| **checks** (3.12 only) | check_arch → check_docs_sync → check_english → mkdocs build --strict | Architecture + documentation + language compliance |

### `deploy-docs.yml` — Runs on push to `main` only

Builds mkdocs site and deploys to GitHub Pages. Uses `mkdocs build --strict` — any broken link blocks deployment.

---

## Makefile Quick Reference

```bash
make lint          # ruff check
make format-check  # ruff format --check
make typecheck     # mypy
make test          # full test suite
make test-quick    # fast tests only (excludes slow + data markers)
make test-cov      # test with coverage report
make docs-serve    # local docs preview (http://localhost:8000)
make docs-build    # strict build (catches broken links)
make check-all     # everything (lint + typecheck + test + docs + arch + sync + english)
make check-arch    # architecture dependency check only
make check-docs    # documentation sync check only
make check-english # language check only
make suggest-updates  # show which docs may need updating
make precommit     # run all pre-commit hooks manually
make bump          # interactive version bump (commitizen)
make clean         # remove build artifacts and caches
```

---

## Related

- [Documentation Standards](documentation-standards.md) — frontmatter spec and controlled vocabularies
- [Architecture Overview](../explanation/architecture/overview.md) — design principles and layer hierarchy
- [CONTRIBUTING.md](https://github.com/wulnkkk/osiris-toolkit/blob/main/CONTRIBUTING.md) — full contributor guide
- [AGENTS.md](https://github.com/wulnkkk/osiris-toolkit/blob/main/AGENTS.md) — AI agent entry point
