"""Extract resource-relevant parameters from a parsed OSIRIS input deck."""

from __future__ import annotations

from dataclasses import dataclass, field


def _extract_value(value, default=None):
    """Normalize a deck value: scalar, list, or wrapped dict with 'value' key."""
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get("value", default)
    if isinstance(value, (list, int, float, str, bool)):
        return value
    return default


def _extract_list(value, default=None):
    """Normalize to a list, handling wrapped dict values."""
    if value is None:
        return default
    if isinstance(value, dict):
        inner = value.get("value", default)
        if isinstance(inner, list):
            return inner
        return default
    if isinstance(value, list):
        return value
    return default if default is not None else [value]


def _extract_int(value, default=0):
    v = _extract_value(value)
    if v is None:
        return default
    if isinstance(v, list):
        return [int(x) for x in v]
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _extract_float(value, default=0.0):
    v = _extract_value(value)
    if v is None:
        return default
    if isinstance(v, list):
        return [float(x) for x in v]
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _extract_bool(value, default=False):
    v = _extract_value(value)
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in (".true.", "true", "t", "yes", "y", "1")
    return default


def _find_section(sections: list[dict], name: str) -> dict | None:
    """Find the first section with the given name."""
    for sec in sections:
        if sec.get("name") == name:
            return sec
    return None


def _find_all_sections(sections: list[dict], name: str) -> list[dict]:
    """Find all sections with the given name."""
    return [sec for sec in sections if sec.get("name") == name]


@dataclass
class ResourceParams:
    """Parameters extracted from a deck for resource estimation."""

    # Grid
    ndim: int = 2
    nx_p: list[int] = field(default_factory=lambda: [32, 32])
    ngrid_total: int = 1024

    # Time
    tmax: float = 0.0
    dt: float = 0.0
    n_steps: int = 0

    # MPI
    node_number: list[int] = field(default_factory=lambda: [1, 1])
    total_nodes: int = 1

    # OpenMP
    n_threads: int = 1

    # Particles
    num_species: int = 0
    species_ppc: list[list[int]] = field(default_factory=list)
    species_names: list[str] = field(default_factory=list)

    # PML
    vpml_bnd_size: int = 0
    n_pml_boundaries: int = 0

    # EMF
    solver: str = "yee"
    solver_ord: int = 2
    interpolation: str = "quadratic"

    # Field smoothing
    smooth_type: str = "none"
    smooth_order: int = 0

    # Moving window
    if_move: bool = False

    # Collisions
    if_collide: bool = False
    n_collide: int = 0

    # Diagnostics
    emf_ndump_fac: int = 0
    species_ndump_fac: list[int] = field(default_factory=list)
    species_ndump_fac_raw: list[int] = field(default_factory=list)
    species_raw_fraction: list[float] = field(default_factory=list)
    restart_ndump_fac: int = 0

    # Precision
    field_precision_bytes: int = 4
    particle_precision_bytes: int = 8

    @classmethod
    def from_deck(cls, deck: dict) -> "ResourceParams":
        """Extract resource-relevant parameters from a parsed deck.

        Raises ValueError if nx_p, tmax, or dt is missing or zero.
        """
        sections = deck.get("sections", [])
        warnings: list[str] = []

        # --- Grid ---
        grid_sec = _find_section(sections, "grid")
        if grid_sec is None:
            raise ValueError("Missing 'grid' section. Cannot determine grid dimensions.")
        gparams = grid_sec.get("params", {})
        raw_nx = _extract_list(gparams.get("nx_p"))
        if raw_nx is None or not raw_nx or all(x == 0 for x in raw_nx):
            raise ValueError("Parameter 'nx_p' is missing or all zeros in 'grid' section.")
        nx_p = [int(x) for x in raw_nx]
        ndim = len(nx_p)
        ngrid_total = 1
        for x in nx_p:
            ngrid_total *= x

        # --- Time ---
        time_sec = _find_section(sections, "time")
        if time_sec is None:
            raise ValueError("Missing 'time' section. Cannot determine tmax.")
        tparams = time_sec.get("params", {})
        tmax = _extract_float(tparams.get("tmax"), 0.0)
        if tmax <= 0:
            raise ValueError("Parameter 'tmax' is missing or <= 0 in 'time' section.")

        ts_sec = _find_section(sections, "time_step")
        dt = 0.0
        if ts_sec is not None:
            dt = _extract_float(ts_sec.get("params", {}).get("dt"), 0.0)
        if dt <= 0:
            raise ValueError("Parameter 'dt' is missing or <= 0 in 'time_step' section.")
        n_steps = int(tmax / dt)

        # --- MPI ---
        nc_sec = _find_section(sections, "node_conf")
        node_number = [1] * ndim
        total_nodes = 1
        n_threads = 1
        if nc_sec is not None:
            nc_params = nc_sec.get("params", {})
            raw_nn = _extract_list(nc_params.get("node_number"))
            if raw_nn:
                node_number = [int(x) for x in raw_nn[:ndim]]
            for x in node_number:
                total_nodes *= x
            n_threads = _extract_int(nc_params.get("n_threads"), 1)

        # --- Particles ---
        part_sec = _find_section(sections, "particles")
        num_species = 0
        if part_sec is not None:
            num_species = _extract_int(part_sec.get("params", {}).get("num_species"), 0)

        species_sections = _find_all_sections(sections, "species")
        species_ppc: list[list[int]] = []
        species_names: list[str] = []
        for sp_sec in species_sections[:max(num_species, 1)]:
            sp_params = sp_sec.get("params", {})
            raw_ppc = _extract_list(sp_params.get("num_par_x"))
            if raw_ppc:
                ppc = [int(x) for x in raw_ppc[:ndim]]
            else:
                ppc = [1] * ndim
                warnings.append(f"Species '{sp_params.get('rqm', '?')}': num_par_x not set, assuming {ppc}")
            species_ppc.append(ppc)
            species_names.append(sp_params.get("species_name", ""))

        # Pad species_ppc if fewer species sections than num_species
        while len(species_ppc) < num_species:
            species_ppc.append([1] * ndim)
            species_names.append("")
            warnings.append(f"Species #{len(species_ppc)}: no section found, assuming 1 ppc per direction")

        # --- PML ---
        emf_bound_sec = _find_section(sections, "emf_bound")
        vpml_bnd_size = 0
        n_pml_boundaries = 0
        if emf_bound_sec is not None:
            eb_params = emf_bound_sec.get("params", {})
            vpml_bnd_size = _extract_int(eb_params.get("vpml_bnd_size"), 0)
            raw_types = _extract_list(eb_params.get("type"))
            if raw_types and vpml_bnd_size > 0:
                for t in raw_types:
                    ts = str(t).lower().strip()
                    if "pml" in ts or "vpml" in ts or " absorbing" in ts or "open" in ts:
                        n_pml_boundaries += 1

        # --- EMF / Solver ---
        emf_sec = _find_section(sections, "el_mag_fld")
        solver = "yee"
        smooth_type = "none"
        smooth_order = 0
        if emf_sec is not None:
            emf_params = emf_sec.get("params", {})
            solver = str(_extract_value(emf_params.get("solver"), "yee")).lower()
            smooth_type = str(_extract_value(emf_params.get("smooth_type"), "none")).lower()
            smooth_order = _extract_int(emf_params.get("smooth_niter"), 0)

        emf_solver_sec = _find_section(sections, "emf_solver")
        solver_ord = 2
        if emf_solver_sec is not None:
            solver_ord = _extract_int(emf_solver_sec.get("params", {}).get("solver_ord"), 2)

        # --- Interpolation ---
        if part_sec is not None:
            interp = str(_extract_value(part_sec.get("params", {}).get("interpolation"), "quadratic")).lower()
        else:
            interp = "quadratic"

        # --- Smooth ---
        smooth_sec = _find_section(sections, "smooth")
        if smooth_sec is not None:
            s_params = smooth_sec.get("params", {})
            st = _extract_value(s_params.get("type"))
            if st and isinstance(st, list):
                for entry in st:
                    if str(entry).lower().strip() not in ("none", ""):
                        smooth_type = str(entry).lower().strip()
                        break
            smooth_order = _extract_int(s_params.get("order"), smooth_order)

        # --- Moving window ---
        space_sec = _find_section(sections, "space")
        if_move = False
        if space_sec is not None:
            sp_params = space_sec.get("params", {})
            if_move = _extract_bool(sp_params.get("if_move"), False)

        # --- Collisions ---
        coll_sec = _find_section(sections, "collisions")
        n_collide = 0
        if coll_sec is not None:
            n_collide = _extract_int(coll_sec.get("params", {}).get("n_collide"), 0)
        if_collide = n_collide > 0

        # --- Diagnostics ---
        diag_emf_sec = _find_section(sections, "diag_emf")
        emf_ndump_fac = 0
        field_precision_bytes = 4
        if diag_emf_sec is not None:
            de_params = diag_emf_sec.get("params", {})
            emf_ndump_fac = _extract_int(de_params.get("ndump_fac"), 0)
            prec = _extract_int(de_params.get("prec"), 4)
            field_precision_bytes = 4 if prec == 4 else 8

        diag_species_all = _find_all_sections(sections, "diag_species")
        species_ndump_fac = []
        species_ndump_fac_raw = []
        species_raw_fraction = []
        for ds_sec in diag_species_all:
            ds_params = ds_sec.get("params", {})
            species_ndump_fac.append(_extract_int(ds_params.get("ndump_fac"), 0))
            species_ndump_fac_raw.append(_extract_int(ds_params.get("ndump_fac_raw"), 0))
            species_raw_fraction.append(_extract_float(ds_params.get("raw_fraction"), 1.0))

        restart_sec = _find_section(sections, "restart")
        restart_ndump_fac = 0
        if restart_sec is not None:
            restart_ndump_fac = _extract_int(restart_sec.get("params", {}).get("ndump_fac"), 0)

        # --- Precision ---
        particle_precision_bytes = 8  # OSIRIS particles are always double by default

        return cls(
            ndim=ndim, nx_p=nx_p, ngrid_total=ngrid_total,
            tmax=tmax, dt=dt, n_steps=n_steps,
            node_number=node_number, total_nodes=total_nodes, n_threads=n_threads,
            num_species=num_species, species_ppc=species_ppc, species_names=species_names,
            vpml_bnd_size=vpml_bnd_size, n_pml_boundaries=n_pml_boundaries,
            solver=solver, solver_ord=solver_ord, interpolation=interp,
            smooth_type=smooth_type, smooth_order=smooth_order,
            if_move=if_move, if_collide=if_collide, n_collide=n_collide,
            emf_ndump_fac=emf_ndump_fac,
            species_ndump_fac=species_ndump_fac,
            species_ndump_fac_raw=species_ndump_fac_raw,
            species_raw_fraction=species_raw_fraction,
            restart_ndump_fac=restart_ndump_fac,
            field_precision_bytes=field_precision_bytes,
            particle_precision_bytes=particle_precision_bytes,
        )

    @property
    def total_particles(self) -> int:
        """Estimated total particles across all species (global)."""
        total = 0
        for ppc in self.species_ppc:
            ppc_total = 1
            for p in ppc:
                ppc_total *= p
            total += self.ngrid_total * ppc_total
        return total

    @property
    def particles_per_node(self) -> int:
        """Estimated particles per MPI node."""
        return self.total_particles // self.total_nodes
