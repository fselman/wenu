"""Style configuration for stellar magnitude–size legends."""

from __future__ import annotations

from dataclasses import dataclass

from .magnitude_legend_workflow import (
    StellarMagnitudeLegendResult,
    draw_visible_stellar_magnitude_legend,
)


@dataclass(frozen=True)
class StellarMagnitudeLegendStyle:
    """Independent appearance and placement of a stellar scale legend."""

    enabled: bool = True
    location: str = "lower right"
    title: str = "Stars"
    frame_on: bool = True
    font_size: float | None = None
    title_font_size: float | None = None
    marker: str = "o"
    marker_edge_color: str | None = None
    marker_edge_width: float = 0.0
    label_spacing: float = 0.5
    handle_text_pad: float = 0.8
    border_pad: float = 0.5
    zorder: float = 1000.0
    text_color: str | None = None
    facecolor: str | None = None
    edgecolor: str | None = None

    def drawing_options(self) -> dict:
        """Return keyword arguments accepted by the workflow renderer."""
        return {
            "location": self.location,
            "title": self.title,
            "frame_on": self.frame_on,
            "font_size": self.font_size,
            "title_font_size": self.title_font_size,
            "marker": self.marker,
            "marker_edge_color": self.marker_edge_color,
            "marker_edge_width": self.marker_edge_width,
            "label_spacing": self.label_spacing,
            "handle_text_pad": self.handle_text_pad,
            "border_pad": self.border_pad,
            "zorder": self.zorder,
            "text_color": self.text_color,
            "facecolor": self.facecolor,
            "edgecolor": self.edgecolor,
        }


def draw_styled_stellar_magnitude_legend(
    ax,
    spherical,
    projected,
    viewport,
    *,
    effective_limit: float,
    area_scale: float = 1.0,
    color: str = "black",
    alpha: float = 1.0,
    magnitude_sizing=None,
    footprint_contains=None,
    include_counts: bool = False,
    legend_style: StellarMagnitudeLegendStyle | None = None,
) -> StellarMagnitudeLegendResult:
    """Draw a visible-star legend using independent style settings."""
    style = (
        StellarMagnitudeLegendStyle()
        if legend_style is None
        else legend_style
    )
    if not style.enabled:
        from .magnitude_legend import visible_star_statistics

        statistics = visible_star_statistics(
            spherical,
            projected,
            viewport,
            effective_limit=effective_limit,
            footprint_contains=footprint_contains,
        )
        return StellarMagnitudeLegendResult(
            statistics=statistics,
            scale=None,
            artist=None,
        )

    options = dict(
        effective_limit=effective_limit,
        area_scale=area_scale,
        color=color,
        alpha=alpha,
        footprint_contains=footprint_contains,
        **style.drawing_options()
    )
    if magnitude_sizing is not None:
        options["magnitude_sizing"] = magnitude_sizing
    if include_counts:
        options["include_counts"] = True
    return draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        viewport,
        **options,
    )
