"""Resource estimation for OSIRIS simulation input decks."""

from osiris_toolkit.resource._estimator import (
    DiskEstimate,
    EstimationReport,
    MemoryEstimate,
    ResourceEstimator,
    RuntimeEstimate,
)
from osiris_toolkit.resource._params import ResourceParams
from osiris_toolkit.resource._report import format_report

__all__ = [
    "DiskEstimate",
    "EstimationReport",
    "MemoryEstimate",
    "ResourceEstimator",
    "ResourceParams",
    "RuntimeEstimate",
    "estimate_resources",
    "format_report",
]


def estimate_resources(
    deck: dict,
    peak_flops_per_core: float = 4.0e9,
    efficiency: float = 0.15,
    io_bandwidth_gbs: float = 1.0,
) -> EstimationReport:
    """Estimate computational resources for a parsed OSIRIS input deck.

    Parameters
    ----------
    deck : dict
        Output of ``parse_deck_file()`` or ``parse_deck_text()``.
    peak_flops_per_core : float
        Peak FLOP/s per CPU core. Default 4.0e9 (4 GFLOP/s).
    efficiency : float
        Sustained fraction of peak. Default 0.15 (15%).
    io_bandwidth_gbs : float
        Sustained I/O write bandwidth in GB/s. Default 1.0.

    Returns
    -------
    EstimationReport
        Full resource estimate.
    """
    params = ResourceParams.from_deck(deck)
    estimator = ResourceEstimator(
        peak_flops_per_core=peak_flops_per_core,
        efficiency=efficiency,
        io_bandwidth_gbs=io_bandwidth_gbs,
    )
    return estimator.estimate(params)
