# Changelog

All notable changes to **osiris-toolkit** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.16.0] - 2026-06-20

### Added
- AGENTS.md: cross-platform AI agent entry point (auto-loaded by Claude Code, Copilot, Cursor)
- Two agent skills in Agent Skills open standard format (`skills/osiris-user/`, `skills/osiris-dev/`)
- CODE_OF_CONDUCT.md (Contributor Covenant v2.1) and SECURITY.md
- Compliance check system: `check_arch.py` (import architecture), `check_docs_sync.py` (path validity), `check_english.py` (language)
- Makefile targets: `check-all`, `check-arch`, `check-docs`, `check-english`
- Pre-commit hooks for architecture, English, and doc-sync checks
- CI `checks` job (parallel to `test`) running all compliance scripts
- Agent Submit Checklist in `skills/osiris-dev/SKILL.md`
- SemVer versioning policy with explicit `[tool.commitizen.bump_map]` (0.x stays in MINOR for breaking changes)
- Design record: `docs/design/doc-system-architecture.md`

### Changed
- **Agent skills adopted open standard**: migrated from `docs/agent-*` wrappers to `skills/*/SKILL.md` directories with proper `name`/`description` frontmatter
- **Documentation architecture**: `docs/` is now pure human documentation; all agent content lives in `skills/`
- Skills now contain full links to all relevant `docs/` documentation (API reference, user guides, architecture)
- Architecture rules unified across CONTRIBUTING.md, skills, and architecture docs (5 rules, consistent wording)
- README, CONTRIBUTING, docs/index all updated with AI-assisted development/usage guidance
- All cross-references migrated from `docs/agent-*` (deleted) to `skills/`
- Links from skills to human docs use GitHub absolute URLs (avoids mkdocs build issues)

### Removed
- `docs/agent-dev/` and `docs/agent-user/` directories — content migrated to `skills/`
- `mkdocs-include-markdown-plugin` dependency (no longer needed)

### Fixed
- HDF5 support description in user skill (was incorrectly marked as unsupported)
- Circular reference between CONTRIBUTING.md and docs/contributing.md
- CLI command tables no longer duplicated (skill references `cli-reference.md`)
- Mkdocs strict mode build failures from relative links crossing docs/ boundary

## [0.15.0] - 2025-06-09

### Added
- Angular k-space analysis with EPW and hot electron diagnostics
- CLI k-space parameters, `--dry-run`, `--progress`, `--json` output for `sim info`
- QuantifiedGrid, QuantifiedSpectrum helper classes for unit-aware visualization
- UnitSystem registry class with resolved scales
- QuantityKind frozen dataclass with 13 pre-defined instances
- `get_system()` method with `get_converter()` deprecation
- `omega0_norm` field to SimulationParams and `_extract_omega0` helper
- Documentation site with mkdocs-material and mkdocstrings (user guides, API reference, ADRs)

### Changed
- **Breaking**: Full `converter → system` migration across the entire codebase:
  - `plot_field` / `plot_all_fields` / `plot_density` / `plot_phasespace`
  - `plot_k_space` / `plot_spectrum` (removed `/(2π)` normalization)
  - `scattering` / `composite` / `comparison` visualization layers
  - `batch` / `PostVisHub` / `parallel` subsystems
  - `analysis` layer — `KSpaceAnalyzer` returns `QuantifiedSpectrum`
  - `PostProcessor` module
- `mask_energy` now accepts `system` parameter (removed `/(2π)` normalization)
- `save_or_show` reads `config.overwrite`, CLI sets `OsirisConfig`

### Fixed
- Auto-detect projection axis in `_auto_k_range` for k-space plots
- Pass `UnitSystem` to `mask_energy` in `ScatteringAnalyzer`
- Close matplotlib figures after parallel worker plots to prevent memory leak
- Use `grid.time` instead of `axes[0].min` for field plot time title
- Ruff F821/F401 type annotation errors in `compute/integrate.py`

## [0.14.0] - 2025-04-28

### Added
- Simulation split into `_DataAccessors` + `_InfoAccessors` mixins
- Parse helpers extracted to `sim/_parse.py`
- Data model extracted to `_models.py` with `diagnostics` as re-export shim

### Removed
- **Breaking**: Removed deprecated `VisEngine`, `Analyzer`, and wrapper functions

### Changed
- Eliminated `io/compute → sim` reverse dependencies

## [0.13.0] - 2025-04-21

### Added
- Custom exception hierarchy (`OsirisToolkitError` and subclasses) for AI-friendly error handling
- `Simulation.to_dict` / `from_dict` for lightweight serialization
- `PipelineContext.save_snapshot` / `load_snapshot` for interrupt-resume
- `PostVisHub.invalidate_cache` and `set_converter` for AI reuse
- `PostAnalysisHub` integration

## [0.12.0] - 2025-04-09

### Added
- HDF5 reader for grid, particles, and tracks files
- `Simulation` extended to discover and read HDF5 files
- `simulation_info` field to `ZdfFileInfo` for HDF5 metadata
- `hdf5` optional dependency (`h5py>=3.0`)

### Changed
- Updated module documentation for v0.12.0 and v0.13.0 features

## [0.11.0] - 2025-03-23

### Added
- VTK export via pyevtk (`Field.to_vtk`)
- `to_npz()` and `to_csv()` methods on `Field` and `ParticleData`
- `list_iterations` step parameter and `LazySimulation` wrapper
- `vtk` optional dependency (`pyevtk>=1.6`)

## [0.10.0] - 2025-03-14

### Added
- `OsirisConfig` singleton for global configuration
- `OsirisConfig` integration into `Simulation`
- `PipelineContext.dry_run` mode
- `ParticleData.filter()` and `compress()` for particle filtering
- `process_simulation` returns `BatchResult`, supports `progress_callback`
- `save_or_show` reads `config.overwrite`

## [0.9.0] - 2025-03-05

### Added
- RAW particle visualization: scatter, momentum, phasespace, energy spectrum
- TRACKS visualization: orbit, energy evolution, field along track
- `TracksAnalyzer` for track energy and field analysis
- Integration of RAW and TRACKS vis into `PostVisHub`

## [0.8.0] - 2025-02-22

### Added
- Field time-evolution animation with GIF/MP4 output
- Field difference and overlay comparison plots
- Energy timeseries, spectrum colormap, and Poynting vector plots
- Coordinate transform framework with `to_cylindrical`
- Bilinear interpolation in `Field.__getitem__` for float indices
- Symmetrical colormap with `EField`/`BField` presets

### Changed
- Updated module documentation for v0.8.0 new vis features

## [0.7.1] - 2025-02-15

### Fixed
- Removed redundant `.T` transpose in: `plot_field`, `plot_all_fields`, `plot_density`,
  `plot_composite`, `plot_phasespace`, `plot_k_space`, `energy`/`Poynting` plots

## [0.7.0] - 2025-02-02

### Added
- 1D line plot support to `plot_field`
- Particle-to-grid deposition engine (NGP / tophat / triangular / spline3)
- `info_field` / `info_raw` / `info_tracks` metadata-only accessors
- Report modifier full-chain support (savg / senv / line / slice / tavg)
- Centralized logging with `--verbose` / `--quiet` CLI options
- `Field` class with operators and `GridAxis` coordinate methods
- `overwrite=False` protection to `save_or_show`, `plot_field`, and batch functions

### Fixed
- Parallel batch performance bottleneck: create `Simulation` once, pickle to workers
- `print → logger` migration in all vis/ modules
- `Field.__getitem__` bounds handling, `_copy_meta` axis isolation, `mean/std` axis support

## [0.6.0] - 2025-01-19

### Added
- HPC cluster test suite
- Matplotlib Agg backend fix for headless environments

### Changed
- **Breaking**: Post-processing three-layer architecture refactor

## [0.5.0] - 2025-01-10

### Added
- Simulation path ownership: absolute resolve + `output_root`
- `save_or_show` auto-creates parent directories
- Plot functions auto-derive output path from `sim.output_root`
- Batch `output_root` defaults to `sim.output_root` (in-place)
- CLI `vis batch -o` optional; `vis plot` auto-saves

### Changed
- **Breaking**: Path I/O architecture refactor

## [0.4.0] - 2024-12-28

### Added
- Parallel data processing architecture

### Fixed
- Cross-platform issues: remove hardcoded batch output path, drop CJK font config

## [0.3.0] - 2024-12-15

### Added
- Resource prediction module (BatchWalltime, HardwareSpec, resource calibration)

## [0.2.0] - 2024-12-01

### Added
- TIMINGS parser
- Format detection
- Sync tests
- Reader refactor with param descriptions
- Comprehensive test suite (255 tests, 55% coverage)
- Per-module developer documentation (8 modules)
- Bundled test deck fixture for self-contained CI tests

### Fixed
- Three P0 blocking issues

### Changed
- Migrated to `[dependency-groups]` for uv compatibility
- Updated GitHub URLs to `wulnkkk/osiris-toolkit`

## [0.1.0] - 2024-11-10

### Added
- Initial release of osiris-toolkit
- OSIRIS input deck parsing (lexer, parser, validator, reporter)
- ZDF data extraction (reader for grid, particles, tracks)
- Unit conversion framework
- Basic simulation browser
- CLI entry point via click

[Unreleased]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.16.0...HEAD
[0.16.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.15.0...v0.16.0
[0.15.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/wulnkkk/osiris-toolkit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/wulnkkk/osiris-toolkit/releases/tag/v0.1.0
