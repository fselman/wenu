"""Backend-independent stellar magnitude-scale descriptions."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from wenu.rendering.preparation import (
    configured_magnitude_sizes,
    magnitude_sizes,
)


@dataclass(frozen=True)
class StellarMagnitudeEntry:
    """One integer magnitude and its chart scatter area in points squared."""

    magnitude: int
    area: float
    cumulative_count: int | None = None


@dataclass(frozen=True)
class StellarMagnitudeScale:
    """Resolved entries and appearance for a stellar magnitude legend."""

    entries: tuple[StellarMagnitudeEntry, ...]
    color: str
    alpha: float = 1.0
    title: str = "Stars"

    @property
    def magnitudes(self):
        return tuple(entry.magnitude for entry in self.entries)

    @property
    def areas(self):
        return tuple(entry.area for entry in self.entries)


@dataclass(frozen=True)
class VisibleStarStatistics:
    """Magnitude statistics for stars inside the resolved chart footprint."""

    brightest_magnitude: float | None
    faintest_magnitude: float | None
    effective_limit: float
    visible_count: int

    @property
    def has_visible_stars(self):
        return self.visible_count > 0


def integer_magnitude_range(
    brightest_magnitude,
    faintest_magnitude,
):
    """Return inclusive integer magnitudes within the supplied limits."""
    brightest = float(brightest_magnitude)
    faintest = float(faintest_magnitude)
    if not math.isfinite(brightest) or not math.isfinite(faintest):
        raise ValueError("Magnitude limits must be finite.")
    if brightest > faintest:
        raise ValueError(
            "brightest_magnitude must not exceed faintest_magnitude."
        )
    first = math.ceil(brightest)
    last = math.floor(faintest)
    if first > last:
        return ()
    return tuple(range(first, last + 1))


def stellar_magnitude_scale(
    brightest_magnitude,
    faintest_magnitude,
    *,
    area_scale=1.0,
    color="white",
    alpha=1.0,
    title="Stars",
    cumulative_counts=None,
    magnitude_sizing=None,
    limiting_magnitude=None,
):
    """Resolve an integer magnitude scale using the chart star-size law."""
    scale = float(area_scale)
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("area_scale must be finite and positive.")
    resolved_alpha = float(alpha)
    if not math.isfinite(resolved_alpha):
        raise ValueError("alpha must be finite.")

    magnitudes = integer_magnitude_range(
        brightest_magnitude,
        faintest_magnitude,
    )
    if not magnitudes:
        entries = ()
    else:
        areas = (
            magnitude_sizes(magnitudes)
            if magnitude_sizing is None
            else configured_magnitude_sizes(
                magnitudes,
                magnitude_sizing,
                limiting_magnitude=limiting_magnitude,
            )
        ) * scale
        counts = (
            (None,) * len(magnitudes)
            if cumulative_counts is None
            else tuple(int(value) for value in cumulative_counts)
        )
        if len(counts) != len(magnitudes):
            raise ValueError(
                "cumulative_counts must match the magnitude entries."
            )
        if any(value is not None and value < 0 for value in counts):
            raise ValueError("cumulative_counts cannot be negative.")
        entries = tuple(
            StellarMagnitudeEntry(
                magnitude=magnitude,
                area=float(area),
                cumulative_count=count,
            )
            for magnitude, area, count in zip(magnitudes, areas, counts)
        )
    return StellarMagnitudeScale(
        entries=entries,
        color=str(color),
        alpha=resolved_alpha,
        title=str(title),
    )


def cumulative_visible_star_counts(
    spherical,
    projected,
    viewport,
    magnitudes,
    *,
    effective_limit,
    footprint_contains=None,
):
    """Count rendered stars at or brighter than each legend magnitude."""
    mask = visible_star_mask(
        spherical,
        projected,
        viewport,
        effective_limit=effective_limit,
        footprint_contains=footprint_contains,
    )
    rendered = np.asarray(
        spherical.metadata["magnitude"], dtype=float
    )[mask]
    return tuple(
        int(np.count_nonzero(rendered <= float(magnitude)))
        for magnitude in magnitudes
    )


def visible_star_mask(
    spherical,
    projected,
    viewport,
    *,
    effective_limit,
    footprint_contains=None,
):
    """Return stars inside all resolved geometric and magnitude limits."""
    magnitudes = np.asarray(
        spherical.metadata["magnitude"],
        dtype=float,
    )
    x = np.asarray(projected.x, dtype=float)
    y = np.asarray(projected.y, dtype=float)
    if x.shape != y.shape or x.shape != magnitudes.shape:
        raise ValueError(
            "Projected coordinates and magnitudes must have equal shapes."
        )
    limit = float(effective_limit)
    if not math.isfinite(limit):
        raise ValueError("effective_limit must be finite.")

    mask = (
        np.isfinite(x)
        & np.isfinite(y)
        & np.isfinite(magnitudes)
        & (x >= float(viewport.x_min))
        & (x <= float(viewport.x_max))
        & (y >= float(viewport.y_min))
        & (y <= float(viewport.y_max))
        & (magnitudes <= limit)
    )
    if footprint_contains is not None:
        footprint = np.asarray(
            footprint_contains(x, y),
            dtype=bool,
        )
        if footprint.shape != mask.shape:
            raise ValueError(
                "footprint_contains must return one value per star."
            )
        mask &= footprint
    return mask


def visible_star_statistics(
    spherical,
    projected,
    viewport,
    *,
    effective_limit,
    footprint_contains=None,
):
    """Summarize stellar magnitudes inside the resolved chart footprint."""
    mask = visible_star_mask(
        spherical,
        projected,
        viewport,
        effective_limit=effective_limit,
        footprint_contains=footprint_contains,
    )
    magnitudes = np.asarray(
        spherical.metadata["magnitude"],
        dtype=float,
    )
    visible = magnitudes[mask]
    limit = float(effective_limit)
    if visible.size == 0:
        return VisibleStarStatistics(
            brightest_magnitude=None,
            faintest_magnitude=None,
            effective_limit=limit,
            visible_count=0,
        )
    return VisibleStarStatistics(
        brightest_magnitude=float(np.min(visible)),
        faintest_magnitude=float(np.max(visible)),
        effective_limit=limit,
        visible_count=int(visible.size),
    )
