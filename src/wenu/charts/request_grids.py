"""Request-time semantic coordinate-grid configuration."""

from __future__ import annotations

from wenu.sky.coordinate_grids import CoordinatesGrid

from .detail import COORDINATE_GRID_LAYERS
from .request import ChartRequest


def requested_coordinate_grids(detail):
    """Return the semantic grids explicitly requested by detail overrides."""
    requested = set(detail.grid_label_layers or ())
    all_requested = False
    for names in (detail.enabled_layers, detail.enabled_layer_additions):
        if not names:
            continue
        if "coordinate_grids" in names:
            all_requested = True
        requested.update(set(names) & COORDINATE_GRID_LAYERS)
    disabled = set(detail.disabled_layers or ())
    if all_requested and "coordinate_grids" not in disabled:
        requested.update(COORDINATE_GRID_LAYERS)
    return frozenset(requested - disabled)


def _latitude_values(limit, step, *, include_zero=False):
    values = set(range(-limit, limit + 1, step))
    if include_zero:
        values.add(0)
    else:
        values.discard(0)
    return tuple(sorted(values))


def _view_span_deg(family, frame):
    if frame is not None:
        diameter = getattr(frame, "field_diameter_deg", None)
        if diameter is not None:
            return float(diameter)
        dimensions = tuple(
            value for value in (
                getattr(frame, "field_width_deg", None),
                getattr(frame, "field_height_deg", None),
            ) if value is not None
        )
        if dimensions:
            return max(map(float, dimensions))
        limiting = getattr(frame, "limiting_declination_deg", None)
        if limiting is not None:
            return 2.0 * (90.0 - abs(float(limiting)))
    if family == "all_sky":
        return 360.0
    return 180.0 if family == "planisphere" else 60.0


def _grid_specifications(family, frame=None):
    span = _view_span_deg(family, frame)
    if family == "circumpolar":
        step = 30
    elif family == "regional" and span <= 60.0:
        step = 15
    else:
        step = 15 if span < 60.0 else 30
    longitudes = tuple(range(0, 360, step))
    latitudes = _latitude_values(
        75, step, include_zero=family == "all_sky"
    )
    galactic_longitudes = longitudes
    galactic_latitudes = latitudes
    if family == "all_sky":
        galactic_longitudes = tuple(range(0, 360, 45))
        galactic_latitudes = tuple(range(-60, 61, 30))
    samples = 721 if step == 15 else 1441
    return {
        "equatorial_grid": {
            "ra": longitudes,
            "dec": latitudes,
            "frame": "fk5",
            "equinox": "J2000",
            "samples": samples,
            "meridian_dec_min": -75.0,
            "meridian_dec_max": 90.0,
        },
        "ecliptic_grid": {
            "longitude": longitudes,
            "latitude": latitudes,
            "equinox": "J2000",
            "samples": samples,
            "include_ecliptic": False,
        },
        "galactic_grid": {
            "longitude": galactic_longitudes,
            "latitude": galactic_latitudes,
            "samples": samples,
            "include_plane": False,
        },
        "altaz_grid": {
            "azimuth": longitudes,
            "altitude": tuple(range(step, 90, step)),
            "samples": samples,
            "include_horizon": False,
        },
    }


def configure_chart_request_grids(sky, request, *, frame=None):
    """Replace request-time grids with the selected family configuration."""
    if not isinstance(request, ChartRequest):
        raise TypeError("request must be a ChartRequest.")
    if not hasattr(sky, "layers") or not callable(getattr(sky, "remove", None)):
        raise TypeError("sky must provide registered layers and remove().")

    for layer in tuple(sky.layers):
        if isinstance(layer, CoordinatesGrid):
            sky.remove(layer)

    requested = requested_coordinate_grids(request.detail)
    specifications = _grid_specifications(request.family, frame)
    configured = []
    for name, method_name in (
        ("equatorial_grid", "add_equatorial_grid"),
        ("ecliptic_grid", "add_ecliptic_grid"),
        ("galactic_grid", "add_galactic_grid"),
        ("altaz_grid", "add_altaz_grid"),
    ):
        if name in requested:
            configured.append(
                getattr(sky, method_name)(**specifications[name])
            )
    return tuple(configured)
