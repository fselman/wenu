# src/wenu/visibility.py
"""
Visibility utilities.

This module determines which samples of a celestial object are visible
and partitions them into contiguous visible segments. It contains no
projection or rendering logic.
"""

from __future__ import annotations

import numpy as np


def visibility_mask(
    alt_deg,
    *,
    min_altitude: float = 0.0,
) -> np.ndarray:
    """
    Return a Boolean mask identifying samples above an altitude limit.

    Parameters
    ----------
    alt_deg
        Altitude samples in degrees.
    min_altitude
        Minimum visible altitude in degrees. Samples exactly at the
        limit are considered not visible.

    Returns
    -------
    numpy.ndarray
        Boolean array with the same shape as ``alt_deg``.
    """
    alt_deg = np.asarray(alt_deg, dtype=float)

    return alt_deg > float(min_altitude)


def split_visible_segments(
    visible,
    *,
    minimum_length: int = 2,
) -> list[np.ndarray]:
    """
    Split a Boolean visibility mask into contiguous index arrays.

    Parameters
    ----------
    visible
        One-dimensional Boolean visibility mask.
    minimum_length
        Minimum number of samples required for a returned segment.

    Returns
    -------
    list of numpy.ndarray
        Contiguous arrays of indices for visible samples.
    """
    visible = np.asarray(visible, dtype=bool)

    if visible.ndim != 1:
        raise ValueError(
            "visible must be a one-dimensional array."
        )

    if minimum_length < 1:
        raise ValueError(
            "minimum_length must be at least 1."
        )

    indices = np.flatnonzero(visible)

    if indices.size == 0:
        return []

    breaks = np.flatnonzero(
        np.diff(indices) > 1
    ) + 1

    segments = np.split(indices, breaks)

    return [
        segment
        for segment in segments
        if segment.size >= minimum_length
    ]


def visible_segments(
    alt_deg,
    *,
    min_altitude: float = 0.0,
    minimum_length: int = 2,
) -> list[np.ndarray]:
    """
    Return contiguous visible sample indices.

    This is a convenience wrapper combining
    ``visibility_mask()`` and ``split_visible_segments()``.
    """
    return split_visible_segments(
        visibility_mask(
            alt_deg,
            min_altitude=min_altitude,
        ),
        minimum_length=minimum_length,
    )



