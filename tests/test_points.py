"""Milestone 9 tests for geometry-only CelestialPoints."""

from types import SimpleNamespace

import numpy as np
import pytest
from astropy.coordinates import BarycentricTrueEcliptic
from astropy.time import Time

from wenu.sky import GeometricalObject, SkyLayer
from wenu.sky.points import CelestialPoints
from wenu.geometry.spherical import SphericalPoints


def make_observer(latitude=-33.0):
    return SimpleNamespace(
        icrs_frame="icrs",
        galactic_frame="galactic",
        ecliptic_frame="geocentrictrueecliptic",
        t=object(),
        t_astropy=object(),
        lat_deg=latitude,
        lon_deg=-71.5,
    )


def test_points_are_geometrical_sky_layer():
    assert issubclass(CelestialPoints, GeometricalObject)
    assert issubclass(CelestialPoints, SkyLayer)


def test_empty_collection_returns_empty_spherical_points():
    observer = make_observer()
    geometry = CelestialPoints(observer).spherical_geometry(observer)

    assert isinstance(geometry, SphericalPoints)
    assert len(geometry) == 0
    assert geometry.labels.size == 0


def test_single_point_returns_collection_and_style_metadata(monkeypatch):
    observer = make_observer()
    points = CelestialPoints(observer)
    points.add_equatorial_point(
        10.0,
        -20.0,
        label="test",
        marker="+",
        size=42.0,
        color="cyan",
        zorder=8,
        fontsize=11,
    )

    def fake_radec_to_altaz(ra, dec, t, lat, lon):
        np.testing.assert_allclose(ra, [10.0])
        np.testing.assert_allclose(dec, [-20.0])
        return np.asarray([35.0]), np.asarray([140.0])

    monkeypatch.setattr(
        "wenu.sky.points.radec_to_altaz",
        fake_radec_to_altaz,
    )
    geometry = points.spherical_geometry(observer)

    assert len(geometry) == 1
    np.testing.assert_allclose(geometry.lon_deg, [140.0])
    np.testing.assert_allclose(geometry.lat_deg, [35.0])
    np.testing.assert_array_equal(geometry.labels, ["test"])
    assert geometry.metadata["marker"][0] == "+"
    assert geometry.metadata["size"][0] == 42.0
    assert geometry.metadata["color"][0] == "cyan"
    assert geometry.metadata["zorder"][0] == 8
    assert geometry.metadata["style"][0]["fontsize"] == 11


def test_visible_pole_uses_observer_hemisphere():
    southern = CelestialPoints(make_observer(-33.0))
    northern = CelestialPoints(make_observer(20.0))

    southern.add_equatorial_pole()
    northern.add_equatorial_pole()

    assert southern._points[0].label == "SCP"
    assert southern._points[0].coord.dec.deg == -90.0
    assert northern._points[0].label == "NCP"
    assert northern._points[0].coord.dec.deg == 90.0


def test_ecliptic_cardinal_labels_are_preserved():
    points = CelestialPoints(make_observer())
    points.add_ecliptic_keypoints()

    assert [point.label for point in points._points] == [
        "♈",
        "♋",
        "♎",
        "♑",
    ]


def test_ecliptic_keypoints_accept_the_reference_grid_frame():
    points = CelestialPoints(make_observer())
    frame = BarycentricTrueEcliptic(equinox=Time("2026-08-16"))

    points.add_ecliptic_keypoints(frame=frame, marker="x")

    assert len(points) == 4
    assert all(
        point.coord.frame.is_equivalent_frame(frame)
        for point in points._points
    )
    assert all(point.marker == "x" for point in points._points)


def test_clear_preserves_collection_api():
    points = CelestialPoints(make_observer())
    points.add_equatorial_point(0.0, 0.0)
    assert len(points) == 1

    assert points.clear() is points
    assert len(points) == 0


def test_domain_layer_has_no_projection_or_rendering_api():
    points = CelestialPoints(make_observer())
    for name in ("draw", "project", "artist", "artists"):
        assert not hasattr(points, name)
