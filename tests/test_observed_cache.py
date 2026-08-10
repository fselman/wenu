"""Observer-dependent catalogue cache contracts."""

from types import SimpleNamespace

import numpy as np
from astropy.table import Table

from wenu.sky import observed_cache


def catalogue():
    return Table(
        {
            "identifier": ["one", "two", "three"],
            "ra_deg": [10.0, 20.0, 30.0],
            "dec_deg": [-10.0, -20.0, -30.0],
        }
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
