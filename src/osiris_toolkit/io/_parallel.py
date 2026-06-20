"""Parallel batch I/O for ZDF files.

Provides ``read_many`` for concurrently reading multiple ZDF files
using a thread pool. Since each ``read_*`` function opens its own
file handle and has no shared state, parallel reads are inherently
safe — no locks or synchronization needed.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


def read_many(
    paths: list[str | Path],
    reader_fn: Callable[[str], T],
    max_workers: int = 4,
    on_error: str = "raise",
) -> list[T | Exception]:
    """Read multiple ZDF files in parallel, preserving input order.

    Parameters
    ----------
    paths : list of str or Path
        Paths to ZDF files.
    reader_fn : callable
        A stateless reader function (e.g. ``read_grid``, ``read_particles``).
        Must accept a single ``str`` path argument.
    max_workers : int
        Maximum number of thread workers.
    on_error : str
        ``"raise"`` — re-raise the first exception encountered.
        ``"return"`` — store exceptions in the result list.

    Returns
    -------
    list
        Results in the same order as ``paths``. If ``on_error="return"``,
        failed entries contain the exception object.

    Examples
    --------
    >>> from osiris_toolkit.io._reader import read_grid
    >>> from osiris_toolkit.io._parallel import read_many
    >>> paths = ["e1-000000.zdf", "e1-000010.zdf", "e1-000020.zdf"]
    >>> results = read_many(paths, read_grid, max_workers=4)
    >>> for (data, grid_info, iteration) in results:
    ...     print(iteration.n, data.shape)
    """
    results: list[Any] = [None] * len(paths)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {executor.submit(reader_fn, str(p)): i for i, p in enumerate(paths)}

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                if on_error == "raise":
                    # Cancel remaining futures and raise
                    for f in future_to_idx:
                        f.cancel()
                    raise
                results[idx] = exc

    return results


def read_many_map(
    paths: list[str | Path],
    reader_fn: Callable[[str], T],
    post_fn: Callable[[T], Any] | None = None,
    max_workers: int = 4,
) -> list[Any]:
    """Read in parallel, optionally applying a post-processing function.

    Parameters
    ----------
    paths : list of str or Path
    reader_fn : callable
    post_fn : callable or None
        Applied to each result after reading.
    max_workers : int

    Returns
    -------
    list
    """
    raw = read_many(paths, reader_fn, max_workers=max_workers, on_error="raise")
    if post_fn is not None:
        return [post_fn(r) for r in raw]  # type: ignore[arg-type]
    return raw
