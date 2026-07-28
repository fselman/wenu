"""Milestone 39B tests for the white atlas preset."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import AtlasChartStyle, ChartStyle


def test_atlas_style_is_a_composed_chart_style():
    style = AtlasChartStyle()
    assert isinstance(style, ChartStyle)
    assert style.canvas.sky_color == "white"
    assert style.stars.color == "#151515"


def test_atlas_stellar_classification_overlays_are_disabled():
    style = AtlasChartStyle()
    assert style.stars.draw_variable_symbols is False
    assert style.stars.draw_multiple_symbols is False
    flat = style.as_publication_style()
    assert flat.draw_variable_star_symbols is False
    assert flat.draw_multiple_star_symbols is False


def test_atlas_palette_matches_the_agreed_visual_roles():
    style = AtlasChartStyle()
    assert style.isophotes.milky_way_color == "#b9d3da"
    assert style.deep_sky.open_cluster_color == "#d2b321"
    assert style.deep_sky.globular_cluster_color == "#c5a000"
    assert style.deep_sky.planetary_nebula_color == "#6f8e4d"
    assert style.deep_sky.galaxy_edge_color == "#b43b37"
    assert style.grids.boundary_linestyle == ":"


def test_atlas_structural_styles_reach_publication_adapter():
    flat = AtlasChartStyle().as_publication_style()
    assert flat.constellation_line_color == "#686868"
    assert flat.constellation_linewidth == 0.35
    assert flat.constellation_label_color == "#5b5b5b"
    assert flat.boundary_color == "#777777"
    assert flat.boundary_linestyle == ":"
    assert flat.grid_linewidth == 0.45
    assert flat.ecliptic_linestyle == "--"


def test_atlas_axes_use_a_white_plotting_field():
    figure, ax = plt.subplots()
    try:
        AtlasChartStyle().configure_axes(ax, title="Atlas")
        assert ax.get_facecolor() == (1.0, 1.0, 1.0, 1.0)
        assert ax.get_title() == "Atlas"
    finally:
        plt.close(figure)


def test_atlas_style_is_exported_at_package_top_level():
    from wenu import AtlasChartStyle as ExportedAtlasChartStyle

    assert ExportedAtlasChartStyle is AtlasChartStyle
