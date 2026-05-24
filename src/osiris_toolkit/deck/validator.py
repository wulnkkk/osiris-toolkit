"""Semantic validation rules for OSIRIS input decks.

Validates a parsed Deck against rules derived from the Fortran source code.
"""

from .ast import Deck, Section
from .reporter import IssueReport, Severity, ValidationIssue
from .schemas.parameters import get_section_params
from .schemas.registry import (
    SectionKind,
    canonical_index,
    get_required_sections,
    get_spec,
    is_species_group_section,
)


def validate_deck(deck: Deck) -> IssueReport:
    """Run all validation rules on a parsed deck and return a report."""
    report = IssueReport()
    _check_required_sections(deck, report)
    _check_section_order(deck, report)
    _check_param_schema(deck, report)
    _check_node_conf(deck, report)
    _check_grid(deck, report)
    _check_time_step(deck, report)
    _check_space(deck, report)
    _check_simulation(deck, report)
    _check_species(deck, report)
    from .cross_validator import check_cross_section
    check_cross_section(deck, report)
    return report


# ---- Required sections ----

def _check_required_sections(deck: Deck, report: IssueReport):
    present = {s.name for s in deck.sections}
    for name in get_required_sections():
        spec = get_spec(name)
        if spec and spec.kind == SectionKind.REQUIRED and name not in present:
            report.add(ValidationIssue(
                rule_id="V-REQUIRED-001",
                severity=Severity.ERROR,
                message=f"Required section '{name}' is missing",
                section=name,
                suggestion=f"Add a '{name} {{ ... }}' block to the input deck",
            ))


# ---- Section ordering ----

def _check_section_order(deck: Deck, report: IssueReport):
    prev_idx = -1
    prev_name = ""
    for sec in deck.sections:
        idx = canonical_index(sec.name)
        if idx == -1:
            report.add(ValidationIssue(
                rule_id="V-ORDER-002",
                severity=Severity.WARNING,
                message=f"Unknown section '{sec.name}'",
                section=sec.name,
                line=sec.line,
            ))
            continue
        # Skip order check for sections that can appear in multiple contexts
        # (e.g. 'smooth' can be EM smoothing or current smoothing)
        spec = get_spec(sec.name)
        if spec and spec.min_repeat == 0 and spec.max_repeat and spec.max_repeat > 1:
            continue
        if is_species_group_section(sec.name):
            continue
        if idx < prev_idx:
            report.add(ValidationIssue(
                rule_id="V-ORDER-001",
                severity=Severity.ERROR,
                message=f"Section '{sec.name}' is out of order (appears after '{prev_name}')",
                section=sec.name,
                line=sec.line,
            ))
        else:
            prev_idx = idx
            prev_name = sec.name


# ---- node_conf ----

def _check_node_conf(deck: Deck, report: IssueReport):
    for sec in deck.sections:
        if sec.name != "node_conf":
            continue
        for dim_key in ["node_number", "node_number(1)", "node_number(1:1)"]:
            val = _resolve(sec, dim_key)
            if val is not None and isinstance(val, (int, float)) and val <= 0:
                report.add(ValidationIssue(
                    rule_id="V-NODE-001",
                    severity=Severity.ERROR,
                    message="node_number must be > 0",
                    section="node_conf", line=sec.line,
                ))
                break
        nt = _resolve(sec, "n_threads")
        if nt is not None and isinstance(nt, (int, float)) and nt < 1:
            report.add(ValidationIssue(
                rule_id="V-NODE-002",
                severity=Severity.ERROR,
                message="n_threads must be >= 1",
                section="node_conf", line=sec.line,
            ))


# ---- grid ----

_VALID_COORDINATES = {"cartesian", "cylindrical"}

def _check_grid(deck: Deck, report: IssueReport):
    for sec in deck.sections:
        if sec.name != "grid":
            continue
        p = sec.params
        # nx_p > 0
        for key in p:
            if key.startswith("nx_p"):
                val = p[key]
                vals = val if isinstance(val, list) else [val]
                if any(v is not None and isinstance(v, (int, float)) and v <= 0 for v in vals):
                    report.add(ValidationIssue(
                        rule_id="V-GRID-001",
                        severity=Severity.ERROR,
                        message="nx_p values must be > 0",
                        section="grid", line=sec.line,
                    ))
                break
        # Coordinates
        coord = _resolve(sec, "coordinates")
        if coord is not None and isinstance(coord, str):
            if coord.lower() not in _VALID_COORDINATES:
                report.add(ValidationIssue(
                    rule_id="V-GRID-002",
                    severity=Severity.ERROR,
                    message=f"Unknown coordinates type '{coord}'. "
                            f"Valid: {', '.join(sorted(_VALID_COORDINATES))}",
                    section="grid", line=sec.line,
                ))


# ---- time_step ----

def _check_time_step(deck: Deck, report: IssueReport):
    for sec in deck.sections:
        if sec.name != "time_step":
            continue
        dt = _resolve(sec, "dt")
        if dt is not None and isinstance(dt, (int, float)):
            if dt == 0:
                report.add(ValidationIssue(
                    rule_id="V-TSTEP-001",
                    severity=Severity.ERROR,
                    message="dt must not be zero",
                    section="time_step", line=sec.line,
                ))
            elif dt < 0:
                report.add(ValidationIssue(
                    rule_id="V-TSTEP-002",
                    severity=Severity.ERROR,
                    message="dt must be positive",
                    section="time_step", line=sec.line,
                ))


# ---- space ----

def _check_space(deck: Deck, report: IssueReport):
    for sec in deck.sections:
        if sec.name != "space":
            continue
        xmin = _resolve(sec, "xmin")
        xmax = _resolve(sec, "xmax")

        if xmin is not None and xmax is not None:
            xmins = xmin if isinstance(xmin, list) else [xmin]
            xmaxs = xmax if isinstance(xmax, list) else [xmax]
            for i, (lo, hi) in enumerate(zip(xmins, xmaxs)):
                if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and lo > hi:
                    report.add(ValidationIssue(
                        rule_id="V-SPACE-001",
                        severity=Severity.ERROR,
                        message=f"xmin[{i + 1}] ({lo}) > xmax[{i + 1}] ({hi})",
                        section="space", line=sec.line,
                    ))
                elif lo == hi and isinstance(lo, (int, float)):
                    report.add(ValidationIssue(
                        rule_id="V-SPACE-004",
                        severity=Severity.INFO,
                        message=f"xmin[{i + 1}] == xmax[{i + 1}] ({lo}) — unused dimension?",
                        section="space", line=sec.line,
                    ))


# ---- simulation ----

def _check_simulation(deck: Deck, report: IssueReport):
    for sec in deck.sections:
        if sec.name != "simulation":
            continue
        omega = _resolve(sec, "omega_p0")
        n0 = _resolve(sec, "n0")
        gamma = _resolve(sec, "gamma")
        if omega is not None and isinstance(omega, (int, float)) and omega < 0:
            report.add(ValidationIssue(
                rule_id="V-SIM-001",
                severity=Severity.ERROR,
                message="omega_p0 must be >= 0",
                section="simulation", line=sec.line,
            ))
        if n0 is not None and isinstance(n0, (int, float)) and n0 < 0:
            report.add(ValidationIssue(
                rule_id="V-SIM-002",
                severity=Severity.ERROR,
                message="n0 must be >= 0",
                section="simulation", line=sec.line,
            ))
        if gamma is not None and isinstance(gamma, (int, float)) and gamma < 1:
            report.add(ValidationIssue(
                rule_id="V-SIM-003",
                severity=Severity.WARNING,
                message=f"gamma ({gamma}) is less than 1",
                section="simulation", line=sec.line,
            ))


# ---- species ----

def _check_species(deck: Deck, report: IssueReport):
    for sec in deck.sections:
        if sec.name != "species":
            continue
        rqm = _resolve(sec, "rqm")
        if rqm is not None and isinstance(rqm, (int, float)) and rqm == 0:
            report.add(ValidationIssue(
                rule_id="V-SPECIES-001",
                severity=Severity.ERROR,
                message="rqm must not be zero",
                section=sec.name, line=sec.line,
            ))


# ---- Parameter schema validation ----

def _check_param_schema(deck: Deck, report: IssueReport):
    """Validate parameters against ParamSpec schemas.

    V-PARAM-001: Unknown parameter name
    V-PARAM-002: Type mismatch
    V-PARAM-003: Value out of range
    V-PARAM-004: Missing required parameter
    V-PARAM-005: Array dimension mismatch
    """
    for sec in deck.sections:
        param_specs = get_section_params(sec.name)
        if not param_specs:
            continue  # No schema defined for this section — skip

        known_names = {ps.name for ps in param_specs}
        spec_by_name = {ps.name: ps for ps in param_specs}

        for key, val in sec.params.items():
            # V-PARAM-001: Unknown parameter
            if key not in known_names:
                report.add(ValidationIssue(
                    rule_id="V-PARAM-001",
                    severity=Severity.INFO,
                    message=f"Unknown parameter '{key}' in section '{sec.name}'",
                    section=sec.name, line=sec.line,
                ))
                continue

            ps = spec_by_name[key]
            actual_val = _unwrap(val)

            # V-PARAM-002: Type mismatch
            _check_type_match(key, actual_val, ps, sec, report)

            # V-PARAM-003: Constraint violation
            _check_constraints(key, actual_val, ps, sec, report)

        # V-PARAM-004: Missing required parameters
        for ps in param_specs:
            if ps.required and ps.name not in sec.params:
                report.add(ValidationIssue(
                    rule_id="V-PARAM-004",
                    severity=Severity.WARNING,
                    message=f"Required parameter '{ps.name}' missing from section '{sec.name}'",
                    section=sec.name, line=sec.line,
                ))


def _check_type_match(key: str, val, ps, sec: Section, report: IssueReport):
    """Check that a value's type matches the ParamSpec type.

    For list/array values, checks each element individually.
    """
    if val is None:
        return
    if isinstance(val, list):
        for v in val:
            _check_type_match(key, v, ps, sec, report)
        return
    if ps.python_type is float and not isinstance(val, (int, float)):
        report.add(_type_issue(key, ps, "float/int", type(val).__name__, sec))
    elif ps.python_type is int and isinstance(val, float) and val != int(val):
        report.add(_type_issue(key, ps, "int", "float (non-integral)", sec))
    elif ps.python_type is bool and not isinstance(val, bool):
        report.add(_type_issue(key, ps, "bool", type(val).__name__, sec))
    elif ps.python_type is str and not isinstance(val, str):
        report.add(_type_issue(key, ps, "str", type(val).__name__, sec))


def _check_constraints(key: str, val, ps, sec: Section, report: IssueReport):
    """Check value against ParamSpec constraints."""
    if val is None or not ps.constraints:
        return
    if isinstance(val, list):
        for i, v in enumerate(val):
            _check_single_constraint(key, v, ps, i, sec, report)
    else:
        _check_single_constraint(key, val, ps, None, sec, report)


def _check_single_constraint(
    key: str, val, ps, idx: int | None, sec: Section, report: IssueReport,
):
    """Check a single scalar value against all constraints."""
    if not isinstance(val, (int, float)):
        return  # Constraints apply only to numerics
    idx_str = f"[{idx + 1}]" if idx is not None else ""
    for c in ps.constraints:
        if c == "> 0" and not (val > 0):
            report.add(ValidationIssue(
                rule_id="V-PARAM-003",
                severity=Severity.ERROR,
                message=f"'{key}{idx_str}' = {val} violates constraint: > 0",
                section=sec.name, line=sec.line,
            ))
        elif c == ">= 0" and not (val >= 0):
            report.add(ValidationIssue(
                rule_id="V-PARAM-003",
                severity=Severity.ERROR,
                message=f"'{key}{idx_str}' = {val} violates constraint: >= 0",
                section=sec.name, line=sec.line,
            ))
        elif c == ">= 1" and not (val >= 1):
            report.add(ValidationIssue(
                rule_id="V-PARAM-003",
                severity=Severity.ERROR,
                message=f"'{key}{idx_str}' = {val} violates constraint: >= 1",
                section=sec.name, line=sec.line,
            ))
        elif c == "!= 0" and val == 0:
            report.add(ValidationIssue(
                rule_id="V-PARAM-003",
                severity=Severity.ERROR,
                message=f"'{key}{idx_str}' = {val} violates constraint: != 0",
                section=sec.name, line=sec.line,
            ))
        elif c.startswith("in ("):
            # Enum constraint like "in (cartesian, cylindrical)"
            pass  # handled separately


def _type_issue(key: str, ps, expected: str, got: str, sec: Section) -> ValidationIssue:
    return ValidationIssue(
        rule_id="V-PARAM-002",
        severity=Severity.WARNING,
        message=f"'{key}' in '{sec.name}': expected {expected}, got {got}",
        section=sec.name, line=sec.line,
    )


# ---- Helpers ----

def _unwrap(val):
    """Extract the actual value from a sliced/wrapped parameter, or return as-is."""
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val


def _resolve(sec: Section, key: str):
    """Resolve a parameter by exact name, returning None if absent."""
    if key in sec.params:
        return _unwrap(sec.params[key])
    return None
