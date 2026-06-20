"""Declarative catalog of OSIRIS diagnostic types.

Maps OSIRIS output directory structure to Python data types and
unit categories. Each entry describes one diagnostic kind; the
Simulation auto-discovery uses this catalog to index output files.
"""

from __future__ import annotations

from dataclasses import dataclass

from osiris_toolkit._models import (
    GridData,
    HistoryData,
    ParticleData,
    PhasespaceData,
    TrackData,
)

# ---------------------------------------------------------------------------
# Diagnostic kind definition
# ---------------------------------------------------------------------------


@dataclass
class DiagKind:
    """Complete definition of one OSIRIS diagnostic type.

    Attributes
    ----------
    name : str
        Canonical name (e.g. "EMF", "DENSITY").
    dir_pattern : str
        Subdirectory pattern relative to simulation root.
        Use ``{species}`` and ``{ps_name}`` for per-species/per-direction
        directories.
    data_class : type
        Python dataclass returned by accessors for this diagnostic.
    is_per_species : bool
        Whether this diagnostic is repeated for each particle species.
    is_per_axis : bool
        Whether individual files represent separate spatial components.
    quantities : list[str]
        Known diagnostic quantity names for this type (from Fortran source).
    unit_category : str | None
        Corresponding physical quantity category in UnitConverter.
    """

    name: str
    dir_pattern: str
    data_class: type
    is_per_species: bool = False
    is_per_axis: bool = False
    quantities: list[str] | None = None
    unit_category: str | None = None


# ---------------------------------------------------------------------------
# Complete OSIRIS diagnostic catalog
#
# Quantity lists are derived from the OSIRIS Fortran source:
#   - EMF:     os-emf-diag-define.f03  (34 quantities)
#   - Species: os-spec-diag-def.f03    (density 9, udist 12)
#   - Current: os-current-diagnostics.f03 (4 quantities)
# ---------------------------------------------------------------------------

OSIRIS_DIAGNOSTICS: dict[str, DiagKind] = {
    # -- EMF ----------------------------------------------------------------
    "EMF": DiagKind(
        name="EMF",
        dir_pattern="MS/FLD",
        data_class=GridData,
        is_per_axis=True,
        quantities=[
            "e1",
            "e2",
            "e3",
            "b1",
            "b2",
            "b3",
            "ext_e1",
            "ext_e2",
            "ext_e3",
            "ext_b1",
            "ext_b2",
            "ext_b3",
            "part_e1",
            "part_e2",
            "part_e3",
            "part_b1",
            "part_b2",
            "part_b3",
            "ene_e1",
            "ene_e2",
            "ene_e3",
            "ene_b1",
            "ene_b2",
            "ene_b3",
            "ene_e",
            "ene_b",
            "ene_emf",
            "div_e",
            "div_b",
            "psi",
            "chargecons",
            "s1",
            "s2",
            "s3",
        ],
        unit_category="e_field",
    ),
    # -- Charge conservation ------------------------------------------------
    "CHARGE_CONS": DiagKind(
        name="CHARGE_CONS",
        dir_pattern="MS/CHARGECONS",
        data_class=GridData,
        quantities=["chargecons"],
        unit_category=None,
    ),
    # -- Species density ----------------------------------------------------
    "DENSITY": DiagKind(
        name="DENSITY",
        dir_pattern="MS/DENSITY/{species}",
        data_class=GridData,
        is_per_species=True,
        quantities=[
            "charge",
            "mass",
            "ene",
            "q1",
            "q2",
            "q3",
            "j1",
            "j2",
            "j3",
        ],
        unit_category="density",
    ),
    # -- Cell-average density -----------------------------------------------
    "CELL_AVG": DiagKind(
        name="CELL_AVG",
        dir_pattern="MS/CELL_AVG/{species}",
        data_class=GridData,
        is_per_species=True,
        quantities=[
            "charge",
            "mass",
            "ene",
            "q1",
            "q2",
            "q3",
            "j1",
            "j2",
            "j3",
        ],
        unit_category="density",
    ),
    # -- U-distribution (momentum-space moments) ----------------------------
    "UDIST": DiagKind(
        name="UDIST",
        dir_pattern="MS/UDIST/{species}",
        data_class=GridData,
        is_per_species=True,
        quantities=[
            "ufl1",
            "ufl2",
            "ufl3",
            "uth1",
            "uth2",
            "uth3",
            "T11",
            "T22",
            "T33",
            "T12",
            "T13",
            "T23",
        ],
        unit_category="momentum",
    ),
    # -- Phasespace ---------------------------------------------------------
    "PHASESPACE": DiagKind(
        name="PHASESPACE",
        dir_pattern="MS/PHA/{ps_name}/{species}",
        data_class=PhasespaceData,
        is_per_species=True,
        quantities=[
            "p1p2",
            "p2p3",
            "p1p3",
            "x1p1",
            "x1p2",
            "x1p3",
            "x2p1",
            "x2p2",
            "x2p3",
            "x3p1",
            "x3p2",
            "x3p3",
        ],
        unit_category="momentum",
    ),
    # -- Raw particles ------------------------------------------------------
    "RAW": DiagKind(
        name="RAW",
        dir_pattern="MS/RAW/{species}",
        data_class=ParticleData,
        is_per_species=True,
        quantities=None,
        unit_category=None,
    ),
    # -- Tracks -------------------------------------------------------------
    "TRACKS": DiagKind(
        name="TRACKS",
        dir_pattern="MS/TRACKS",
        data_class=TrackData,
        quantities=None,
        unit_category=None,
    ),
    # -- Current ------------------------------------------------------------
    "CURRENT": DiagKind(
        name="CURRENT",
        dir_pattern="MS/CURRENT",
        data_class=GridData,
        quantities=["j1", "j2", "j3", "div_j"],
        unit_category="density",
    ),
    # -- Ionization ---------------------------------------------------------
    "ION": DiagKind(
        name="ION",
        dir_pattern="MS/ION/{species}",
        data_class=GridData,
        is_per_species=True,
        quantities=None,
        unit_category=None,
    ),
    # -- Wall (field at walls) ----------------------------------------------
    "WALL": DiagKind(
        name="WALL",
        dir_pattern="MS/FLD_WALL_*/{name}",
        data_class=GridData,
        quantities=None,
        unit_category="e_field",
    ),
    # -- History time series ------------------------------------------------
    "HISTORY": DiagKind(
        name="HISTORY",
        dir_pattern="HIST",
        data_class=HistoryData,
        quantities=None,
        unit_category=None,
    ),
}
