"""Quantified data wrappers — GridData + UnitSystem facade for vis/analysis."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from osiris_toolkit._models import GridData
from osiris_toolkit.compute.fft import compute_k_space
from osiris_toolkit.exceptions import UnitConversionError
from osiris_toolkit.units._quantity import QuantityKind
from osiris_toolkit.units.converter import UnitSystem


@dataclass
class _QuantityView:
    """A data array bound to a specific QuantityKind."""

    data: np.ndarray
    quantity: QuantityKind

    def to(self, unit: str = "auto") -> np.ndarray:
        return self.quantity.to(self.data, unit)

    def label(self, unit: str = "auto") -> str:
        return self.quantity.label(unit)

    def latex(self, unit: str = "auto") -> str:
        return self.quantity.latex(unit)


@dataclass
class _AxisView:
    """A single axis of a GridData, bound to a QuantityKind via UnitSystem."""

    grid: GridData
    axis_index: int
    system: UnitSystem | None
    force_quantity: str | None = None

    def to(self, unit: str = "auto") -> tuple[float, float]:
        """Return (min, max) in target units."""
        axis = self.grid.axes[self.axis_index]
        if self.system is None:
            if unit in ("auto", "norm"):
                return (axis.min, axis.max)
            raise UnitConversionError(
                f"No UnitSystem available to convert to {unit!r}. "
                f"Provide a deck or use 'norm'."
            )
        q = self._get_quantity()
        return (q.to(axis.min, unit), q.to(axis.max, unit))

    def label(self, unit: str = "auto") -> str:
        if self.system is None or (unit in ("auto", "norm") and self.system is None):
            axis = self.grid.axes[self.axis_index]
            return f"x{self.axis_index + 1} [{axis.units or 'c/omega_p'}]"
        q = self._get_quantity()
        return q.label(unit)

    def latex(self, unit: str = "auto") -> str:
        if self.system is None:
            return self.label(unit)
        q = self._get_quantity()
        return q.latex(unit)

    def _get_quantity(self) -> QuantityKind:
        if self.force_quantity is not None:
            return self.system[self.force_quantity]  # type: ignore[index]
        return self.system.length  # type: ignore[union-attr]


@dataclass
class QuantifiedGrid:
    """A GridData with attached UnitSystem for automatic unit conversion.

    This is the primary interface for vis/analysis modules.  It wraps a
    bare GridData and provides:

    - Automatic quantity inference for spatial axes (:meth:`to`, :meth:`x`, :meth:`y`)
    - Explicit quantity override for values (:meth:`as_quantity`)
    - Unit-aware axis labels with LaTeX support

    Parameters
    ----------
    grid : GridData
        The raw simulation data in normalized units.
    system : UnitSystem or None
        The unit system for conversion.  If None, only ``"norm"`` unit is available.
    """

    grid: GridData
    system: UnitSystem | None

    def to(self, unit: str = "auto") -> np.ndarray:
        """Convert grid data, auto-inferring quantity from *unit*.

        For field data (e.g. e1, b2) use :meth:`as_quantity` to specify
        ``e_field`` or ``b_field`` explicitly.  This method is primarily
        for spatial coordinate conversion.
        """
        if self.system is None:
            if unit in ("auto", "norm"):
                return self.grid.data
            raise UnitConversionError(
                f"No UnitSystem available to convert to {unit!r}. Use 'norm'."
            )
        q = self._infer_quantity(unit)
        return q.to(self.grid.data, unit)

    def norm(self) -> np.ndarray:
        """Return raw normalized data (always works, even without UnitSystem)."""
        return self.grid.data

    def as_quantity(self, name: str) -> _QuantityView:
        """Explicitly select a quantity for value/colorbar conversion.

        Parameters
        ----------
        name : str
            Quantity name, e.g. ``"e_field"``, ``"density"``.

        Returns
        -------
        _QuantityView
        """
        if self.system is None:
            raise UnitConversionError(
                f"No UnitSystem available; cannot resolve quantity {name!r}."
            )
        return _QuantityView(self.grid.data, self.system[name])

    @property
    def x(self) -> _AxisView:
        """X-axis (auto-inferred as 'length')."""
        return _AxisView(self.grid, 0, self.system)

    @property
    def y(self) -> _AxisView:
        """Y-axis (auto-inferred as 'length')."""
        if len(self.grid.axes) < 2:
            raise UnitConversionError("Grid has fewer than 2 axes; no y-axis available.")
        return _AxisView(self.grid, 1, self.system)

    @property
    def time_axis(self) -> _AxisView:
        """Time coordinate (uses the grid's scalar ``time`` field)."""
        return _AxisView(self.grid, 0, self.system, force_quantity="time")

    def _infer_quantity(self, unit: str) -> QuantityKind:
        """Find the unique QuantityKind where *unit* is valid."""
        candidates = [q for q in self.system.quantities if unit in q.scales]  # type: ignore[union-attr]
        if len(candidates) == 0:
            raise UnitConversionError(
                f"No quantity supports unit {unit!r}."
            )
        if len(candidates) == 1:
            return candidates[0]
        names = [c.name for c in candidates]
        raise UnitConversionError(
            f"Unit {unit!r} is ambiguous among {names}. "
            f"Use .as_quantity(name).to(unit) to disambiguate."
        )


@dataclass
class QuantifiedSpectrum:
    """FFT spectrum result bound to a UnitSystem for k-space unit conversion.

    Parameters
    ----------
    kx_norm : ndarray
        Raw k_x from ``compute_k_space`` in normalized angular wavenumber.
    ky_norm : ndarray
        Raw k_y from ``compute_k_space``.
    spectrum : ndarray
        |FFT| amplitude.
    quantity : str
        Field component name (e.g. ``"e1"``).
    iteration : int
    time : float
    system : UnitSystem
    """

    kx_norm: np.ndarray
    ky_norm: np.ndarray
    spectrum: np.ndarray
    quantity: str
    iteration: int
    time: float
    system: UnitSystem

    @property
    def kx(self) -> _QuantityView:
        return _QuantityView(self.kx_norm, self.system.wavenumber)

    @property
    def ky(self) -> _QuantityView:
        return _QuantityView(self.ky_norm, self.system.wavenumber)

    @classmethod
    def from_field(cls, grid: GridData, system: UnitSystem) -> QuantifiedSpectrum:
        """Compute FFT spectrum from a field GridData.

        Parameters
        ----------
        grid : GridData
            2-D field data in normalized units.
        system : UnitSystem
            Must be provided (k-space requires unit context).

        Returns
        -------
        QuantifiedSpectrum
        """
        if grid.data.ndim < 2:
            raise UnitConversionError("K-space requires 2-D field data.")
        nx, ny = grid.data.shape
        dx = (grid.axes[0].max - grid.axes[0].min) / nx
        dy = (grid.axes[1].max - grid.axes[1].min) / ny
        kx, ky, spectrum = compute_k_space(grid.data, dx, dy)
        return cls(
            kx_norm=kx, ky_norm=ky, spectrum=spectrum,
            quantity=grid.label, iteration=grid.iteration,
            time=grid.time, system=system,
        )
