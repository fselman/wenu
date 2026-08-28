"""Keys for observer-dependent spherical-geometry caches."""

from __future__ import annotations

import numpy as np

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import (
    icrs_catalogue_spec,
    observation_context,
    observer_altaz_spec,
)
from wenu.geometry.spherical import SphericalCurves, SphericalPoints


def observer_geometry_key(observer):
    """Return a complete stable key for one observer and instant."""
    if observer is None:
        raise ValueError("An observer is required for observed geometry.")

    utc_datetime = getattr(observer, "utc_datetime", None)
    if utc_datetime is not None:
        instant = utc_datetime.isoformat()
    else:
        astropy_time = getattr(observer, "t_astropy", None)
        if astropy_time is not None:
            utc = astropy_time.utc
            instant = (
                "astropy",
                float(utc.jd1),
                float(utc.jd2),
            )
        else:
            instant = id(getattr(observer, "t", observer))

    coordinates = tuple(
        getattr(observer, name, None)
        for name in ("lat_deg", "lon_deg", "elevation_m")
    )
    if all(value is None for value in coordinates):
        coordinates = (id(observer),)

    return (
        coordinates,
        instant,
        getattr(observer, "ephemeris_name", None),
        str(getattr(observer, "data_directory", "")),
    )


def observed_polygon_arrays(cache, observer, *, source_key, build):
    """Return immutable maximal polygon arrays from an observed cache."""
    key = (observer_geometry_key(observer), source_key)
    cached = cache.get(key)
    if cached is None:
        longitude, latitude = build()
        longitude = tuple(
            _immutable_float_array(values) for values in longitude
        )
        latitude = tuple(
            _immutable_float_array(values) for values in latitude
        )
        if len(longitude) != len(latitude):
            raise ValueError(
                "Observed polygon longitude and latitude must align."
            )
        cached = (longitude, latitude)
        cache[key] = cached
    return cached


def _immutable_float_array(values):
    array = np.asarray(values, dtype=float)
    array.setflags(write=False)
    return array


def _icrs_catalogue_altaz(table, observer):
    return icrs_point_arrays_to_altaz(
        np.asarray(table["ra_deg"], dtype=float),
        np.asarray(table["dec_deg"], dtype=float),
        observer,
        provider="wenu observed catalogue",
    )


def icrs_point_arrays_to_altaz(
    longitude,
    latitude,
    observer,
    *,
    provider,
):
    """Transform ICRS point arrays through CoordinateService."""
    native = SphericalPoints(
        lon_deg=np.asarray(longitude, dtype=float),
        lat_deg=np.asarray(latitude, dtype=float),
        coordinate_spec=icrs_catalogue_spec(provider),
    )
    horizontal = CoordinateService().transform(
        native,
        observer_altaz_spec(observer, provider=provider),
        observation=observation_context(observer),
    )
    return horizontal.lon_deg, horizontal.lat_deg


def icrs_curve_arrays_to_altaz(
    longitudes,
    latitudes,
    observer,
    *,
    provider,
):
    """Transform disconnected ICRS curves through CoordinateService."""
    if not longitudes:
        return (), ()
    native = SphericalCurves(
        lon_deg=tuple(
            np.mod(np.asarray(values, dtype=float), 360.0)
            for values in longitudes
        ),
        lat_deg=tuple(
            np.asarray(values, dtype=float) for values in latitudes
        ),
        coordinate_spec=icrs_catalogue_spec(provider),
    )
    horizontal = CoordinateService().transform(
        native,
        observer_altaz_spec(observer, provider=provider),
        observation=observation_context(observer),
    )
    return horizontal.lon_deg, horizontal.lat_deg


def catalogue_point_altaz(
    cache,
    observer,
    *,
    source_table,
    selected_table,
    source_key,
):
    """Return one selected point catalogue from cached maximal Alt/Az."""
    if len(selected_table) == 0:
        empty = np.asarray([], dtype=float)
        return empty, empty.copy()

    key = (observer_geometry_key(observer), source_key)
    cached = cache.get(key)
    if cached is None:
        azimuth, altitude = _icrs_catalogue_altaz(
            source_table,
            observer,
        )
        azimuth = np.asarray(azimuth, dtype=float)
        altitude = np.asarray(altitude, dtype=float)
        azimuth.setflags(write=False)
        altitude.setflags(write=False)
        cached = (azimuth, altitude)
        cache[key] = cached

    positions = {
        str(identifier): index
        for index, identifier in enumerate(source_table["identifier"])
    }
    try:
        selected_positions = np.asarray(
            [
                positions[str(identifier)]
                for identifier in selected_table["identifier"]
            ],
            dtype=int,
        )
    except KeyError as error:
        raise RuntimeError(
            "The point selection is not contained in the loaded source "
            "catalogue."
        ) from error
    return cached[0][selected_positions], cached[1][selected_positions]
