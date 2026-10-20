"""Keys for observer-dependent spherical-geometry caches."""

from __future__ import annotations

from hashlib import sha256

import numpy as np

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import PositionStatus
from wenu.coordinates import (
    icrs_catalogue_spec,
    observation_context,
    observer_altaz_spec,
)
from wenu.geometry.spherical import SphericalCurves, SphericalPoints


def skyfield_stellar_altaz(stars, observer):
    """Apply the existing stellar observation policy to an admitted target.

    Skyfield owns observer subtraction and apparent corrections. This path
    retains the historical no-deflectors policy and adds no propagation.
    """
    apparent = observer.skyfield.at(observer.t).observe(stars).apparent(deflectors=[])
    altitude, azimuth, _ = apparent.altaz()
    return (np.asarray(altitude.degrees, dtype=float),
            np.asarray(azimuth.degrees, dtype=float))


def _array_identity(values):
    array = np.ma.asarray(values)
    return (str(array.dtype), array.shape,
            sha256(np.ascontiguousarray(array.data).tobytes()).hexdigest(),
            sha256(np.ascontiguousarray(np.ma.getmaskarray(array)).tobytes()).hexdigest())


def _backend_geometry_key(observer):
    """Describe active inputs, rather than their mutable names or paths.

    Astropy remains responsible for its existing resource-loading policy. This
    key neither chooses an EOP product nor changes the observation calculation.
    """
    import astropy
    import erfa
    import skyfield
    from astropy.coordinates import solar_system_ephemeris
    from astropy.utils import iers

    resources = getattr(observer, "geometry_resource_identity", None)
    ephemeris = resources() if callable(resources) else None
    table = iers.earth_orientation_table.get()
    eop = (type(table), repr(table.meta), tuple((name, str(table[name].unit),
                              _array_identity(table[name])) for name in table.colnames))
    time = getattr(observer, "t", None)
    timescale = getattr(time, "ts", getattr(observer, "timescale", None))
    time_inputs = tuple((name, _array_identity(getattr(timescale, name)))
                        for name in ("leap_dates", "leap_offsets", "_leap_utc",
                                     "_leap_offsets", "_leap_tai", "delta_t_table",
                                     "polar_motion_table")
                        if getattr(timescale, name, None) is not None)
    event = tuple((name, _array_identity(getattr(time, name)))
                  for name in ("tt", "ut1") if hasattr(time, name))
    return (astropy.__version__, erfa.__version__, skyfield.__version__,
            eop, (iers.conf.auto_download, iers.conf.auto_max_age,
                  iers.conf.iers_degraded_accuracy),
            _array_identity(erfa.leap_seconds.get()),
            solar_system_ephemeris.get(), id(solar_system_ephemeris._kernel),
            ephemeris, id(getattr(observer, "ephemeris", None)),
            id(getattr(observer, "skyfield", None)),
            id(time), event, time_inputs,
            id(getattr(timescale, "delta_t_function", None)))


def observer_geometry_key(observer):
    """Return a process-local reuse key after current resource checks."""
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

    # Frame-only compatibility observers must follow the same normalized
    # site/event consumed by CoordinateService, not just object identity.
    try:
        context = observation_context(observer)
    except (TypeError, AttributeError):
        context = None  # opaque test/legacy observer: existing identity fallback

    return (
        context,
        coordinates,
        instant,
        getattr(observer, "ephemeris_name", None),
        str(getattr(observer, "data_directory", "")),
        _backend_geometry_key(observer),
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
    source_spec=None,
):
    """Transform ICRS point arrays through CoordinateService."""
    native = SphericalPoints(
        lon_deg=np.asarray(longitude, dtype=float),
        lat_deg=np.asarray(latitude, dtype=float),
        coordinate_spec=source_spec if source_spec is not None else icrs_catalogue_spec(provider),
    )
    horizontal = CoordinateService().transform(
        native,
        observer_altaz_spec(
            observer,
            position_status=PositionStatus.APPARENT,
            provider=provider,
        ),
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
        observer_altaz_spec(
            observer,
            position_status=PositionStatus.APPARENT,
            provider=provider,
        ),
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
