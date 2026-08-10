"""Keys for observer-dependent spherical-geometry caches."""

from __future__ import annotations

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord


def observer_geometry_key(observer):
    """Return a complete stable key for one observer and instant."""
    if observer is None:
        raise ValueError("An observer is required for observed geometry.")

    utc_datetime = getattr(observer, "utc_datetime", None)
    if utc_datetime is not None:
        instant = utc_datetime.isoformat()
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


def _icrs_catalogue_altaz(table, observer):
    coordinates = SkyCoord(
        ra=np.asarray(table["ra_deg"], dtype=float) * u.deg,
        dec=np.asarray(table["dec_deg"], dtype=float) * u.deg,
        frame="icrs",
    )
    horizontal = coordinates.transform_to(observer.altaz_frame)
    return (
        horizontal.az.to_value(u.deg),
        horizontal.alt.to_value(u.deg),
    )


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
