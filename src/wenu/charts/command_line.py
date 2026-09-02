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
    chart_disk_options,
    chart_disk_sequence_options,
    chart_legend_selection,
    chart_reference_policy,
    chart_sky_content,
    chart_style_overrides,
    chart_track_options,
)
from .drawing import chart_view_request, draw_chart_view
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
from wenu.translations import translate_label
from wenu.sky.solar_system_tracks import SolarSystemTrackRequest
from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG


_REFERENCE_LABELS = {
    "equatorial": "Celestial equator",
    "ecliptic": "Ecliptic",
    "galactic": "Galactic plane",
}


class _DisableDefaultEquatorialGrid(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, "equatorial_grid", False)
        setattr(namespace, "equatorial_grid_labels", False)


def add_chart_cli_arguments(
    parser, *, default_output, default_equatorial_grid=True
):
    """Add the complete common CLI contract for ordinary chart views."""
    add_chart_arguments(parser, default_output=default_output)
    parser.add_argument(
        "--config",
        type=Path,
        help="load a partial user TOML configuration overlay",
    )
    parser.set_defaults(
        equatorial_grid=bool(default_equatorial_grid),
        equatorial_grid_labels=bool(default_equatorial_grid),
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
    language=None,
    ecliptic_keypoints=None,
    ecliptic_keypoint_legend=False,
    stellar_reference_magnitude=None,
    stellar_reference_range=None,
    stellar_background=None,
    stellar_label_suffix="",
    legend_plan=None,
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
    keypoint_state = (
        base.references.ecliptic_keypoints
        if ecliptic_keypoints is None else ecliptic_keypoints
    )

    def selected(name, fallback):
        value = getattr(arguments, name, None)
        return fallback if value is None else bool(value)

    if language is None:
        language = getattr(arguments, "language", None)
    if language is None and configuration is not None:
        language = configuration.furniture_product_export.product.language
    language = "en" if language is None else language
    labels = {
        name: translate_label(label, language)
        for name, label in _REFERENCE_LABELS.items()
    }
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
            if not references and ecliptic_keypoints is None
            else ReferenceAnnotations(
                celestial_equator=(
                    reference("equatorial")
                    if references else base.references.celestial_equator
                ),
                ecliptic=(
                    reference("ecliptic")
                    if references else base.references.ecliptic
                ),
                galactic_plane=(
                    reference("galactic")
                    if references else base.references.galactic_plane
                ),
                ecliptic_keypoints=keypoint_state,
                ecliptic_keypoint_legend=(
                    ecliptic_keypoint_legend
                    or base.references.ecliptic_keypoint_legend
                ),
                ecliptic_keypoint_names=tuple(
                    translate_label(name, language)
                    for name in base.references.ecliptic_keypoint_names
                ),
                ecliptic_keypoint_zodiac_names=tuple(
                    translate_label(name, language)
                    for name in (
                        base.references.ecliptic_keypoint_zodiac_names
                    )
                ),
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
            plan=(
                legend_plan
                if legend_plan is not None
                else None if base.legends is None else base.legends.plan
            ),
            symbol_labels=tuple(symbol_labels),
            stellar_title=stellar_title,
            stellar_reference_magnitude=stellar_reference_magnitude,
            stellar_reference_range=stellar_reference_range,
            stellar_background=stellar_background,
            stellar_label_suffix=stellar_label_suffix,
        ),
        context=ChartContextOptions(
            center=selected("center", base_context.center),
            grid=selected("grid", base_context.grid),
            location=selected("location", base_context.location),
            date=selected("date", base_context.date),
            local_time=selected("local_time", base_context.local_time),
        ),
    )


def _chart_view_argument_plans(
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
    sequence=False,
):
    """Resolve CLI-selected products into shared drawing plans.

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
    if language is None:
        language = getattr(arguments, "language", None)
    if language is None and product_defaults is not None:
        language = product_defaults.language
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
            language=language,
        )
        if furniture is None else furniture
    )
    detail_overrides = chart_detail_overrides(effective_arguments)
    content = chart_content_options(effective_arguments)
    parsed_track = chart_track_options(effective_arguments)
    track_request = (
        None
        if parsed_track is None
        else SolarSystemTrackRequest(
            descriptor=SOLAR_SYSTEM_BODY_CATALOG.resolve(parsed_track.body),
            start_instant=parsed_track.start_instant,
            start_time_scale="utc",
            sample_step_days=parsed_track.sample_step_days,
            tick_step_days=parsed_track.tick_step_days,
            tick_count=parsed_track.tick_count,
        )
    )
    if track_request is not None and getattr(view, "family", None) not in {
        "regional", "binocular"
    }:
        raise ValueError(
            "--planet-track is supported only by regional and binocular charts."
        )
    disk_requests = chart_disk_options(arguments)
    disk_sequence = chart_disk_sequence_options(arguments)
    family = getattr(view, "family", None)
    unsupported_disks = tuple(
        disk for disk in disk_requests
        if not disk.descriptor.supports_resolved_disk_in(family)
    )
    if unsupported_disks:
        raise ValueError(
            f"resolved {unsupported_disks[0].descriptor.display_name} disks "
            f"are not supported by {family} charts."
        )
    if (
        disk_sequence is not None
        and not disk_sequence.supports_chart_family(family)
    ):
        selector = (
            "--moon-disk-sequence"
            if disk_sequence.target == "moon"
            else "--planet-disk-sequence"
        )
        raise ValueError(
            f"{selector} is not supported by {family} charts for "
            f"{disk_sequence.sequence.descriptor.display_name}."
        )
    configured_policy = (
        None if configuration is None else configuration.reference_policy
    )
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
    if sequence:
        if options.all_products:
            raise ValueError("A chart sequence accepts one chart product.")
        if options.output_format is None:
            raise ValueError(
                "A chart sequence requires an explicit output format."
            )
        selected_outputs = ((options.products[0], options.output),)
    else:
        extension = (
            None if product_defaults is None else product_defaults.extension
        )
        selected_outputs = options.outputs(
            stem=stem,
            extension=extension,
        )
    plans = []
    for product, destination in selected_outputs:
        plans.append((
            destination,
            {
                "style": product.style,
                "mode": product.mode,
                "detail": details.get(
                    product,
                    details.get(product.style, detail),
                ),
                "detail_overrides": detail_overrides,
                "horizon": content.horizon,
                "horizon_mask": content.horizon_mask,
                "furniture": furniture,
                "style_overrides": style_overrides,
                "title": title,
                "language": language,
                "output_format": options.output_format,
                "reference_policy": chart_reference_policy(
                    arguments, default=configured_policy
                ),
                "content": chart_sky_content(arguments),
                "solar_system_track": track_request,
                "solar_system_disks": disk_requests,
                "solar_system_disk_sequence": disk_sequence,
                "solar_system_track_tick_labels": (
                    False if parsed_track is None else parsed_track.label_ticks
                ),
            },
        ))
    return tuple(plans)


def chart_view_requests_from_arguments(view, arguments, **options):
    """Translate CLI products into immutable requests without rendering."""
    plans = _chart_view_argument_plans(view, arguments, **options)
    return tuple(
        chart_view_request(view, destination, **request_options)
        for destination, request_options in plans
    )


def draw_chart_view_from_arguments(view, arguments, **options):
    """Draw CLI products through the same centrally resolved plans."""
    plans = _chart_view_argument_plans(view, arguments, **options)
    return tuple(
        draw_chart_view(view, destination, **request_options)
        for destination, request_options in plans
    )
