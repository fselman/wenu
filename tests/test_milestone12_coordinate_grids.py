"""Milestone 12 domain tests for coordinate grids."""

from types import SimpleNamespace

import numpy as np

from wenu.sky.coordinate_grids import (
    CoordinatesGrid,
    SphericalCoordinatesGrid,
)
from wenu.sky.geometrical_object import GeometricalObject
from wenu.geometry.spherical import SphericalCurves, SphericalGrid


class StubGrid(CoordinatesGrid):
    coordinate_system = "test"

    def _native_to_icrs(self, longitude_deg, latitude_deg):
        return (
            np.asarray(longitude_deg) + 10.0,
            np.asarray(latitude_deg) - 5.0,
        )


def observer(time):
    return SimpleNamespace(
        t=time,
        lat_deg=-33.0,
        lon_deg=-71.5,
    )


def test_grid_hierarchy_and_compatibility_alias():
    assert issubclass(CoordinatesGrid, GeometricalObject)
    assert SphericalCoordinatesGrid is CoordinatesGrid


def test_parallel_and_meridian_return_spherical_collections(monkeypatch):
    grid = StubGrid(observer(1.0), samples=5)

    def fake_transform(ra, dec, time, lat, lon):
        return np.asarray(dec) + time, np.asarray(ra) + time

    monkeypatch.setattr(
        "wenu.sky.coordinate_grids.radec_to_altaz",
        fake_transform,
    )
    parallel = grid.parallel(20.0, style={"linewidth": 1.5})
    meridian = grid.meridian(30.0)

    assert isinstance(parallel, SphericalCurves)
    assert isinstance(meridian, SphericalCurves)
    assert len(parallel) == len(meridian) == 1
    assert parallel.closed.tolist() == [True]
    assert meridian.closed.tolist() == [False]
    assert parallel.metadata["styles"] == ({"linewidth": 1.5},)


def test_complete_grid_preserves_component_groups(monkeypatch):
    monkeypatch.setattr(
        "wenu.sky.coordinate_grids.radec_to_altaz",
        lambda ra, dec, *args: (np.asarray(dec), np.asarray(ra)),
    )
    geometry = StubGrid(observer(0.0), samples=5).grid(
        longitudes=[0.0, 90.0],
        latitudes=[-30.0, 30.0],
    )

    assert isinstance(geometry, SphericalGrid)
    assert set(geometry.components) == {"meridians", "parallels"}
    assert len(geometry["meridians"]) == 2
    assert len(geometry["parallels"]) == 2
    assert geometry.metadata["coordinate_system"] == "test"


def test_coordinate_geometry_uses_observer_time(monkeypatch):
    def fake_transform(ra, dec, time, lat, lon):
        return np.asarray(dec) + time, np.asarray(ra) + time

    monkeypatch.setattr(
        "wenu.sky.coordinate_grids.radec_to_altaz",
        fake_transform,
    )
    first = StubGrid(observer(1.0), samples=5).parallel(0.0)
    second = StubGrid(observer(4.0), samples=5).parallel(0.0)

    np.testing.assert_allclose(
        second.lon_deg[0] - first.lon_deg[0],
        3.0,
    )
    np.testing.assert_allclose(
        second.lat_deg[0] - first.lat_deg[0],
        3.0,
    )

