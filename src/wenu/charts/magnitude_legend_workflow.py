"""Chart-level workflow for stellar magnitude–size legends."""

from __future__ import annotations

from dataclasses import dataclass

from matplotlib.legend import Legend

from .magnitude_legend import (
    StellarMagnitudeScale,
    VisibleStarStatistics,
    stellar_magnitude_scale,
    visible_star_statistics,
)
from .magnitude_legend_matplotlib import (
    draw_stellar_magnitude_legend,
)


@dataclass(frozen=True)
class StellarMagnitudeLegendResult:
    """Products of the chart magnitude-legend workflow."""

    statistics: VisibleStarStatistics
    scale: StellarMagnitudeScale | None
    artist: Legend | None

    @property
    def drawn(self) -> bool:
        return self.artist is not None


def draw_visible_stellar_magnitude_legend(
    ax,
    spherical,
    projected,
    viewport,
    *,
    effective_limit: float,
    area_scale: float = 1.0,
    color: str = "black",
    alpha: float = 1.0,
    title: str = "Stars",
    footprint_contains=None,
    location: str = "lower right",
    frame_on: bool = True,
    font_size: float | None = None,
    title_font_size: float | None = None,
    marker: str = "o",
    marker_edge_color: str | None = None,
    marker_edge_width: float = 0.0,
    label_spacing: float = 0.5,
    handle_text_pad: float = 0.8,
    border_pad: float = 0.5,
    zorder: float = 1000.0,
) -> StellarMagnitudeLegendResult:
    """Calculate and draw the legend for stars visible in a chart.

    No legend is drawn when the chart contains no visible stars or when
    the visible magnitude interval contains no integer magnitude.
    """
    statistics = visible_star_statistics(
        spherical,
        projected,
        viewport,
        effective_limit=effective_limit,
        footprint_contains=footprint_contains,
    )
    if not statistics.has_visible_stars:
        return StellarMagnitudeLegendResult(
            statistics=statistics,
            scale=None,
            artist=None,
        )

    scale = stellar_magnitude_scale(
        statistics.brightest_magnitude,
        statistics.faintest_magnitude,
        area_scale=area_scale,
        color=color,
        alpha=alpha,
        title=title,
    )
    if not scale.entries:
        return StellarMagnitudeLegendResult(
            statistics=statistics,
            scale=scale,
            artist=None,
        )

    artist = draw_stellar_magnitude_legend(
        ax,
        scale,
        location=location,
        frame_on=frame_on,
        font_size=font_size,
        title_font_size=title_font_size,
        marker=marker,
        marker_edge_color=marker_edge_color,
        marker_edge_width=marker_edge_width,
        label_spacing=label_spacing,
        handle_text_pad=handle_text_pad,
        border_pad=border_pad,
        zorder=zorder,
    )
    return StellarMagnitudeLegendResult(
        statistics=statistics,
        scale=scale,
        artist=artist,
    )
