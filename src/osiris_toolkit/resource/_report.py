"""Console report formatting for resource estimates."""

from __future__ import annotations

from osiris_toolkit.resource._estimator import EstimationReport


def _fmt_size(mb: float) -> str:
    if mb < 1:
        return f"{mb * 1024:.1f} KB"
    elif mb < 1024:
        return f"{mb:.2f} MB"
    else:
        return f"{mb / 1024:.2f} GB"


def _fmt_hours(h: float) -> str:
    if h < 0.01:
        return f"{h * 60:.1f} min"
    elif h < 168:
        return f"{h:.1f} h"
    else:
        return f"{h / 24:.1f} days"


def format_report(report: EstimationReport) -> str:
    """Format an EstimationReport as a human-readable text table."""
    p = report.params
    m = report.memory
    r = report.runtime
    d = report.disk

    lines: list[str] = []

    # Header
    lines.append("")
    lines.append("Resource Estimation Report")
    lines.append("==========================")

    # Simulation Summary
    lines.append("")
    lines.append("--- Simulation Summary ---")
    dim_label = f"{p.ndim}D"
    grid_str = " x ".join(str(x) for x in p.nx_p)
    lines.append(f"  Dimensions:            {dim_label}")
    lines.append(f"  Grid:                  {grid_str} ({p.ngrid_total:,} cells)")
    lines.append(f"  MPI Decomposition:     {' x '.join(str(n) for n in p.node_number)} ({p.total_nodes} node(s))")
    if p.n_threads > 1:
        lines.append(f"  OpenMP threads:        {p.n_threads} per rank")
    lines.append(f"  Time:                  tmax={p.tmax:.2f}, dt={p.dt:.4f} ({p.n_steps:,} steps)")
    if p.num_species > 0:
        for i, ppc in enumerate(p.species_ppc):
            ppc_str = "x".join(str(x) for x in ppc)
            ppc_total = 1
            for x in ppc:
                ppc_total *= x
            name_str = f" ({p.species_names[i]})" if i < len(p.species_names) and p.species_names[i] else ""
            lines.append(f"  Species #{i + 1}{name_str}: {ppc_str} = {ppc_total} ppc")
        lines.append(f"  Total particles:       {p.total_particles:,}")
    else:
        lines.append("  Species:               none (num_species=0)")
    if p.vpml_bnd_size > 0:
        lines.append(f"  PML:                   {p.vpml_bnd_size} cells, {p.n_pml_boundaries} boundaries")
    if p.if_move:
        lines.append("  Moving window:         enabled")
    if p.if_collide:
        lines.append(f"  Collisions:            {p.n_collide} pair(s)")
    prec_label = "single" if p.field_precision_bytes == 4 else "double"
    lines.append(f"  Field precision:       {prec_label} ({p.field_precision_bytes} bytes)")
    lines.append(f"  Solver:                {p.solver} (order={p.solver_ord})")

    # Warnings
    if report.warnings:
        lines.append("")
        lines.append("  [!] Warnings:")
        for w in report.warnings:
            lines.append(f"    - {w}")

    # Memory
    lines.append("")
    lines.append("--- Memory (per-node peak) ---")
    lines.append(f"  Particle arrays:       {_fmt_size(m.particle_mb)}")
    lines.append(f"  Field arrays (EMF):    {_fmt_size(m.field_mb)}")
    lines.append(f"  Current arrays:         {_fmt_size(m.current_mb)}")
    if m.pml_mb > 0:
        lines.append(f"  PML overhead:           {_fmt_size(m.pml_mb)}")
    lines.append(f"  Diagnostic buffers:     {_fmt_size(m.diag_buf_mb)}")
    lines.append(f"  TOTAL (per node):       {_fmt_size(m.total_mb)} ({m.total_gb:.2f} GB)")
    if m.total_gb > 0:
        lines.append(
            f"  TOTAL (all nodes):      ~{_fmt_size(m.total_mb * p.total_nodes)} ({m.total_gb * p.total_nodes:.1f} GB)"
        )
    if m.notes:
        for n in m.notes:
            lines.append(f"  [i] {n}")

    # Runtime
    lines.append("")
    lines.append("--- Runtime (order-of-magnitude) ---")
    lines.append(f"  Total time steps:      {r.n_steps:,}")
    lines.append(f"  Est. CPU-hours:         {_fmt_hours(r.cpu_hours)}")
    lines.append(f"  Est. wall time:         {_fmt_hours(r.wall_hours_lower)} -- {_fmt_hours(r.wall_hours_upper)}")
    if r.io_overhead_hours > 0:
        lines.append(f"  I/O overhead:           {_fmt_hours(r.io_overhead_hours)}")
    if r.notes:
        for n in r.notes:
            lines.append(f"  [i] {n}")
    lines.append("")
    lines.append("  NOTE: Runtime estimates are order-of-magnitude only.")
    lines.append("  Actual performance depends on hardware, compiler optimizations,")
    lines.append("  and simulation-specific factors (ionization, moving window, etc).")

    # Disk Space
    lines.append("")
    lines.append("--- Disk Space ---")
    if d.emf_n_dumps > 0:
        lines.append(
            f"  EMF dumps:             {_fmt_size(d.emf_dump_mb)} x{d.emf_n_dumps:,} = {d.emf_total_gb:.2f} GB"
        )
    else:
        lines.append("  EMF dumps:             disabled")
    if d.raw_n_dumps > 0:
        lines.append(
            f"  Raw particle dumps:    {_fmt_size(d.raw_dump_mb)} x{d.raw_n_dumps:,} = {d.raw_total_gb:.2f} GB"
        )
    else:
        lines.append("  Raw particle dumps:    disabled")
    if d.restart_n_dumps > 0:
        lines.append(
            f"  Restart dumps:         {_fmt_size(d.restart_dump_mb)}"
            f" x{d.restart_n_dumps:,} = {d.restart_total_gb:.2f} GB"
        )
    else:
        lines.append("  Restart dumps:         disabled")
    lines.append(f"  TOTAL output:           {d.total_gb:.2f} GB")
    if d.notes:
        for n in d.notes:
            lines.append(f"  [i] {n}")

    lines.append("")
    return "\n".join(lines)
