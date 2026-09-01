"""Ordinary drawing of prepared observer-bound chart views."""

from __future__ import annotations

from dataclasses import replace

from .detail import DetailOverrides, SkyContentSelection
from .furniture import ChartFurnitureOptions
from .product_options import ChartProduct, ChartProductOptions
from .request import ChartRequest
from .request_chart import PreparedChartRequest, _chart_from_resolved
from .request_composition import ChartProductCompositionOptions
from .request_disks import configure_chart_request_disks
from .request_disks import FrozenEarthSolarSystemDiskSequenceDisplayRequest
from .request_generation import export_prepared_chart
from .request_grids import configure_chart_request_grids
from .request_horizon import configure_chart_request_horizon
from .request_tracks import configure_chart_request_track
from .style_overrides import ChartStyleOverrides
from .view import ChartView


_GRID_NAMES = {
    "altaz": "altaz_grid",
    "altaz_grid": "altaz_grid",
    "equatorial": "equatorial_grid",
    "equatorial_grid": "equatorial_grid",
    "ecliptic": "ecliptic_grid",
    "ecliptic_grid": "ecliptic_grid",
    "galactic": "galactic_grid",
    "galactic_grid": "galactic_grid",
}


def _empty_sky_content():
    empty = frozenset()
    return SkyContentSelection(
        constellation_lines=empty, constellation_boundaries=empty,
        constellation_labels=empty, nonstellar_objects=empty,
        galaxies=empty, open_clusters=empty, globular_clusters=empty,
        planetary_nebulae=empty, supernova_remnants=empty,
        milky_way_levels=empty, lmc_levels=empty, smc_levels=empty,
        solar_system_objects=empty,
    )


def _is_frozen_sequence(value):
    return isinstance(value, FrozenEarthSolarSystemDiskSequenceDisplayRequest)


def _furniture_product_export_defaults(configuration=None):
    if configuration is not None:
        return configuration.furniture_product_export
    from wenu.configuration import (
        packaged_furniture_product_export_defaults,
    )

    return packaged_furniture_product_export_defaults()


def _default_furniture(family, configuration=None):
    configured = _furniture_product_export_defaults(
        configuration
    ).furniture_by_family[
        family
    ]
    return ChartFurnitureOptions(
        references=configured.references,
        poles=configured.poles,
        footer=configured.footer,
    )


def _product_defaults(configuration=None):
    return _furniture_product_export_defaults(configuration).product


def chart_view_request(
    view,
    destination,
    *,
    style=None,
    mode=None,
    detail=None,
    detail_overrides=None,
    grids=(),
    grid_labels=(),
    horizon=False,
    horizon_mask=False,
    furniture=None,
    style_overrides=None,
    title=None,
    language=None,
    output_format=None,
    reference_policy=None,
    content=None,
    solar_system_track=None,
    solar_system_track_tick_labels=False,
    solar_system_disks=(),
    solar_system_disk_sequence=None,
):
    """Translate one prepared view and product into an immutable request."""
    if not isinstance(view, ChartView):
        raise TypeError("view must be a ChartView.")
    overrides = (
        DetailOverrides()
        if detail_overrides is None
        else detail_overrides
    )
    if not isinstance(overrides, DetailOverrides):
        raise TypeError("detail_overrides must be a DetailOverrides value.")
    if overrides.content_selection is not None:
        raise ValueError(
            "ChartView content is fixed during view preparation."
        )
    requested_grids = _grid_layers(grids)
    requested_labels = _grid_layers(grid_labels)
    if (
        view.family == "all_sky"
        and not requested_grids
        and not requested_labels
        and not overrides.enabled_layer_additions
        and not overrides.grid_label_layers
        and not overrides.disabled_layers
    ):
        requested_grids = frozenset({"galactic_grid"})
        requested_labels = requested_grids
    additions = frozenset(overrides.enabled_layer_additions or ())
    labels = frozenset(overrides.grid_label_layers or ())
    frozen = _is_frozen_sequence(solar_system_disk_sequence)
    if frozen:
        if horizon or horizon_mask or solar_system_track or solar_system_disks:
            raise ValueError(
                "frozen-Earth ecliptic sequences exclude horizon, tracks, "
                "and ordinary resolved disks."
            )
        forbidden = (requested_grids | requested_labels | additions | labels) - {
            "equatorial_grid"
        }
        if forbidden:
            raise ValueError(
                "frozen-Earth ecliptic sequences permit only the equatorial grid."
            )
        frozen_layers = {
            "venus_disk_sequence_frozen_illuminated",
            "venus_disk_sequence_frozen_limb",
            "venus_disk_sequence_frozen_terminator",
            "venus_disk_sequence_frozen_labels",
            "frozen_earth_sun",
        }
        if "equatorial_grid" in (
            requested_grids | requested_labels | additions | labels
        ):
            frozen_layers.add("equatorial_grid")
        overrides = replace(overrides, enabled_layers=frozenset(frozen_layers))
    overrides = replace(
        overrides,
        enabled_layer_additions=additions | requested_grids,
        grid_label_layers=labels | requested_labels,
    )
    furniture = (
        (
            _default_furniture(view.family)
            if view.configuration is None
            else _default_furniture(view.family, view.configuration)
        )
        if furniture is None else furniture
    )
    if frozen:
        furniture = ChartFurnitureOptions()
    if not isinstance(furniture, ChartFurnitureOptions):
        raise TypeError("furniture must be a ChartFurnitureOptions value.")
    if style_overrides is not None and not isinstance(
        style_overrides, ChartStyleOverrides
    ):
        raise TypeError(
            "style_overrides must be a ChartStyleOverrides value."
        )
    if content is not None and not isinstance(content, SkyContentSelection):
        raise TypeError("content must be a SkyContentSelection or None.")

    defaults = (
        _product_defaults()
        if view.configuration is None
        else _product_defaults(view.configuration)
    )
    product = ChartProduct(
        defaults.product.style if style is None else style,
        defaults.product.mode if mode is None else mode,
    )
    request = replace(
        view._prepared.resolved.request,
        product=ChartProductOptions(
            output=destination,
            style=product.style,
            mode=product.mode,
        ),
        detail=overrides,
        content=(
            _empty_sky_content() if frozen else (
                view._prepared.resolved.request.content
                if content is None else content
            )
        ),
        solar_system_track=solar_system_track,
        solar_system_track_tick_labels=bool(solar_system_track_tick_labels),
        solar_system_disks=tuple(solar_system_disks),
        solar_system_disk_sequence=solar_system_disk_sequence,
        horizon=bool(horizon),
        horizon_mask=bool(horizon_mask),
        furniture=furniture,
        product_compositions=(ChartProductCompositionOptions(
            product=product,
            detail=detail,
            style_overrides=style_overrides,
        ),),
        title=(
            "Frozen-Earth Venus sequence"
            if frozen and title is None
            else (defaults.title if title is None else title)
        ),
        language=defaults.language if language is None else language,
        reference_policy=(
            view._prepared.resolved.request.reference_policy
            if reference_policy is None else reference_policy
        ),
        coordinate_frame=(
            "ecliptic"
            if frozen
            else view._prepared.resolved.request.coordinate_frame
        ),
    )
    if output_format is not None:
        request = replace(
            request,
            product=replace(
                request.product,
                output_format=output_format,
            ),
        )
    return request


def draw_chart_view_request(view, request):
    """Render one translated request through its prepared view resources."""
    if not isinstance(view, ChartView):
        raise TypeError("view must be a ChartView.")
    if not isinstance(request, ChartRequest):
        raise TypeError("request must be a ChartRequest.")
    _validate_load_profile(view, request.detail)
    configure_chart_request_grids(
        view.sky, request, frame=view.frame, observer=view.observer
    )
    configure_chart_request_horizon(view.sky, request)
    configure_chart_request_track(view.sky, request)
    configure_chart_request_disks(view.sky, request)
    chart = view.chart
    if _is_frozen_sequence(request.solar_system_disk_sequence):
        chart = _chart_from_resolved(
            view.sky,
            replace(view._prepared.resolved, request=request),
            view.observer,
        )
    prepared = PreparedChartRequest(
        chart=chart,
        resolved=replace(view._prepared.resolved, request=request),
    )
    export_options = {"observer": view.observer}
    if view.configuration is not None:
        export_options["configuration"] = view.configuration
    generation = export_prepared_chart(
        view.sky,
        prepared,
        **export_options,
    )
    if len(generation.exports) != 1:
        raise RuntimeError("A chart-view drawing must export exactly once.")
    return generation.exports[0]


def draw_chart_view(view, destination, **options):
    """Compose, render, and export one product from a chart view."""
    request = chart_view_request(view, destination, **options)
    return draw_chart_view_request(view, request)


def _grid_layers(values):
    if values is None:
        return frozenset()
    resolved = set()
    for value in values:
        name = str(value).strip().lower()
        try:
            resolved.add(_GRID_NAMES[name])
        except KeyError as error:
            raise ValueError(
                "grids must contain altaz, equatorial, ecliptic, or "
                "galactic."
            ) from error
    return frozenset(resolved)


def _validate_load_profile(view, detail):
    profile = getattr(view.sky, "load_profile", None)
    if profile is None:
        raise ValueError("view sky must declare a load profile.")
    profile.require(
        star_magnitude_limit=detail.star_magnitude_limit,
        galaxy_magnitude_limit=detail.galaxy_magnitude_limit,
        extended_object_samples=detail.extended_object_samples,
    )
