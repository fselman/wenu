"""Shared command-line adaptation for ordinary chart views."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields

from .chart_arguments import (
    add_chart_arguments,
    chart_content_options,
    chart_detail_overrides,
    chart_legend_selection,
    chart_style_overrides,
)
from .drawing import draw_chart_view
from .furniture import (
    ChartContextOptions,
    ChartFurnitureOptions,
    FooterOptions,
    PoleAnnotations,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
)
from .legend_plan import LegendOptions
from .product_options import ChartProduct, chart_product_options
from .style_overrides import ChartStyleOverrides


_REFERENCE_LABELS = {
    "equatorial": "Celestial equator",
    "ecliptic": "Ecliptic",
    "galactic": "Galactic plane",
}


def add_chart_cli_arguments(parser, *, default_output):
    """Add the complete common CLI contract for ordinary chart views."""
    add_chart_arguments(parser, default_output=default_output)
    parser.add_argument("--credits", action="store_true")
    parser.add_argument(
        "--no-center", action="store_false", dest="center",
        help="omit chart-center coordinate context",
    )
    parser.add_argument(
        "--no-grid", action="store_false", dest="grid",
        help="omit coordinate-grid context",
    )
    parser.add_argument("--location", action="store_true")
    parser.add_argument("--date", action="store_true")
    parser.add_argument("--local-time", action="store_true")
    return parser


def chart_cli_furniture(
    arguments,
    *,
    reference_labels=None,
    pole_selection="visible",
    copyright=None,
    symbol_labels=(),
    stellar_title="Stars",
):
    """Translate shared parsed controls into immutable chart furniture."""
    labels = dict(_REFERENCE_LABELS)
    if reference_labels is not None:
        labels.update(reference_labels)
    references = chart_content_options(arguments).grid_references

    def reference(name):
        return ReferencePlaneAnnotation(
            state="labeled" if name in references else "none",
            label=labels[name],
        )

    poles = pole_selection if arguments.poles else "none"
    legends = chart_legend_selection(arguments)
    return ChartFurnitureOptions(
        references=ReferenceAnnotations(
            celestial_equator=reference("equatorial"),
            ecliptic=reference("ecliptic"),
            galactic_plane=reference("galactic"),
        ),
        poles=PoleAnnotations(
            celestial=poles,
            ecliptic=poles,
            galactic=poles,
            labels=arguments.pole_labels,
        ),
        footer=FooterOptions(
            application=arguments.credits,
            copyright=(copyright if arguments.credits else None),
        ),
        legends=LegendOptions(
            objects=legends.objects,
            stellar_magnitudes=legends.stellar_magnitudes,
            stellar_counts=legends.stellar_counts,
            context=False,
            symbol_labels=tuple(symbol_labels),
            stellar_title=stellar_title,
        ),
        context=ChartContextOptions(
            center=arguments.center,
            grid=arguments.grid,
            location=arguments.location,
            date=arguments.date,
            local_time=arguments.local_time,
        ),
    )


def draw_chart_view_from_arguments(
    view,
    arguments,
    *,
    stem,
    detail=None,
    product_details=None,
    furniture=None,
    style_overrides=None,
    title=None,
    language="en",
):
    """Draw every CLI-selected product through the ordinary view facade.

    ``product_details`` may key policies by exact ``ChartProduct`` values or
    by the shared ``atlas`` and ``cartoon`` style names. Exact products take
    precedence. Optional family style overrides are merged over parsed CLI
    values without discarding unrelated explicit switches.
    """
    options = chart_product_options(arguments)
    details = {} if product_details is None else product_details
    if not isinstance(details, Mapping):
        raise TypeError("product_details must be a mapping.")
    unknown = set(details) - set(options.products) - {"atlas", "cartoon"}
    if unknown:
        raise ValueError(
            "product_details keys must be selected products or styles."
        )
    furniture = (
        chart_cli_furniture(arguments) if furniture is None else furniture
    )
    detail_overrides = chart_detail_overrides(arguments)
    parsed_style = chart_style_overrides(arguments)
    if style_overrides is not None:
        if not isinstance(style_overrides, ChartStyleOverrides):
            raise TypeError(
                "style_overrides must be a ChartStyleOverrides value."
            )
        style_overrides = ChartStyleOverrides(**{
            field.name: (
                getattr(style_overrides, field.name)
                if getattr(style_overrides, field.name) is not None
                else getattr(parsed_style, field.name)
            )
            for field in fields(ChartStyleOverrides)
        })
    else:
        style_overrides = parsed_style
    exports = []
    for product, destination in options.outputs(stem=stem):
        exports.append(draw_chart_view(
            view,
            destination,
            style=product.style,
            mode=product.mode,
            detail=details.get(product, details.get(product.style, detail)),
            detail_overrides=detail_overrides,
            furniture=furniture,
            style_overrides=style_overrides,
            title=title,
            language=language,
        ))
    return tuple(exports)
