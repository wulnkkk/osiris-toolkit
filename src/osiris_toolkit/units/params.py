"""Simulation physical parameters extracted from a parsed input deck.

Provides a clean bridge between the deck parser and the unit converter,
replacing the previous ad-hoc regex-based omega_p0 extraction.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SimulationParams:
    """Physical parameters needed for unit conversion and analysis.

    Extracted from the ``simulation`` section of a parsed OSIRIS input deck.

    Attributes
    ----------
    omega_p0 : float
        Reference plasma frequency in rad/s. This is the only required
        parameter for unit conversion.
    n0 : float | None
        Reference density in normalized units (optional).
    gamma : float | None
        Relativistic factor of the reference frame (optional).

    Examples
    --------
    >>> from osiris_toolkit.deck import parse_deck_file
    >>> deck = parse_deck_file("input/simulation.in")
    >>> params = SimulationParams.from_deck(deck)
    >>> converter = UnitConverter(params)
    """

    omega_p0: float
    n0: float | None = None
    gamma: float | None = None

    @classmethod
    def from_deck(cls, deck: dict) -> "SimulationParams":
        """Extract physical parameters from a parsed deck dictionary.

        Parameters
        ----------
        deck : dict
            Output of ``parse_deck_text()`` or ``parse_deck_file()``,
            containing a ``"sections"`` key with a list of section dicts.

        Returns
        -------
        SimulationParams
            Extracted parameters. Raises ValueError if ``omega_p0``
            is not found.

        Raises
        ------
        ValueError
            If the ``simulation`` section is missing or does not contain
            ``omega_p0``.
        """
        sim_section = None
        for section in deck.get("sections", []):
            if section.get("name") == "simulation":
                sim_section = section
                break

        if sim_section is None:
            raise ValueError(
                "Missing 'simulation' section in deck. "
                "Cannot determine omega_p0 for unit conversion."
            )

        params = sim_section.get("params", {})
        omega_p0 = params.get("omega_p0")
        if omega_p0 is None:
            raise ValueError(
                "Parameter 'omega_p0' not found in 'simulation' section. "
                "This is required for unit conversion."
            )

        if isinstance(omega_p0, (list, dict)):
            omega_p0 = float(omega_p0[0] if isinstance(omega_p0, list) else omega_p0["value"])
        omega_p0 = float(omega_p0)

        if omega_p0 <= 0:
            raise ValueError(f"omega_p0 must be > 0, got {omega_p0}")

        n0 = params.get("n0")
        if n0 is not None:
            if isinstance(n0, list):
                n0 = n0[0]
            elif isinstance(n0, dict):
                n0 = n0.get("value", n0)
            n0 = float(n0)

        gamma = params.get("gamma")
        if gamma is not None:
            if isinstance(gamma, list):
                gamma = gamma[0]
            elif isinstance(gamma, dict):
                gamma = gamma.get("value", gamma)
            gamma = float(gamma)

        return cls(omega_p0=omega_p0, n0=n0, gamma=gamma)

    @classmethod
    def from_omega_p0(cls, omega_p0: float) -> "SimulationParams":
        """Create params directly from a known omega_p0 value."""
        return cls(omega_p0=omega_p0)
