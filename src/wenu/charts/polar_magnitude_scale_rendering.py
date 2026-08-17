"""Shared Matplotlib realization of polar-only magnitude-scale furniture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.polar_magnitude_scale import (
    PolarMagnitudeScale,
    PolarMagnitudeScalePlacement,
)
from wenu.rendering.symbols import DEFAULT_SYMBOLS


@dataclass(frozen=True)
class PolarMagnitudeScaleRendering:
    """Inspectable artists for one physical polar magnitude scale."""

    title: object
    markers: tuple[object, ...]
    labels: tuple[object, ...]

    @property
    def artists(self):
        return (self.title, *self.markers, *self.labels)


def draw_polar_magnitude_scale(
    ax,
    scale,
    placement,
    *,
    color,
    zorder=110,
):
    """Draw one resolved scale without recalculating stellar marker areas."""
    if not isinstance(scale, PolarMagnitudeScale):
        raise TypeError("scale must be a PolarMagnitudeScale value.")
    if not isinstance(placement, PolarMagnitudeScalePlacement):
        raise TypeError("placement must be a PolarMagnitudeScalePlacement value.")
    title = ax.text(
        *placement.title_position_mm,
        scale.title,
        color=color,
        fontsize=5.2,
        fontweight="bold",
        ha="center",
        va="center",
        zorder=zorder,
    )
    markers = []
    labels = []
    for entries, center in (
        (scale.bright_entries, placement.bright_center_mm),
        (scale.ordinary_entries, placement.ordinary_center_mm),
    ):
        positions = _centered_positions(
            center,
            len(entries),
            placement.entry_spacing_mm,
        )
        for entry, position in zip(entries, positions, strict=True):
            marker = (
                DEFAULT_SYMBOLS.filled_five_point_star
                if entry.symbol == "five_point"
                else "o"
            )
            markers.append(
                ax.plot(
                    *position,
                    marker=marker,
                    markersize=np.sqrt(entry.marker_area_points2),
                    markerfacecolor=color,
                    markeredgecolor="none",
                    linestyle="none",
                    zorder=zorder,
                )[0]
            )
            labels.append(
                ax.text(
                    position[0],
                    position[1] + placement.label_offset_mm,
                    entry.label,
                    color=color,
                    fontsize=4.2,
                    ha="center",
                    va="top",
                    zorder=zorder,
                )
            )
    return PolarMagnitudeScaleRendering(
        title=title,
        markers=tuple(markers),
        labels=tuple(labels),
    )


def _centered_positions(center, count, spacing):
    start = float(center[0]) - (count - 1) * float(spacing) / 2.0
    return tuple(
        (start + index * float(spacing), float(center[1]))
        for index in range(count)
    )
