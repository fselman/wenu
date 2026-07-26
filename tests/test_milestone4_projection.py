import numpy as np
import pytest

from wenu.geometry.clipping import (
    clip_curve_to_viewport,
    clip_polygon_to_viewport,
)
from wenu.geometry.projected import ProjectedCurve, ProjectedPolygon
from wenu.projection import StereographicProjection
from wenu.geometry.spherical import SphericalPoints
from wenu.geometry.frame import SphericalFrame


def test_default_frame_preserves_existing_projection_exactly():
    lon_deg = np.array([0.0, 30.0, 90.0, 180.0])
    lat_deg = np.array([90.0, 60.0, 30.0, 0.0])

    projection = StereographicProjection(
        radius=2.0,
        flip_ew=True,
    )

    actual_x, actual_y = projection.project_spherical(
        lon_deg,
        lat_deg,
    )

    radius = 2.0 * np.tan(
        (np.pi / 2.0 - np.radians(lat_deg)) / 2.0
    )
    expected_x = -radius * np.sin(np.radians(lon_deg))
    expected_y = radius * np.cos(np.radians(lon_deg))

    np.testing.assert_array_equal(actual_x, expected_x)
    np.testing.assert_array_equal(actual_y, expected_y)


def test_arbitrary_tangent_point_maps_to_origin():
    frame = SphericalFrame(
        pole_lon_deg=123.0,
        pole_lat_deg=-37.0,
    )
    projection = StereographicProjection(
        flip_ew=False,
        frame=frame,
    )

    point = projection.project_point(123.0, -37.0)

    assert point.x == pytest.approx(0.0, abs=1e-7)
    assert point.y == pytest.approx(0.0, abs=1e-7)


def test_arbitrary_frame_applies_to_geometry_collections():
    frame = SphericalFrame(
        pole_lon_deg=45.0,
        pole_lat_deg=20.0,
    )
    projection = StereographicProjection(
        flip_ew=False,
        frame=frame,
    )
    points = SphericalPoints(
        lon_deg=[45.0],
        lat_deg=[20.0],
        ids=["center"],
    )

    projected = projection.project_geometry(points)

    assert projected.x[0] == pytest.approx(0.0, abs=1e-7)
    assert projected.y[0] == pytest.approx(0.0, abs=1e-7)
    assert projected.ids[0] == "center"


def test_zero_position_angle_places_source_north_on_positive_y():
    frame = SphericalFrame(
        pole_lon_deg=0.0,
        pole_lat_deg=0.0,
        position_angle_deg=0.0,
    )
    projection = StereographicProjection(
        radius=2.0,
        flip_ew=False,
        frame=frame,
    )

    x, y = projection.project_spherical(0.0, 30.0)

    assert x == pytest.approx(0.0, abs=1e-14)
    assert y > 0.0


def test_positive_position_angle_rotates_north_toward_negative_x():
    zero = StereographicProjection(
        radius=2.0,
        flip_ew=False,
        frame=SphericalFrame(
            pole_lon_deg=0.0,
            pole_lat_deg=0.0,
            position_angle_deg=0.0,
        ),
    )
    rotated = StereographicProjection(
        radius=2.0,
        flip_ew=False,
        frame=SphericalFrame(
            pole_lon_deg=0.0,
            pole_lat_deg=0.0,
            position_angle_deg=90.0,
        ),
    )

    zero_x, zero_y = zero.project_spherical(0.0, 30.0)
    rotated_x, rotated_y = rotated.project_spherical(0.0, 30.0)

    assert zero_x == pytest.approx(0.0, abs=1e-14)
    assert zero_y > 0.0
    assert rotated_x == pytest.approx(-zero_y, abs=1e-14)
    assert rotated_y == pytest.approx(0.0, abs=1e-14)
    assert np.hypot(rotated_x, rotated_y) == pytest.approx(
        np.hypot(zero_x, zero_y)
    )


def test_angular_radius_conversion_and_viewport():
    projection = StereographicProjection(radius=3.0)

    assert projection.projected_radius(90.0) == pytest.approx(3.0)

    viewport = projection.viewport_for_angular_radius(60.0)
    expected_radius = 3.0 * np.tan(np.radians(30.0))

    assert viewport.xlim == pytest.approx(
        (-expected_radius, expected_radius)
    )
    assert viewport.ylim == pytest.approx(
        (-expected_radius, expected_radius)
    )


@pytest.mark.parametrize(
    "angular_radius_deg",
    [0.0, -1.0, 180.0, 181.0, np.nan, np.inf],
)
def test_invalid_angular_radius_is_rejected(angular_radius_deg):
    projection = StereographicProjection()

    with pytest.raises(ValueError, match="between 0 and 180"):
        projection.projected_radius(angular_radius_deg)


def test_regional_viewport_clips_crossing_curve_and_polygon():
    projection = StereographicProjection(
        radius=2.0,
        flip_ew=False,
    )
    viewport = projection.viewport_for_angular_radius(30.0)
    limit = projection.projected_radius(30.0)

    curve = ProjectedCurve(
        x=[-2.0 * limit, 2.0 * limit],
        y=[0.0, 0.0],
        name="crossing",
    )
    polygon = ProjectedPolygon(
        x=[-2.0 * limit, 2.0 * limit, 2.0 * limit, -2.0 * limit],
        y=[-0.5 * limit, -0.5 * limit, 0.5 * limit, 0.5 * limit],
        name="crossing",
    )

    clipped_curves = clip_curve_to_viewport(curve, viewport)
    clipped_polygon = clip_polygon_to_viewport(polygon, viewport)

    assert len(clipped_curves) == 1
    assert clipped_curves[0].bounds == pytest.approx(
        (-limit, limit, 0.0, 0.0)
    )
    assert clipped_curves[0].name == "crossing"
    assert clipped_polygon is not None
    assert clipped_polygon.bounds == pytest.approx(
        (-limit, limit, -0.5 * limit, 0.5 * limit)
    )
    assert clipped_polygon.name == "crossing"


def test_frame_argument_validation():
    with pytest.raises(TypeError, match="SphericalFrame"):
        StereographicProjection(frame=object())
