"""Milestone 39A tests for composed, output-neutral styles."""

from dataclasses import replace
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from wenu import ChartStyle, PublicationStyle
from wenu.charts.style_components import (
    CanvasStyle,
    DeepSkyStyle,
    GridStyle,
    IsophoteStyle,
    MaskStyle,
    StellarStyle,
)


def stellar_metadata():
    return SimpleNamespace(
        metadata={
            "magnitude": np.asarray((1.0, 2.0, 3.0)),
            "is_variable": np.asarray((True, False, True)),
            "is_multiple": np.asarray((False, True, True)),
        }
    )


def test_default_composed_style_exactly_matches_publication_defaults():
    assert ChartStyle().as_publication_style() == PublicationStyle()


def test_sections_are_focused_immutable_values():
    style = ChartStyle()
    assert isinstance(style.canvas, CanvasStyle)
    assert isinstance(style.stars, StellarStyle)
    assert isinstance(style.isophotes, IsophoteStyle)
    assert isinstance(style.deep_sky, DeepSkyStyle)
    assert isinstance(style.grids, GridStyle)
    assert isinstance(style.mask, MaskStyle)

    changed = replace(
        style,
        canvas=replace(style.canvas, sky_color="white"),
        stars=replace(style.stars, color="black", area_scale=0.5),
    )
    assert style.canvas.sky_color == "midnightblue"
    assert changed.canvas.sky_color == "white"
    assert changed.stars.color == "black"
    assert changed.stars.area_scale == 0.5


def test_custom_sections_map_to_the_flat_compatibility_layer():
    style = ChartStyle(
        canvas=CanvasStyle(
            sky_color="white",
            foreground_color="black",
            label_fontsize=8.0,
        ),
        stars=StellarStyle(
            color="black",
            area_scale=0.75,
            draw_variable_symbols=False,
            draw_multiple_symbols=False,
        ),
        grids=GridStyle(
            boundary_color="gray",
            equatorial_color="gray",
            ecliptic_color="gray",
            galactic_color="gray",
        ),
    ).as_publication_style()
    assert style.sky_color == "white"
    assert style.foreground_color == "black"
    assert style.star_color == "black"
    assert style.star_area_scale == 0.75
    assert style.label_fontsize == 8.0
    assert style.draw_variable_star_symbols is False
    assert style.draw_multiple_star_symbols is False
    assert style.boundary_color == "gray"


def test_default_star_rendering_is_output_equivalent():
    spherical = stellar_metadata()
    old = PublicationStyle()._star_render_options(spherical, None)
    new = ChartStyle().as_publication_style()._star_render_options(
        spherical,
        None,
    )
    assert old["point_overlays"] == new["point_overlays"] == []
    assert old["style"]["c"] == new["style"]["c"]
    assert old["style"]["zorder"] == new["style"]["zorder"]
    assert np.array_equal(old["style"]["s"], new["style"]["s"])


def test_chart_style_implements_the_existing_style_protocol():
    style = ChartStyle(mask=MaskStyle(alpha=0.42, zorder=21.0))
    assert style.outside_mask_style() == (
        style.as_publication_style().outside_mask_style()
    )

    figure, ax = plt.subplots()
    try:
        returned = style.configure_axes(ax, title="Test")
        assert returned is ax
        assert ax.get_facecolor() == (
            0.09803921568627451,
            0.09803921568627451,
            0.4392156862745098,
            1.0,
        )
        assert ax.get_title() == "Test"
    finally:
        plt.close(figure)


def test_top_level_chart_style_export_is_available():
    from wenu import ChartStyle as ExportedChartStyle

    assert ExportedChartStyle is ChartStyle
