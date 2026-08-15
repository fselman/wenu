"""Late chart-context realization for declarative request furniture."""

from __future__ import annotations

from dataclasses import replace

from astropy import units as u

from .furniture import ChartFurnitureOptions
from .legend_metadata import chart_context_lines, observer_context_lines
from .legend_plan import ChartLegendPlan, LegendOptions


def binocular_product_title(target, field_diameter_deg, *, display_name=None):
    """Return one publication title with target, center, and field size."""
    coordinate = target.coordinate
    ra = coordinate.ra.to_string(unit=u.hour, sep="hms", precision=0)
    dec = coordinate.dec.to_string(
        unit=u.deg, sep="°′″", precision=0, alwayssign=True
    )
    name = target.display_name if display_name is None else str(display_name)
    return (
        f"{name} — center RA {ra}, Dec {dec} — "
        f"{float(field_diameter_deg):g}° binocular field"
    )


def resolve_request_furniture_context(
    furniture, chart, sky, *, observer=None
):
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
    chart_options = {
        "center": context.center,
        "grid": context.grid,
    }
    if observer is not None:
        chart_options["observer"] = observer
    lines = (
        chart_context_lines(chart, sky, **chart_options)
        + observer_context_lines(
            getattr(sky, "observer", None) if observer is None else observer,
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
