"""Milestone 44F.B.3 trichromatic cartoon products."""

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import pytest

from wenu import FullSkyChart, cartoon_chart_style, compose_chart
from wenu.charts.cartoon_modes import (
    CARTOON_PRESENTATION_PALETTE,
    CARTOON_PRINT_PALETTE,
)


YELLOW = "#FFE066"
BLUE = "#1677A6"


def test_presentation_palette_contains_only_three_resolved_colors():
    assert set(vars(CARTOON_PRESENTATION_PALETTE).values()) == {
        BLUE,
        YELLOW,
        "#FFFFFF",
    }


def test_print_palette_contains_only_white_and_black():
    assert set(vars(CARTOON_PRINT_PALETTE).values()) == {
        "white",
        "#000000",
    }


def test_presentation_uses_yellow_for_all_chart_structure():
    style = cartoon_chart_style("presentation")

    assert style.stars.color == YELLOW
    assert style.canvas.foreground_color == YELLOW
    assert style.grids.constellation_line_color == YELLOW
    assert style.grids.constellation_label_color == YELLOW
    assert style.grids.boundary_color == YELLOW
    assert style.grids.equatorial_color == YELLOW
    assert style.grids.ecliptic_color == YELLOW
    assert style.grids.galactic_color == YELLOW
    assert style.isophotes.milky_way_color == YELLOW
    assert style.isophotes.milky_way_alpha == pytest.approx(0.0)
    assert style.isophotes.milky_way_contour_color == YELLOW
    assert style.isophotes.milky_way_contour_linestyle == ":"
    assert style.isophotes.lmc_alpha == pytest.approx(0.0)
    assert style.isophotes.lmc_edge_color == YELLOW
    assert style.isophotes.lmc_linestyle == ":"
    assert style.isophotes.smc_alpha == pytest.approx(0.0)
    assert style.isophotes.smc_edge_color == YELLOW
    assert style.isophotes.smc_linestyle == ":"
    assert style.deep_sky.galaxy_edge_color == YELLOW
    assert style.legend.facecolor == BLUE
    assert style.legend.edgecolor == YELLOW
    assert style.legend.text_color == YELLOW
    assert style.canvas.footer_color == "#FFFFFF"


def test_print_uses_black_for_structure_and_footer():
    style = cartoon_chart_style("print")

    assert style.canvas.sky_color == "white"
    assert style.stars.color == "#000000"
    assert style.canvas.foreground_color == "#000000"
    assert style.grids.constellation_line_color == "#000000"
    assert style.grids.boundary_color == "#000000"
    assert style.isophotes.milky_way_alpha == pytest.approx(0.0)
    assert style.isophotes.milky_way_contour_color == "#000000"
    assert style.isophotes.lmc_edge_color == "#000000"
    assert style.isophotes.smc_edge_color == "#000000"
    assert style.legend.facecolor == "white"
    assert style.legend.edgecolor == "#000000"
    assert style.legend.text_color == "#000000"
    assert style.canvas.footer_color == "#000000"


@pytest.mark.parametrize(
    ("mode", "color"),
    [("presentation", YELLOW), ("print", "#000000")],
)
def test_cartoon_title_frame_and_circular_boundary_share_structure_color(
    mode,
    color,
):
    style = cartoon_chart_style(mode)
    figure, ax = plt.subplots()
    style.configure_axes(ax, title="Context")

    assert ax.title.get_color() == color
    assert {spine.get_edgecolor() for spine in ax.spines.values()} == {
        to_rgba(color),
    }
    assert style.chart_boundary_style()["edgecolor"] == color
    assert style.chart_boundary_style()["linewidth"] == pytest.approx(
        style.grids.constellation_linewidth
    )
    plt.close(figure)


def test_planisphere_keeps_horizon_geometry_independent_of_style():
    chart = FullSkyChart(horizon_altitude_deg=0.0)
    printed = cartoon_chart_style("print").chart_boundary_style()
    presented = cartoon_chart_style("presentation").chart_boundary_style()

    assert chart.horizon_altitude_deg == pytest.approx(0.0)
    assert chart.horizon.name == "horizon"
    assert chart.horizon.closed is True
    assert printed["edgecolor"] == "#000000"
    assert presented["edgecolor"] == YELLOW


def test_canonical_cartoon_composition_keeps_mode_context_methods():
    composition = compose_chart(
        FullSkyChart(),
        style="cartoon",
        mode="presentation",
    )
    figure, ax = plt.subplots()

    composition.style.configure_axes(ax, title="Context")

    assert ax.title.get_color() == YELLOW
    assert {spine.get_edgecolor() for spine in ax.spines.values()} == {
        to_rgba(YELLOW),
    }
    assert composition.style.chart_boundary_style()["edgecolor"] == YELLOW
    plt.close(figure)
