"""Canonical section registry for OSIRIS input decks.

Defines standard section ordering, required/optional marking, conditional
dispatch, and species-group repeat boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .parameters import ParamSpec


class SectionKind(Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"  # appears only when another section/parameter triggers it


class SectionContext(Enum):
    GLOBAL = "global"
    SPECIES_GROUP = "species_group"  # repeated once per species
    ANTENNA_GROUP = "antenna_group"  # inside antenna_array


@dataclass(frozen=True)
class SectionSpec:
    """Specification for a single section type."""

    name: str
    kind: SectionKind
    context: SectionContext = SectionContext.GLOBAL
    min_repeat: int = 1
    max_repeat: int | None = 1  # None = unlimited
    condition: str | None = None  # human-readable condition
    description: str = ""
    params: list[ParamSpec] | None = None  # parameter-level schema (from parameters)


# Canonical section definitions, in order
# Order must match os-simulation.f03 :: read_input_sim() call sequence
_SECTIONS: list[SectionSpec] = [
    # ---- Setup ----
    SectionSpec(
        "simulation",
        SectionKind.OPTIONAL,
        description="Global simulation metadata (omega_p0, n0, gamma, random_seed)",
    ),
    SectionSpec(
        "node_conf",
        SectionKind.REQUIRED,
        description="Parallel node configuration",
    ),
    SectionSpec(
        "grid",
        SectionKind.REQUIRED,
        description="Spatial grid definition",
    ),
    SectionSpec(
        "time_step",
        SectionKind.REQUIRED,
        description="Time step and output frequency",
    ),
    SectionSpec(
        "restart",
        SectionKind.OPTIONAL,
        description="Restart configuration",
    ),
    # ---- Space / Time ----
    SectionSpec(
        "space",
        SectionKind.REQUIRED,
        description="Spatial extent and moving window",
    ),
    SectionSpec(
        "time",
        SectionKind.REQUIRED,
        description="Time range",
    ),
    # ---- EM Fields ----
    SectionSpec(
        "el_mag_fld",
        SectionKind.OPTIONAL,
        description="EM field solver type and external fields",
    ),
    SectionSpec(
        "emf_bound",
        SectionKind.REQUIRED,
        description="EM field boundary conditions",
    ),
    SectionSpec(
        "emf_solver",
        SectionKind.CONDITIONAL,
        condition="Solver type requires extra parameters (custom/fei, lehe, ndfx, stencil)",
        description="Advanced EM solver parameters",
    ),
    SectionSpec(
        "smooth",
        SectionKind.OPTIONAL,
        min_repeat=0,
        max_repeat=2,
        description="Smoothing configuration. First occurrence (before diag_emf) is EM smoothing; "
        "second (after current) is current smoothing",
    ),
    SectionSpec(
        "diag_emf",
        SectionKind.OPTIONAL,
        description="EM field diagnostics",
    ),
    SectionSpec(
        "pgc",
        SectionKind.CONDITIONAL,
        condition="Compiled with metamaterial/PGC support (__HAS_PGC__)",
        description="Metamaterial/PGC (Perfectly Guided Conductor) configuration",
    ),
    # ---- Particles ----
    SectionSpec(
        "particles",
        SectionKind.REQUIRED,
        description="Particle species count and global settings",
    ),
    # Species group — repeated num_species times (conditional: num_species > 0)
    SectionSpec(
        "species",
        SectionKind.CONDITIONAL,
        context=SectionContext.SPECIES_GROUP,
        condition="num_species > 0 in particles section",
        min_repeat=1,
        max_repeat=None,
        description="Per-species configuration",
    ),
    SectionSpec(
        "udist",
        SectionKind.OPTIONAL,
        context=SectionContext.SPECIES_GROUP,
        min_repeat=0,
        max_repeat=None,
        description="Per-species velocity distribution",
    ),
    SectionSpec(
        "sdist",
        SectionKind.CONDITIONAL,
        context=SectionContext.SPECIES_GROUP,
        condition="Compiled with spin support (__HAS_SPIN__)",
        min_repeat=0,
        max_repeat=None,
        description="Per-species spin distribution",
    ),
    SectionSpec(
        "profile",
        SectionKind.CONDITIONAL,
        context=SectionContext.SPECIES_GROUP,
        condition="Standard species (read_prof=.true., not associated with cathode/neutral)",
        min_repeat=1,
        max_repeat=None,
        description="Per-species density profile",
    ),
    SectionSpec(
        "spe_bound",
        SectionKind.OPTIONAL,
        context=SectionContext.SPECIES_GROUP,
        min_repeat=0,
        max_repeat=None,
        description="Per-species boundary conditions",
    ),
    SectionSpec(
        "piston",
        SectionKind.CONDITIONAL,
        context=SectionContext.SPECIES_GROUP,
        condition="num_pistons > 0 in species section",
        min_repeat=0,
        max_repeat=None,
        description="Per-species piston boundaries",
    ),
    SectionSpec(
        "diag_species",
        SectionKind.OPTIONAL,
        context=SectionContext.SPECIES_GROUP,
        min_repeat=0,
        max_repeat=None,
        description="Per-species diagnostics",
    ),
    # ---- Cathodes / Neutrals / Collisions ----
    SectionSpec(
        "cathode",
        SectionKind.CONDITIONAL,
        condition="num_cathode > 0 in particles section",
        min_repeat=1,
        max_repeat=None,
        description="Cathode injection parameters",
    ),
    SectionSpec(
        "neutral",
        SectionKind.CONDITIONAL,
        condition="num_neutral > 0 in particles section (compiled with ionization)",
        min_repeat=1,
        max_repeat=None,
        description="Neutral gas configuration",
    ),
    SectionSpec(
        "neutral_mov_ions",
        SectionKind.CONDITIONAL,
        condition="num_neutral_mov_ions > 0 in particles section",
        min_repeat=1,
        max_repeat=None,
        description="Moving ions in neutral gas",
    ),
    SectionSpec(
        "num_ene",
        SectionKind.CONDITIONAL,
        condition="inside neutral with if_impact and custom gas type",
        min_repeat=0,
        max_repeat=None,
        description="Number of energy points for custom cross-sections",
    ),
    SectionSpec(
        "cross",
        SectionKind.CONDITIONAL,
        condition="inside neutral with if_impact and custom gas type",
        min_repeat=0,
        max_repeat=None,
        description="Cross-section data for custom gas",
    ),
    SectionSpec(
        "diag_neutral",
        SectionKind.OPTIONAL,
        condition="inside neutral",
        min_repeat=0,
        max_repeat=None,
        description="Neutral gas diagnostics",
    ),
    SectionSpec(
        "collisions",
        SectionKind.CONDITIONAL,
        condition="Compiled with collision support (__HAS_COLLISIONS__)",
        description="Collision configuration",
    ),
    # ---- ZPulse variants (mutually exclusive, zero or more) ----
    SectionSpec(
        "zpulse",
        SectionKind.OPTIONAL,
        min_repeat=0,
        max_repeat=None,
        description="Standard laser pulse configuration",
    ),
    SectionSpec(
        "zpulse_wall",
        SectionKind.OPTIONAL,
        min_repeat=0,
        max_repeat=None,
        description="Wall-injected laser pulse configuration",
    ),
    SectionSpec(
        "zpulse_point",
        SectionKind.OPTIONAL,
        min_repeat=0,
        max_repeat=None,
        description="Point-source laser pulse configuration",
    ),
    SectionSpec(
        "zpulse_speckle",
        SectionKind.OPTIONAL,
        min_repeat=0,
        max_repeat=None,
        description="Laser speckle pulse configuration (ISI, RPP, CPP, SSD, CPURP)",
    ),
    # ---- Current ----
    SectionSpec(
        "current",
        SectionKind.OPTIONAL,
        description="Current deposition configuration",
    ),
    SectionSpec(
        "diag_current",
        SectionKind.OPTIONAL,
        description="Current diagnostics",
    ),
    # ---- Antennas ----
    SectionSpec(
        "antenna_array",
        SectionKind.OPTIONAL,
        description="Antenna array container",
    ),
    SectionSpec(
        "antenna",
        SectionKind.CONDITIONAL,
        context=SectionContext.ANTENNA_GROUP,
        condition="n_antenna > 0 in antenna_array",
        min_repeat=0,
        max_repeat=None,
        description="Individual antenna configuration",
    ),
]


def get_section_specs() -> list[SectionSpec]:
    """Return all section specs in canonical order."""
    return list(_SECTIONS)


def get_section_names() -> list[str]:
    """Return all known section names in canonical order."""
    return [s.name for s in _SECTIONS]


def get_required_sections() -> list[str]:
    """Return the names of required sections."""
    return [s.name for s in _SECTIONS if s.kind == SectionKind.REQUIRED]


def get_spec(name: str) -> SectionSpec | None:
    """Look up a section spec by name."""
    for s in _SECTIONS:
        if s.name == name:
            return s
    return None


def is_species_group_section(name: str) -> bool:
    """Check whether a section belongs to the per-species group."""
    spec = get_spec(name)
    return spec is not None and spec.context == SectionContext.SPECIES_GROUP


def is_known_section(name: str) -> bool:
    """Check whether a section name is known."""
    return get_spec(name) is not None


def canonical_index(name: str) -> int:
    """Return the canonical position index of a section, or -1 if unknown."""
    for i, s in enumerate(_SECTIONS):
        if s.name == name:
            return i
    return -1


def get_species_group_sections() -> list[str]:
    """Return the subset of section names that form the species group block."""
    return [s.name for s in _SECTIONS if s.context == SectionContext.SPECIES_GROUP]


def get_spec_with_params(name: str) -> SectionSpec | None:
    """Look up a SectionSpec with populated parameter schemas."""
    spec = get_spec(name)
    if spec is None:
        return None
    from .parameters import get_section_params

    param_list = get_section_params(name)
    # Always populate params (empty list for sections with no parameters)
    return SectionSpec(
        name=spec.name,
        kind=spec.kind,
        context=spec.context,
        min_repeat=spec.min_repeat,
        max_repeat=spec.max_repeat,
        condition=spec.condition,
        description=spec.description,
        params=param_list,
    )
