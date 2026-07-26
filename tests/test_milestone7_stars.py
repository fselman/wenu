"""Milestone 7 tests for AstronomicalObject and Stars."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from wenu.objects.astronomical_object import AstronomicalObject
from wenu.objects.stars import Stars
from wenu.sky import SkyLayer
from wenu.geometry.spherical import SphericalPoints


class FakeAngle:
    def __init__(self, degrees):
        self.degrees = np.asarray(degrees, dtype=float)


class FakeApparent:
    def __init__(self, alt, az):
        self.alt = alt
        self.az = az

    def apparent(self, deflectors):
        assert deflectors == []
        return self

    def altaz(self):
        return FakeAngle(self.alt), FakeAngle(self.az), None


class FakeAt:
    def __init__(self, apparent):
        self.apparent_result = apparent

    def observe(self, stars):
        return self.apparent_result


class FakeSkyfieldObserver:
    def __init__(self, apparent):
        self.apparent = apparent

    def at(self, time):
        return FakeAt(self.apparent)


def make_stars():
    apparent = FakeApparent(
        alt=[20.0, -20.0, 40.0],
        az=[100.0, 200.0, 300.0],
    )
    observer = SimpleNamespace(
        skyfield=FakeSkyfieldObserver(apparent),
        t=object(),
    )
    stars = Stars(observer=observer)
    stars.catalog = pd.DataFrame(
        {
            "ra_hours": [1.0, 2.0, 3.0],
            "dec_degrees": [-10.0, -20.0, -30.0],
            "magnitude": [1.0, 2.0, 3.0],
        },
        index=[100, 200, 300],
    )
    stars.hip_df = stars.catalog.copy()
    stars.skyfield_stars = object()
    return stars, observer


def test_astronomical_object_is_abstract_sky_layer():
    assert issubclass(AstronomicalObject, SkyLayer)

    with pytest.raises(TypeError):
        AstronomicalObject()


def test_stars_is_concrete_astronomical_object():
    stars, _ = make_stars()

    assert isinstance(stars, AstronomicalObject)
    assert isinstance(stars, SkyLayer)
    assert stars.layer_name == "stars"


def test_stars_returns_aligned_spherical_points():
    stars, observer = make_stars()

    geometry = stars.spherical_geometry(
        observer,
        alt_min=0.0,
    )

    assert isinstance(geometry, SphericalPoints)
    np.testing.assert_allclose(geometry.lon_deg, [100.0, 300.0])
    np.testing.assert_allclose(geometry.lat_deg, [20.0, 40.0])
    np.testing.assert_array_equal(geometry.ids, [100, 300])
    np.testing.assert_allclose(
        geometry.metadata["magnitude"],
        [1.0, 3.0],
    )
    assert geometry.metadata["catalog"] == "hipparcos"


def test_spherical_geometry_preserves_hip_lookup():
    stars, observer = make_stars()

    stars.spherical_geometry(observer, alt_min=0.0)

    assert stars.hip_index == {100: 0, 300: 1}


def test_repeated_geometry_starts_from_stable_catalogue():
    stars, observer = make_stars()

    first = stars.spherical_geometry(observer, alt_min=0.0)
    second = stars.spherical_geometry(observer, alt_min=-30.0)

    assert len(first) == 2
    assert len(second) == 3
    assert len(stars.catalog) == 3


def test_stars_contains_no_projection_or_rendering_api():
    stars, _ = make_stars()

    for name in (
        "draw",
        "project",
        "prepare",
        "compute_sizes",
        "projection",
        "artist",
        "x",
        "y",
        "sizes",
    ):
        assert not hasattr(stars, name)

