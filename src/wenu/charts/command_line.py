"""Shared command-line adaptation for ordinary chart views."""

from __future__ import annotations

import argparse
from copy import copy
from collections.abc import Mapping
from dataclasses import fields
from pathlib import Path

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


class _DisableDefaultEquatorialGrid(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, "equatorial_grid", False)
        setattr(namespace, "equatorial_grid_labels", False)


def add_chart_cli_arguments(parser, *, default_output):
    """Add the complete common CLI contract for ordinary chart views."""
    add_chart_arguments(parser, default_output=default_output)
    parser.add_argument(
        "--config",
        type=Path,
        help="load a partial user TOML configuration overlay",
    )
    parser.set_defaults(
        equatorial_grid=True,
        equatorial_grid_labels=True,
    )
    parser.add_argument(
        "--no-equatorial-grid",
        action=_DisableDefaultEquatorialGrid,
        nargs=0,
        help="omit the default labeled equatorial grid",
    )
    parser.add_argument("--credits", action="store_true", default=None)
    parser.add_argument(
        "--no-center", action="store_false", dest="center", default=None,
        help="omit chart-center coordinate context",
    )
    parser.add_argument(
        "--no-grid", action="store_false", dest="grid", default=None,
        help="omit coordinate-grid context",
    )
    parser.add_argument("--location", action="store_true", default=None)
    parser.add_argument("--date", action="store_true", default=None)
    parser.add_argument("--local-time", action="store_true", default=None)
    return parser


def chart_configuration(arguments):
    """Load one immutable effective configuration for parsed arguments."""
    from wenu.configuration import load_configuration_defaults

    return load_configuration_defaults(getattr(arguments, "config", None))


def chart_cli_furniture(
    arguments,
    *,
    reference_labels=None,
    pole_selection="visible",
    copyright=None,
    symbol_labels=(),
    stellar_title="Stars",
    configuration=None,
    family=None,
):
    """Translate shared parsed controls into immutable chart furniture."""
    if configuration is None:
        base = ChartFurnitureOptions()
    else:
        if family is None:
            raise TypeError("family is required with configuration.")
        base = configuration.furniture_product_export.furniture_by_family[
            family
        ]
    base_context = base.context or ChartContextOptions()

    def selected(name, fallback):
        value = getattr(arguments, name, None)
        return fallback if value is None else bool(value)

    labels = dict(_REFERENCE_LABELS)
    if reference_labels is not None:
        labels.update(reference_labels)
    references = chart_content_options(arguments).grid_references

    def reference(name):
        return ReferencePlaneAnnotation(
            state="labeled" if name in references else "none",
            label=labels[name],
        )

    poles = (
        base.poles.celestial
        if arguments.poles is None
        else pole_selection if arguments.poles else "none"
    )
    legends = chart_legend_selection(arguments)
    return ChartFurnitureOptions(
        references=(
            base.references
            if not references
            else ReferenceAnnotations(
                celestial_equator=reference("equatorial"),
                ecliptic=reference("ecliptic"),
                galactic_plane=reference("galactic"),
            )
        ),
        poles=PoleAnnotations(
            celestial=poles,
            ecliptic=poles,
            galactic=poles,
            labels=selected("pole_labels", base.poles.labels),
        ),
        footer=(
            base.footer
            if arguments.credits is None
            else FooterOptions(
                application=arguments.credits,
                copyright=(copyright if arguments.credits else None),
            )
        ),
        legends=LegendOptions(
            objects=legends.objects,
            stellar_magnitudes=legends.stellar_magnitudes,
            stellar_counts=legends.stellar_counts,
            context=False,
            plan=(None if base.legends is None else base.legends.plan),
            symbol_labels=tuple(symbol_labels),
            stellar_title=stellar_title,
        ),
        context=ChartContextOptions(
            center=selected("center", base_context.center),
            grid=selected("grid", base_context.grid),
            location=selected("location", base_context.location),
            date=selected("date", base_context.date),
            local_time=selected("local_time", base_context.local_time),
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
    language=None,
):
    """Draw every CLI-selected product through the ordinary view facade.

    ``product_details`` may key policies by exact ``ChartProduct`` values or
    by the shared ``atlas`` and ``cartoon`` style names. Exact products take
    precedence. Optional family style overrides are merged over parsed CLI
    values without discarding unrelated explicit switches.
    """
    configuration = getattr(view, "configuration", None)
    product_defaults = (
        None
        if configuration is None
        else configuration.furniture_product_export.product
    )
    options = chart_product_options(arguments, defaults=product_defaults)
    details = {} if product_details is None else product_details
    if not isinstance(details, Mapping):
        raise TypeError("product_details must be a mapping.")
    unknown = set(details) - set(options.products) - {"atlas", "cartoon"}
    if unknown:
        raise ValueError(
            "product_details keys must be selected products or styles."
        )
    effective_arguments = arguments
    if (
        getattr(view, "family", None) == "all_sky"
        and getattr(arguments, "equatorial_grid", False)
        and not getattr(arguments, "_equatorial_grid_explicit", False)
    ):
        effective_arguments = copy(arguments)
        effective_arguments.equatorial_grid = False
        effective_arguments.equatorial_grid_labels = False
        effective_arguments.galactic_grid = True
        effective_arguments.galactic_grid_labels = True
    furniture = (
        chart_cli_furniture(
            effective_arguments,
            configuration=configuration,
            family=getattr(view, "family", None),
        )
        if furniture is None else furniture
    )
    detail_overrides = chart_detail_overrides(effective_arguments)
    content = chart_content_options(effective_arguments)
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
    extension = (
        None if product_defaults is None else product_defaults.extension
    )
    for product, destination in options.outputs(
        stem=stem,
        extension=extension,
    ):
        exports.append(draw_chart_view(
            view,
            destination,
            style=product.style,
            mode=product.mode,
            detail=details.get(product, details.get(product.style, detail)),
            detail_overrides=detail_overrides,
            horizon=content.horizon,
            horizon_mask=content.horizon_mask,
            furniture=furniture,
            style_overrides=style_overrides,
            title=title,
            language=language,
        ))
    return tuple(exports)
