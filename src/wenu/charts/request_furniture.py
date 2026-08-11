"""Late chart-context realization for declarative request furniture."""

from __future__ import annotations

from dataclasses import replace

from .furniture import ChartFurnitureOptions
from .legend_metadata import chart_context_lines, observer_context_lines
from .legend_plan import ChartLegendPlan, LegendOptions


def resolve_request_furniture_context(furniture, chart, sky):
    """Resolve generic chart and observer metadata after construction."""
    if not isinstance(furniture, ChartFurnitureOptions):
        raise TypeError("furniture must be a ChartFurnitureOptions value.")
    context = furniture.context
    if context is None:
        return furniture
    legends = furniture.legends
    if legends is None:
        legends = LegendOptions(context=False)
    elif isinstance(legends, ChartLegendPlan):
        legends = LegendOptions(plan=legends, context=False)
    lines = (
        chart_context_lines(
            chart,
            sky,
            center=context.center,
            grid=context.grid,
        )
        + observer_context_lines(
            sky.observer,
            location=context.location,
            date=context.date,
            local_time=context.local_time,
            labels=context.labels,
        )
        + tuple(legends.context_lines)
    )
    return replace(
        furniture,
        legends=replace(legends, context=False, context_lines=lines),
        context=None,
    )
