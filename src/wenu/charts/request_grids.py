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


def _latitude_values(limit, step):
    return tuple(value for value in range(-limit, limit + 1, step) if value)


def _grid_specifications(family):
    if family == "binocular":
        longitudes = tuple(range(0, 360, 5))
        latitudes = _latitude_values(85, 5)
        return {
            "equatorial_grid": {
                "ra": longitudes,
                "dec": latitudes,
                "frame": "fk5",
                "equinox": "J2000",
                "include_equator": False,
            },
            "ecliptic_grid": {
                "longitude": longitudes,
                "latitude": latitudes,
                "equinox": "J2000",
                "include_ecliptic": False,
            },
            "galactic_grid": {
                "longitude": longitudes,
                "latitude": latitudes,
                "include_plane": False,
            },
            "altaz_grid": {
                "azimuth": longitudes,
                "altitude": tuple(range(5, 90, 5)),
                "include_horizon": False,
            },
        }
    if family == "regional":
        longitudes = tuple(range(0, 360, 15))
        latitudes = _latitude_values(75, 15)
        return {
            "equatorial_grid": {
                "ra": longitudes,
                "dec": latitudes,
                "frame": "fk5",
                "equinox": "J2000",
            },
            "ecliptic_grid": {
                "longitude": longitudes,
                "latitude": latitudes,
                "equinox": "J2000",
                "include_ecliptic": False,
            },
            "galactic_grid": {
                "longitude": longitudes,
                "latitude": latitudes,
                "include_plane": False,
            },
            "altaz_grid": {
                "azimuth": longitudes,
                "altitude": tuple(range(15, 90, 15)),
                "include_horizon": False,
            },
        }
    longitudes = tuple(range(0, 360, 30))
    samples = 1441
    if family == "circumpolar":
        equatorial_latitudes = (-85, -80, -75)
        other_latitudes = _latitude_values(75, 15)
    else:
        equatorial_latitudes = _latitude_values(75, 15)
        other_latitudes = _latitude_values(60, 15)
    return {
        "equatorial_grid": {
            "ra": longitudes,
            "dec": equatorial_latitudes,
            "frame": "fk5",
            "equinox": "J2000",
            "samples": samples,
            "meridian_dec_min": -75.0,
            "meridian_dec_max": 90.0,
        },
        "ecliptic_grid": {
            "longitude": longitudes,
            "latitude": other_latitudes,
            "equinox": "J2000",
            "samples": samples,
            "include_ecliptic": False,
        },
        "galactic_grid": {
            "longitude": longitudes,
            "latitude": other_latitudes,
            "samples": samples,
            "include_plane": False,
        },
        "altaz_grid": {
            "azimuth": longitudes,
            "altitude": tuple(range(15, 90, 15)),
            "samples": samples,
            "include_horizon": False,
        },
    }


def configure_chart_request_grids(sky, request):
    """Replace request-time grids with the selected family configuration."""
    if not isinstance(request, ChartRequest):
        raise TypeError("request must be a ChartRequest.")
    if not hasattr(sky, "layers") or not callable(getattr(sky, "remove", None)):
        raise TypeError("sky must provide registered layers and remove().")

    for layer in tuple(sky.layers):
        if isinstance(layer, CoordinatesGrid):
            sky.remove(layer)

    requested = requested_coordinate_grids(request.detail)
    specifications = _grid_specifications(request.family)
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
