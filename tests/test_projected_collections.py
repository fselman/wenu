import numpy as np
import pytest

from wenu.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPoint,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)


def test_projected_points_are_vectorized_not_point_wrappers():
    points = ProjectedPoints(
        x=[0.0, 1.0, np.nan],
        y=[2.0, 3.0, 4.0],
        metadata={"catalogue": "hipparcos"},
    )

    assert len(points) == 3
    assert isinstance(points.x, np.ndarray)
    assert not isinstance(points.x[0], ProjectedPoint)
    np.testing.assert_array_equal(points.finite, [True, True, False])
    assert points.bounds == (0.0, 1.0, 2.0, 3.0)
    assert points.metadata == {"catalogue": "hipparcos"}


def test_projected_points_require_matching_one_dimensional_arrays():
    with pytest.raises(ValueError, match="one-dimensional"):
        ProjectedPoints(x=[[0.0, 1.0]], y=[[2.0, 3.0]])

    with pytest.raises(ValueError, match="same shape"):
        ProjectedPoints(x=[0.0, 1.0], y=[2.0])


def test_projected_curves_wrap_singular_curves_and_copy_metadata():
    curve = ProjectedCurve(x=[0.0, 1.0], y=[2.0, 3.0])
    metadata = {"frame": "icrs"}
    curves = ProjectedCurves(items=[curve], metadata=metadata)
    metadata["frame"] = "galactic"

    assert list(curves) == [curve]
    assert curves[0] is curve
    assert curves.metadata == {"frame": "icrs"}


def test_projected_curves_reject_non_curve_items():
    with pytest.raises(TypeError, match="ProjectedCurve"):
        ProjectedCurves(items=[ProjectedPoint(0.0, 0.0)])


def test_projected_grid_is_a_semantic_curve_collection():
    curve = ProjectedCurve(x=[0.0, 1.0], y=[2.0, 3.0])
    meridians = ProjectedCurves(items=[curve])
    grid = ProjectedGrid(
        components={"meridians": meridians},
        metadata={"coordinate_system": "equatorial"},
    )

    assert grid["meridians"] is meridians
    assert grid.metadata["coordinate_system"] == "equatorial"


def test_projected_polygons_wrap_singular_polygons():
    polygon = ProjectedPolygon(
        x=[0.0, 1.0, 0.0],
        y=[0.0, 0.0, 1.0],
    )
    polygons = ProjectedPolygons(
        items=[polygon],
        metadata={"layer": "boundaries"},
    )

    assert list(polygons) == [polygon]
    assert polygons.metadata == {"layer": "boundaries"}


def test_projected_polygons_reject_non_polygon_items():
    curve = ProjectedCurve(x=[0.0, 1.0], y=[2.0, 3.0])

    with pytest.raises(TypeError, match="ProjectedPolygon"):
        ProjectedPolygons(items=[curve])
