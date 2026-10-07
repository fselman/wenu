import pytest
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
from wenu.geometry.viewport import Viewport
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


def test_renderer_culls_projected_points_outside_viewport():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    renderer.apply_viewport(Viewport.centered(width=2.0, height=2.0))
    points = ProjectedPoints(
        x=[-10.0, 0.0, 10.0],
        y=[0.0, 0.0, 0.0],
    )

    artists = renderer.draw(
        points,
        style={
            "s": np.asarray([10.0, 20.0, 30.0]),
            "c": ["red", "blue", "green"],
        },
    )

    assert len(artists) == 1
    np.testing.assert_allclose(artists[0].get_offsets(), [[0.0, 0.0]])
    np.testing.assert_allclose(artists[0].get_sizes(), [20.0])
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


def test_point_labels_can_render_without_anchor_markers():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    points = ProjectedPoints(
        x=[0.0, 1.0],
        y=[2.0, 3.0],
        labels=["Cen", "Cru"],
    )

    artists = renderer.draw(
        points,
        draw_markers=False,
        draw_labels=True,
        label_style={"fontsize": 8},
    )

    assert len(artists) == 2
    assert all(
        artist.get_text() in {"Cen", "Cru"}
        for artist in artists
    )
    assert not any(isinstance(artist, PathCollection) for artist in artists)
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


@pytest.mark.parametrize("dpi", [100, 300])
def test_curve_endpoint_clearance_is_physical_and_does_not_trim_clipped_ends(dpi):
    fig, ax = plt.subplots(figsize=(4, 2), dpi=dpi)
    ax.set_xlim(0, 10); ax.set_ylim(-1, 1)
    renderer = MatplotlibRenderer(ax)
    renderer.draw(ProjectedPoints([0, 10], [0, 0]), style={"s": [16, 64]})
    curve = ProjectedCurve([0, 4, 10], [0, 0, 0])
    line = renderer.draw(curve, style={"endpoint_clearance_points": (3, 5)})[0]
    original = ax.transData.transform([[0, 0], [10, 0]])
    rendered = ax.transData.transform(np.column_stack(line.get_data()))
    np.testing.assert_allclose(rendered[0]-original[0], [3*dpi/72, 0], atol=1e-9)
    np.testing.assert_allclose(original[1]-rendered[-1], [5*dpi/72, 0], atol=1e-9)
    np.testing.assert_array_equal(curve.x, [0, 4, 10])
    clipped = renderer.draw(ProjectedCurve([2, 10], [0, 0]),
                            style={"endpoint_clearance_points": (3, 5)})[0]
    assert clipped.get_xdata()[0] == pytest.approx(2)
    with pytest.raises(ValueError, match="clearances"):
        renderer.draw(curve, style={"endpoint_clearance_points": (-1, 0)})
    assert renderer.draw(curve, style={"endpoint_clearance_points": (10000, 10000)}) == []
    plt.close(fig)


def test_auto_point_labels_avoid_neighbouring_symbols_and_labels_without_background():
    fig, ax = plt.subplots(figsize=(3, 3), dpi=100)
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1)
    renderer = MatplotlibRenderer(ax)
    points = ProjectedPoints([0, 0.025, 0.08], [0, 0.025, 0.08], labels=["Antares", "σ", "τ"])
    renderer.draw(points, style={"s": [100, 16, 16]}, draw_labels=True,
                  label_style={"fontsize": 9, "placement": "auto"})
    renderer.draw(ProjectedCurve([-1, 1], [-0.2, 0.2]), style={"linewidth": 1})
    renderer.finalize_label_placement()
    backend = fig.canvas.get_renderer()
    boxes = [text.get_window_extent(backend) for text in ax.texts]
    assert all(not first.overlaps(second) for index, first in enumerate(boxes) for second in boxes[index+1:])
    for text, box in zip(ax.texts, boxes):
        assert text.get_bbox_patch() is None
        for x, y, radius in renderer._point_obstacles:
            centre = ax.transData.transform((x,y))
            assert not box.contains(*centre)
    before = [text.get_position() for text in ax.texts]
    renderer.finalize_label_placement()
    np.testing.assert_allclose([text.get_position() for text in ax.texts], before)
    np.testing.assert_array_equal(points.x, [0, .025, .08])
    plt.close(fig)


@pytest.mark.parametrize("angle", [0, 45, 90, 180, 270])
@pytest.mark.parametrize("dpi", [100, 300])
def test_auto_labels_keep_compact_ownership_after_rotation(angle, dpi):
    fig, ax = plt.subplots(figsize=(3, 3), dpi=dpi)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_aspect("equal")
    radians = np.deg2rad(angle)
    rotation = np.array([[np.cos(radians), -np.sin(radians)],
                         [np.sin(radians), np.cos(radians)]])
    positions = np.array([[0, 0], [.04, .10], [-.08, -.12]]) @ rotation.T
    points = ProjectedPoints(positions[:, 0], positions[:, 1], labels=["τ", "σ", "π"])
    renderer = MatplotlibRenderer(ax)
    renderer.draw(points, style={"s": [16, 16, 16]}, draw_labels=True,
                  label_style={"fontsize": 9, "placement": "auto"})
    fig.canvas.draw()
    renderer.finalize_label_placement()
    scale = dpi / 72
    centres = ax.transData.transform(positions)
    boxes = [artist.get_window_extent(fig.canvas.get_renderer()) for artist in ax.texts]
    for index, box in enumerate(boxes):
        distances = np.hypot(np.maximum(np.maximum(box.x0-centres[:, 0], centres[:, 0]-box.x1), 0),
                             np.maximum(np.maximum(box.y0-centres[:, 1], centres[:, 1]-box.y1), 0))
        assert distances[index] <= min(np.delete(distances, index)) + 1e-8
        assert distances[index] / scale <= renderer._point_obstacles[index][2] + 2.25 + 1e-8
    assert all(not first.overlaps(second) for i, first in enumerate(boxes) for second in boxes[i+1:])
    np.testing.assert_array_equal(points.x, positions[:, 0])
    np.testing.assert_array_equal(points.y, positions[:, 1])
    plt.close(fig)


def test_isolated_greek_label_prefers_vertical_alignment():
    fig, ax = plt.subplots(figsize=(3, 3))
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    renderer = MatplotlibRenderer(ax)
    renderer.draw(ProjectedPoints([0], [0], labels=["θ"]), style={"s": 16},
                  draw_labels=True, label_style={"fontsize": 9, "placement": "auto"})
    fig.canvas.draw()
    renderer.finalize_label_placement()
    anchor = ax.transData.transform((0, 0))
    box = ax.texts[0].get_window_extent(fig.canvas.get_renderer())
    assert (box.x0 + box.x1) / 2 == pytest.approx(anchor[0])
    assert box.y0 > anchor[1]
    plt.close(fig)


@pytest.mark.parametrize("dpi", [100, 300])
def test_auto_labels_respect_the_actual_circular_boundary(dpi):
    from wenu.charts.boundaries import circular_boundary

    fig, ax = plt.subplots(figsize=(4, 4), dpi=dpi)
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_aspect("equal")
    renderer = MatplotlibRenderer(ax)
    renderer.set_clip_boundary(circular_boundary(2))
    angle = np.deg2rad(np.arange(0, 360, 45))
    renderer.draw(
        ProjectedPoints(1.97 * np.cos(angle), 1.97 * np.sin(angle),
                        labels=["Canopus"] * len(angle)),
        style={"s": 36}, draw_labels=True,
        label_style={"fontsize": 9, "placement": "auto"},
    )
    renderer.finalize_label_placement()
    boundary = renderer._clip_patch.get_path().transformed(renderer._clip_patch.get_transform())
    for text in ax.texts:
        box = text.get_window_extent(fig.canvas.get_renderer())
        corners = [(box.x0, box.y0), (box.x0, box.y1),
                   (box.x1, box.y0), (box.x1, box.y1)]
        assert boundary.contains_points(corners).all()
        assert text.get_rotation() == 0
    before = [text.get_position() for text in ax.texts]
    renderer.finalize_label_placement()
    np.testing.assert_allclose([text.get_position() for text in ax.texts], before, atol=1e-12)
    plt.close(fig)


@pytest.mark.parametrize("dpi", [100, 300])
@pytest.mark.parametrize("angle", [0, 180])
def test_vertical_labelled_chain_prefers_side_alignment_without_hiding_faint_stars(dpi, angle):
    fig, ax = plt.subplots(figsize=(3, 3), dpi=dpi)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    factor = 1 if angle == 0 else -1
    points = ProjectedPoints([0, 0, 0, -.06 * factor],
                             [.12 * factor, 0, -.12 * factor, 0],
                             labels=["σ", "Antares", "τ", None])
    renderer = MatplotlibRenderer(ax)
    renderer.draw(points, style={"s": [4, 36, 4, 1]}, draw_labels=True,
                  label_style={"fontsize": 9, "placement": "auto"})
    fig.canvas.draw()
    renderer.finalize_label_placement()
    boxes = []
    for text, x, y in renderer._auto_labels:
        anchor = ax.transData.transform((x, y))
        box = text.get_window_extent(fig.canvas.get_renderer())
        assert (box.y0 + box.y1) / 2 == pytest.approx(anchor[1])
        assert box.x1 < anchor[0] or box.x0 > anchor[0]
        for other_x, other_y, _ in renderer._point_obstacles:
            assert not box.contains(*ax.transData.transform((other_x, other_y)))
        boxes.append(box)
    assert all(not a.overlaps(b) for i, a in enumerate(boxes) for b in boxes[i+1:])
    plt.close(fig)
