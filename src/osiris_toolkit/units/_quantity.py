"""QuantityKind — categorical description of a physical quantity.

Each instance encodes the normalized-to-physical conversion table (*scales*),
human-readable labels, and axis-type classification used by the unit system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from osiris_toolkit.exceptions import UnitConversionError

if TYPE_CHECKING:
    from numpy.typing import NDArray


@dataclass(frozen=True)
class QuantityKind:
    """Frozen descriptor for one physical quantity.

    Parameters
    ----------
    name : str
        Machine-readable short name (e.g. ``"length"``).
    description : str
        Human-readable description.
    norm_unit_label : str
        Plain-text label of the OSIRIS normalised unit.
    norm_unit_latex : str
        LaTeX label of the OSIRIS normalised unit.
    scales : dict[str, float]
        Map from unit key to conversion factor.  ``"norm"`` is always present
        and equals 1.0; physical keys are resolved later by ``UnitSystem``.
    auto_unit : str
        Default unit key used when ``unit="auto"``.
    label_template : str
        Template string for ``label()``.  The placeholder ``${unit}$`` is
        replaced by the actual unit name.
    latex_template : str or None, optional
        Template string for ``latex()``.  Falls back to ``label()`` when
        ``None``.
    axis_types : tuple[int, ...], optional
        Axis type(s) relevant to this quantity (default ``()``).
    """

    name: str
    description: str
    norm_unit_label: str
    norm_unit_latex: str
    scales: dict[str, float]
    auto_unit: str
    label_template: str
    latex_template: str | None = None
    axis_types: tuple[int, ...] = ()

    def to(self, data: NDArray[np.floating] | float, unit: str = "auto") -> NDArray[np.floating] | float:
        """Convert normalised *data* to *unit*.

        Parameters
        ----------
        data : ndarray or float
            Normalised data (1.0 corresponds to the OSIRIS normalised unit).
        unit : str, optional
            Target unit key.  ``"auto"`` uses *auto_unit*.

        Returns
        -------
        ndarray or float
            Data in the requested physical unit.

        Raises
        ------
        UnitConversionError
            If *unit* is not found in *scales*.
        """
        unit = self.auto_unit if unit == "auto" else unit
        try:
            scale = self.scales[unit]
        except KeyError:
            raise UnitConversionError(
                f"Unknown unit '{unit}' for quantity '{self.name}'. Available: {sorted(self.scales.keys())}"
            ) from None
        if isinstance(data, np.ndarray):
            return data * scale  # type: ignore[return-value]
        return float(data) * scale

    def label(self, unit: str = "auto") -> str:
        """Human-readable label including the unit suffix.

        Parameters
        ----------
        unit : str, optional
            Unit key.  ``"norm"`` returns the normalised unit label directly.
            ``"auto"`` uses *auto_unit*.

        Returns
        -------
        str
        """
        unit = self.auto_unit if unit == "auto" else unit
        if unit == "norm":
            return f"[{self.norm_unit_label}]"
        return self.label_template.replace("${unit}$", unit)

    def latex(self, unit: str = "auto") -> str:
        """LaTeX-formatted label.

        Parameters
        ----------
        unit : str, optional
            Unit key.  ``"norm"`` uses *norm_unit_latex*. ``"auto"`` uses
            *auto_unit*.

        Returns
        -------
        str
        """
        unit = self.auto_unit if unit == "auto" else unit
        if unit == "norm":
            return rf"[{self.norm_unit_latex}]"
        if self.latex_template is not None:
            return self.latex_template.replace("${unit}$", unit)
        return self.label(unit)


# ---------------------------------------------------------------------------
# Pre-defined QuantityKind instances
# ---------------------------------------------------------------------------

LENGTH = QuantityKind(
    name="length",
    description="Spatial coordinate",
    norm_unit_label="c/omega_p",
    norm_unit_latex=r"c/\omega_p",
    scales={"norm": 1.0},
    auto_unit="um",
    label_template=r"x [${unit}$]",
    latex_template=r"$x\ [\mathrm{${unit}$}]$",
    axis_types=(0, 1),
)

TIME = QuantityKind(
    name="time",
    description="Time",
    norm_unit_label="1/omega_p",
    norm_unit_latex=r"1/\omega_p",
    scales={"norm": 1.0},
    auto_unit="ps",
    label_template=r"t [${unit}$]",
    latex_template=r"$t\ [\mathrm{${unit}$}]$",
)

VELOCITY = QuantityKind(
    name="velocity",
    description="Velocity",
    norm_unit_label="c",
    norm_unit_latex="c",
    scales={"norm": 1.0},
    auto_unit="c",
    label_template=r"v [${unit}$]",
    latex_template=r"$v\ [\mathrm{${unit}$}]$",
)

MOMENTUM = QuantityKind(
    name="momentum",
    description="Momentum",
    norm_unit_label="m_e * c",
    norm_unit_latex=r"m_e c",
    scales={"norm": 1.0},
    auto_unit="MeV/c",
    label_template=r"p [${unit}$]",
    latex_template=r"$p\ [\mathrm{${unit}$}]$",
)

ENERGY = QuantityKind(
    name="energy",
    description="Energy",
    norm_unit_label="m_e * c^2",
    norm_unit_latex=r"m_e c^2",
    scales={"norm": 1.0},
    auto_unit="MeV",
    label_template=r"E [${unit}$]",
    latex_template=r"$E\ [\mathrm{${unit}$}]$",
)

E_FIELD = QuantityKind(
    name="e_field",
    description="Electric field",
    norm_unit_label="m_e * c * omega_p / e",
    norm_unit_latex=r"m_e c \omega_p / e",
    scales={"norm": 1.0},
    auto_unit="GV/m",
    label_template=r"E [${unit}$]",
    latex_template=r"$E\ [\mathrm{${unit}$}]$",
)

B_FIELD = QuantityKind(
    name="b_field",
    description="Magnetic field",
    norm_unit_label="m_e * omega_p / e",
    norm_unit_latex=r"m_e \omega_p / e",
    scales={"norm": 1.0},
    auto_unit="T",
    label_template=r"B [${unit}$]",
    latex_template=r"$B\ [\mathrm{${unit}$}]$",
)

DENSITY = QuantityKind(
    name="density",
    description="Number density",
    norm_unit_label="n_0",
    norm_unit_latex="n_0",
    scales={"norm": 1.0},
    auto_unit="cm^-3",
    label_template=r"n [${unit}$]",
    latex_template=r"$n\ [\mathrm{${unit}$}]$",
)

FREQUENCY = QuantityKind(
    name="frequency",
    description="Frequency",
    norm_unit_label="omega_p",
    norm_unit_latex=r"\omega_p",
    scales={"norm": 1.0},
    auto_unit="THz",
    label_template=r"$\omega$ [${unit}$]",
    latex_template=r"$\omega\ [\mathrm{${unit}$}]$",
)

CHARGE = QuantityKind(
    name="charge",
    description="Charge",
    norm_unit_label="e",
    norm_unit_latex="e",
    scales={"norm": 1.0},
    auto_unit="nC",
    label_template=r"Q [${unit}$]",
    latex_template=r"$Q\ [\mathrm{${unit}$}]$",
)

CURRENT = QuantityKind(
    name="current",
    description="Current density",
    norm_unit_label="e * n_0 * c",
    norm_unit_latex=r"e n_0 c",
    scales={"norm": 1.0},
    auto_unit="A/m^2",
    label_template=r"j [${unit}$]",
    latex_template=r"$j\ [\mathrm{${unit}$}]$",
)

MASS = QuantityKind(
    name="mass",
    description="Mass",
    norm_unit_label="m_e",
    norm_unit_latex="m_e",
    scales={"norm": 1.0},
    auto_unit="kg",
    label_template=r"m [${unit}$]",
    latex_template=r"$m\ [\mathrm{${unit}$}]$",
)

WAVENUMBER = QuantityKind(
    name="wavenumber",
    description="k-vector magnitude",
    norm_unit_label="omega_p/c",
    norm_unit_latex=r"\omega_p/c",
    scales={"norm": 1.0},
    auto_unit="k0",
    label_template=r"$k\ [${unit}$]",
    latex_template=r"$k\ [\mathrm{${unit}$}]$",
)
