"""Canonical high-level export for resolved chart compositions."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .composition import ChartComposition


@dataclass(frozen=True)
class ChartExportResult:
    """Inspectable result of one composed render, legend, and save."""

    rendering: object
    output: object
    composition: ChartComposition
    layer_options: dict
    export_options: object
    furniture_rendering: object | None = None
    footer_rendering: object | None = None
    additional_furniture_rendering: object | None = None

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
    from .context import BoundaryKind

    canvas = getattr(composition.style, "canvas", None)
    circular = composition.context.boundary_kind is BoundaryKind.CIRCULAR
    configuration = getattr(composition, "configuration", None)
    if configuration is None:
        from wenu.configuration import (
            packaged_furniture_product_export_defaults,
        )

        defaults = packaged_furniture_product_export_defaults().export_options
    else:
        defaults = (
            configuration.furniture_product_export.export_options
        )
    return replace(
        defaults,
        dpi=composition.mode.dpi,
        transparent=(
            True if circular else composition.mode.transparent
        ),
        facecolor=(
            "none"
            if circular
            else getattr(canvas, "sky_color", None)
        ),
    )


def export_composed_chart(
    chart,
    sky,
    renderer,
    path,
    *,
    observer=None,
    composition,
    layer_options=None,
    export_options=None,
    render_options=None,
    additional_furniture=None,
    svg_provenance=None,
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
        observer=observer,
        style=composition.style,
        layer_options=application.layer_options,
        **({} if render_options is None else dict(render_options)),
    )
    furniture_rendering = None
    if composition.furniture is not None:
        from .reference_furniture import (
            draw_celestial_reference_furniture,
        )

        furniture_rendering = draw_celestial_reference_furniture(
            chart,
            sky,
            renderer,
            composition,
            observer=observer,
        )
    if composition.legends is not None:
        from .chart_legend_workflow import draw_resolved_chart_legends

        legend_options = {}
        configuration = getattr(composition, "configuration", None)
        if configuration is not None:
            legend_options["stellar_legend_style"] = (
                configuration.furniture_product_export.magnitude_legend
            )
        rendering = draw_resolved_chart_legends(
            chart,
            sky,
            renderer,
            composition.style,
            rendering,
            composition.detail,
            composition.legends,
            **legend_options,
        )
    footer_rendering = None
    if composition.furniture is not None:
        footer = composition.furniture.footer
        from .footer_furniture import draw_chart_footer

        canvas = getattr(composition.style, "canvas", None)
        footer_options = {}
        configuration = getattr(composition, "configuration", None)
        if configuration is not None:
            footer_options["layout"] = (
                configuration.furniture_product_export.footer_layout
            )
        footer_rendering = draw_chart_footer(
            renderer,
            footer,
            composition.mode,
            color=(
                getattr(canvas, "footer_color", None)
                or getattr(canvas, "foreground_color", "black")
            ),
            **footer_options,
        )
    additional_furniture_rendering = None
    if additional_furniture is not None:
        if not callable(additional_furniture):
            raise TypeError("additional_furniture must be callable or None.")
        additional_furniture_rendering = additional_furniture(
            chart=chart,
            sky=sky,
            renderer=renderer,
            composition=composition,
            rendering=rendering,
        )
    from wenu.chart_document import (
        assign_canvas_semantics,
        assign_furniture_semantics,
    )

    assign_canvas_semantics(renderer)
    assign_furniture_semantics(
        renderer,
        rendering,
        footer_rendering=footer_rendering,
    )
    options = (
        _composition_export_options(composition)
        if export_options is None
        else export_options
    )
    if svg_provenance is not None:
        options = replace(options, svg_provenance=svg_provenance)
    output = options.save(figure, path)
    return ChartExportResult(
        rendering=rendering,
        output=output,
        composition=composition,
        layer_options=application.layer_options,
        export_options=options,
        furniture_rendering=furniture_rendering,
        footer_rendering=footer_rendering,
        additional_furniture_rendering=(
            additional_furniture_rendering
        ),
    )
