"""Render a chart and compose its independent legends in one workflow."""

from __future__ import annotations

from dataclasses import dataclass

from .automatic_legends import draw_automatic_chart_legends


def _publication_style(chart_style):
    converter = getattr(chart_style, "as_publication_style", None)
    return converter() if callable(converter) else chart_style


@dataclass(frozen=True)
class RenderedChartWithLegends:
    """Chart rendering result paired with its composed legends."""

    rendering: object
    legends: object

    @property
    def artists(self):
        """Return legend artists without flattening chart artists."""
        return self.legends.artists


def draw_resolved_chart_legends(
    chart,
    sky,
    renderer,
    chart_style,
    rendering,
    resolved_detail,
    legend_options,
):
    """Attach resolved canonical legends to an existing rendering."""
    if legend_options is None:
        return rendering
    if not hasattr(chart_style, "legend"):
        raise TypeError(
            "Canonical legends require a composed chart style."
        )
    options = dict(
        resolved_detail=resolved_detail,
        plan=legend_options.plan,
        include_objects=legend_options.plan.objects.enabled,
        include_context=legend_options.context,
        context_lines=legend_options.context_lines,
        symbol_labels=legend_options.symbol_labels,
        stellar_title=legend_options.stellar_title,
    )
    if legend_options.stellar_counts:
        options["stellar_counts"] = True
    legends = draw_automatic_chart_legends(
        renderer.ax,
        chart,
        sky,
        chart_style,
        rendering,
        **options,
    )
    return RenderedChartWithLegends(
        rendering=rendering,
        legends=legends,
    )


def render_chart_with_legends(
    chart,
    sky,
    renderer,
    chart_style,
    resolved_detail,
    *,
    plan=None,
    layer_options=None,
    footprint_contains=None,
    stellar_legend_style=None,
    star_layer=None,
    grid=None,
    object_title=None,
    context_lines=None,
    render_options=None,
    include_objects=True,
    include_context=None,
) -> RenderedChartWithLegends:
    """Render ``chart`` and add automatically composed independent legends.

    ``chart_style`` may be either a composed style or a PublicationStyle.
    The renderer-facing form is used for chart layers while the original
    style remains available to the legend resolvers.
    """
    publication = _publication_style(chart_style)
    options = {} if render_options is None else dict(render_options)
    if layer_options is not None:
        options["layer_options"] = layer_options
    rendering = chart.render(
        sky,
        renderer,
        style=publication,
        **options,
    )
    legends = draw_automatic_chart_legends(
        renderer.ax,
        chart,
        sky,
        chart_style,
        rendering,
        resolved_detail=resolved_detail,
        plan=plan,
        footprint_contains=footprint_contains,
        stellar_legend_style=stellar_legend_style,
        star_layer=star_layer,
        grid=grid,
        object_title=object_title,
        context_lines=context_lines,
        include_objects=include_objects,
        include_context=include_context,
    )
    return RenderedChartWithLegends(
        rendering=rendering,
        legends=legends,
    )
