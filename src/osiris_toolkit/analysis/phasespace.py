"""Phase-space analysis — particle phase-space diagnostics."""

from __future__ import annotations

from ._protocol import DiagnosticAnalyzer


class PhasespaceAnalyzer(DiagnosticAnalyzer):
    """Phase-space diagnostic analysis (placeholder).

    Full implementation pending phasespace diagnostic data model support.
    """

    diagnostic_kind = "PHASESPACE"

    def list_available(self) -> list[str]:
        return list(self._sim._phasespace.keys())
