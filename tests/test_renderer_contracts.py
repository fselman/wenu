"""Milestone 13 tests for the generic projected-geometry renderer."""

import inspect

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.rendering.matplotlib import MatplotlibRenderer


def test_renderer_has_no_astronomical_or_projection_dependency():
    source = inspect.getsource(
        __import__(
            "wenu.rendering.matplotlib",
            fromlist=["MatplotlibRenderer"],
        )
    )
    assert "wenu.sky" not in source
    assert "wenu.objects" not in source
    assert "wenu.projection" not in source


def test_vectorized_points_and_style_forwarding():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    points = ProjectedPoints(
        x=[0.0, 1.0, np.nan],
        y=[2.0, 3.0, 4.0],
    )

    artists = renderer.draw(
        points,
        style={
            "s": np.asarray([10.0, 20.0, 30.0]),
            "c": ["red", "blue", "green"],
            "zorder": 5,
        },
    )

    assert len(artists) == 1
    assert isinstance(artists[0], PathCollection)
    np.testing.assert_allclose(
        artists[0].get_offsets(),
        [[0.0, 2.0], [1.0, 3.0]],
    )
    np.testing.assert_allclose(artists[0].get_sizes(), [10.0, 20.0])
    assert artists[0].get_zorder() == 5
    plt.close(figure)


def test_point_labels_and_individual_styles():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    points = ProjectedPoints(
        x=[0.0, 1.0],
        y=[2.0, 3.0],
        labels=["A", "B"],
    )

    artists = renderer.draw(
        points,
        styles=(
            {"marker": "x", "color": "red"},
            {"marker": "+", "color": "blue"},
        ),
        draw_labels=True,
        label_style={"fontsize": 8},
        label_offset=(0.1, 0.2),
    )

    assert len(artists) == 4
    assert [artist.get_text() for artist in artists[2:]] == ["A", "B"]
    assert artists[2].get_position() == (0.1, 2.2)
    plt.close(figure)


def test_entity_label_formatter_can_rename_or_suppress_labels():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    points = ProjectedPoints(
        x=[0.0, 1.0],
        y=[2.0, 3.0],
        labels=["NGC0224", "NGC3034"],
    )
    labels = {"NGC0224": "M31", "NGC3034": None}

    artists = renderer.draw(
        points,
        draw_labels=True,
        label_formatter=labels.get,
    )

    assert len(artists) == 2
    assert artists[1].get_text() == "M31"
    plt.close(figure)


def test_curves_preserve_nan_segmentation_and_style():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    curves = ProjectedCurves(
        items=[
            ProjectedCurve(
                x=[0.0, 1.0, np.nan, 2.0, 3.0],
                y=[0.0, 1.0, np.nan, 2.0, 3.0],
            )
        ]
    )

    artists = renderer.draw(
        curves,
        style={"linewidth": 1.75, "linestyle": "--"},
    )

    assert len(artists) == 1
    assert isinstance(artists[0], Line2D)
    assert artists[0].get_linewidth() == 1.75
    assert artists[0].get_linestyle() == "--"
    assert np.isnan(artists[0].get_xdata()[2])
    plt.close(figure)


def test_grid_component_styles_are_separate():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    grid = ProjectedGrid(
        components={
            "meridians": ProjectedCurves(
                [ProjectedCurve([0.0, 1.0], [0.0, 1.0])]
            ),
            "parallels": ProjectedCurves(
                [ProjectedCurve([2.0, 3.0], [2.0, 3.0])]
            ),
        }
    )

    artists = renderer.draw(
        grid,
        style={"alpha": 0.5},
        component_styles={
            "meridians": {"color": "red"},
            "parallels": {"color": "blue"},
        },
    )

    assert len(artists) == 2
    assert artists[0].get_color() == "red"
    assert artists[1].get_color() == "blue"
    assert all(artist.get_alpha() == 0.5 for artist in artists)
    plt.close(figure)


def test_polygons_render_as_patches_with_labels():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    polygons = ProjectedPolygons(
        items=[
            ProjectedPolygon(
                x=[0.0, 1.0, 0.0],
                y=[0.0, 0.0, 1.0],
                name="region",
            )
        ]
    )

    artists = renderer.draw(
        polygons,
        style={"facecolor": "none", "edgecolor": "white"},
        draw_labels=True,
    )

    assert len(artists) == 2
    assert isinstance(artists[0], Polygon)
    assert artists[1].get_text() == "region"
    plt.close(figure)


def test_noninteractive_export(tmp_path):
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    renderer.draw(
        ProjectedPoints(x=[0.0], y=[0.0]),
        style={"s": 20.0, "c": "white"},
    )
    output = tmp_path / "renderer.png"
    figure.savefig(output)

    assert output.exists()
    assert output.stat().st_size > 0
    plt.close(figure)


def test_unknown_geometry_is_rejected():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)

    try:
        renderer.draw(object())
    except TypeError as error:
        assert "Unsupported projected geometry type" in str(error)
    else:
        raise AssertionError("Expected TypeError")
    finally:
        plt.close(figure)
