"""Chart-owned astronomical coordinate-frame transformations."""

from types import SimpleNamespace

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, Galactic, ICRS, SkyCoord
from astropy.time import Time
import numpy as np
import pytest

from wenu.coordinates import GENERIC_SPHERICAL_SPEC

from wenu.charts.coordinate_frames import (
    horizontal_to_equatorial,
    horizontal_to_galactic,
)
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


def observer(*, time, latitude, longitude):
    location = EarthLocation.from_geodetic(
        lon=longitude * u.deg,
        lat=latitude * u.deg,
        height=50.0 * u.m,
    )
    return SimpleNamespace(
        altaz_frame=AltAz(obstime=Time(time), location=location),
        galactic_frame=Galactic(),
        icrs_frame=ICRS(),
    )


def horizontal_points(coordinates, actual_observer):
    horizontal = coordinates.transform_to(actual_observer.altaz_frame)
    return SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=horizontal.az.deg,
        lat_deg=horizontal.alt.deg,
        ids=("a", "b"),
        labels=("A", "B"),
        names=("Alpha", "Beta"),
        metadata={"catalogue": "test"},
    )


def test_galactic_result_is_invariant_across_observers_and_instants():
    fixed = SkyCoord(
        ra=[266.4051, 83.6331] * u.deg,
        dec=[-28.936175, 22.0145] * u.deg,
        frame="icrs",
    )
    observers = (
        observer(
            time="2026-08-16T01:00:00",
            latitude=-32.443342,
            longitude=-71.230289,
        ),
        observer(
            time="2026-02-10T12:00:00",
            latitude=19.8207,
            longitude=-155.4681,
        ),
    )
    transformed = tuple(
        horizontal_to_galactic(
            horizontal_points(fixed, value), value
        )
        for value in observers
    )
    expected = fixed.galactic

    for result in transformed:
        np.testing.assert_allclose(
            result.lon_deg, expected.l.deg, atol=1.0e-7
        )
        np.testing.assert_allclose(
            result.lat_deg, expected.b.deg, atol=1.0e-7
        )
        assert result.metadata == {
            "catalogue": "test",
            "source_coordinate_system": "altaz",
            "coordinate_system": "galactic",
        }
    np.testing.assert_allclose(
        transformed[0].lon_deg, transformed[1].lon_deg, atol=1.0e-7
    )
    np.testing.assert_allclose(
        transformed[0].lat_deg, transformed[1].lat_deg, atol=1.0e-7
    )


def test_equatorial_result_recovers_observer_independent_icrs():
    fixed = SkyCoord(
        ra=[0.0, 83.6331, 266.4051] * u.deg,
        dec=[-60.0, 22.0145, -28.936175] * u.deg,
        frame="icrs",
    )
    actual_observer = observer(
        time="2026-08-16T01:00:00",
        latitude=-32.443342,
        longitude=-71.230289,
    )
    horizontal = fixed.transform_to(actual_observer.altaz_frame)
    points = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=horizontal.az.deg,
        lat_deg=horizontal.alt.deg,
        metadata={"catalogue": "test"},
    )

    transformed = horizontal_to_equatorial(points, actual_observer)

    np.testing.assert_allclose(transformed.lon_deg, fixed.ra.deg, atol=1e-7)
    np.testing.assert_allclose(transformed.lat_deg, fixed.dec.deg, atol=1e-7)
    assert transformed.metadata == {
        "catalogue": "test",
        "source_coordinate_system": "altaz",
        "coordinate_system": "equatorial",
    }


def test_curve_polygon_and_grid_structure_and_identity_are_preserved():
    actual_observer = observer(
        time="2026-08-16T01:00:00",
        latitude=-32.443342,
        longitude=-71.230289,
    )
    curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([10.0, 20.0], [30.0, 40.0, 50.0]),
        lat_deg=([5.0, 6.0], [7.0, 8.0, 9.0]),
        closed=(False, True),
        ids=("c1", "c2"),
        names=("first", "second"),
        metadata={"kind": "curves"},
    )
    polygons = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([10.0, 20.0, 15.0],),
        lat_deg=([5.0, 5.0, 10.0],),
        names=("region",),
        metadata={"kind": "polygons"},
    )
    grid = SphericalGrid(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        components={"meridians": curves},
        metadata={"kind": "grid"},
    )

    transformed_curves = horizontal_to_galactic(
        curves, actual_observer
    )
    transformed_polygons = horizontal_to_galactic(
        polygons, actual_observer
    )
    transformed_grid = horizontal_to_galactic(grid, actual_observer)

    assert tuple(map(len, transformed_curves.lon_deg)) == (2, 3)
    np.testing.assert_array_equal(transformed_curves.closed, [False, True])
    np.testing.assert_array_equal(transformed_curves.ids, ["c1", "c2"])
    np.testing.assert_array_equal(
        transformed_curves.names, ["first", "second"]
    )
    assert len(transformed_polygons) == 1
    assert len(transformed_polygons.lon_deg[0]) == 3
    assert tuple(transformed_grid.components) == ("meridians",)
    assert transformed_grid["meridians"].metadata["kind"] == "curves"
    assert transformed_grid.metadata["coordinate_system"] == "galactic"


def test_empty_collections_and_invalid_inputs_are_explicit():
    actual_observer = observer(
        time="2026-08-16T01:00:00",
        latitude=-32.443342,
        longitude=-71.230289,
    )
    empty = horizontal_to_galactic(
        SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC, lon_deg=(), lat_deg=()), actual_observer
    )

    assert len(empty) == 0
    with pytest.raises(TypeError, match="Unsupported spherical geometry"):
        horizontal_to_galactic(object(), actual_observer)
    with pytest.raises(TypeError, match="altaz_frame and galactic_frame"):
        horizontal_to_galactic(
            SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC, lon_deg=[0.0], lat_deg=[0.0]), object()
        )
    with pytest.raises(TypeError, match="altaz_frame and icrs_frame"):
        horizontal_to_equatorial(
            SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC, lon_deg=[0.0], lat_deg=[0.0]), object()
        )
