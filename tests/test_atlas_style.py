"""Current atlas appearance and grid-label contracts."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import AtlasChartStyle
from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
)
from wenu.rendering import MatplotlibRenderer


def test_atlas_deep_sky_symbols_are_compact():
    deep = AtlasChartStyle().deep_sky
    assert deep.open_cluster_symbol_size == 18.0
    assert deep.planetary_nebula_symbol_size == 18.0


def test_atlas_enables_coordinate_labels():
    grids = AtlasChartStyle().grids
    assert grids.draw_coordinate_labels is True
    flat = AtlasChartStyle().as_publication_style()
    assert flat.grid_draw_labels is True
    assert flat._coordinate_label("right_ascension_270") == "18:00"
    assert flat._coordinate_label("right_ascension_277.5") == "18:30"
    assert flat._coordinate_label("declination_-15") == "-15°"
    assert flat._coordinate_label("ecliptic_longitude_270") == "270°"
    assert flat._coordinate_label("ecliptic_latitude_-60") == "-60°"
    assert flat._coordinate_label("galactic_longitude_30") == "30°"
    assert flat._coordinate_label("galactic_latitude_60") == "+60°"


def test_grid_renderer_supports_formatter_and_edge_anchor():
    figure, ax = plt.subplots()
    ax.set_xlim(-1.0, 1.0)
    ax.set_ylim(-1.0, 1.0)
    grid = ProjectedGrid(
        components={
            "meridians": ProjectedCurves(
                [
                    ProjectedCurve(
                        [0.0, 0.0],
                        [-1.0, 1.0],
                        name="right_ascension_270",
                    )
                ]
            ),
            "parallels": ProjectedCurves(
                [
                    ProjectedCurve(
                        [-1.0, 1.0],
                        [0.0, 0.0],
                        name="declination_0",
                    )
                ]
            ),
        }
    )
    style = AtlasChartStyle().as_publication_style()
    artists = MatplotlibRenderer(ax).draw(
        grid,
        draw_labels=True,
        label_formatter=style._coordinate_label,
        label_anchor=style._coordinate_label_anchor,
    )
    labels = [artist for artist in artists if hasattr(artist, "get_text")]
    assert [label.get_text() for label in labels] == ["18:00", "+0°"]
    assert labels[0].get_position()[1] < -0.9
    assert labels[1].get_position()[0] < -0.9
    plt.close(figure)


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
