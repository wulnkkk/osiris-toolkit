"""Cross-section consistency validation rules.

Validates constraints that span multiple sections, all derived from
OSIRIS v1.0.0 Fortran source code.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from .ast import Deck, Section
from .reporter import IssueReport, Severity, ValidationIssue
from .schemas.registry import get_species_group_sections

# ---- Helpers ----


def _get_param(deck: Deck, section_name: str, param_name: str) -> Any | None:
    """Get a single scalar/array parameter value across sections."""
    for sec in deck.sections:
        if sec.name == section_name:
            val = sec.params.get(param_name)
            if val is None:
                return None
            return _unwrap(val)
    return None


def _get_section_count(deck: Deck, name: str) -> int:
    """Return the count of sections with a given name in the deck."""
    return sum(1 for s in deck.sections if s.name == name)


def _get_periodic(deck: Deck) -> list | None:
    """Extract the if_periodic array from node_conf."""
    return _get_param(deck, "node_conf", "if_periodic")


def _get_coordinates(deck: Deck) -> str | None:
    """Extract normalized coordinate type from grid."""
    val = _get_param(deck, "grid", "coordinates")
    if isinstance(val, str):
        return val.lower()
    return None


def _get_dimension(deck: Deck) -> int:
    """Infer effective dimension from grid.nx_p length. grid always exists (REQUIRED)."""
    nx_p = _get_param(deck, "grid", "nx_p")
    if isinstance(nx_p, list):
        return len(nx_p)
    return 1


def _unwrap(val: Any) -> Any:
    """Unwrap a slice-wrapped dict value."""
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val


def _to_list(val: Any) -> list:
    """Normalize a value to a list."""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [val]


def _get_boundary_types(deck: Deck) -> list:
    """Get the full 2x2 2D array of emf_bound type (Fortran column-major).

    Reconstructs partial slices like (1:2, 2:2) into a full 4-element list,
    with unspecified positions filled with None. Returns empty list if no
    type parameter is present.
    """
    for sec in deck.sections:
        if sec.name == "emf_bound":
            raw = sec.params.get("type")
            if raw is None:
                return []
            if isinstance(raw, dict) and "value" in raw:
                value = raw["value"]
                dims: list = raw.get("dims", [])
                if len(dims) == 2 and isinstance(value, list):
                    full: list = [None, None, None, None]
                    r1_range = dims[0]   # (row_start, row_end)
                    r2_range = dims[1]   # (col_start, col_end)
                    idx = 0
                    for col in range(r2_range[0], r2_range[1] + 1):
                        for row in range(r1_range[0], r1_range[1] + 1):
                            flat = (col - 1) * 2 + (row - 1)
                            if idx < len(value):
                                full[flat] = value[idx]
                            idx += 1
                    return full
                return _to_list(value)
            return _to_list(raw)
    return []


# ---- Species group iterator ----


@dataclass
class SpeciesGroup:
    """One species and its associated child sections."""
    species: Section
    subsections: dict[str, list[Section]] = field(default_factory=dict)
    index: int = 0


_SPECIES_GROUP_NAMES: set[str] = set(get_species_group_sections())
_SPECIES_GROUP_ORDER: list[str] = [
    "udist", "sdist", "profile", "spe_bound", "piston", "diag_species"
]


def _iter_species_groups(deck: Deck) -> Iterator[SpeciesGroup]:
    """Iterate through the deck, grouping adjacent species and their child sections."""
    current: SpeciesGroup | None = None
    species_index = 0

    for sec in deck.sections:
        if sec.name == "species":
            if current is not None:
                yield current
            species_index += 1
            current = SpeciesGroup(species=sec, index=species_index)
        elif sec.name in _SPECIES_GROUP_NAMES and current is not None:
            current.subsections.setdefault(sec.name, []).append(sec)

    if current is not None:
        yield current


# ---- Stub functions (implemented in subsequent tasks) ----


# ---- A. Count matching rules ----


_COUNT_RULES: list[tuple[str, str, str, str]] = [
    # (parent section, param name, target section name, rule ID)
    ("particles", "num_species", "species", "V-XSEC-001"),
    ("particles", "num_cathode", "cathode", "V-XSEC-002"),
    ("particles", "num_neutral", "neutral", "V-XSEC-003"),
    ("particles", "num_neutral_mov_ions", "neutral_mov_ions", "V-XSEC-004"),
    ("antenna_array", "n_antenna", "antenna", "V-XSEC-005"),
]


def _check_count_match(deck: Deck, report: IssueReport) -> None:
    """Verify that count parameters match actual section counts."""
    for parent_name, param_name, target_name, rule_id in _COUNT_RULES:
        declared = _get_param(deck, parent_name, param_name)
        if declared is None:
            continue  # Parameter absent, not triggered (may be caught by V-REQUIRED)
        if isinstance(declared, bool):
            continue
        if not isinstance(declared, (int, float)):
            continue
        declared_int = int(declared)
        actual = _get_section_count(deck, target_name)
        if declared_int != actual:
            report.add(ValidationIssue(
                rule_id=rule_id,
                severity=Severity.ERROR,
                message=(
                    f"{parent_name}.{param_name} = {declared_int}, "
                    f"but found {actual} '{target_name}' section(s)"
                ),
                section=parent_name,
            ))


# ---- B. Dimensional consistency ----


def _check_dimensional_consistency(deck: Deck, report: IssueReport) -> None:
    """Verify that all per-dimension array lengths match the nx_p dimension."""
    p_x_dim = _get_dimension(deck)

    # V-XSEC-011: node_number dimension
    node_number = _get_param(deck, "node_conf", "node_number")
    if node_number is not None:
        nn_list = _to_list(node_number)
        if len(nn_list) != p_x_dim:
            report.add(ValidationIssue(
                rule_id="V-XSEC-011",
                severity=Severity.ERROR,
                message=f"node_number has {len(nn_list)} component(s), "
                        f"but nx_p has {p_x_dim} (they must match)",
                section="node_conf",
            ))

    # V-XSEC-012/013: xmin/xmax dimensions
    space_sec = None
    for sec in deck.sections:
        if sec.name == "space":
            space_sec = sec
            break

    if space_sec is not None:
        for arr_name, rule_id in [("xmin", "V-XSEC-012"), ("xmax", "V-XSEC-013")]:
            arr = _get_param(deck, "space", arr_name)
            if arr is not None:
                arr_list = _to_list(arr)
                if len(arr_list) != p_x_dim:
                    report.add(ValidationIssue(
                        rule_id=rule_id,
                        severity=Severity.ERROR,
                        message=f"{arr_name} has {len(arr_list)} component(s), "
                                f"but nx_p has {p_x_dim} (they must match)",
                        section="space",
                    ))

    # V-XSEC-014: if_periodic dimension
    if_periodic = _get_periodic(deck)
    if if_periodic is not None:
        ip_list = _to_list(if_periodic)
        if len(ip_list) != p_x_dim:
            report.add(ValidationIssue(
                rule_id="V-XSEC-014",
                severity=Severity.WARNING,
                message=f"if_periodic has {len(ip_list)} component(s), "
                        f"but nx_p has {p_x_dim}",
                section="node_conf",
            ))

    # V-XSEC-015: if_move dimension
    if_move = _get_param(deck, "space", "if_move")
    if if_move is not None:
        im_list = _to_list(if_move)
        if len(im_list) != p_x_dim:
            report.add(ValidationIssue(
                rule_id="V-XSEC-015",
                severity=Severity.WARNING,
                message=f"if_move has {len(im_list)} component(s), "
                        f"but nx_p has {p_x_dim}",
                section="space",
            ))


# ---- C. Species group structure ----


def _check_species_group_structure(deck: Deck, report: IssueReport) -> None:
    """Validate the internal structure of species groups."""
    for group in _iter_species_groups(deck):
        sec = group.species

        # V-XSEC-020: Child section ordering (checked by actual deck order)
        prev_order_idx = -1
        prev_name = ""
        in_group = False
        for s in deck.sections:
            if s is sec:
                in_group = True
                continue
            if s.name == "species":
                break  # Next group starts, stop checking
            if not in_group:
                continue
            if s.name in group.subsections and s.name in _SPECIES_GROUP_ORDER:
                order_idx = _SPECIES_GROUP_ORDER.index(s.name)
                if order_idx < prev_order_idx:
                    report.add(ValidationIssue(
                        rule_id="V-XSEC-020",
                        severity=Severity.WARNING,
                        message=f"In species group #{group.index}: '{s.name}' "
                                f"appears after '{prev_name}' — may be out of order",
                        section=sec.name, line=sec.line,
                    ))
                prev_order_idx = order_idx
                prev_name = s.name

        # V-XSEC-021: piston count match
        num_pistons = sec.params.get("num_pistons")
        if num_pistons is not None and isinstance(num_pistons, (int, float)):
            np_int = int(num_pistons)
            actual_pistons = len(group.subsections.get("piston", []))
            if np_int != actual_pistons:
                report.add(ValidationIssue(
                    rule_id="V-XSEC-021",
                    severity=Severity.ERROR,
                    message=f"Species #{group.index}: num_pistons = {np_int}, "
                            f"but found {actual_pistons} piston section(s)",
                    section=sec.name, line=sec.line,
                ))

        # V-XSEC-022: Standard species should have a profile
        has_profile = "profile" in group.subsections
        if not has_profile:
            report.add(ValidationIssue(
                rule_id="V-XSEC-022",
                severity=Severity.INFO,
                message=f"Species #{group.index}: no 'profile' section found "
                        "(expected for standard species)",
                section=sec.name, line=sec.line,
            ))


# ---- D. Neutral gas custom ----

def _check_neutral_gas(deck: Deck, report: IssueReport) -> None:
    """Validate neutral gas custom cross-section setup."""
    for sec in deck.sections:
        if sec.name != "neutral":
            continue
        neutral_gas = sec.params.get("neutral_gas")
        if_impact = sec.params.get("if_impact")
        has_num_ene = _get_section_count(deck, "num_ene") > 0
        has_cross = _get_section_count(deck, "cross") > 0

        if isinstance(neutral_gas, str) and neutral_gas.lower() == "custom":
            if not has_num_ene and not has_cross:
                report.add(ValidationIssue(
                    rule_id="V-XSEC-030",
                    severity=Severity.INFO,
                    message="neutral_gas = 'custom' but no 'num_ene'/'cross' sections found",
                    section="neutral", line=sec.line,
                ))

        if isinstance(if_impact, bool) and if_impact:
            if not has_num_ene and not has_cross:
                report.add(ValidationIssue(
                    rule_id="V-XSEC-031",
                    severity=Severity.WARNING,
                    message="if_impact = .true. but no 'num_ene'/'cross' sections found",
                    section="neutral", line=sec.line,
                ))


# ---- E. Physics compatibility ----


def _check_physics_compatibility(deck: Deck, report: IssueReport) -> None:
    """Validate cross-section physics compatibility constraints."""
    p_x_dim = _get_dimension(deck)
    if_periodic = _get_periodic(deck)
    if_move = _get_param(deck, "space", "if_move")
    coordinates = _get_coordinates(deck)
    xmin = _get_param(deck, "space", "xmin")
    emb_types = _get_boundary_types(deck)  # full 2x2 array with None placeholders

    ip_list = _to_list(if_periodic) if if_periodic is not None else []
    im_list = _to_list(if_move) if if_move is not None else []
    xmin_list = _to_list(xmin) if xmin is not None else []

    # V-XSEC-100: if_move & periodic are mutually exclusive (migrated from V-SPACE-002)
    if ip_list and im_list:
        n = min(len(ip_list), len(im_list))
        for i in range(n):
            pi = ip_list[i]
            mi = im_list[i]
            if isinstance(pi, bool) and isinstance(mi, bool) and pi and mi:
                report.add(ValidationIssue(
                    rule_id="V-XSEC-100",
                    severity=Severity.ERROR,
                    message=f"Direction {i + 1}: moving window and periodic boundaries "
                            "are mutually exclusive",
                    section="space",
                ))

    # V-XSEC-101: Cylindrical r_min == 0.0 (migrated from V-SPACE-003)
    if coordinates == "cylindrical" and len(xmin_list) >= 2:
        if isinstance(xmin_list[1], (int, float)) and xmin_list[1] != 0.0:
            report.add(ValidationIssue(
                rule_id="V-XSEC-101",
                severity=Severity.ERROR,
                message=f"Cylindrical radial minimum must be 0.0 (got {xmin_list[1]})",
                section="space",
            ))

    # V-XSEC-102: Cylindrical requires 2D (migrated from V-GRID-004)
    if coordinates == "cylindrical" and p_x_dim != 2:
        report.add(ValidationIssue(
            rule_id="V-XSEC-102",
            severity=Severity.ERROR,
            message=f"Cylindrical coordinates require 2D, but nx_p has {p_x_dim} component(s)",
            section="grid",
        ))

    # V-XSEC-103: No moving window along radial in cylindrical
    if coordinates == "cylindrical" and len(im_list) >= 2:
        if isinstance(im_list[1], bool) and im_list[1]:
            report.add(ValidationIssue(
                rule_id="V-XSEC-103",
                severity=Severity.ERROR,
                message="Moving window not allowed along radial direction "
                        "in cylindrical geometry",
                section="space",
            ))

    # V-XSEC-104: io_nmerge divides node_number evenly
    io_nmerge = _get_param(deck, "grid", "io_nmerge")
    node_number = _get_param(deck, "node_conf", "node_number")
    if io_nmerge is not None and node_number is not None:
        io_list = _to_list(io_nmerge)
        nn_list = _to_list(node_number)
        n = min(len(io_list), len(nn_list))
        for i in range(n):
            io_val = io_list[i]
            nn_val = nn_list[i]
            if isinstance(io_val, (int, float)) and isinstance(nn_val, (int, float)):
                if int(nn_val) % int(io_val) != 0:
                    report.add(ValidationIssue(
                        rule_id="V-XSEC-104",
                        severity=Severity.ERROR,
                        message=f"io_nmerge[{i + 1}] ({int(io_val)}) must divide "
                                f"node_number[{i + 1}] ({int(nn_val)}) evenly",
                        section="grid",
                    ))

    # V-XSEC-105: smooth_type="local" incompatible with PML
    smooth_type = _get_param(deck, "el_mag_fld", "smooth_type")
    if isinstance(smooth_type, str) and smooth_type.lower() == "local":
        if emb_types:
            for t in emb_types:
                if isinstance(t, str) and t.lower() == "vpml":
                    report.add(ValidationIssue(
                        rule_id="V-XSEC-105",
                        severity=Severity.ERROR,
                        message="PML boundary conditions cannot be used "
                                "with 'local' EMF smoothing",
                        section="el_mag_fld",
                    ))
                    break

    # V-XSEC-106: Non-periodic non-moving directions must have valid boundary conditions
    if emb_types and ip_list is not None:
        n = min(len(ip_list), len(emb_types) // 2)
        for i in range(n):
            if not ip_list[i]:
                lower = emb_types[i * 2] if i * 2 < len(emb_types) else None
                upper = emb_types[i * 2 + 1] if i * 2 + 1 < len(emb_types) else None
                for j, bc in enumerate([lower, upper]):
                    if bc is None:
                        continue  # Unspecified boundary → Fortran default
                    if isinstance(bc, str) and bc.lower() in ("", "none"):
                        side = "lower" if j == 0 else "upper"
                        report.add(ValidationIssue(
                            rule_id="V-XSEC-106",
                            severity=Severity.ERROR,
                            message=f"Direction {i + 1} ({side}) is non-periodic "
                                    "but has no boundary condition specified",
                            section="emf_bound",
                        ))

    # V-XSEC-107: type="periodic" requires global periodic already set
    if emb_types and ip_list is not None:
        for i in range(min(len(ip_list), len(emb_types) // 2)):
            if not ip_list[i]:
                for j in range(2):
                    idx = i * 2 + j
                    if idx < len(emb_types):
                        bc = emb_types[idx]
                        if isinstance(bc, str) and bc.lower() == "periodic":
                            report.add(ValidationIssue(
                                rule_id="V-XSEC-107",
                                severity=Severity.ERROR,
                                message=f"Direction {i + 1}: periodic EMF boundary "
                                        "requires global periodic in node_conf",
                                section="emf_bound",
                            ))

    # V-XSEC-108: Axial boundary only on radial lower boundary
    if emb_types and coordinates == "cylindrical":
        for idx, bc in enumerate(emb_types):
            if isinstance(bc, str) and bc.lower() == "axial":
                direction = idx // 2 + 1  # 1-based direction
                side = "lower" if idx % 2 == 0 else "upper"
                if direction != 2 or side != "lower":
                    report.add(ValidationIssue(
                        rule_id="V-XSEC-108",
                        severity=Severity.ERROR,
                        message=f"'axial' boundary on direction {direction} "
                                f"({side}) — must be on radial lower boundary only",
                        section="emf_bound",
                    ))

    # V-XSEC-109: Lindman at most one direction
    if emb_types and ip_list is not None:
        lindman_dirs = 0
        for i in range(min(len(ip_list), len(emb_types) // 2)):
            if not ip_list[i]:
                for j in range(2):
                    idx = i * 2 + j
                    if idx < len(emb_types):
                        bc = emb_types[idx]
                        if isinstance(bc, str) and bc.lower() == "lindman":
                            lindman_dirs += 1
                            break
        if lindman_dirs > 1:
            report.add(ValidationIssue(
                rule_id="V-XSEC-109",
                severity=Severity.ERROR,
                message="Lindman boundaries cannot be specified "
                        "for more than one direction",
                section="emf_bound",
            ))


# ---- F. Parameter dependencies ----


_SOLVER_1D_RESTRICTED: set[str] = {"lehe", "ndfx", "stencil", "fei"}
_SOLVER_CYLINDRICAL_RESTRICTED: set[str] = {"lehe", "ndfx", "stencil"}


def _check_parameter_dependencies(deck: Deck, report: IssueReport) -> None:
    """Validate cross-section parameter dependency constraints."""
    omega_p0 = _get_param(deck, "simulation", "omega_p0")

    # V-XSEC-120: num_neutral > 0 or num_neutral_mov_ions > 0 requires omega_p0 > 0
    num_neutral = _get_param(deck, "particles", "num_neutral")
    num_neutral_mov = _get_param(deck, "particles", "num_neutral_mov_ions")
    need_ionization_omega = False
    if isinstance(num_neutral, (int, float)) and num_neutral > 0:
        need_ionization_omega = True
    if isinstance(num_neutral_mov, (int, float)) and num_neutral_mov > 0:
        need_ionization_omega = True
    if need_ionization_omega:
        if omega_p0 is None or (isinstance(omega_p0, (int, float)) and omega_p0 <= 0):
            report.add(ValidationIssue(
                rule_id="V-XSEC-120",
                severity=Severity.ERROR,
                message="num_neutral > 0 or num_neutral_mov_ions > 0 requires "
                        "omega_p0 > 0 in simulation section",
                section="particles",
            ))

    # V-XSEC-121/122/123: Per-species checks
    for sec in deck.sections:
        if sec.name != "species":
            continue
        push_type = sec.params.get("push_type")
        rad_react = sec.params.get("rad_react")

        # V-XSEC-121: push_type="radcool" requires omega_p0 > 0
        if isinstance(push_type, str) and push_type.lower() == "radcool":
            if omega_p0 is None or (isinstance(omega_p0, (int, float)) and omega_p0 <= 0):
                report.add(ValidationIssue(
                    rule_id="V-XSEC-121",
                    severity=Severity.ERROR,
                    message="push_type='radcool' requires omega_p0 > 0 in simulation section",
                    section=sec.name, line=sec.line,
                ))

        # V-XSEC-122: rad_react requires omega_p0 > 0
        if isinstance(rad_react, bool) and rad_react:
            if omega_p0 is None or (isinstance(omega_p0, (int, float)) and omega_p0 <= 0):
                report.add(ValidationIssue(
                    rule_id="V-XSEC-122",
                    severity=Severity.ERROR,
                    message="rad_react=.true. requires omega_p0 > 0 in simulation section",
                    section=sec.name, line=sec.line,
                ))

            # V-XSEC-123: rad_react only compatible with standard/exact push
            if isinstance(push_type, str):
                pt_lower = push_type.lower()
                if pt_lower not in ("standard", "exact", "analytic"):
                    report.add(ValidationIssue(
                        rule_id="V-XSEC-123",
                        severity=Severity.ERROR,
                        message=f"rad_react=.true. requires push_type='standard' or "
                                f"'exact', got '{push_type}'",
                        section=sec.name, line=sec.line,
                    ))

    # V-XSEC-124: Solver compatibility
    solver = _get_param(deck, "el_mag_fld", "solver")
    if isinstance(solver, str):
        solver_lower = solver.lower()
        p_x_dim = _get_dimension(deck)
        coordinates = _get_coordinates(deck)

        if p_x_dim == 1 and solver_lower in _SOLVER_1D_RESTRICTED:
            report.add(ValidationIssue(
                rule_id="V-XSEC-124",
                severity=Severity.ERROR,
                message=f"EMF solver '{solver}' is not implemented in 1D",
                section="el_mag_fld",
            ))

        if (coordinates == "cylindrical"
                and solver_lower in _SOLVER_CYLINDRICAL_RESTRICTED):
            report.add(ValidationIssue(
                rule_id="V-XSEC-124",
                severity=Severity.ERROR,
                message=f"EMF solver '{solver}' is not implemented "
                        "in 2D cylindrical geometry",
                section="el_mag_fld",
            ))


# ---- G. Smooth section structure ----


def _check_smooth_structure(deck: Deck, report: IssueReport) -> None:
    """Validate the structural placement of smooth sections."""
    smooth_count = _get_section_count(deck, "smooth")

    # V-XSEC-040: At most 2
    if smooth_count > 2:
        report.add(ValidationIssue(
            rule_id="V-XSEC-040",
            severity=Severity.ERROR,
            message=f"Found {smooth_count} 'smooth' sections; at most 2 are allowed "
                    "(EM smoothing before diag_emf, current smoothing after current)",
            section="smooth",
        ))

    # V-XSEC-041: Position validation
    if smooth_count >= 1:
        smooth_positions = [
            i for i, s in enumerate(deck.sections) if s.name == "smooth"
        ]
        diag_emf_positions = [
            i for i, s in enumerate(deck.sections) if s.name == "diag_emf"
        ]
        current_positions = [
            i for i, s in enumerate(deck.sections) if s.name == "current"
        ]

        first_smooth = smooth_positions[0]
        if diag_emf_positions and first_smooth > diag_emf_positions[0]:
            report.add(ValidationIssue(
                rule_id="V-XSEC-041",
                severity=Severity.WARNING,
                message="First 'smooth' (EM smoothing) should appear before 'diag_emf'",
                section="smooth",
            ))

        if smooth_count >= 2 and current_positions:
            second_smooth = smooth_positions[1]
            if second_smooth < current_positions[0]:
                report.add(ValidationIssue(
                    rule_id="V-XSEC-041",
                    severity=Severity.WARNING,
                    message="Second 'smooth' (current smoothing) should appear "
                            "after 'current'",
                    section="smooth",
                ))


# ---- H. Advanced checks ----


def _check_advanced(deck: Deck, report: IssueReport) -> None:
    """Courant condition and grid partition feasibility."""
    # V-XSEC-130: Courant condition (WARNING level)
    dt = _get_param(deck, "time_step", "dt")
    xmin = _get_param(deck, "space", "xmin")
    xmax = _get_param(deck, "space", "xmax")
    nx_p = _get_param(deck, "grid", "nx_p")

    if all(v is not None for v in [dt, xmin, xmax, nx_p]):
        dt_val = float(dt)
        xmin_list = _to_list(xmin)
        xmax_list = _to_list(xmax)
        nx_list = _to_list(nx_p)
        p_x_dim = len(nx_list)

        for i in range(min(p_x_dim, len(xmin_list), len(xmax_list))):
            if xmin_list[i] is None or xmax_list[i] is None:
                continue
            lo = float(xmin_list[i])
            hi = float(xmax_list[i])
            ncells = int(nx_list[i])
            if hi <= lo or ncells <= 0:
                continue
            dx = (hi - lo) / ncells
            if dt_val > dx:
                report.add(ValidationIssue(
                    rule_id="V-XSEC-130",
                    severity=Severity.WARNING,
                    message=f"Direction {i + 1}: dt ({dt_val}) > dx ({dx:.4g}) — "
                            "Courant condition may be violated",
                    section="time_step",
                ))
                break

    # V-XSEC-131: Grid partition feasibility
    node_number = _get_param(deck, "node_conf", "node_number")
    if node_number is not None and nx_p is not None:
        nn_list = _to_list(node_number)
        nx_list = _to_list(nx_p)
        for i in range(min(len(nn_list), len(nx_list))):
            nn = int(nn_list[i]) if isinstance(nn_list[i], (int, float)) else 0
            nx = int(nx_list[i]) if isinstance(nx_list[i], (int, float)) else 0
            if nn > 0 and nx > 0 and nn > nx:
                report.add(ValidationIssue(
                    rule_id="V-XSEC-131",
                    severity=Severity.ERROR,
                    message=f"Direction {i + 1}: node_number ({nn}) exceeds "
                            f"nx_p ({nx}) — too many partitions for grid size",
                    section="node_conf",
                ))


# ---- Entry point ----


def check_cross_section(deck: Deck, report: IssueReport) -> None:
    """Run all cross-section validation rules."""
    _check_count_match(deck, report)
    _check_dimensional_consistency(deck, report)
    _check_species_group_structure(deck, report)
    _check_neutral_gas(deck, report)
    _check_physics_compatibility(deck, report)
    _check_parameter_dependencies(deck, report)
    _check_smooth_structure(deck, report)
    _check_advanced(deck, report)
