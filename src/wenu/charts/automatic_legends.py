"""High-level automatic composition of chart legends."""

from __future__ import annotations

from dataclasses import dataclass

from .legend_plan import ChartLegendPlan, default_chart_legend_plan
from .rendered_legend_composition import draw_rendered_chart_legends


_CLASS_CHART_TYPES = {
    "RegionalChart": "regional",
    "FullSkyChart": "planisphere",
    "CircumpolarChart": "circumpolar",
    "BinocularChart": "binocular",
}


def chart_type_name(chart) -> str:
    """Return the semantic chart type used by layout policies.

    The mapping deliberately depends only on the public chart class name,
    keeping this small composition adapter free of chart-implementation
    imports and avoiding circular dependencies.
    """
    explicit = getattr(chart, "chart_type", None)
    if explicit is not None:
        normalized = str(explicit).strip().lower()
        if normalized in set(_CLASS_CHART_TYPES.values()):
            return normalized
    name = type(chart).__name__
    try:
        return _CLASS_CHART_TYPES[name]
    except KeyError as error:
        raise ValueError(
            f"Cannot infer a legend plan for chart class {name!r}; "
            "pass plan explicitly."
        ) from error


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
    legends = draw_rendered_chart_legends(
        ax,
        chart,
        sky,
        chart_style,
        resolved_plan,
        rendering_result,
        resolved_detail=resolved_detail,
        footprint_contains=footprint_contains,
        stellar_legend_style=stellar_legend_style,
        star_layer=star_layer,
        grid=grid,
        object_title=object_title,
        context_lines=context_lines,
    )
    return AutomaticChartLegends(
        chart_type=inferred,
        plan=resolved_plan,
        legends=legends,
    )
