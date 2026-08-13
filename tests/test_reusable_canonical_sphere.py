"""Family-spanning contracts for one reusable canonical celestial sphere."""

from dataclasses import fields
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from wenu import Observer, generate_celestial_sphere, get_chart_view
from wenu.charts.detail import SkyContentSelection
from wenu.sky.observed_cache import observer_geometry_key


VIEW_REQUESTS = (
    (
        "planisphere",
        {
            "family": "planisphere",
            "constellations": ("Cru", "Cen"),
            "mask": True,
        },
    ),
    (
        "regional-single",
        {
            "family": "regional",
            "constellations": ("Cru",),
            "mask": True,
        },
    ),
    (
        "regional-group",
        {
            "family": "regional",
            "group": "galactic-center",
        },
    ),
    (
        "circumpolar",
        {
            "family": "circumpolar",
            "pole": "south",
            "limiting_declination_deg": -69.75,
        },
    ),
    (
        "binocular",
        {
            "family": "binocular",
            "target": "omega-centauri",
            "field_diameter_deg": 6.5,
        },
    ),
    ("all-sky", {"family": "all_sky"}),
)


@pytest.fixture(scope="module")
def canonical_sphere():
    return generate_celestial_sphere()


@pytest.fixture(scope="module")
def observers():
    values = (
        Observer(location="La Ligua", time="2026-08-15 21:00"),
        Observer(location="La Ligua", time="2026-08-16 00:00"),
        Observer(location="Papudo", time="2026-08-15 21:00"),
    )
    yield values
    for observer in values:
        observer.close()


def _content_summary(view):
    content = view._prepared.resolved.request.content
    return tuple(
        (field.name, getattr(content, field.name))
        for field in fields(SkyContentSelection)
    )


def _view_summary(view):
    return (
        view.family,
        view.mask,
        None if view.target is None else view.target.key,
        (
            None
            if view.constellations is None
            else view.constellations.key
        ),
        view.frame,
        _content_summary(view),
    )


@pytest.mark.integration
def test_every_chart_family_prepares_from_one_observer_independent_sphere(
    canonical_sphere,
    observers,
):
    observer = observers[0]
    canonical_layers = canonical_sphere.layers

    views = {
        name: get_chart_view(canonical_sphere, observer, **arguments)
        for name, arguments in VIEW_REQUESTS
    }

    assert canonical_sphere.observer is None
    assert all(view.sky is canonical_sphere for view in views.values())
    assert all(view.observer is observer for view in views.values())
    assert canonical_sphere.layers == canonical_layers
    assert views["planisphere"].constellations.key == "cru+cen"
    assert views["planisphere"].mask is True
    assert views["regional-single"].constellations.key == "cru"
    assert views["regional-single"].mask is True
    assert views["regional-group"].constellations.key == "galactic-center"
    assert views["circumpolar"].frame.pole == "south"
    assert views["binocular"].target.key == "omega-centauri"
    assert views["all-sky"].coordinate_frame == "galactic"


@pytest.mark.integration
def test_family_order_does_not_change_selection_subjects_or_masks(
    canonical_sphere,
    observers,
):
    observer = observers[0]
    canonical_layers = canonical_sphere.layers

    forward = {
        name: _view_summary(
            get_chart_view(canonical_sphere, observer, **arguments)
        )
        for name, arguments in VIEW_REQUESTS
    }
    reverse = {
        name: _view_summary(
            get_chart_view(canonical_sphere, observer, **arguments)
        )
        for name, arguments in reversed(VIEW_REQUESTS)
    }

    assert reverse == forward
    assert canonical_sphere.layers == canonical_layers


@pytest.mark.integration
def test_observers_and_instants_use_separate_reusable_observed_caches(
    canonical_sphere,
    observers,
):
    stars = canonical_sphere.stars

    first = stars.observed_altaz(observers[0])
    later = stars.observed_altaz(observers[1])
    papudo = stars.observed_altaz(observers[2])
    repeated = stars.observed_altaz(observers[0])

    assert repeated[1] is first[1]
    assert repeated[2] is first[2]
    assert later[1] is not first[1]
    assert papudo[1] is not first[1]
    keys = {
        key[0]
        for key in stars._observed_altaz_cache
    }
    assert {
        observer_geometry_key(observer)
        for observer in observers
    } <= keys
    assert canonical_sphere.observer is None


def test_observed_cache_identity_includes_ephemeris():
    common = {
        "lat_deg": -32.443342,
        "lon_deg": -71.230289,
        "elevation_m": 52.0,
        "utc_datetime": datetime(
            2026, 8, 16, 1, 0, tzinfo=timezone.utc
        ),
        "data_directory": "/tmp/wenu-cache",
    }
    first = SimpleNamespace(ephemeris_name="de440s.bsp", **common)
    second = SimpleNamespace(ephemeris_name="de421.bsp", **common)

    assert observer_geometry_key(first) != observer_geometry_key(second)
