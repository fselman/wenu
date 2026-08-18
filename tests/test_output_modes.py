"""Current output modes contracts."""

# Contracts consolidated from test_milestone41a_cartoon_output_styles.py.
import pytest

from wenu import (
    CARTOON_PRESENTATION_PALETTE,
    CARTOON_PRINT_PALETTE,
    CartoonDetailPolicy,
    PresentationMode,
    PrintMode,
    cartoon_chart_style,
)
from wenu.charts.detail import CARTOON_CONTENT_LAYERS


def test_print_cartoon_uses_white_paper_palette():
    style = cartoon_chart_style("print")
    assert style.canvas.sky_color == "white"
    assert style.stars.color == CARTOON_PRINT_PALETTE.stars
    assert (
        style.grids.constellation_line_color
        == CARTOON_PRINT_PALETTE.constellation_lines
    )
    assert not style.stars.draw_variable_symbols
    assert not style.stars.draw_multiple_symbols


def test_presentation_uses_agreed_projector_palette():
    style = cartoon_chart_style("presentation")
    assert style.canvas.sky_color == "#0262AD"
    assert style.stars.color == "#FFE066"
    assert style.grids.constellation_line_color == "#FFE066"
    assert style.grids.constellation_label_color == "#FFE066"
    assert style.canvas.foreground_color == "#FFE066"
    assert style.canvas.footer_color == "#FFFFFF"
    assert style.isophotes.milky_way_color == "#FFE066"


def test_presentation_contains_no_red_primary_chart_colors():
    palette = CARTOON_PRESENTATION_PALETTE
    values = tuple(vars(palette).values())
    assert "#ff0000" not in {value.lower() for value in values}
    assert "red" not in {value.lower() for value in values}


def test_presentation_increases_screen_readability():
    printed = cartoon_chart_style(PrintMode())
    presented = cartoon_chart_style(PresentationMode())
    assert (
        presented.canvas.label_fontsize
        > printed.canvas.label_fontsize
    )
    assert (
        presented.grids.constellation_linewidth
        > printed.grids.constellation_linewidth
    )
    assert presented.stars.area_scale > printed.stars.area_scale


def test_mode_selection_rejects_unknown_names():
    with pytest.raises(ValueError, match="print or presentation"):
        cartoon_chart_style("night")


def test_visual_mode_does_not_resolve_content():
    detail = CartoonDetailPolicy().resolve(object(), object())
    assert detail.enabled_layers == CARTOON_CONTENT_LAYERS
    assert detail.constellation_star_mode == "selected"


def test_publication_styles_preserve_mode_colors():
    presented = cartoon_chart_style("presentation")
    publication = presented.as_publication_style()
    assert publication.sky_color == "#0262AD"
    assert publication.star_color == "#FFE066"
    assert publication.constellation_line_color == "#FFE066"
    assert publication.constellation_label_color == "#FFE066"

# Contracts consolidated from test_milestone43d_atlas_presentation.py.
"""Milestone 43D contracts for atlas presentation output."""

from dataclasses import fields, replace
from types import SimpleNamespace

import numpy as np
import pytest
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time
from astropy import units as u

from wenu import (
    ATLAS_PRESENTATION_PALETTE,
    AtlasChartStyle,
    BinocularChart,
    CircumpolarChart,
    FullSkyChart,
    PresentationMode,
    RegionalChart,
    atlas_chart_style,
    compose_chart,
)


def charts():
    observer = SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-08-02T00:00:00"),
            location=EarthLocation(
                lat=-32.44 * u.deg,
                lon=-71.23 * u.deg,
            ),
        )
    )
    return (
        RegionalChart(
            center_alt_deg=35.0,
            center_az_deg=210.0,
            field_width_deg=30.0,
            field_height_deg=20.0,
        ),
        FullSkyChart(),
        CircumpolarChart(
            observer=observer,
            pole="south",
            limiting_declination_deg=-30.0,
        ),
        BinocularChart(center_alt_deg=45.0, center_az_deg=180.0),
    )


@pytest.mark.parametrize("chart", charts())
def test_presentation_changes_no_chart_geometry(chart):
    before = chart.chart_context
    printed = compose_chart(chart, style="atlas", mode="print")
    presented = compose_chart(chart, style="atlas", mode="presentation")

    assert_same_geometry(printed.context, presented.context)
    assert_same_geometry(presented.context, before)
    assert printed.detail == presented.detail
    assert_same_geometry(chart.chart_context, before)


def assert_same_geometry(left, right):
    """Compare contexts without ambiguous NumPy array equality."""
    assert replace(left, clip_boundary=None) == replace(
        right,
        clip_boundary=None,
    )
    left_boundary = left.clip_boundary
    right_boundary = right.clip_boundary
    if left_boundary is None or right_boundary is None:
        assert left_boundary is right_boundary is None
        return
    assert left_boundary.closed == right_boundary.closed
    assert left_boundary.name == right_boundary.name
    np.testing.assert_allclose(left_boundary.x, right_boundary.x)
    np.testing.assert_allclose(left_boundary.y, right_boundary.y)


def test_presentation_uses_high_contrast_atlas_palette():
    style = atlas_chart_style("presentation")
    palette = ATLAS_PRESENTATION_PALETTE

    assert style.canvas.sky_color == palette.sky
    assert style.canvas.foreground_color == palette.foreground
    assert style.stars.color == palette.stars
    assert style.grids.constellation_line_color == palette.structure
    assert style.grids.constellation_label_color == palette.labels
    assert style.isophotes.milky_way_color == palette.milky_way
    assert style.deep_sky.galaxy_edge_color == palette.foreground
    assert style.deep_sky.supernova_remnant_color == palette.structure
    assert "#b43b37" not in _style_colors(style)


def _style_colors(style):
    colors = []
    for section_name in (
        "canvas", "stars", "isophotes", "deep_sky", "grids", "mask", "legend"
    ):
        section = getattr(style, section_name)
        for item in fields(section):
            if "color" in item.name:
                colors.append(getattr(section, item.name))
    return colors


def test_presentation_applies_mode_visual_scales_and_screen_output():
    composition = compose_chart(
        charts()[0],
        style="atlas",
        mode=PresentationMode(
            width_inches=12.0,
            dpi=144,
            font_scale=1.5,
            line_scale=1.4,
            symbol_scale=1.3,
        ),
    )
    baseline = AtlasChartStyle()

    assert composition.mode.width_inches == 12.0
    assert composition.mode.dpi == 144
    assert composition.style.canvas.label_fontsize == pytest.approx(
        baseline.canvas.label_fontsize * 1.5
    )
    assert composition.style.grids.coordinate_linewidth == pytest.approx(
        baseline.grids.coordinate_linewidth * 1.4
    )
    assert composition.style.stars.area_scale == pytest.approx(
        baseline.stars.area_scale * 1.3
    )


def test_print_is_unchanged_and_mode_resolution_is_render_local():
    chart = charts()[0]
    direct = AtlasChartStyle()
    assert atlas_chart_style("print", base=direct) is direct

    first_print = compose_chart(chart, style="atlas", mode="print")
    presentation = compose_chart(chart, style="atlas", mode="presentation")
    second_print = compose_chart(chart, style="atlas", mode="print")

    assert first_print.style == second_print.style == AtlasChartStyle()
    assert presentation.style != first_print.style
    assert first_print.style is not presentation.style
    assert first_print.mode == second_print.mode
