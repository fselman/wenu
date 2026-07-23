import pytest
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon as MatplotlibPolygon
from matplotlib.text import Text

from wenu.projected import (
    ProjectedCurve,
    ProjectedPoint,
    ProjectedPolygon,
)
from wenu.renderers.matplotlib import (
    render_curve,
    render_point,
    render_points,
    render_text,
    render_polygon,
)

def test_render_points_returns_scatter_artist():
    fig, ax = plt.subplots()

    artist = render_points(
        ax,
        x=[0.0, 1.0, 2.0],
        y=[2.0, 3.0, 4.0],
        s=[10.0, 20.0, 30.0],
    )

    assert isinstance(
        artist,
        PathCollection,
    )

    np.testing.assert_allclose(
        artist.get_offsets(),
        [
            [0.0, 2.0],
            [1.0, 3.0],
            [2.0, 4.0],
        ],
    )

    np.testing.assert_allclose(
        artist.get_sizes(),
        [10.0, 20.0, 30.0],
    )

    plt.close(fig)


def test_render_points_requires_one_dimensional_coordinates():
    fig, ax = plt.subplots()

    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        render_points(
            ax,
            x=[[0.0, 1.0]],
            y=[[2.0, 3.0]],
        )

    plt.close(fig)


def test_render_points_requires_matching_shapes():
    fig, ax = plt.subplots()

    with pytest.raises(
        ValueError,
        match="same shape",
    ):
        render_points(
            ax,
            x=[0.0, 1.0],
            y=[2.0],
        )

    plt.close(fig)


def test_render_point_returns_scatter_artist():
    fig, ax = plt.subplots()

    point = ProjectedPoint(
        x=1.5,
        y=-2.0,
    )

    artist = render_point(
        ax,
        point,
        s=20.0,
    )

    assert isinstance(
        artist,
        PathCollection,
    )

    np.testing.assert_allclose(
        artist.get_offsets(),
        [[1.5, -2.0]],
    )

    plt.close(fig)


def test_render_point_forwards_style():
    fig, ax = plt.subplots()

    point = ProjectedPoint(
        x=1.0,
        y=2.0,
    )

    artist = render_point(
        ax,
        point,
        s=30.0,
        zorder=5,
    )

    np.testing.assert_allclose(
        artist.get_sizes(),
        [30.0],
    )

    assert artist.get_zorder() == 5

    plt.close(fig)


def test_render_curve_returns_line_artist():
    fig, ax = plt.subplots()

    curve = ProjectedCurve(
        x=[0.0, 1.0, 2.0],
        y=[2.0, 3.0, 4.0],
    )

    artist = render_curve(
        ax,
        curve,
    )

    assert isinstance(
        artist,
        Line2D,
    )

    np.testing.assert_allclose(
        artist.get_xdata(),
        [0.0, 1.0, 2.0],
    )

    np.testing.assert_allclose(
        artist.get_ydata(),
        [2.0, 3.0, 4.0],
    )

    plt.close(fig)


def test_render_curve_preserves_nonfinite_segment_breaks():
    fig, ax = plt.subplots()

    curve = ProjectedCurve(
        x=[0.0, 1.0, np.nan, 3.0, 4.0],
        y=[0.0, 1.0, np.nan, 1.0, 0.0],
    )

    artist = render_curve(
        ax,
        curve,
    )

    np.testing.assert_array_equal(
        artist.get_xdata(),
        curve.x,
    )

    np.testing.assert_array_equal(
        artist.get_ydata(),
        curve.y,
    )

    plt.close(fig)


def test_render_closed_curve_appends_first_sample():
    fig, ax = plt.subplots()

    curve = ProjectedCurve(
        x=[0.0, 1.0, 0.0],
        y=[0.0, 0.0, 1.0],
        closed=True,
    )

    artist = render_curve(
        ax,
        curve,
    )

    np.testing.assert_allclose(
        artist.get_xdata(),
        [0.0, 1.0, 0.0, 0.0],
    )

    np.testing.assert_allclose(
        artist.get_ydata(),
        [0.0, 0.0, 1.0, 0.0],
    )

    plt.close(fig)


def test_render_closed_curve_does_not_duplicate_existing_closure():
    fig, ax = plt.subplots()

    curve = ProjectedCurve(
        x=[0.0, 1.0, 0.0, 0.0],
        y=[0.0, 0.0, 1.0, 0.0],
        closed=True,
    )

    artist = render_curve(
        ax,
        curve,
    )

    assert len(
        artist.get_xdata()
    ) == 4

    assert len(
        artist.get_ydata()
    ) == 4

    plt.close(fig)


def test_render_curve_forwards_style():
    fig, ax = plt.subplots()

    curve = ProjectedCurve(
        x=[0.0, 1.0],
        y=[0.0, 1.0],
    )

    artist = render_curve(
        ax,
        curve,
        linewidth=2.5,
        linestyle="--",
        zorder=3,
    )

    assert artist.get_linewidth() == 2.5
    assert artist.get_linestyle() == "--"
    assert artist.get_zorder() == 3

    plt.close(fig)


def test_render_polygon_returns_patch_and_adds_it_to_axis():
    fig, ax = plt.subplots()

    polygon = ProjectedPolygon(
        x=[0.0, 2.0, 1.0],
        y=[0.0, 0.0, 1.0],
    )

    artist = render_polygon(
        ax,
        polygon,
    )

    assert isinstance(
        artist,
        MatplotlibPolygon,
    )

    assert artist in ax.patches

    plt.close(fig)


def test_render_polygon_contains_projected_vertices():
    fig, ax = plt.subplots()

    polygon = ProjectedPolygon(
        x=[0.0, 2.0, 1.0],
        y=[0.0, 0.0, 1.0],
    )

    artist = render_polygon(
        ax,
        polygon,
    )

    vertices = artist.get_xy()

    np.testing.assert_allclose(
        vertices,
        [
            [0.0, 0.0],
            [2.0, 0.0],
            [1.0, 1.0],
            [0.0, 0.0],
        ],
    )

    plt.close(fig)


def test_render_polygon_forwards_style():
    fig, ax = plt.subplots()

    polygon = ProjectedPolygon(
        x=[0.0, 2.0, 1.0],
        y=[0.0, 0.0, 1.0],
    )

    artist = render_polygon(
        ax,
        polygon,
        linewidth=1.5,
        zorder=2,
    )

    assert artist.get_linewidth() == 1.5
    assert artist.get_zorder() == 2

    plt.close(fig)

def test_render_text_returns_text():
    fig, ax = plt.subplots()

    artist = render_text(
        ax,
        1.0,
        2.0,
        "GC",
        fontsize=12,
        color="yellow",
        zorder=4,
    )

    assert isinstance(
        artist,
        Text,
    )

    assert artist.get_text() == "GC"
    assert artist.get_position() == (1.0, 2.0)
    assert artist.get_fontsize() == 12
    assert artist.get_color() == "yellow"
    assert artist.get_zorder() == 4

    plt.close(fig)



