"""Polar azimuthal-equidistant projection contracts."""

import numpy as np
import pytest

from wenu import PolarAzimuthalEquidistantProjection
from wenu.coordinates import GENERIC_SPHERICAL_SPEC

from wenu.geometry.projected import (
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPoints,
    ProjectedPolygons,
)
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


def projection(**kwargs):
    kwargs.setdefault("flip_ew", False)
    return PolarAzimuthalEquidistantProjection(
        radius=2.0,
        **kwargs,
    )


@pytest.mark.parametrize(
    ("pole", "latitudes"),
    (("north", [90.0, 0.0]), ("south", [-90.0, 0.0])),
)
def test_pole_and_equatorial_quadrants(pole, latitudes):
    value = projection(pole=pole)
    x, y = value.project_spherical(
        [123.0, 0.0, 90.0, 180.0, -90.0],
        [latitudes[0], *([latitudes[1]] * 4)],
    )

    assert (x[0], y[0]) == pytest.approx((0.0, 0.0), abs=1.0e-12)
    np.testing.assert_allclose(
        np.column_stack((x[1:], y[1:])),
        [[0.0, 2.0], [2.0, 0.0], [0.0, -2.0], [-2.0, 0.0]],
        atol=1.0e-12,
    )


@pytest.mark.parametrize("pole", ("north", "south"))
def test_forward_inverse_round_trip(pole):
    value = projection(
        pole=pole,
        position_angle_deg=17.0,
        flip_ew=True,
    )
    longitude = np.array([-170.0, -45.0, 0.0, 80.0, 179.0])
    latitude = (
        np.array([70.0, 30.0, 0.0, -30.0, -70.0])
        if pole == "north"
        else np.array([-70.0, -30.0, 0.0, 30.0, 70.0])
    )

    x, y = value.project_spherical(longitude, latitude)
    restored = value.unproject_spherical(x, y)

    np.testing.assert_allclose(restored.lon_deg, longitude, atol=1.0e-12)
    np.testing.assert_allclose(restored.lat_deg, latitude, atol=1.0e-12)


@pytest.mark.parametrize(
    ("pole", "latitudes"),
    (("north", [70.0, 50.0, 30.0]), ("south", [-70.0, -50.0, -30.0])),
)
def test_radial_spacing_is_linear_in_declination(pole, latitudes):
    x, y = projection(pole=pole).project_spherical(0.0, latitudes)

    np.testing.assert_allclose(
        np.diff(np.hypot(x, y)),
        [2.0 / 4.5, 2.0 / 4.5],
        atol=1.0e-12,
    )


def test_position_angle_precedes_east_west_flip():
    normal = projection(position_angle_deg=90.0)
    flipped = PolarAzimuthalEquidistantProjection(
        radius=2.0,
        flip_ew=True,
        position_angle_deg=90.0,
    )

    normal_x, normal_y = normal.project_spherical(0.0, 0.0)
    flipped_x, flipped_y = flipped.project_spherical(0.0, 0.0)

    assert (normal_x, normal_y) == pytest.approx((-2.0, 0.0), abs=1.0e-12)
    assert flipped_x == pytest.approx(-normal_x)
    assert flipped_y == pytest.approx(normal_y)


def test_radius_conversions_and_viewport_are_linear():
    value = projection()

    assert value.projected_radius(45.0) == pytest.approx(1.0)
    assert value.projected_radius(90.0) == pytest.approx(2.0)
    assert value.angular_radius_for_projected_radius(3.0) == pytest.approx(
        135.0
    )
    viewport = value.viewport_for_angular_radius(90.0)
    assert (
        viewport.x_min,
        viewport.x_max,
        viewport.y_min,
        viewport.y_max,
    ) == pytest.approx(
        (-2.0, 2.0, -2.0, 2.0)
    )


def test_projection_rejects_invalid_configuration_and_domain():
    with pytest.raises(ValueError, match="positive"):
        PolarAzimuthalEquidistantProjection(radius=0.0)
    with pytest.raises(ValueError, match="finite"):
        PolarAzimuthalEquidistantProjection(radius=np.nan)
    with pytest.raises(ValueError, match="pole"):
        projection(pole="east")
    with pytest.raises(ValueError, match="position_angle_deg"):
        projection(position_angle_deg=np.nan)
    with pytest.raises(ValueError, match="latitude"):
        projection().project_spherical(0.0, 91.0)
    with pytest.raises(ValueError, match="longitude"):
        projection().project_spherical(np.nan, 0.0)
    with pytest.raises(ValueError, match="opposite pole"):
        projection().project_spherical(0.0, -90.0)
    with pytest.raises(ValueError, match="between"):
        projection().projected_radius(180.0)
    with pytest.raises(ValueError, match="twice"):
        projection().angular_radius_for_projected_radius(4.0)
    with pytest.raises(ValueError, match="domain"):
        projection().unproject_spherical(4.0, 0.0)


def test_geometry_dispatch_preserves_types_and_metadata():
    value = projection()
    points = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=[0.0],
        lat_deg=[30.0],
        ids=[1],
        labels=["A"],
        names=["alpha"],
        metadata={"kind": "points"},
    )
    curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([0.0, 10.0],),
        lat_deg=([30.0, 30.0],),
        names=["curve"],
    )
    polygons = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([0.0, 10.0, 5.0],),
        lat_deg=([30.0, 30.0, 40.0],),
        names=["polygon"],
    )
    grid = SphericalGrid(coordinate_spec=GENERIC_SPHERICAL_SPEC, components={"meridians": curves})

    projected_points = value.project_geometry(points)
    projected_curves = value.project_geometry(curves)
    projected_polygons = value.project_geometry(polygons)
    projected_grid = value.project_geometry(grid)

    assert isinstance(projected_points, ProjectedPoints)
    assert isinstance(projected_curves, ProjectedCurves)
    assert isinstance(projected_polygons, ProjectedPolygons)
    assert isinstance(projected_grid, ProjectedGrid)
    assert projected_points.metadata == {"kind": "points"}
    np.testing.assert_array_equal(projected_points.ids, [1])
    assert projected_curves[0].name == "curve"
    assert projected_polygons[0].name == "polygon"
    assert set(projected_grid.components) == {"meridians"}

