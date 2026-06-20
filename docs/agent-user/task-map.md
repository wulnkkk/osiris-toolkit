---
audience: [agent]
role: user
topic: agent
kind: reference
updated: 2026-06-20
---

# Agent Task Map — User Intent to Tool Invocation

Each entry maps a user intent (English or Chinese trigger phrases) to concrete CLI commands and Python API calls.

## discover simulations

- **Trigger:** "find simulations", "list sims", "scan directory"
- **CLI:** `osiris-toolkit sim info <DIR>`
- **CLI (batch):** (scan manually; no built-in recursive scan)
- **API:** `Simulation(str(path))`, then `sim.list_fields()`, `sim.list_species()`
- **Pre-condition:** Directory must contain MS/ subdirectory with ZDF files
- **Verify:** Output shows field quantities with iteration ranges

## parse deck

- **Trigger:** "parse input", "check deck", "validate deck"
- **CLI:** `osiris-toolkit deck parse <FILE>`, `osiris-toolkit deck validate <FILE>`, `osiris-toolkit deck lint <FILE>`
- **API:** `parse_deck_file(str(path))`, `lint_deck_file(str(path))`
- **Pre-condition:** File must be a valid OSIRIS input deck text file
- **Verify:** JSON output contains sections with parameters; lint reports 0 errors

## estimate resources

- **Trigger:** "estimate resources", "how much memory", "runtime estimate"
- **CLI:** `osiris-toolkit deck estimate <FILE> [-c CORES] [-e EFFICIENCY]`
- **API:** `estimate_resources(deck, efficiency=0.15)`, `format_report(report)`
- **Pre-condition:** Parsed input deck with grid/particle parameters
- **Verify:** Output shows memory (GB/node), runtime estimate, disk space

## plot field

- **Trigger:** "plot e1", "plot field", "show field"
- **CLI:** `osiris-toolkit vis plot <DIR> -k EMF -q e1 -i 50 [-o out.png]`
- **API:** `plot_field(sim=sim, system=system, quantity="e1", iteration=50)` or `pp.vis.field.plot("e1", 50)`
- **Pre-condition:** EMF diagnostic available at specified iteration
- **Verify:** PNG file generated at output path, non-zero file size

## plot k-space

- **Trigger:** "k-space", "FFT", "k space", "frequency domain"
- **CLI:** `osiris-toolkit vis plot <DIR> -k KSPACE -q e1 -i 50 --k-unit k0 [--clim -4,2] [--log-scale] [--omega0-norm 10.0]`
- **API:** `plot_k_space(sim=sim, system=system, quantity="e1", iteration=50, k_unit="k0")` or `pp.vis.plot_k_space("e1", 50, k_unit="k0")`
- **Pre-condition:** 2-D field data available at specified iteration
- **Note:** Advanced params (`omega0_norm`, `clim`, `white_low`, `xlim`/`ylim`) require Python API or CLI flags
- **Verify:** PNG with log-scale color map, axes labeled in chosen k-unit

## plot density

- **Trigger:** "density", "species density"
- **CLI:** (use `vis plot` with kind workaround or Python API)
- **API:** `plot_density(sim=sim, system=system, species="electrons", iteration=50, quantity="charge")`
- **Pre-condition:** Species density diagnostic available
- **Verify:** PNG showing 2-D density colormap

## batch process

- **Trigger:** "batch process", "process all", "process data"
- **CLI:** `osiris-toolkit vis batch <PATH> <NAME> [-o OUTDIR] [-j N] [--progress] [--dry-run]`
- **API:** `process_simulation(sim_path, sim_name, output_root=..., max_workers=...)` or `pp.batch(sim_name="run01")`
- **Pre-condition:** Simulation output directory with MS/ subdirectory
- **Verify:** Count PNG files in output dir, check for zero-byte files

## compare two simulations

- **Trigger:** "compare", "side by side", "compare two simulations"
- **CLI:** (no direct CLI command)
- **API:** Load two `Simulation` objects, use `plot_difference()` or `plot_overlay()` from `osiris_toolkit.vis.comparison`
- **Pre-condition:** Both simulations have the same diagnostic types at compatible iterations
- **Verify:** Side-by-side or overlay PNG with both datasets visible

## analyze field energy

- **Trigger:** "field energy", "total energy", "EM energy"
- **CLI:** `osiris-toolkit analyze describe <DIR> -q e1 -i 50` (basic stats only)
- **API:** `pp.analyze.emf.field_energy("e1", iteration=50)` returns energy breakdown
- **Pre-condition:** EMF field data at the specified iteration
- **Verify:** Printed or returned energy values (total, electric, magnetic components)

## analyze FFT spectrum

- **Trigger:** "analyze spectrum", "spectral analysis", "frequency analysis"
- **CLI:** (no direct CLI command)
- **API:** `pp.analyze.kspace.analyze("e1", iteration=50)` returns spectrum statistics
- **Pre-condition:** 2-D field data available
- **Verify:** Spectrum statistics (peak wavenumber, spectral width, etc.)

## analyze species

- **Trigger:** "species stats", "particle stats"
- **CLI:** (no direct CLI command)
- **API:** `pp.analyze.species.analyze("electrons")` returns species-level statistics
- **Pre-condition:** Species diagnostic data available
- **Verify:** Particle count, mean energy, temperature, etc.

## convert units

- **Trigger:** "convert units", "normalized to SI"
- **CLI:** (no direct CLI command)
- **API:** `system.convert(value, QuantityKind.LENGTH, "um")`, `system.convert(value, QuantityKind.TIME, "fs")`
- **Pre-condition:** `UnitSystem` initialized from a parsed input deck
- **Verify:** Converted value is physically reasonable (order-of-magnitude check)

## plot energy timeline

- **Trigger:** "energy over time", "energy history"
- **CLI:** (no direct CLI command)
- **API:** `plot_energy_timeline(results)`, `plot_energy_timeseries(results)` from `osiris_toolkit.vis.energy`
- **Pre-condition:** Time-series energy analysis results
- **Verify:** Line plot with time on x-axis, energy on y-axis

## plot phasespace

- **Trigger:** "phase space"
- **CLI:** (use `vis plot` workaround or Python API)
- **API:** `plot_phasespace(sim=sim, system=system, ps_name="x1-x2", species="electrons", iteration=50)` or `pp.vis.plot_phasespace("x1-x2", "electrons", 50)`
- **Pre-condition:** Phasespace diagnostic available for the species
- **Verify:** 2-D histogram in position-momentum space

## plot scattering

- **Trigger:** "scattering"
- **CLI:** (no direct CLI command)
- **API:** `plot_scattering_fraction(...)` from `osiris_toolkit.vis.scattering`
- **Pre-condition:** Scattering diagnostic data
- **Verify:** Angular distribution plot or fraction summary

## extract Fortran definitions

- **Trigger:** "sync definitions", "update generated", "extract from Fortran"
- **CLI:** `osiris-toolkit sync extract --osiris-path <PATH> [--docs-path <PATH>]`
- **API:** Use `osiris_toolkit.sync` submodules directly
- **Pre-condition:** Path to OSIRIS Fortran source tree
- **Verify:** Files written to `src/osiris_toolkit/_generated/`
