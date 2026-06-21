# Changelog

All notable changes to **osiris-toolkit** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


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

## v0.17.0 (2026-06-21)

### Feat

- **history**: add HISTORY timeseries analysis and visualization
- add suggest_updates.py — sync suggestion tool
- self-describing documentation system with automated frontmatter validation
- sync Decision Records policy to agent side
- replace note file references with GitHub Issue ADRs
- add GitHub Pages deploy step to Deploy Docs workflow
- add pre-push hook (check-all), CI failure policy, PR CI checkbox

### Fix

- **sim**: support flat {quant}-{species}-{iter}.zdf filenames for DENSITY/RAW/PHA
- **vis**: parallel batch now returns populated BatchResult instead of stub
- **analysis**: unify field_energy_all dict key from energy to total_energy
- update stale path references in docs after Diataxis reorganization
- repair encoding corruption in all docs/ files
- repair encoding corruption in docs/devlog/0.15.0.md
- add --extra docs to checks job so mkdocs is available for docs-build step
- add mkdocs build --strict to CI checks job, so docs build is verified on every push/PR
- quote BREAKING CHANGE key in pyproject.toml bump_map — TOML does not allow spaces in bare keys
- add devlog-exists check to check_docs_sync.py — version bump must have corresponding devlog

### Refactor

- decouple toolchain from uv — remove uv run from Makefile and pre-commit config
- update frontmatter and references for Diataxis structure
- reorganize docs/ into Diataxis structure

## v0.16.0 (2026-06-20)

### Feat

- add compliance check system — arch, doc-sync, english scripts + pre-commit + CI + Agent checklist
- adopt Agent Skills open standard — migrate to .claude/skills/ with spec-compliant frontmatter, docs/ wraps via include-markdown
- add AGENTS.md as cross-platform agent entry point, install Reasonix skills
- **analysis**: comprehensive PIC post-processing - angular k-space + EPW + hot electrons

### Fix

- sync inconsistencies — update stale docs/agent-* paths, unify architecture rules across CONTRIBUTING/dev-skill, add make bump to dev-skill
- update stale maintenance checklist paths from docs/agent-* to skills/
- use absolute URL for CONTRIBUTING.md link in dev-skill.md to fix mkdocs strict build
- simplify Deploy Docs workflow to build-only, remove failing deploy step (requires GitHub Pages config)
- resolve all residual CI issues
- adjust mypy strictness to pass CI with existing codebase
- resolve ruff errors and format issues for CI pass
- **vis**: use grid.time instead of axes[0].min for field plot time title
- **vis**: auto-detect projection axis in _auto_k_range for k-space plots
- **analysis**: pass UnitSystem to mask_energy in ScatteringAnalyzer
- **vis**: close matplotlib figures after parallel worker plots to prevent memory leak
- add UnitSystem to __all__ to fix CI lint error

### Refactor

- migrate all agent docs from docs/agent-* to skills/*/references/, remove include-markdown dependency
- move agent skills to skills/ (cross-platform), remove .claude/ dependency, add config guidance in AGENTS.md
- **docs**: split agent docs into user/dev, add role dimension to frontmatter

## v0.15.0 (2026-06-04)

### Feat

- add CLI k-space params, --dry-run, --progress, sim info --json
- add get_system(); deprecate get_converter()
- add system param to mask_energy, remove /(2*pi) normalization
- add omega0_norm field to SimulationParams and _extract_omega0 helper
- add QuantifiedGrid, QuantifiedSpectrum, and helper classes to vis/_quantified.py
- add UnitSystem registry class with resolved scales
- add QuantityKind frozen dataclass with 13 pre-defined instances
- add PostVisHub.invalidate_cache and set_converter for AI reuse
- add PipelineContext.save_snapshot/load_snapshot for interrupt-resume
- add Simulation.to_dict/from_dict for lightweight serialization
- add custom exception hierarchy for AI-friendly error handling
- extend Simulation to discover and read HDF5 files
- add HDF5 reader for grid, particles, tracks files
- add simulation_info field to ZdfFileInfo for HDF5 metadata
- add list_iterations step param and LazySimulation wrapper
- add VTK export via pyevtk (Field.to_vtk)
- add to_npz() and to_csv() to Field and ParticleData
- add ParticleData.filter() and compress() for particle filtering
- process_simulation returns BatchResult, supports progress_callback
- add PipelineContext.dry_run mode to Pipeline
- save_or_show reads config.overwrite, CLI sets OsirisConfig
- integrate OsirisConfig into Simulation
- add OsirisConfig singleton for global configuration
- integrate RAW and TRACKS vis into PostVisHub
- add TRACKS visualization — orbit, energy evolution, field along track
- add RAW particle visualization — scatter, momentum, phasespace, energy spectrum
- integrate TracksAnalyzer into PostAnalysisHub
- add TracksAnalyzer for track energy and field analysis
- add momentum_stats() to SpeciesAnalyzer
- add MomentumStatsResult dataclass for raw particle analysis
- add field time-evolution animation with GIF/MP4 output (#36)
- add field difference and overlay comparison plots (#35)
- add energy timeseries, spectrum colormap, and Poynting vector plots (#34)
- add coordinate transform framework with to_cylindrical (#39)
- add bilinear interpolation to Field.__getitem__ for float indices (#38)
- add symmetrical colormap with EField/BField presets (#42)
- add overwrite=False protection to save_or_show, plot_field, and batch functions
- add 1D line plot support to plot_field
- add particle-to-grid deposition engine with NGP/tophat/triangular/spline3
- add info_field/info_raw/info_tracks metadata-only accessors
- add report modifier full-chain support (savg/senv/line/slice/tavg)
- add centralized logging with --verbose/--quiet CLI options
- add Field class with operators and GridAxis coordinate methods
- CLI vis batch -o optional, vis plot auto-saves
- VisEngine.batch output_root defaults to sim.output_root
- batch output_root defaults to sim.output_root (in-place)
- plot functions auto-derive output path from sim.output_root
- Simulation path ownership — absolute resolve + output_root

### Fix

- ruff F821/F401 in compute/integrate.py UnitSystem type annotation
- set pipeline logger level to INFO in dry_run test to fix caplog capture
- resolve ruff lint errors — import ordering and F821 OsirisConfig
- clamp float indices to valid range in Field._interpolate
- add input validation and constants to symmetrical_colormap
- remove redundant .T transpose in energy/Poynting plots
- remove redundant .T transpose in k-space plot
- remove redundant .T transpose in plot_phasespace
- remove redundant .T transpose in plot_composite
- remove redundant .T transpose in plot_density
- remove redundant .T transpose in plot_field and plot_all_fields
- resolve test_pipeline naming conflict and exclude hpc tests from CI
- resolve all ruff lint errors (E402 import ordering, E501 line length, F841 unused var)
- resolve F821 undefined name errors (FieldInfo/ParticleInfo/TrackInfo/overwrite)
- complete print->logger migration in all vis/ modules
- Field.__getitem__ bounds handling, _copy_meta axis isolation, mean/std axis support
- save_or_show auto-creates parent directories

### Refactor

- add DeprecationWarning to UnitConverter
- PostProcessor converter→system
- analysis layer converter→system, KSpaceAnalyzer returns QuantifiedSpectrum
- batch/PostVisHub/parallel converter→system
- scattering/composite/comparison converter→system
- plot_spectrum remove /(2π), converter→system
- plot_k_space remove /(2π), add _auto_k_range, converter→system
- plot_phasespace converter→system
- plot_density converter→system
- plot_field/plot_all_fields converter→system
- remove omega0_norm normalization from compute_k_space and spectral_power
- remove deprecated VisEngine, Analyzer, and wrapper functions
- split Simulation into _DataAccessors + _InfoAccessors mixins
- extract parse helpers to sim/_parse.py
- update imports to use _models, eliminate io/compute → sim reverse dependencies
- extract data model to _models.py, keep diagnostics as re-export shim
- replace built-in exceptions with custom exception hierarchy

### Perf

- fix parallel batch bottleneck — create Simulation once, pickle to workers
