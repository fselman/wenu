"""Milestone 38B tests for vectorized stellar symbol overlays."""

from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from wenu.charts.styles import PublicationStyle
from wenu.geometry.projected import ProjectedPoints
from wenu.rendering import layers
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.rendering.symbols import DEFAULT_SYMBOLS


def points():
    return ProjectedPoints(
        x=np.asarray((0.0, 1.0, 2.0, np.nan)),
        y=np.asarray((0.0, 1.0, 2.0, np.nan)),
        ids=np.asarray((1, 2, 3, 4)),
    )


def test_renderer_draws_each_overlay_as_one_vectorized_collection():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    artists = renderer.draw(
        points(),
        style={"s": 5.0, "color": "white"},
        point_overlays=[
            {
                "mask": [True, False, True, True],
                "style": {
                    "marker": DEFAULT_SYMBOLS.variable_star,
                    "s": 20.0,
                    "facecolors": "none",
                    "edgecolors": "cyan",
                },
            },
            {
                "mask": [False, True, True, False],
                "style": {
                    "marker": DEFAULT_SYMBOLS.multiple_star,
                    "s": 20.0,
                    "facecolors": "none",
                    "edgecolors": "gold",
                },
            },
        ],
    )
    try:
        assert len(artists) == 3
        assert len(artists[0].get_offsets()) == 3
        assert len(artists[1].get_offsets()) == 2
        assert len(artists[2].get_offsets()) == 2
    finally:
        plt.close(figure)


def test_renderer_rejects_misaligned_overlay_mask():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    try:
        with pytest.raises(ValueError, match="must match"):
            renderer.draw(
                points(),
                point_overlays=[{"mask": [True, False]}],
            )
    finally:
        plt.close(figure)


def spherical_metadata():
    return SimpleNamespace(
        metadata={
            "magnitude": np.asarray((1.0, 2.0, 3.0)),
            "is_variable": np.asarray((True, False, True)),
            "is_multiple": np.asarray((False, True, True)),
        }
    )


def test_stellar_symbol_overlays_are_independently_optional():
    plain = PublicationStyle()._star_render_options(
        spherical_metadata(),
        None,
    )
    assert plain["point_overlays"] == []

    variable = PublicationStyle(
        draw_variable_star_symbols=True,
    )._star_render_options(spherical_metadata(), None)
    assert len(variable["point_overlays"]) == 1
    assert variable["point_overlays"][0]["mask"].tolist() == [
        True, False, True,
    ]

    multiple = PublicationStyle(
        draw_multiple_star_symbols=True,
    )._star_render_options(spherical_metadata(), None)
    assert len(multiple["point_overlays"]) == 1
    assert multiple["point_overlays"][0]["mask"].tolist() == [
        False, True, True,
    ]


def test_stellar_overlay_styles_use_named_layer_zorders():
    options = PublicationStyle(
        draw_variable_star_symbols=True,
        draw_multiple_star_symbols=True,
        variable_star_color="cyan",
        multiple_star_color="gold",
    )._star_render_options(spherical_metadata(), None)
    multiple, variable = options["point_overlays"]
    assert multiple["style"]["zorder"] == layers.MULTIPLE_STARS
    assert variable["style"]["zorder"] == layers.VARIABLE_STARS
    assert multiple["style"]["edgecolors"] == "gold"
    assert variable["style"]["edgecolors"] == "cyan"
    assert layers.STARS < layers.MULTIPLE_STARS < layers.VARIABLE_STARS


def test_base_star_scatter_remains_vectorized():
    options = PublicationStyle(
        draw_variable_star_symbols=True,
        draw_multiple_star_symbols=True,
    )._star_render_options(spherical_metadata(), None)
    assert np.asarray(options["style"]["s"]).shape == (3,)
    assert options["style"]["zorder"] == layers.STARS
