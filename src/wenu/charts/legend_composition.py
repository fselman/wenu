"""Coordinate independently rendered object and stellar legends."""

from __future__ import annotations

from dataclasses import dataclass, replace

from matplotlib.legend import Legend

from .legend import draw_chart_legend
from .legend_plan import ChartLegendPlan, LegendPlacement
from .magnitude_legend_style import (
    StellarMagnitudeLegendStyle,
    draw_styled_stellar_magnitude_legend,
)
from .magnitude_legend_workflow import StellarMagnitudeLegendResult


@dataclass(frozen=True)
class ComposedChartLegends:
    """Artists produced by one dual-legend composition."""

    plan: ChartLegendPlan
    objects: Legend | None
    stars: StellarMagnitudeLegendResult | None

    @property
    def artists(self) -> tuple[Legend, ...]:
        artists = []
        if self.objects is not None:
            artists.append(self.objects)
        if self.stars is not None and self.stars.artist is not None:
            artists.append(self.stars.artist)
        return tuple(artists)


def _outside_anchor(location: str) -> tuple[float, float]:
    horizontal = 0.0 if "left" in location else 1.0
    vertical = 0.0 if "lower" in location else 1.0
    offset = -0.02 if horizontal == 0.0 else 1.02
    return (offset, vertical)


def _outside_location(location: str) -> str:
    vertical = "lower" if "lower" in location else "upper"
    horizontal = "right" if "left" in location else "left"
    return f"{vertical} {horizontal}"


def apply_legend_placement(
    legend: Legend | None,
    placement: LegendPlacement,
) -> Legend | None:
    """Apply a resolved placement to an already-created legend."""
    if legend is None:
        return None
    location = (
        _outside_location(placement.location)
        if placement.outside
        else placement.location
    )
    legend.set_loc(location)
    anchor = placement.anchor
    if anchor is None and placement.outside:
        anchor = _outside_anchor(placement.location)
    if anchor is not None:
        legend.set_bbox_to_anchor(anchor)
    return legend


def draw_planned_chart_legends(
    ax,
    chart,
    sky,
    chart_style,
    plan: ChartLegendPlan,
    *,
    star_spherical,
    star_projected,
    viewport,
    effective_limit: float,
    star_area_scale: float = 1.0,
    star_color: str = "black",
    star_alpha: float = 1.0,
    stellar_magnitude_sizing=None,
    footprint_contains=None,
    stellar_legend_style: StellarMagnitudeLegendStyle | None = None,
    grid=None,
    object_title=None,
    context_lines=None,
    include_objects=True,
    include_context=None,
    resolved_detail=None,
    stellar_counts: bool = False,
    symbol_labels=None,
    stellar_title="Stars",
) -> ComposedChartLegends:
    """Draw the planned object and stellar legends for a chart."""
    object_artist = None
    context_enabled = (
        plan.objects.enabled
        if include_context is None
        else bool(include_context)
    )
    if plan.objects.enabled or context_enabled:
        legend_kwargs = dict(
            grid=grid,
            title=object_title,
            context_lines=context_lines,
        )
        if symbol_labels is not None:
            legend_kwargs["symbol_labels"] = symbol_labels
        if not include_objects:
            legend_kwargs["include_objects"] = False
        if include_context is not None:
            legend_kwargs["include_context"] = context_enabled
        if resolved_detail is not None:
            legend_kwargs["resolved_detail"] = resolved_detail
        object_artist = draw_chart_legend(
            ax,
            chart,
            sky,
            chart_style,
            **legend_kwargs,
        )
        apply_legend_placement(object_artist, plan.objects)

    stars_result = None
    if plan.stars.enabled:
        chart_legend_style = getattr(chart_style, "legend", None)
        base_style = (
            (
                StellarMagnitudeLegendStyle()
                if chart_legend_style is None
                else StellarMagnitudeLegendStyle(
                    font_size=chart_legend_style.fontsize,
                    title_font_size=chart_legend_style.title_fontsize,
                    text_color=chart_legend_style.text_color,
                    facecolor=chart_legend_style.facecolor,
                    edgecolor=chart_legend_style.edgecolor,
                )
            )
            if stellar_legend_style is None
            else stellar_legend_style
        )
        resolved_style = replace(
            base_style,
            enabled=True,
            location=plan.stars.location,
            title=str(stellar_title),
        )
        star_options = dict(
            effective_limit=effective_limit,
            area_scale=star_area_scale,
            color=star_color,
            alpha=star_alpha,
            footprint_contains=footprint_contains,
            legend_style=resolved_style,
        )
        if stellar_magnitude_sizing is not None:
            star_options["magnitude_sizing"] = stellar_magnitude_sizing
        if stellar_counts:
            star_options["include_counts"] = True
        stars_result = draw_styled_stellar_magnitude_legend(
            ax,
            star_spherical,
            star_projected,
            viewport,
            **star_options,
        )
        apply_legend_placement(
            stars_result.artist,
            plan.stars,
        )

    return ComposedChartLegends(
        plan=plan,
        objects=object_artist,
        stars=stars_result,
    )
