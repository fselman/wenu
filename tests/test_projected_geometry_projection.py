import numpy as np
import pytest

from wenu.projected import (
    ProjectedCurve,
    ProjectedPoint,
    ProjectedPolygon,
)
from wenu.projection import StereographicProjection


@pytest.fixture
def projection():
    return StereographicProjection(
        radius=2.0,
        flip_ew=False,
    )


def test_project_point_returns_projected_point(
    projection,
):
    point = projection.project_point(
        lon_deg=0.0,
        lat_deg=90.0,
        name="tangent point",
    )

    assert isinstance(
        point,
        ProjectedPoint,
    )

    assert point.name == "tangent point"

    np.testing.assert_allclose(
        [point.x, point.y],
        [0.0, 0.0],
        atol=1.0e-12,
    )


def test_project_point_rejects_arrays(
    projection,
):
    with pytest.raises(
        ValueError,
        match="scalar",
    ):
        projection.project_point(
            lon_deg=[0.0, 10.0],
            lat_deg=[45.0, 45.0],
        )


def test_project_curve_returns_projected_curve(
    projection,
):
    curve = projection.project_curve(
        lon_deg=[0.0, 90.0, 180.0],
        lat_deg=[45.0, 45.0, 45.0],
        closed=False,
        name="test curve",
    )

    assert isinstance(
        curve,
        ProjectedCurve,
    )

    assert curve.name == "test curve"
    assert not curve.closed
    assert len(curve) == 3


def test_project_curve_matches_project_spherical(
    projection,
):
    lon_deg = np.array(
        [0.0, 45.0, 90.0]
    )

    lat_deg = np.array(
        [30.0, 45.0, 60.0]
    )

    expected_x, expected_y = (
        projection.project_spherical(
            lon_deg=lon_deg,
            lat_deg=lat_deg,
        )
    )

    curve = projection.project_curve(
        lon_deg=lon_deg,
        lat_deg=lat_deg,
    )

    np.testing.assert_allclose(
        curve.x,
        expected_x,
    )

    np.testing.assert_allclose(
        curve.y,
        expected_y,
    )


def test_project_curve_validates_matching_shapes(
    projection,
):
    with pytest.raises(
        ValueError,
        match="same shape",
    ):
        projection.project_curve(
            lon_deg=[0.0, 1.0],
            lat_deg=[0.0],
        )


def test_project_curve_validates_dimensions(
    projection,
):
    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        projection.project_curve(
            lon_deg=[[0.0, 1.0]],
            lat_deg=[[0.0, 1.0]],
        )


def test_project_polygon_returns_projected_polygon(
    projection,
):
    polygon = projection.project_polygon(
        lon_deg=[0.0, 120.0, 240.0],
        lat_deg=[45.0, 45.0, 45.0],
        name="triangle",
    )

    assert isinstance(
        polygon,
        ProjectedPolygon,
    )

    assert polygon.name == "triangle"
    assert len(polygon) == 3


def test_project_polygon_requires_three_vertices(
    projection,
):
    with pytest.raises(
        ValueError,
        match="at least three",
    ):
        projection.project_polygon(
            lon_deg=[0.0, 90.0],
            lat_deg=[45.0, 45.0],
        )


