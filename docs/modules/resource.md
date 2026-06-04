---
audience: [human, agent]
topic: modules
kind: reference
module: resource
updated: 2026-06-04
---

# resource — Simulation Resource Estimation

Predicts computational resources (memory, runtime, disk) for an OSIRIS input deck
*before* submitting to the cluster.

## Architecture

```
resource/
├── __init__.py     Public API: estimate_resources(deck) -> EstimationReport
├── _params.py      ResourceParams: extracts 25+ parameters from parsed deck
├── _estimator.py   ResourceEstimator: memory/runtime/disk calculation formulas
└── _report.py      format_report(): human-readable console table
```

## Usage

### CLI

```bash
osiris-toolkit deck estimate input.in
```

### Python API

```python
from osiris_toolkit.deck import parse_deck_file
from osiris_toolkit.resource import estimate_resources, format_report

deck = parse_deck_file("input.in")
report = estimate_resources(deck, efficiency=0.15)
print(format_report(report))

# Access individual estimates
print(report.memory.total_mb)   # per-node peak memory (MB)
print(report.runtime.cpu_hours)  # aggregate CPU-hours
print(report.disk.total_gb)      # total output size (GB)
```

## Estimation Methods

### Memory

- **Particle arrays**: cells_per_node × ppc × bytes_per_particle (1D:44B, 2D:56B, 3D:68B double precision)
- **Field arrays (EMF)**: nVDFs × 3 components × grid_with_guard × field_bytes. VDF count: 2 (e, b) + 2 (e_part, b_part if smoothing enabled)
- **Current arrays**: n_threads × 3 components × grid_with_guard × field_bytes
- **PML overhead**: n_boundaries × vpml_bnd_size × surface_cells × auxiliary_variables × field_bytes
- **Diagnostic buffers**: ~30% of field arrays

### Runtime

- **Total steps**: tmax / dt
- **Operations per step**: particle_push (60 FLOP/particle) + current_deposit (80 FLOP/particle) + FDTD (12 FLOP/cell/component × 6 components × 2 stencils) + smoothing + sort (amortized) + collisions
- **CPU-hours**: total_ops / (peak_flops_per_core × efficiency × 3600)
- **Wall time**: CPU-hours / cores × (1.0–1.4 MPI overhead)
- **Defaults**: peak_flops=4e9, efficiency=0.15, io_bandwidth=1 GB/s

### Disk

- **EMF dumps**: 6 components × global_grid × field_bytes per dump
- **Raw particle dumps**: total_particles × raw_fraction × particle_bytes per dump
- **Restart dumps**: full particle + field state snapshot

## Key Design Decisions

- **Order-of-magnitude runtime**: PIC performance is heavily hardware-dependent. All runtime numbers are labeled as estimates.
- **Conservative memory defaults**: assumes double precision particles (8B), single precision fields (4B). Override via `--precision` flag.
- **Missing parameters**: required params (nx_p, tmax, dt) raise ValueError; optional params use sensible defaults (0 = disabled, 1 node, etc.).
- **Based on OSIRIS source analysis**: formulas derived from `init_buffer_spec`, `init_emf`, `init_current`, and the 23-step `iter_sim` main loop in `osiris-1.0.0/source/`.

## Limitations

- Particle memory uses average ppc, not `num_par_max` (pre-allocation upper bound). Actual usage may be higher.
- Collision workspace, sorting buffers, and other auxiliary arrays are not fully accounted.
- Runtime estimates are order-of-magnitude; actual performance depends on compiler optimization, CPU architecture, and MPI fabric.

## Reference

- `analysis/osiris-runtime-mechanism-analysis.md` — detailed OSIRIS runtime mechanism analysis
- `docs/devlog/0.3.0.md` — version release notes
