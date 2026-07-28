"""Milestone 39D atlas refinement tests."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import AtlasChartStyle


def test_atlas_milky_way_uses_subtle_dotted_contours():
    iso = AtlasChartStyle().isophotes
    assert iso.milky_way_contour_color == "#555555"
    assert iso.milky_way_contour_linestyle == ":"
    assert iso.milky_way_contour_linewidth <= 0.4
    assert iso.milky_way_contour_alpha <= 0.3
    flat = AtlasChartStyle().as_publication_style()
    assert flat.milky_way_contour_color == "#555555"
    assert flat.milky_way_contour_linestyle == ":"


def test_atlas_legend_is_enabled_and_configurable():
    legend = AtlasChartStyle().legend
    assert legend.visible is True
    assert legend.location == "upper right"
    assert legend.columns == 1


def test_atlas_supernova_remnants_use_complete_circles():
    deep_sky = AtlasChartStyle().deep_sky
    assert deep_sky.supernova_remnant_linestyle == "-"
    assert deep_sky.supernova_remnant_linewidth == 0.55


def test_atlas_example_curates_remnants_and_declares_j2000_grid():
    source = Path("examples/atlas_style.py").read_text(
        encoding="utf-8"
    )
    assert "add_supernova_remnants(selected=SUPERNOVA_REMNANTS)" in source
    assert 'equinox="J2000"' in source
    assert "draw_chart_legend(ax, chart, sky, style)" in source


def test_legacy_style_keeps_new_features_disabled():
    from wenu.charts.style_components import ChartStyle

    style = ChartStyle()
    assert style.legend.visible is False
    assert style.isophotes.milky_way_contour_color is None


def test_atlas_axes_configuration_remains_valid():
    figure, ax = plt.subplots()
    AtlasChartStyle().configure_axes(ax, title="Atlas")
    assert ax.get_title() == "Atlas"
    plt.close(figure)


def test_chart_legend_accepts_observation_context_lines():
    from inspect import signature
    from wenu.charts.legend import draw_chart_legend

    parameters = signature(draw_chart_legend).parameters
    assert "context_lines" in parameters
