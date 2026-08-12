"""Render-local spatial catalogue selection for resolved chart fields."""

from __future__ import annotations

from dataclasses import fields, replace

import numpy as np

from .detail import SkyContentSelection
from .request_resolver import ResolvedChartRequest


FIELD_CATALOGUE_LAYERS = {
    "nonstellar_objects": "nonstellar",
    "galaxies": "galaxies",
    "open_clusters": "open_clusters",
    "globular_clusters": "globular_clusters",
    "planetary_nebulae": "planetary_nebulae",
    "supernova_remnants": "supernova_remnants",
}


def _visible_identifiers(sky, chart, layer, observer):
    centers = getattr(layer, "spherical_centers", None)
    geometry = (
        centers(observer)
        if callable(centers)
        else layer.spherical_geometry(observer)
    )
    x, y = chart.projection.project_spherical(
        geometry.lon_deg, geometry.lat_deg
    )
    visible = np.asarray(chart.viewport.contains(x, y), dtype=bool)
    field_stop = getattr(chart, "field_stop", None)
    if field_stop is None:
        field_stop = getattr(chart, "horizon", None)
    if field_stop is not None:
        finite = field_stop.finite
        radius = float(np.nanmedian(np.hypot(
            field_stop.x[finite], field_stop.y[finite]
        )))
        visible &= np.hypot(x, y) <= radius
    return frozenset(
        str(identifier)
        for identifier in np.asarray(geometry.ids, dtype=object)[visible]
    )


def select_spatial_chart_content(sky, chart, resolved, *, observer=None):
    """Return a new resolved request containing every field catalogue ID."""
    if not isinstance(resolved, ResolvedChartRequest):
        raise TypeError("resolved must be a ResolvedChartRequest.")
    resolved_observer = getattr(sky, "observer", None) if observer is None else observer
    if resolved_observer is None:
        raise TypeError("spatial selection requires an observer.")
    values = {
        field.name: getattr(resolved.request.content, field.name)
        for field in fields(SkyContentSelection)
    }
    for content_name, attribute in FIELD_CATALOGUE_LAYERS.items():
        layer = getattr(sky, attribute, None)
        if layer is None:
            continue
        automatic = _visible_identifiers(
            sky, chart, layer, resolved_observer
        )
        explicit = values[content_name]
        selected = (
            automatic if explicit is None else automatic | explicit
        )
        values[content_name] = selected - getattr(
            resolved.request.exclusions, content_name
        )
    content = SkyContentSelection(**values)
    request = replace(resolved.request, content=content)
    return replace(resolved, request=request)
