"""Milestone 30 tests for filled galaxy polygon preparation/rendering."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from wenu.geometry.projected import (
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.geometry.spherical import SphericalPolygons
from wenu.rendering import layers
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.rendering.preparation import (
    clip_polygons_to_latitude,
)


def polygon_collections():
    spherical = SphericalPolygons(
        lon_deg=([0.0, 1.0, 1.0, 0.0],),
        lat_deg=([-1.0, -1.0, 1.0, 1.0],),
        names=["test"],
        metadata={
            "magnitude": np.asarray([10.0]),
            "catalog": "galaxies",
        },
    )
    projected = ProjectedPolygons(
        items=[
            ProjectedPolygon(
                x=[-1.0, 1.0, 1.0, -1.0],
                y=[-1.0, -1.0, 1.0, 1.0],
                name="test",
            )
        ],
        metadata={
            "magnitude": np.asarray([10.0]),
            "catalog": "galaxies",
        },
    )
    return spherical, projected


def test_filled_polygon_latitude_clipping_preserves_polygon_semantics():
    spherical, projected = polygon_collections()
    clipped = clip_polygons_to_latitude(
        spherical,
        projected,
        minimum=0.0,
    )
    assert isinstance(clipped, ProjectedPolygons)
    assert len(clipped) == 1
    assert clipped[0].name == "test"
    assert np.min(clipped[0].y) == pytest.approx(0.0)
    assert np.max(clipped[0].y) == pytest.approx(1.0)
    assert clipped.metadata["magnitude"].tolist() == [10.0]
    assert clipped.metadata["catalog"] == "galaxies"


def test_filled_polygon_clipping_removes_invisible_polygon():
    spherical, projected = polygon_collections()
    clipped = clip_polygons_to_latitude(
        spherical,
        projected,
        minimum=2.0,
    )
    assert isinstance(clipped, ProjectedPolygons)
    assert len(clipped) == 0
    assert clipped.metadata["magnitude"].size == 0


def test_renderer_draws_fill_and_continuous_outline_separately():
    _, projected = polygon_collections()
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    artists = renderer.draw(
        projected,
        polygon_fill_style={
            "facecolor": "gold",
            "face_alpha": 0.25,
            "zorder": layers.GALAXY_FILLS,
        },
        polygon_outline_style={
            "edgecolor": "cyan",
            "edge_alpha": 0.8,
            "linewidth": 1.2,
            "linestyle": "-",
            "zorder": layers.GALAXIES,
        },
    )
    try:
        assert len(artists) == 2
        fill, outline = artists
        assert fill.get_facecolor()[3] == pytest.approx(0.25)
        assert fill.get_edgecolor()[3] == pytest.approx(0.0)
        assert fill.get_zorder() == layers.GALAXY_FILLS
        assert outline.get_edgecolor()[3] == pytest.approx(0.8)
        assert outline.get_facecolor()[3] == pytest.approx(0.0)
        assert outline.get_linestyle() == "-"
        assert outline.get_zorder() == layers.GALAXIES
    finally:
        plt.close(figure)


def test_renderer_supports_outline_without_fill():
    _, projected = polygon_collections()
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    artists = renderer.draw(
        projected,
        polygon_outline_style={
            "edgecolor": "white",
            "edge_alpha": 0.9,
            "facecolor": "none",
            "linestyle": "-",
            "zorder": layers.GALAXIES,
        },
    )
    try:
        assert len(artists) == 1
        assert artists[0].get_facecolor()[3] == pytest.approx(0.0)
        assert artists[0].get_edgecolor()[3] == pytest.approx(0.9)
    finally:
        plt.close(figure)


def test_combined_polygon_style_supports_independent_alpha():
    _, projected = polygon_collections()
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    artists = renderer.draw(
        projected,
        style={
            "edgecolor": "red",
            "facecolor": "blue",
            "edge_alpha": 0.7,
            "face_alpha": 0.15,
            "zorder": layers.GALAXIES,
        },
    )
    try:
        assert len(artists) == 1
        assert artists[0].get_edgecolor()[3] == pytest.approx(0.7)
        assert artists[0].get_facecolor()[3] == pytest.approx(0.15)
    finally:
        plt.close(figure)


def test_global_alpha_cannot_override_independent_polygon_alpha():
    _, projected = polygon_collections()
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    try:
        with pytest.raises(ValueError, match="cannot be combined"):
            renderer.draw(
                projected,
                style={
                    "edgecolor": "white",
                    "alpha": 0.5,
                    "edge_alpha": 0.8,
                },
            )
    finally:
        plt.close(figure)


def test_named_galaxy_zorders_have_required_order():
    assert layers.MILKY_WAY < layers.GALAXY_FILLS
    assert layers.GALAXY_FILLS < layers.BOUNDARIES
    assert layers.CONSTELLATIONS < layers.GALAXIES
    assert layers.GALAXIES < layers.STARS
    assert layers.GALAXY_LABELS == layers.LABELS
