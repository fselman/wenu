"""Observer-dependent catalogue cache contracts."""

from types import SimpleNamespace

import numpy as np
from astropy.table import Table
from astropy.time import Time

from wenu.sky import observed_cache


def catalogue():
    return Table(
        {
            "identifier": ["one", "two", "three"],
            "ra_deg": [10.0, 20.0, 30.0],
            "dec_deg": [-10.0, -20.0, -30.0],
        }
    )


def test_astropy_observer_time_has_stable_value_identity():
    first = SimpleNamespace(
        t_astropy=Time("2026-08-16T01:00:00"),
        lat_deg=-33.0,
        lon_deg=-71.5,
        elevation_m=52.0,
    )
    equivalent = SimpleNamespace(
        t_astropy=Time("2026-08-16T01:00:00"),
        lat_deg=-33.0,
        lon_deg=-71.5,
        elevation_m=52.0,
    )
    later = SimpleNamespace(
        t_astropy=Time("2026-08-16T07:00:00"),
        lat_deg=-33.0,
        lon_deg=-71.5,
        elevation_m=52.0,
    )

    assert (
        observed_cache.observer_geometry_key(first)
        == observed_cache.observer_geometry_key(equivalent)
    )
    assert (
        observed_cache.observer_geometry_key(first)
        != observed_cache.observer_geometry_key(later)
    )


def test_point_selections_share_one_maximal_transform(monkeypatch):
    source = catalogue()
    cache = {}
    calls = []

    def transform(table, observer):
        calls.append((table, observer))
        return np.asarray([100.0, 200.0, 300.0]), np.asarray(
            [1.0, 2.0, 3.0]
        )

    monkeypatch.setattr(
        observed_cache,
        "_icrs_catalogue_altaz",
        transform,
    )
    observer = SimpleNamespace(altaz_frame=object())

    first = observed_cache.catalogue_point_altaz(
        cache,
        observer,
        source_table=source,
        selected_table=source[[2, 0]],
        source_key=("catalogue", 1),
    )
    second = observed_cache.catalogue_point_altaz(
        cache,
        observer,
        source_table=source,
        selected_table=source[[1]],
        source_key=("catalogue", 1),
    )

    np.testing.assert_allclose(first[0], [300.0, 100.0])
    np.testing.assert_allclose(first[1], [3.0, 1.0])
    np.testing.assert_allclose(second[0], [200.0])
    assert len(calls) == 1
    cached_azimuth, cached_altitude = next(iter(cache.values()))
    assert cached_azimuth.flags.writeable is False
    assert cached_altitude.flags.writeable is False


def test_observer_and_source_revision_select_distinct_entries(monkeypatch):
    source = catalogue()
    cache = {}
    calls = []

    def transform(table, observer):
        calls.append(observer)
        return np.arange(len(table)), np.arange(len(table))

    monkeypatch.setattr(
        observed_cache,
        "_icrs_catalogue_altaz",
        transform,
    )
    first_observer = SimpleNamespace(altaz_frame=object())
    second_observer = SimpleNamespace(altaz_frame=object())

    for observer, revision in (
        (first_observer, 1),
        (first_observer, 2),
        (second_observer, 2),
    ):
        observed_cache.catalogue_point_altaz(
            cache,
            observer,
            source_table=source,
            selected_table=source,
            source_key=("catalogue", revision),
        )

    assert len(calls) == 3
    assert len(cache) == 3


def test_empty_selection_does_not_transform_or_populate_cache(monkeypatch):
    source = catalogue()
    cache = {}

    def unexpected(*args):
        raise AssertionError("empty selections must not transform")

    monkeypatch.setattr(
        observed_cache,
        "_icrs_catalogue_altaz",
        unexpected,
    )
    azimuth, altitude = observed_cache.catalogue_point_altaz(
        cache,
        SimpleNamespace(altaz_frame=object()),
        source_table=source,
        selected_table=source[:0],
        source_key=("catalogue", 1),
    )

    assert azimuth.size == altitude.size == 0
    assert cache == {}


def test_polygon_cache_builds_maximal_immutable_arrays_once():
    cache = {}
    observer = SimpleNamespace(altaz_frame=object())
    calls = []

    def build():
        calls.append(True)
        return ([1.0, 2.0], [3.0]), ([4.0, 5.0], [6.0])

    first = observed_cache.observed_polygon_arrays(
        cache,
        observer,
        source_key=("polygons", 1, 0.5),
        build=build,
    )
    second = observed_cache.observed_polygon_arrays(
        cache,
        observer,
        source_key=("polygons", 1, 0.5),
        build=build,
    )

    assert first is second
    assert len(calls) == 1
    assert all(
        array.flags.writeable is False
        for coordinate in first
        for array in coordinate
    )


def test_polygon_quality_selects_a_distinct_cache_entry():
    cache = {}
    observer = SimpleNamespace(altaz_frame=object())
    calls = []

    def build():
        calls.append(True)
        return ([1.0],), ([2.0],)

    for quality in (0.5, 0.25):
        observed_cache.observed_polygon_arrays(
            cache,
            observer,
            source_key=("boundaries", 1, quality),
            build=build,
        )

    assert len(calls) == 2
    assert len(cache) == 2


def test_warm_point_and_polygon_caches_follow_active_resources(monkeypatch):
    """Same site/time/path must not conceal changed effective backend inputs."""
    import erfa
    from astropy.utils import iers
    from astropy.coordinates import solar_system_ephemeris
    from astropy import units as u

    # Synthetic EOP table: the transform below is deliberately a test double.
    eop = Table({'MJD': [60000., 60001.], 'UT1_UTC': [.1, .2]})
    eop['UT1_UTC'].unit = u.s
    monkeypatch.setattr(iers.earth_orientation_table, 'get', lambda: eop)
    observer = SimpleNamespace(lat_deg=-33., lon_deg=-71., elevation_m=52.,
                               t_astropy=Time('2026-08-16T01:00:00'))
    source = catalogue()
    points, polygons, calls = {}, {}, []
    value = [1.]
    def transform(*args):
        calls.append(value[0])
        return np.full(3, value[0]), np.full(3, -value[0])
    monkeypatch.setattr(observed_cache, '_icrs_catalogue_altaz', transform)
    def evaluate():
        result = observed_cache.catalogue_point_altaz(points, observer,
            source_table=source, selected_table=source[[2, 0]], source_key='synthetic')
        outline = observed_cache.observed_polygon_arrays(polygons, observer,
            source_key='synthetic', build=lambda: (([value[0]],), ([-value[0]],)))
        np.testing.assert_array_equal(result[0], [value[0], value[0]])
        assert outline[0][0][0] == value[0]
    evaluate(); evaluate()
    assert len(calls) == len(points) == len(polygons) == 1
    # In-place EOP edits retain the exact same table object and provenance.
    value[0] = 2.; eop['UT1_UTC'][0] += .5
    evaluate()
    leaps = erfa.leap_seconds.get().copy()
    leaps['tai_utc'][-1] += 1  # synthetic key input only, never installed globally
    monkeypatch.setattr(erfa.leap_seconds, 'get', lambda: leaps)
    value[0] = 3.; evaluate()
    monkeypatch.setattr(solar_system_ephemeris, 'get', lambda: 'synthetic-other-backend')
    value[0] = 4.; evaluate()
    assert len(calls) == len(points) == len(polygons) == 4


def test_observer_resource_refusal_precedes_warm_cache(monkeypatch):
    import pytest
    source = catalogue(); cache = {}; polygons = {}; calls = []
    admitted = [True]
    def identity():
        if not admitted[0]:
            raise RuntimeError('synthetic closed resource')
        return 'synthetic admitted resource'
    observer = SimpleNamespace(geometry_resource_identity=identity)
    monkeypatch.setattr(observed_cache, '_icrs_catalogue_altaz',
                        lambda *a: (calls.append(1) or np.arange(3), np.arange(3)))
    def evaluate():
        return observed_cache.catalogue_point_altaz(cache, observer,
            source_table=source, selected_table=source, source_key='synthetic')
    evaluate()
    observed_cache.observed_polygon_arrays(polygons, observer, source_key='synthetic',
        build=lambda: (([1.],), ([2.],)))
    admitted[0] = False
    with pytest.raises(RuntimeError, match='closed resource'):
        evaluate()
    with pytest.raises(RuntimeError, match='closed resource'):
        observed_cache.observed_polygon_arrays(polygons, observer, source_key='synthetic',
            build=lambda: pytest.fail('refused resource must not build'))
    assert len(cache) == len(polygons) == len(calls) == 1


def test_skyfield_time_and_backend_replacement_invalidate_geometry_key():
    observer = SimpleNamespace(timescale=SimpleNamespace(
        leap_dates=np.array([1., 2.]), leap_offsets=np.array([10., 11.])),
        t=object(), skyfield=object(), ephemeris=object())
    first = observed_cache.observer_geometry_key(observer)
    observer.timescale.leap_offsets[0] += 1
    second = observed_cache.observer_geometry_key(observer)
    observer.skyfield = object()
    third = observed_cache.observer_geometry_key(observer)
    assert first != second != third


def test_frame_only_observer_key_tracks_the_context_consumed_by_service():
    from astropy.coordinates import AltAz, EarthLocation
    from astropy import units as u
    site = EarthLocation.from_geodetic(-71*u.deg, -33*u.deg, 52*u.m)
    observer = SimpleNamespace(altaz_frame=AltAz(obstime=Time('2017-01-02'), location=site))
    first = observed_cache.observer_geometry_key(observer)
    observer.altaz_frame = AltAz(obstime=Time('2017-01-03'), location=site)
    second = observed_cache.observer_geometry_key(observer)
    observer.altaz_frame = AltAz(obstime=Time('2017-01-03'),
        location=EarthLocation.from_geodetic(-70*u.deg, -33*u.deg, 52*u.m))
    assert first != second != observed_cache.observer_geometry_key(observer)
