import numpy as np
import pytest

from wenu.clipping import (
    _clip_polyline_to_viewport,
    clip_curve_to_viewport,
    clip_line_segment_to_viewport,
    clip_point_to_viewport,
    clip_polygon_to_viewport,
)
from wenu.viewport import Viewport
from wenu.projected import (
        ProjectedPolygon,
        ProjectedCurve,
        ProjectedPoint,
)


@pytest.fixture
def viewport():
    return Viewport(
        x_min=-1.0,
        x_max=1.0,
        y_min=-1.0,
        y_max=1.0,
    )

def test_polygon_inside_viewport_is_retained(
    viewport,
):
    polygon = ProjectedPolygon(
        x=[-0.5, 0.5, 0.0],
        y=[-0.5, -0.5, 0.5],
        name="inside",
    )

    clipped = clip_polygon_to_viewport(
        polygon,
        viewport,
    )

    assert clipped is not None
    assert np.allclose(
        clipped.x,
        polygon.x,
    )
    assert np.allclose(
        clipped.y,
        polygon.y,
    )
    assert clipped.name == "inside"


def test_polygon_outside_viewport_is_removed(
    viewport,
):
    polygon = ProjectedPolygon(
        x=[2.0, 3.0, 2.5],
        y=[0.0, 0.0, 1.0],
    )

    assert (
        clip_polygon_to_viewport(
            polygon,
            viewport,
        )
        is None
    )


def test_polygon_crossing_viewport_is_clipped(
    viewport,
):
    polygon = ProjectedPolygon(
        x=[-2.0, 2.0, 2.0, -2.0],
        y=[-0.5, -0.5, 0.5, 0.5],
        name="crossing",
    )

    clipped = clip_polygon_to_viewport(
        polygon,
        viewport,
    )

    assert clipped is not None
    assert clipped.name == "crossing"
    assert clipped.bounds == pytest.approx(
        (
            -1.0,
            1.0,
            -0.5,
            0.5,
        )
    )


def test_polygon_containing_viewport_becomes_viewport_rectangle(
    viewport,
):
    polygon = ProjectedPolygon(
        x=[-2.0, 2.0, 2.0, -2.0],
        y=[-2.0, -2.0, 2.0, 2.0],
    )

    clipped = clip_polygon_to_viewport(
        polygon,
        viewport,
    )

    assert clipped is not None
    assert clipped.bounds == pytest.approx(
        (
            -1.0,
            1.0,
            -1.0,
            1.0,
        )
    )
    assert len(clipped) == 4


def test_nonfinite_polygon_is_removed(
    viewport,
):
    polygon = ProjectedPolygon(
        x=[0.0, np.nan, 0.5],
        y=[0.0, 0.5, 0.0],
    )

    assert (
        clip_polygon_to_viewport(
            polygon,
            viewport,
        )
        is None
    )

def test_nonfinite_samples_split_curve(
    viewport,
):
    curve = ProjectedCurve(
        x=[-0.5, 0.0, np.nan, 0.0, 0.5],
        y=[0.0, 0.5, np.nan, -0.5, 0.0],
        name="split",
    )

    clipped = clip_curve_to_viewport(
        curve,
        viewport,
    )

    assert len(clipped) == 2

    assert np.allclose(
        clipped[0].x,
        [-0.5, 0.0],
    )
    assert np.allclose(
        clipped[0].y,
        [0.0, 0.5],
    )

    assert np.allclose(
        clipped[1].x,
        [0.0, 0.5],
    )
    assert np.allclose(
        clipped[1].y,
        [-0.5, 0.0],
    )

    assert all(
        fragment.name == "split"
        for fragment in clipped
    )

def test_closed_curve_clips_final_to_first_segment(
    viewport,
):
    curve = ProjectedCurve(
        x=[-2.0, -2.0, 2.0],
        y=[0.0, 2.0, 0.0],
        closed=True,
        name="closed",
    )

    clipped = clip_curve_to_viewport(
        curve,
        viewport,
    )

    assert len(clipped) == 2

    assert any(
        np.allclose(fragment.x, [1.0, -1.0])
        and np.allclose(fragment.y, [0.0, 0.0])
        for fragment in clipped
    )

    assert all(
        fragment.closed is False
        for fragment in clipped
    )
    assert all(
        fragment.name == "closed"
        for fragment in clipped
    )

def test_curve_inside_viewport_is_retained(
    viewport,
):
    curve = ProjectedCurve(
        x=[-0.5, 0.0, 0.5],
        y=[0.0, 0.25, 0.0],
        name="inside",
    )

    clipped = clip_curve_to_viewport(
        curve,
        viewport,
    )

    assert len(clipped) == 1
    assert isinstance(clipped[0], ProjectedCurve)
    assert np.allclose(
        clipped[0].x,
        curve.x,
    )
    assert np.allclose(
        clipped[0].y,
        curve.y,
    )
    assert clipped[0].name == "inside"
    assert clipped[0].closed is False


def test_curve_outside_viewport_is_removed(
    viewport,
):
    curve = ProjectedCurve(
        x=[2.0, 3.0],
        y=[0.0, 0.0],
    )

    assert (
        clip_curve_to_viewport(
            curve,
            viewport,
        )
        == []
    )


def test_curve_crossing_viewport_is_clipped(
    viewport,
):
    curve = ProjectedCurve(
        x=[-2.0, 2.0],
        y=[0.0, 0.0],
        name="crossing",
    )

    clipped = clip_curve_to_viewport(
        curve,
        viewport,
    )

    assert len(clipped) == 1
    assert np.allclose(
        clipped[0].x,
        [-1.0, 1.0],
    )
    assert np.allclose(
        clipped[0].y,
        [0.0, 0.0],
    )
    assert clipped[0].name == "crossing"


def test_curve_can_produce_disconnected_fragments(
    viewport,
):
    curve = ProjectedCurve(
        x=[
            -2.0,
            0.0,
            2.0,
            2.0,
            0.0,
            -2.0,
        ],
        y=[
            0.0,
            0.0,
            0.0,
            2.0,
            0.0,
            0.0,
        ],
    )

    clipped = clip_curve_to_viewport(
        curve,
        viewport,
    )

    assert len(clipped) == 2
    assert all(
        isinstance(fragment, ProjectedCurve)
        for fragment in clipped
    )

def test_closed_curve_includes_closing_segment(
    viewport,
):
    curve = ProjectedCurve(
        x=[-2.0, -2.0, 2.0],
        y=[2.0, -2.0, 2.0],
        closed=True,
        name="closed",
    )

    clipped = clip_curve_to_viewport(
        curve,
        viewport,
    )

    assert len(clipped) >= 1
    assert all(
        fragment.closed is False
        for fragment in clipped
    )
    assert all(
        fragment.name == "closed"
        for fragment in clipped
    )

def test_point_inside_viewport_is_retained(
    viewport,
):
    point = ProjectedPoint(
        x=0.25,
        y=-0.5,
        name="inside",
    )

    clipped = clip_point_to_viewport(
        point,
        viewport,
    )

    assert clipped is point


def test_point_on_viewport_boundary_is_retained(
    viewport,
):
    point = ProjectedPoint(
        x=1.0,
        y=0.0,
    )

    clipped = clip_point_to_viewport(
        point,
        viewport,
    )

    assert clipped is point


def test_point_outside_viewport_is_removed(
    viewport,
):
    point = ProjectedPoint(
        x=2.0,
        y=0.0,
    )

    assert (
        clip_point_to_viewport(
            point,
            viewport,
        )
        is None
    )


def test_non_finite_point_is_removed(
    viewport,
):
    point = ProjectedPoint(
        x=np.nan,
        y=0.0,
    )

    assert (
        clip_point_to_viewport(
            point,
            viewport,
        )
        is None
    )

def test_segment_inside_viewport_is_unchanged(
    viewport,
):
    clipped = clip_line_segment_to_viewport(
        -0.5,
        0.0,
        0.5,
        0.0,
        viewport,
    )

    assert clipped == (
        -0.5,
        0.0,
        0.5,
        0.0,
    )


def test_segment_outside_viewport_is_rejected(
    viewport,
):
    clipped = clip_line_segment_to_viewport(
        -2.0,
        2.0,
        2.0,
        2.0,
        viewport,
    )

    assert clipped is None


def test_horizontal_crossing_segment_is_clipped(
    viewport,
):
    clipped = clip_line_segment_to_viewport(
        -2.0,
        0.0,
        2.0,
        0.0,
        viewport,
    )

    np.testing.assert_allclose(
        clipped,
        (-1.0, 0.0, 1.0, 0.0),
    )


def test_vertical_crossing_segment_is_clipped(
    viewport,
):
    clipped = clip_line_segment_to_viewport(
        0.0,
        -2.0,
        0.0,
        2.0,
        viewport,
    )

    np.testing.assert_allclose(
        clipped,
        (0.0, -1.0, 0.0, 1.0),
    )


def test_diagonal_segment_is_clipped(
    viewport,
):
    clipped = clip_line_segment_to_viewport(
        -2.0,
        -2.0,
        2.0,
        2.0,
        viewport,
    )

    np.testing.assert_allclose(
        clipped,
        (-1.0, -1.0, 1.0, 1.0),
    )


def test_parallel_segment_outside_is_rejected(
    viewport,
):
    clipped = clip_line_segment_to_viewport(
        -2.0,
        1.5,
        2.0,
        1.5,
        viewport,
    )

    assert clipped is None


def test_nonfinite_segment_is_rejected(
    viewport,
):
    clipped = clip_line_segment_to_viewport(
        np.nan,
        0.0,
        1.0,
        0.0,
        viewport,
    )

    assert clipped is None


def test_polyline_crossing_viewport_is_retained(
    viewport,
):
    polylines = _clip_polyline_to_viewport(
        x=[-2.0, 2.0],
        y=[0.0, 0.0],
        viewport=viewport,
    )

    assert len(polylines) == 1

    clipped_x, clipped_y = polylines[0]

    np.testing.assert_allclose(
        clipped_x,
        [-1.0, 1.0],
    )

    np.testing.assert_allclose(
        clipped_y,
        [0.0, 0.0],
    )


def test_polyline_can_produce_separate_parts(
    viewport,
):
    polylines = _clip_polyline_to_viewport(
        x=[
            -2.0,
            0.0,
            2.0,
            2.0,
            0.0,
            -2.0,
        ],
        y=[
            0.0,
            0.0,
            0.0,
            2.0,
            0.0,
            0.0,
        ],
        viewport=viewport,
    )

    assert len(polylines) == 2


def test_polyline_validates_dimensions(
    viewport,
):
    with pytest.raises(ValueError):
        _clip_polyline_to_viewport(
            x=[[0.0, 1.0]],
            y=[[0.0, 1.0]],
            viewport=viewport,
        )


def test_polyline_validates_matching_shapes(
    viewport,
):
    with pytest.raises(ValueError):
        _clip_polyline_to_viewport(
            x=[0.0, 1.0],
            y=[0.0],
            viewport=viewport,
        )


