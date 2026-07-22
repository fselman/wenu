import numpy as np
import pytest

from wenu.projected import (
    ProjectedCurve,
    ProjectedPoint,
    ProjectedPolygon,
)


def test_projected_point_converts_coordinates_to_float():
    point = ProjectedPoint(
        x=np.float64(1.5),
        y=np.float64(-2.0),
    )

    assert point.x == 1.5
    assert point.y == -2.0
    assert isinstance(point.x, float)
    assert isinstance(point.y, float)


def test_projected_point_reports_finite_coordinates():
    assert ProjectedPoint(
        x=1.0,
        y=2.0,
    ).finite

    assert not ProjectedPoint(
        x=np.inf,
        y=2.0,
    ).finite


def test_projected_curve_converts_coordinates_to_arrays():
    curve = ProjectedCurve(
        x=[0.0, 1.0],
        y=[2.0, 3.0],
    )

    np.testing.assert_allclose(
        curve.x,
        [0.0, 1.0],
    )

    np.testing.assert_allclose(
        curve.y,
        [2.0, 3.0],
    )


def test_projected_curve_requires_one_dimensional_coordinates():
    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        ProjectedCurve(
            x=[[0.0, 1.0]],
            y=[[0.0, 1.0]],
        )


def test_projected_curve_requires_matching_shapes():
    with pytest.raises(
        ValueError,
        match="same shape",
    ):
        ProjectedCurve(
            x=[0.0, 1.0],
            y=[0.0],
        )


def test_projected_curve_requires_two_samples():
    with pytest.raises(
        ValueError,
        match="at least two",
    ):
        ProjectedCurve(
            x=[0.0],
            y=[0.0],
        )


def test_projected_curve_finite_mask():
    curve = ProjectedCurve(
        x=[0.0, np.nan, 2.0],
        y=[0.0, 1.0, np.inf],
    )

    np.testing.assert_array_equal(
        curve.finite,
        [True, False, False],
    )


def test_projected_curve_bounds_ignore_nonfinite_samples():
    curve = ProjectedCurve(
        x=[-2.0, np.nan, 3.0],
        y=[4.0, 10.0, -1.0],
    )

    assert curve.bounds == (
        -2.0,
        3.0,
        -1.0,
        4.0,
    )


def test_projected_curve_bounds_are_none_without_finite_samples():
    curve = ProjectedCurve(
        x=[np.nan, np.inf],
        y=[0.0, 1.0],
    )

    assert curve.bounds is None


def test_projected_polygon_requires_three_vertices():
    with pytest.raises(
        ValueError,
        match="at least three",
    ):
        ProjectedPolygon(
            x=[0.0, 1.0],
            y=[0.0, 1.0],
        )


def test_projected_polygon_bounds():
    polygon = ProjectedPolygon(
        x=[-1.0, 2.0, 0.0],
        y=[1.0, -2.0, 3.0],
    )

    assert polygon.bounds == (
        -1.0,
        2.0,
        -2.0,
        3.0,
    )
