import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PathCollection
from matplotlib.text import Text
from types import SimpleNamespace

from wenu.projected import ProjectedPoint
from wenu.sky.points import CelestialPoints


class DummyProjection:
    def __init__(self):
        self.calls = []

    def project_point(
        self,
        lon_deg,
        lat_deg,
        *,
        name=None,
    ):
        self.calls.append(
            {
                "lon_deg": lon_deg,
                "lat_deg": lat_deg,
                "name": name,
            }
        )

        return ProjectedPoint(
            x=float(lon_deg),
            y=float(lat_deg),
            name=name,
        )


def make_observer():
    return SimpleNamespace(
        icrs_frame="icrs",
        t=object(),
        lat_deg=-33.0,
        lon_deg=-71.5,
    )


def test_point_below_horizon_is_not_rendered(
    monkeypatch,
):
    observer = make_observer()
    points = CelestialPoints(observer)

    points.add_equatorial_point(
        ra_deg=0.0,
        dec_deg=0.0,
        label="hidden",
    )

    def fake_radec_to_altaz(
        ra_deg,
        dec_deg,
        t,
        lat_deg,
        lon_deg,
    ):
        return -5.0, 120.0

    monkeypatch.setattr(
        "wenu.sky.points.radec_to_altaz",
        fake_radec_to_altaz,
    )

    projection = DummyProjection()

    fig, ax = plt.subplots()

    artists = points.draw(
        ax,
        projection,
    )

    assert artists == []
    assert projection.calls == []

    plt.close(fig)


def test_visible_unlabelled_point_creates_marker(
    monkeypatch,
):
    observer = make_observer()
    points = CelestialPoints(observer)

    points.add_equatorial_point(
        ra_deg=10.0,
        dec_deg=-20.0,
    )

    def fake_radec_to_altaz(
        ra_deg,
        dec_deg,
        t,
        lat_deg,
        lon_deg,
    ):
        return 35.0, 140.0

    monkeypatch.setattr(
        "wenu.sky.points.radec_to_altaz",
        fake_radec_to_altaz,
    )

    projection = DummyProjection()

    fig, ax = plt.subplots()

    artists = points.draw(
        ax,
        projection,
    )

    assert len(artists) == 1
    assert isinstance(
        artists[0],
        PathCollection,
    )

    plt.close(fig)


def test_visible_labelled_point_creates_marker_and_text(
    monkeypatch,
):
    observer = make_observer()
    points = CelestialPoints(observer)

    points.add_equatorial_point(
        ra_deg=10.0,
        dec_deg=-20.0,
        label="test point",
    )

    def fake_radec_to_altaz(
        ra_deg,
        dec_deg,
        t,
        lat_deg,
        lon_deg,
    ):
        return 35.0, 140.0

    monkeypatch.setattr(
        "wenu.sky.points.radec_to_altaz",
        fake_radec_to_altaz,
    )

    projection = DummyProjection()

    fig, ax = plt.subplots()

    artists = points.draw(
        ax,
        projection,
    )

    assert len(artists) == 2

    assert isinstance(
        artists[0],
        PathCollection,
    )

    assert isinstance(
        artists[1],
        Text,
    )

    assert artists[1].get_text() == "test point"

    plt.close(fig)


def test_point_projection_uses_azimuth_as_longitude_and_altitude_as_latitude(
    monkeypatch,
):
    observer = make_observer()
    points = CelestialPoints(observer)

    points.add_equatorial_point(
        ra_deg=10.0,
        dec_deg=-20.0,
        label="test point",
    )

    def fake_radec_to_altaz(
        ra_deg,
        dec_deg,
        t,
        lat_deg,
        lon_deg,
    ):
        np.testing.assert_allclose(
            ra_deg,
            10.0,
        )
        np.testing.assert_allclose(
            dec_deg,
            -20.0,
        )

        assert t is observer.t
        assert lat_deg == observer.lat_deg
        assert lon_deg == observer.lon_deg

        return 35.0, 140.0

    monkeypatch.setattr(
        "wenu.sky.points.radec_to_altaz",
        fake_radec_to_altaz,
    )

    projection = DummyProjection()

    fig, ax = plt.subplots()

    points.draw(
        ax,
        projection,
    )

    assert len(projection.calls) == 1

    call = projection.calls[0]

    assert call["lon_deg"] == 140.0
    assert call["lat_deg"] == 35.0
    assert call["name"] == "test point"

    plt.close(fig)


