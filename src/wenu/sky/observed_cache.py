"""Keys for observer-dependent spherical-geometry caches."""

from __future__ import annotations


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
