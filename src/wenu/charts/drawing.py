"""Ordinary drawing of prepared observer-bound chart views."""

from __future__ import annotations

from dataclasses import replace

from .detail import DetailOverrides
from .furniture import ChartFurnitureOptions
from .product_options import ChartProduct, ChartProductOptions
from .request_chart import PreparedChartRequest
from .request_composition import ChartProductCompositionOptions
from .request_generation import export_prepared_chart
from .request_grids import configure_chart_request_grids
from .request_horizon import configure_chart_request_horizon
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


def _furniture_product_export_defaults():
    from wenu.configuration import (
        packaged_furniture_product_export_defaults,
    )

    return packaged_furniture_product_export_defaults()


def _default_furniture(family):
    configured = _furniture_product_export_defaults().furniture_by_family[
        family
    ]
    return ChartFurnitureOptions(
        references=configured.references,
        poles=configured.poles,
        footer=configured.footer,
    )


def _product_defaults():
    return _furniture_product_export_defaults().product


def draw_chart_view(
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
):
    """Compose, render, and export one product from a chart view."""
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
    overrides = replace(
        overrides,
        enabled_layer_additions=additions | requested_grids,
        grid_label_layers=labels | requested_labels,
    )
    furniture = (
        _default_furniture(view.family)
        if furniture is None else furniture
    )
    if not isinstance(furniture, ChartFurnitureOptions):
        raise TypeError("furniture must be a ChartFurnitureOptions value.")
    if style_overrides is not None and not isinstance(
        style_overrides, ChartStyleOverrides
    ):
        raise TypeError(
            "style_overrides must be a ChartStyleOverrides value."
        )

    defaults = _product_defaults()
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
        horizon=bool(horizon),
        horizon_mask=bool(horizon_mask),
        furniture=furniture,
        product_compositions=(ChartProductCompositionOptions(
            product=product,
            detail=detail,
            style_overrides=style_overrides,
        ),),
        title=defaults.title if title is None else title,
        language=defaults.language if language is None else language,
    )
    _validate_load_profile(view, overrides)
    configure_chart_request_grids(view.sky, request, frame=view.frame)
    configure_chart_request_horizon(view.sky, request)
    prepared = PreparedChartRequest(
        chart=view.chart,
        resolved=replace(view._prepared.resolved, request=request),
    )
    generation = export_prepared_chart(
        view.sky,
        prepared,
        observer=view.observer,
    )
    if len(generation.exports) != 1:
        raise RuntimeError("A chart-view drawing must export exactly once.")
    return generation.exports[0]


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
