"""Canonical high-level export for resolved chart compositions."""

from __future__ import annotations

from dataclasses import dataclass

from .composition import ChartComposition


@dataclass(frozen=True)
class ChartExportResult:
    """Inspectable result of one composed render, legend, and save."""

    rendering: object
    output: object
    composition: ChartComposition
    layer_options: dict
    export_options: object

    def __iter__(self):
        """Preserve established ``rendering, output = export(...)`` use."""
        yield self.rendering
        yield self.output


def _validate_composition(chart, composition):
    if not isinstance(composition, ChartComposition):
        raise TypeError("composition must be a ChartComposition.")
    expected = chart.chart_context
    actual = composition.context
    comparable = (
        "viewport",
        "angular_width_deg",
        "angular_height_deg",
        "tangent_longitude_deg",
        "tangent_latitude_deg",
        "boundary_kind",
    )
    if any(getattr(actual, name) != getattr(expected, name) for name in comparable):
        raise ValueError("composition was resolved for a different chart.")


def _configure_figure(renderer, composition):
    figure = renderer.ax.figure
    set_size = getattr(figure, "set_size_inches", None)
    if callable(set_size):
        set_size(
            composition.mode.width_inches,
            composition.mode.height_inches,
            forward=True,
        )
    return figure


def _composition_export_options(composition):
    from .regional import ExportOptions

    canvas = getattr(composition.style, "canvas", None)
    return ExportOptions(
        dpi=composition.mode.dpi,
        transparent=composition.mode.transparent,
        facecolor=getattr(canvas, "sky_color", None),
    )


def export_composed_chart(
    chart,
    sky,
    renderer,
    path,
    *,
    composition,
    layer_options=None,
    export_options=None,
    render_options=None,
):
    """Render, decorate, and save one resolved composition exactly once."""
    _validate_composition(chart, composition)
    figure = _configure_figure(renderer, composition)
    application = composition.layer_options(
        sky,
        overrides=layer_options,
    )
    rendering = chart.render(
        sky,
        renderer,
        style=composition.style,
        layer_options=application.layer_options,
        **({} if render_options is None else dict(render_options)),
    )
    if composition.legends is not None:
        from .chart_legend_workflow import draw_resolved_chart_legends

        rendering = draw_resolved_chart_legends(
            chart,
            sky,
            renderer,
            composition.style,
            rendering,
            composition.detail,
            composition.legends,
        )
    options = (
        _composition_export_options(composition)
        if export_options is None
        else export_options
    )
    output = options.save(figure, path)
    return ChartExportResult(
        rendering=rendering,
        output=output,
        composition=composition,
        layer_options=application.layer_options,
        export_options=options,
    )
