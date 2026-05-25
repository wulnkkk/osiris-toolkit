"""Core resource estimation formulas for OSIRIS simulations."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from osiris_toolkit.resource._params import ResourceParams

# Bytes per particle by dimension and precision
# Derived from init_buffer_spec in os-spec-define.f03
# x: D*8, ix: D*4, p: 3*8, q: 8  (double precision, no spin, no tag)
_BYTES_PER_PARTICLE_DOUBLE = {1: 44, 2: 56, 3: 68}
_BYTES_PER_PARTICLE_SINGLE = {1: 28, 2: 36, 3: 44}
_SPIN_EXTRA = 24
_TAG_EXTRA = 8


def _bytes_per_particle(ndim: int, particle_precision_bytes: int) -> int:
    base = _BYTES_PER_PARTICLE_DOUBLE[ndim] if particle_precision_bytes == 8 else _BYTES_PER_PARTICLE_SINGLE[ndim]
    return base


@dataclass
class MemoryEstimate:
    """Memory usage estimate per node."""

    particle_mb: float = 0.0
    field_mb: float = 0.0
    current_mb: float = 0.0
    pml_mb: float = 0.0
    diag_buf_mb: float = 0.0
    total_mb: float = 0.0
    total_gb: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class RuntimeEstimate:
    """Runtime estimate."""

    n_steps: int = 0
    cpu_hours: float = 0.0
    wall_hours_lower: float = 0.0
    wall_hours_upper: float = 0.0
    io_overhead_hours: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class DiskEstimate:
    """Disk space estimate."""

    emf_dump_mb: float = 0.0
    emf_n_dumps: int = 0
    emf_total_gb: float = 0.0
    raw_dump_mb: float = 0.0
    raw_n_dumps: int = 0
    raw_total_gb: float = 0.0
    restart_dump_mb: float = 0.0
    restart_n_dumps: int = 0
    restart_total_gb: float = 0.0
    total_gb: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class EstimationReport:
    """Full resource estimation report."""

    params: ResourceParams = field(default_factory=ResourceParams)
    memory: MemoryEstimate = field(default_factory=MemoryEstimate)
    runtime: RuntimeEstimate = field(default_factory=RuntimeEstimate)
    disk: DiskEstimate = field(default_factory=DiskEstimate)
    warnings: list[str] = field(default_factory=list)


class ResourceEstimator:
    """Compute resource estimates from extracted parameters."""

    def __init__(
        self,
        peak_flops_per_core: float = 4.0e9,
        efficiency: float = 0.15,
        io_bandwidth_gbs: float = 1.0,
    ):
        self.peak_flops_per_core = peak_flops_per_core
        self.efficiency = efficiency
        self.io_bandwidth_gbs = io_bandwidth_gbs

    def estimate(self, params: ResourceParams) -> EstimationReport:
        """Produce a full resource estimation report."""
        warnings: list[str] = []
        memory = self._estimate_memory(params, warnings)
        runtime = self._estimate_runtime(params, memory, warnings)
        disk = self._estimate_disk(params, memory, warnings)
        return EstimationReport(params=params, memory=memory, runtime=runtime, disk=disk, warnings=warnings)

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def _estimate_memory(self, params: ResourceParams, warnings: list[str]) -> MemoryEstimate:
        notes: list[str] = []
        ndim = params.ndim
        ngrid = params.ngrid_total
        nodes = params.total_nodes
        fb = params.field_precision_bytes
        pb = params.particle_precision_bytes

        # Grid cells per node (subdomain)
        if nodes > 1:
            n_cells_node = ngrid // nodes
            cells_per_dim = []
            for i in range(ndim):
                cells_per_dim.append(max(1, params.nx_p[i] // params.node_number[i] if i < len(params.node_number) else params.nx_p[i]))
        else:
            n_cells_node = ngrid
            cells_per_dim = list(params.nx_p)

        # Guard cells: +3 per dimension (1 lower + 2 upper for standard FDTD)
        for i in range(ndim):
            cells_per_dim[i] += 3

        n_with_guard = 1
        for c in cells_per_dim:
            n_with_guard *= c

        # Particle memory
        particle_bytes = 0
        bpp = _bytes_per_particle(ndim, pb)
        for ppc in params.species_ppc:
            ppc_total = 1
            for p in ppc:
                ppc_total *= p
            particle_bytes += n_cells_node * ppc_total * bpp
        particle_mb = particle_bytes / (1024 ** 2)

        # VDF count: e, b = 2 always. +e_part+b_part if smoothing or part_grid_center
        n_vdfs = 2
        has_smoothing = params.smooth_type not in ("none", "") or params.smooth_order > 0
        if has_smoothing:
            n_vdfs += 2
            notes.append("e_part, b_part allocated for field smoothing")
        if params.if_move:
            notes.append("moving window enabled (minor additional memory)")

        # Field memory
        field_bytes = n_vdfs * 3 * n_with_guard * fb
        field_mb = field_bytes / (1024 ** 2)

        # Current memory: n_threads VDFs
        current_bytes = params.n_threads * 3 * n_with_guard * fb
        current_mb = current_bytes / (1024 ** 2)

        # PML memory
        pml_mb = 0.0
        if params.vpml_bnd_size > 0 and params.n_pml_boundaries > 0:
            n_cells_per_surface = 1
            for i in range(ndim):
                prod = 1
                for j in range(ndim):
                    if j != i:
                        prod *= cells_per_dim[j]
                n_cells_per_surface += prod
            pml_cells = params.n_pml_boundaries // 2 * params.vpml_bnd_size * n_cells_per_surface // ndim
            pml_bytes = pml_cells * 4 * fb
            pml_mb = pml_bytes / (1024 ** 2)

        # Diagnostic buffers (~30% of field arrays, rough)
        diag_mb = field_mb * 0.3

        total_mb = particle_mb + field_mb + current_mb + pml_mb + diag_mb

        return MemoryEstimate(
            particle_mb=particle_mb,
            field_mb=field_mb,
            current_mb=current_mb,
            pml_mb=pml_mb,
            diag_buf_mb=diag_mb,
            total_mb=total_mb,
            total_gb=total_mb / 1024,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    def _estimate_runtime(
        self, params: ResourceParams, mem: MemoryEstimate, warnings: list[str]
    ) -> RuntimeEstimate:
        notes: list[str] = []
        n_steps = params.n_steps
        ngrid = params.ngrid_total
        total_parts = params.total_particles
        cores = params.total_nodes * params.n_threads
        ndim = params.ndim

        if cores == 0:
            cores = 1

        # Operations per step (order-of-magnitude)
        # Push (60) + Deposit (80) per particle
        ops_push_deposit = total_parts * 140

        # FDTD: 6 components × 2 stencil ops × 12 flops
        solver_factor = 1.0
        if params.solver == "psatd":
            solver_factor = 3.0
            notes.append("PSATD solver: ~3× more expensive per cell than Yee")
        if params.solver_ord > 2:
            solver_factor *= (params.solver_ord / 2)
            notes.append(f"solver_ord={params.solver_ord}: higher-order stencil increases cost")
        ops_fdtd = ngrid * 3 * 12 * solver_factor

        # Smoothing
        ops_smooth = 0
        if params.smooth_type not in ("none", "") and params.smooth_order > 0:
            ops_smooth = ngrid * 3 * 20 * params.smooth_order * params.n_threads
            notes.append(f"current smoothing ({params.smooth_order} passes) adds ~{ops_smooth/1e9:.1f} GFLOP/step")

        # Sort (amortized)
        ops_sort = total_parts * 10 / 25

        # Collisions
        ops_coll = 0
        if params.if_collide:
            ops_coll = params.n_collide * 200 * total_parts / ngrid
            notes.append(f"collisions ({params.n_collide} pairs) add Monte Carlo overhead")

        ops_per_step = ops_push_deposit + ops_fdtd + ops_smooth + ops_sort + ops_coll
        total_ops = ops_per_step * n_steps
        effective_flops_per_core = self.peak_flops_per_core * self.efficiency

        # CPU-hours: aggregate core-time (1 core would need this many hours)
        cpu_hours = total_ops / (effective_flops_per_core * 3600)

        # Wall time: CPU-hours distributed across cores, plus MPI/IO overhead
        wall_hours_lower = cpu_hours / cores if cores > 0 else cpu_hours
        wall_hours_upper = wall_hours_lower * 1.4

        # I/O overhead
        io_gb = 0.0
        if mem.total_gb > 0 and params.emf_ndump_fac > 0:
            n_emf_dumps = n_steps // params.emf_ndump_fac if params.emf_ndump_fac > 0 else 0
            io_gb += (ngrid * 3 * 2 * params.field_precision_bytes / (1024 ** 3)) * n_emf_dumps
        io_hours = io_gb / (self.io_bandwidth_gbs * 3600) if self.io_bandwidth_gbs > 0 else 0
        if io_hours > wall_hours_lower * 0.1:
            notes.append(f"I/O overhead ({io_hours:.1f} h) may be significant")

        if params.if_move:
            notes.append("moving window shift adds minor per-step overhead")

        return RuntimeEstimate(
            n_steps=n_steps,
            cpu_hours=cpu_hours,
            wall_hours_lower=wall_hours_lower,
            wall_hours_upper=wall_hours_upper,
            io_overhead_hours=io_hours,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Disk
    # ------------------------------------------------------------------

    def _estimate_disk(
        self, params: ResourceParams, mem: MemoryEstimate, warnings: list[str]
    ) -> DiskEstimate:
        notes: list[str] = []
        n_steps = params.n_steps
        fb = params.field_precision_bytes

        # EMF dumps: 6 components × global grid × precision
        emf_bytes_per_dump = 6 * params.ngrid_total * fb
        emf_mb_per_dump = emf_bytes_per_dump / (1024 ** 2)
        emf_n_dumps = n_steps // params.emf_ndump_fac if params.emf_ndump_fac > 0 else 0
        emf_total_gb = (emf_bytes_per_dump * emf_n_dumps) / (1024 ** 3)

        # Raw particle dumps
        raw_bytes_per_dump = 0
        bpp = _bytes_per_particle(params.ndim, params.particle_precision_bytes)
        for i, ppc in enumerate(params.species_ppc):
            ppc_total = 1
            for p in ppc:
                ppc_total *= p
            n_parts = params.ngrid_total * ppc_total
            frac = params.species_raw_fraction[i] if i < len(params.species_raw_fraction) else 1.0
            raw_bytes_per_dump += int(n_parts * frac * bpp)
        raw_mb_per_dump = raw_bytes_per_dump / (1024 ** 2)

        max_raw_ndump = 0
        for f in params.species_ndump_fac_raw:
            if f > 0:
                max_raw_ndump = max(max_raw_ndump, f)
        raw_n_dumps = n_steps // max_raw_ndump if max_raw_ndump > 0 else 0
        raw_total_gb = (raw_bytes_per_dump * raw_n_dumps) / (1024 ** 3)

        # Restart dumps
        restart_bytes_per_dump = (mem.total_gb * (1024 ** 3)) * params.total_nodes
        restart_mb_per_dump = restart_bytes_per_dump / (1024 ** 2)
        restart_n_dumps = n_steps // params.restart_ndump_fac if params.restart_ndump_fac > 0 else 0
        restart_total_gb = (restart_bytes_per_dump * restart_n_dumps) / (1024 ** 3)

        total_gb = emf_total_gb + raw_total_gb + restart_total_gb

        if total_gb > 1000:
            notes.append(f"Warning: estimated output > 1 TB ({total_gb:.0f} GB)")

        return DiskEstimate(
            emf_dump_mb=emf_mb_per_dump,
            emf_n_dumps=emf_n_dumps,
            emf_total_gb=emf_total_gb,
            raw_dump_mb=raw_mb_per_dump,
            raw_n_dumps=raw_n_dumps,
            raw_total_gb=raw_total_gb,
            restart_dump_mb=restart_mb_per_dump,
            restart_n_dumps=restart_n_dumps,
            restart_total_gb=restart_total_gb,
            total_gb=total_gb,
            notes=notes,
        )
