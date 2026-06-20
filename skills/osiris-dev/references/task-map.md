---
audience: [agent]
role: developer
topic: dev-task-map
kind: reference
updated: 2026-06-20
---

# Agent Dev Task Map — Development Intent to Code Action

Each entry maps a development intent to the relevant code locations, patterns, and commands.

> For the **User** task map (how to process simulation data), see [`skills/osiris-user/references/task-map.md`](../../osiris-user/references/task-map.md).

---

## add a new analysis function

- **Intent:** "add energy spectrum", "new analyzer", "add scattering diagnostic"
- **Location:** `src/osiris_toolkit/analysis/`
- **Pattern:**
  1. Create a new `*Analyzer` class following the protocol in `_protocol.py`
  2. Define result dataclass in `_result_types.py` (if needed)
  3. Register in `__init__.py` `__all__`
  4. Expose through `PostAnalysisHub` if appropriate
- **Example:** `analysis/scattering.py` → `ScatteringAnalyzer`
- **Test:** `tests/test_analysis/`

## add a new visualization

- **Intent:** "plot density", "new vis type", "add k-space plot"
- **Location:** `src/osiris_toolkit/vis/`
- **Pattern:**
  1. Create a new plot function accepting `sim`, `system`, `output` params
  2. Use `QuantifiedGrid` for unit-aware data access
  3. Register in `__init__.py` `__all__`
  4. Optionally integrate into `PostVisHub`
- **Key conventions:**
  - Plot functions save to disk, don't `plt.show()`
  - Accept `output: str | Path | None` parameter
  - Use `system` parameter (not deprecated `converter`)
- **Test:** `tests/test_vis/`

## add a new CLI command

- **Intent:** "add CLI subcommand", "new vis subcommand", "extend CLI"
- **Location:** `src/osiris_toolkit/cli.py`
- **Pattern:**
  1. Add a `@click.group()` or `@click.command()` function
  2. Wire into existing group (e.g., `vis_plot` under `vis` group)
  3. Use `OsirisConfig` for global defaults
- **Key conventions:**
  - CLI commands delegate to Python API (thin wrapper pattern)
  - `--dry-run`, `--progress`, `--json` flags for agent-friendly output
- **Test:** `tests/test_cli/`

## add a new data format reader

- **Intent:** "read HDF5", "add VTK support", "new ZDF type"
- **Location:** `src/osiris_toolkit/io/`
- **Pattern:**
  1. Add reader function in `_reader_hdf5.py` (for HDF5) or `_reader.py` (for ZDF)
  2. Update `_types.py` if new record types needed
  3. Extend `Simulation` discovery in `sim/simulation.py`
- **Key file:** `io/__init__.py` defines `read_grid`, `read_particles`, `read_tracks`, `read_info`

## add a new physical quantity for unit conversion

- **Intent:** "add temperature unit", "new QuantityKind"
- **Location:** `src/osiris_toolkit/units/_quantity.py`
- **Pattern:**
  1. Add a new `QuantityKind(...)` instance in `_quantity.py`
  2. If it has a wavenumber dimension, also update `_build_wavenumber_scales` in `converter.py`
  3. The new quantity becomes available in `UnitSystem` automatically
- **Note:** `UnitConverter` is deprecated — only extend `UnitSystem`

## refactor a module (non-breaking)

- **Intent:** "extract helper", "rename function", "split module"
- **Rules:**
  - Maintain public API exports in `__init__.py`
  - Deprecate old names with `DeprecationWarning` (1-version deprecation cycle)
  - Never break the dependency hierarchy
- **Check:** `uv run ruff check src/` must pass with no new errors

## make a breaking change

- **Intent:** "remove deprecated API", "change function signature"
- **Process:**
  1. Mark old API as deprecated first (1 version prior)
  2. Use `refactor!` or `feat!` commit type
  3. Update `CHANGELOG.md` with migration notes
  4. Update all callers in tests, examples, and docs
- **Check:** `git log --oneline -S "deprecated"` to find deprecation history

## regenerate `_generated/` files

- **Intent:** "update parameter definitions", "sync with OSIRIS source"
- **Command:** `python dev-tools/extract_definitions.py /path/to/osiris-1.0.0/source`
- **Output:** `src/osiris_toolkit/_generated/{parameters,quantities,sections}.py`
- **Note:** These files are read-only — never edit manually

## run the full verification suite

- **Intent:** "verify changes", "pre-submit check"
- **Commands:**
  ```bash
  make lint        # ruff check
  make format      # ruff format
  make typecheck   # mypy
  make test        # pytest (without slow/data markers)
  make docs-build  # mkdocs strict build
  ```
- **Expected:** Lint/typecheck/docs clean; tests: 500+ pass, 1 known pipeline failure

## release a new version

- **Intent:** "bump version", "release vX.Y.Z"
- **Steps:**
  1. `uv run cz bump --changelog` — bumps version, creates tag
  2. Manual: update `[Unreleased]` → `[vX.Y.Z]` in `CHANGELOG.md`, add date
  3. `git push --follow-tags`
  4. Create GitHub Release
- **Note:** Tag format is `v$version` (e.g., `v0.16.0`)

## fix a privacy leak

- **Intent:** "remove hardcoded path", "PII in git history"
- **Pre-commit check:** Search for `/work/home/`, `xiaochengzhuo`, cluster paths
- **If already committed:** `git filter-branch --tree-filter 'sed -i "s|OLD_PATH|NEW_PATH|g" files...' -- origin/main..HEAD`
- **After rewrite:** `git push --force-with-lease`
