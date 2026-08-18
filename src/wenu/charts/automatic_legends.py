"""High-level automatic composition of chart legends."""

from __future__ import annotations

from dataclasses import dataclass

from .legend_plan import (
    ChartLegendPlan,
    chart_type_name,
    default_chart_legend_plan,
)
from .rendered_legend_composition import draw_rendered_chart_legends


@dataclass(frozen=True)
class AutomaticChartLegends:
    """Resolved plan and artists produced by automatic composition."""

    chart_type: str
    plan: ChartLegendPlan
    legends: object

    @property
    def artists(self):
        return self.legends.artists


def draw_automatic_chart_legends(
    ax,
    chart,
    sky,
    chart_style,
    rendering_result,
    *,
    resolved_detail,
    plan: ChartLegendPlan | None = None,
    footprint_contains=None,
    stellar_legend_style=None,
    star_layer=None,
    grid=None,
    object_title=None,
    context_lines=None,
    include_objects=True,
    include_context=None,
    stellar_counts: bool = False,
    symbol_labels=None,
    stellar_title="Stars",
    stellar_reference_magnitude=None,
    stellar_reference_range=None,
    stellar_background=None,
    stellar_label_suffix="",
) -> AutomaticChartLegends:
    """Draw both chart legends with no duplicated scientific/style inputs."""
    inferred = (
        plan.chart_type if plan is not None else chart_type_name(chart)
    )
    resolved_plan = (
        default_chart_legend_plan(inferred)
        if plan is None
        else plan
    )
    options = dict(
        resolved_detail=resolved_detail,
        footprint_contains=footprint_contains,
        stellar_legend_style=stellar_legend_style,
        star_layer=star_layer,
        grid=grid,
        object_title=object_title,
        context_lines=context_lines,
        include_objects=include_objects,
        include_context=include_context,
        symbol_labels=symbol_labels,
        stellar_title=stellar_title,
        stellar_reference_magnitude=stellar_reference_magnitude,
        stellar_reference_range=stellar_reference_range,
        stellar_background=stellar_background,
        stellar_label_suffix=stellar_label_suffix,
    )
    if stellar_counts:
        options["stellar_counts"] = True
    legends = draw_rendered_chart_legends(
        ax,
        chart,
        sky,
        chart_style,
        resolved_plan,
        rendering_result,
        **options,
    )
    return AutomaticChartLegends(
        chart_type=inferred,
        plan=resolved_plan,
        legends=legends,
    )
