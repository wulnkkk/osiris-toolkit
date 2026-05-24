"""Unit conversion between OSIRIS normalized and physical units.

OSIRIS uses normalized simulation units where all physical quantities
are scaled by combinations of these base quantities: electron mass (m_e),
speed of light (c), elementary charge (e), and reference plasma
frequency (omega_p).

    E/B field  : m_e * c * omega_p / e
    time       : 1 / omega_p
    length     : c / omega_p  (skin depth)
    momentum   : m_e * c
    energy     : m_e * c^2
    density    : n_0 (reference density)
    current    : e * n_0 * c

See Also
--------
units.params.SimulationParams :
    Provides omega_p0 from a parsed input deck.
"""

from __future__ import annotations

import numpy as np

from osiris_toolkit.units.params import SimulationParams

# Physical constants (SI)
C_LIGHT = 2.99792458e8        # m/s
M_ELECTRON = 9.10938356e-31   # kg
E_CHARGE = 1.602176634e-19    # C
EPSILON0 = 8.854187817e-12    # F/m

# SI: omega_p^2 = n0_cm3 * 1e6 * e^2 / (eps0 * m_e)
_SI_N0CM3_TO_OMEGAP_SQ = 1e6 * E_CHARGE**2 / (EPSILON0 * M_ELECTRON)

UNIT_DEFINITIONS: dict[str, tuple[str, str, str]] = {
    "time":      ("time",      "1/omega_p",            "omega_p^{-1}"),
    "length":    ("length",    "c/omega_p",            "skin depth"),
    "velocity":  ("velocity",  "c",                    "speed of light"),
    "momentum":  ("momentum",  "m_e * c",              "electron mass * c"),
    "energy":    ("energy",    "m_e * c^2",            "electron rest energy"),
    "density":   ("density",   "n_0",                  "reference plasma density"),
    "e_field":   ("E-field",   "m_e * c * omega_p / e", "cold wave-breaking field"),
    "b_field":   ("B-field",   "m_e * omega_p / e",    "~E/c"),
    "current":   ("current",   "e * n_0 * c",          "e n_0 c"),
    "charge":    ("charge",    "e",                    "elementary charge"),
    "mass":      ("mass",      "m_e",                  "electron mass"),
    "frequency": ("frequency", "omega_p",              "plasma frequency"),
}


def _build_scales(omega_p: float) -> dict[str, dict[str, float]]:
    """Build the scale-factor lookup table for a given omega_p [rad/s]."""
    l_si = C_LIGHT / omega_p               # m per normalized length
    t_si = 1.0 / omega_p                   # s per normalized time
    e_si = M_ELECTRON * C_LIGHT * omega_p / E_CHARGE   # V/m per normalized E
    b_si = M_ELECTRON * omega_p / E_CHARGE             # T per normalized B
    n0_cm3 = omega_p**2 / _SI_N0CM3_TO_OMEGAP_SQ      # reference density in cm^-3

    return {
        "time": {
            "norm": 1.0, "s": t_si, "fs": t_si * 1e15,
            "ps": t_si * 1e12, "ns": t_si * 1e9,
        },
        "length": {
            "norm": 1.0, "m": l_si, "mm": l_si * 1e3,
            "um": l_si * 1e6, "nm": l_si * 1e9, "A": l_si * 1e10,
        },
        "velocity": {
            "norm": 1.0, "m/s": C_LIGHT, "c": 1.0,
        },
        "momentum": {
            "norm": 1.0, "kg*m/s": M_ELECTRON * C_LIGHT,
            "MeV/c": M_ELECTRON * C_LIGHT * C_LIGHT / (E_CHARGE * 1e6),
        },
        "energy": {
            "norm": 1.0, "J": M_ELECTRON * C_LIGHT**2,
            "eV": M_ELECTRON * C_LIGHT**2 / E_CHARGE,
            "keV": M_ELECTRON * C_LIGHT**2 / (E_CHARGE * 1e3),
            "MeV": M_ELECTRON * C_LIGHT**2 / (E_CHARGE * 1e6),
            "GeV": M_ELECTRON * C_LIGHT**2 / (E_CHARGE * 1e9),
        },
        "e_field": {
            "norm": 1.0, "V/m": e_si,
            "GV/m": e_si / 1e9, "TV/m": e_si / 1e12,
        },
        "b_field": {
            "norm": 1.0, "T": b_si,
            "kT": b_si / 1e3, "MT": b_si / 1e6,
        },
        "density": {
            "norm": 1.0, "m^-3": n0_cm3 * 1e6, "cm^-3": n0_cm3,
        },
        "frequency": {
            "norm": 1.0, "rad/s": omega_p,
            "THz": omega_p / (2 * np.pi * 1e12),
        },
        "charge": {
            "norm": 1.0, "C": E_CHARGE,
            "nC": E_CHARGE * 1e9, "pC": E_CHARGE * 1e12,
        },
    }


# quantity -> default "auto" unit
_AUTO_UNITS: dict[str, str] = {
    "time": "ps", "length": "um", "velocity": "c",
    "momentum": "MeV/c", "energy": "MeV", "e_field": "GV/m",
    "b_field": "T", "density": "cm^-3", "frequency": "THz",
    "charge": "nC",
}

# quantity -> LaTeX label template
_LABELS: dict[str, str] = {
    "time":      r"t [${unit}$]",
    "length":    r"x [${unit}$]",
    "velocity":  r"v [${unit}$]",
    "momentum":  r"p [${unit}$]",
    "energy":    r"E [${unit}$]",
    "e_field":   r"E [${unit}$]",
    "b_field":   r"B [${unit}$]",
    "density":   r"n [${unit}$]",
    "frequency": r"$\omega$ [${unit}$]",
    "charge":    r"Q [${unit}$]",
}

# ---------------------------------------------------------------------------
# Legacy SI -> normalized conversion functions
# ---------------------------------------------------------------------------


def plasma_frequency(n0: float) -> float:
    """Compute plasma frequency omega_p from density n0 [m^-3]."""
    return float(np.sqrt(n0 * E_CHARGE**2 / (EPSILON0 * M_ELECTRON)))


def skin_depth(n0: float) -> float:
    """Compute collisionless skin depth c / omega_p from n0 [m^-3]."""
    return C_LIGHT / plasma_frequency(n0)


def normalize_time(t_si: float, omega_p: float) -> float:
    """Convert time from SI [s] to normalized units."""
    return t_si * omega_p


def normalize_length(x_si: float, omega_p: float) -> float:
    """Convert length from SI [m] to normalized units."""
    return x_si * omega_p / C_LIGHT


def normalize_density(n_si: float, n0: float) -> float:
    """Convert density from SI [m^-3] to normalized units."""
    return n_si / n0


def normalize_efield(e_si: float, omega_p: float) -> float:
    """Convert E-field from SI [V/m] to normalized units."""
    return e_si * E_CHARGE / (M_ELECTRON * C_LIGHT * omega_p)


def normalize_bfield(b_si: float, omega_p: float) -> float:
    """Convert B-field from SI [T] to normalized units."""
    return b_si * E_CHARGE / (M_ELECTRON * omega_p)


def normalize_momentum(p_si: float) -> float:
    """Convert momentum from SI [kg*m/s] to normalized units."""
    return p_si / (M_ELECTRON * C_LIGHT)


def normalize_energy(en_si: float) -> float:
    """Convert energy from SI [J] to normalized units."""
    return en_si / (M_ELECTRON * C_LIGHT * C_LIGHT)


def normalize_current(j_si: float, n0: float) -> float:
    """Convert current density from SI [A/m^2] to normalized units."""
    return j_si / (E_CHARGE * n0 * C_LIGHT)


# ---------------------------------------------------------------------------
# UnitConverter class
# ---------------------------------------------------------------------------


class UnitConverter:
    """Bidirectional converter between OSIRIS normalized and physical units.

    Parameters
    ----------
    omega_p : float
        Reference plasma frequency in rad/s.

    Attributes
    ----------
    omega_p : float
        The plasma frequency used to build all scale factors.
    n0_cm3 : float
        Reference density in cm^-3.

    Examples
    --------
    >>> uc = UnitConverter(3.55e15)
    >>> uc.convert(10.0, "time", "fs")
    2.816...
    >>> uc.get_label("length", "um")
    'x [um]'

    Using with SimulationParams from a parsed deck:

    >>> from osiris_toolkit.deck import parse_deck_file
    >>> from osiris_toolkit.units import SimulationParams
    >>> deck = parse_deck_file("input/simulation.in")
    >>> params = SimulationParams.from_deck(deck)
    >>> uc = UnitConverter(params.omega_p0)
    """

    def __init__(self, omega_p: float) -> None:
        if omega_p <= 0:
            raise ValueError(f"omega_p must be > 0, got {omega_p}")
        self.omega_p = omega_p
        self._scales = _build_scales(omega_p)

    # -- public API ---------------------------------------------------------

    def get_scale(self, quantity: str, unit: str) -> float:
        """Return the scale factor: result = normalized_value * scale."""
        q_scales = self._scales.get(quantity)
        if q_scales is None:
            raise KeyError(
                f"Unknown quantity {quantity!r}. Known: {sorted(self._scales)}"
            )
        if unit == "auto":
            unit = _AUTO_UNITS.get(quantity, "norm")
        s = q_scales.get(unit)
        if s is None:
            raise KeyError(
                f"Unknown unit {unit!r} for {quantity}. Known: {sorted(q_scales)}"
            )
        return s

    def convert(
        self,
        data: np.ndarray | float,
        quantity: str,
        unit: str,
    ) -> np.ndarray | float:
        """Convert normalized data to the target unit.

        Parameters
        ----------
        data : array or float
            Value(s) in OSIRIS normalized units.
        quantity : str
            Physical quantity type ('time', 'length', 'e_field', etc.).
        unit : str
            Target unit ('ps', 'um', 'GV/m', etc.), or 'auto', or 'norm'.

        Returns
        -------
        Converted data, matching input shape and type.
        """
        scale = self.get_scale(quantity, unit)
        if isinstance(data, np.ndarray):
            return data * scale
        return data * scale

    def get_label(self, quantity: str, unit: str) -> str:
        """Return an axis label string for the given quantity and unit."""
        if unit == "auto":
            unit = _AUTO_UNITS.get(quantity, "norm")
        if unit == "norm":
            info = UNIT_DEFINITIONS.get(quantity)
            if info:
                return f"[{info[1]}]"
            return f"[norm {quantity}]"
        template = _LABELS.get(quantity, f"{{{unit}}}")
        return template.format(unit=unit)

    def get_time_label(self, unit: str) -> str:
        """Convenience: time axis label."""
        return self.get_label("time", unit)

    def get_length_label(self, unit: str, axis: str = "x") -> str:
        """Convenience: spatial axis label."""
        if unit == "auto":
            unit = _AUTO_UNITS.get("length", "norm")
        if unit == "norm":
            return f"{axis} [c/omega_p]"
        return f"{axis} [{unit}]"

    @property
    def n0_cm3(self) -> float:
        """Reference density in cm^-3."""
        return self._scales["density"]["cm^-3"]

    # -- factory methods ----------------------------------------------------

    @classmethod
    def from_params(cls, params: SimulationParams) -> "UnitConverter":
        """Create a UnitConverter from SimulationParams.

        This is the recommended constructor when working with a parsed
        input deck.
        """
        return cls(params.omega_p0)

    def __repr__(self) -> str:
        return (
            f"UnitConverter(omega_p={self.omega_p:.4g} rad/s, "
            f"n0={self.n0_cm3:.4g} cm^-3)"
        )
