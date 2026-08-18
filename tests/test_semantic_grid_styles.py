"""Milestone 45D semantic grid styles and canonical configuration."""

from dataclasses import replace
from pathlib import Path

import pytest

from wenu import AtlasChartStyle, CartoonChartStyle, ChartStyle
from wenu.charts.atlas_modes import atlas_chart_style
from wenu.charts.cartoon_modes import cartoon_chart_style
from wenu.sky.coordinate_grids import (
    AltAzGrid,
    EclipticGrid,
    EquatorialGrid,
    GalacticGrid,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = (
    ROOT / "examples" / "planisphere.py",
    ROOT / "examples" / "regional_constellation_group.py",
    ROOT / "examples" / "regional_constellation.py",
    ROOT / "examples" / "circumpolar.py",
    ROOT / "examples" / "binocular_object.py",
)
SEMANTIC_COLORS = {
    "altaz": "black",
    "equatorial": "black",
    "ecliptic": "orange",
    "galactic": "blue",
}


def grid_options(style, grid):
    return style.as_publication_style()._grid_options(grid)


@pytest.mark.parametrize(
    ("style", "equatorial_color"),
    [(ChartStyle(), "black"), (CartoonChartStyle(), "#667788")],
)
def test_base_grid_lines_and_labels_share_semantic_colors(
    style, equatorial_color
):
    grids = (
        AltAzGrid(None),
        EquatorialGrid(None),
        EclipticGrid(None),
        GalacticGrid(None),
    )
    for grid in grids:
        options = grid_options(style, grid)["render"]
        expected = (
            equatorial_color
            if grid.coordinate_system == "equatorial"
            else SEMANTIC_COLORS[grid.coordinate_system]
        )
        assert options["style"]["color"] == expected
        assert options["label_style"]["color"] == expected


@pytest.mark.parametrize(
    "style",
    [atlas_chart_style("print"), cartoon_chart_style("print")],
)
def test_print_modes_subdue_altaz_without_changing_other_grid_defaults(style):
    assert style.grids.equatorial_color == "#667788"
    assert style.grids.altaz_color == "#707070"
    assert style.grids.ecliptic_color == "orange"
    assert style.grids.galactic_color == "blue"
    assert style.grids.coordinate_label_color is None


def test_named_print_styles_use_the_shared_subtle_grid_baseline():
    for style in (
        atlas_chart_style("print"), cartoon_chart_style("print")
    ):
        assert style.grids.equatorial_color == "#667788"
        assert style.grids.coordinate_linewidth == pytest.approx(0.35)
        assert style.grids.coordinate_alpha <= 0.45


@pytest.mark.parametrize(
    "style",
    [atlas_chart_style("presentation"), cartoon_chart_style("presentation")],
)
def test_presentation_grid_colors_remain_distinct_and_labels_follow(style):
    grids = (
        AltAzGrid(None),
        EquatorialGrid(None),
        EclipticGrid(None),
        GalacticGrid(None),
    )
    colors = []
    for grid in grids:
        options = grid_options(style, grid)["render"]
        colors.append(options["style"]["color"])
        assert (
            options["label_style"]["color"]
            == options["style"]["color"]
        )
    assert len(set(colors)) >= 3


def test_explicit_coordinate_label_color_retains_precedence():
    base = AtlasChartStyle()
    style = replace(
        base,
        grids=replace(base.grids, coordinate_label_color="purple"),
    )
    options = grid_options(style, EclipticGrid(None))["render"]

    assert options["style"]["color"] == "orange"
    assert options["label_style"]["color"] == "purple"


def test_ecliptic_can_be_strengthened_without_changing_equatorial_grid():
    base = CartoonChartStyle()
    style = replace(
        base,
        grids=replace(base.grids, ecliptic_linewidth=1.25),
    )

    ecliptic = grid_options(style, EclipticGrid(None))["render"]
    equatorial = grid_options(style, EquatorialGrid(None))["render"]

    assert ecliptic["style"]["linewidth"] == pytest.approx(1.25)
    assert equatorial["style"]["linewidth"] == pytest.approx(
        base.grids.coordinate_linewidth
    )


@pytest.mark.parametrize(
    ("name", "label"),
    (
        ("ecliptic_longitude_45", "45°"),
        ("ecliptic_latitude_-60", "-60°"),
        ("galactic_longitude_315", "315°"),
        ("galactic_latitude_60", "+60°"),
    ),
)
def test_ecliptic_and_galactic_labels_contain_only_values(name, label):
    formatter = AtlasChartStyle().as_publication_style()._coordinate_label
    assert formatter(name) == label


@pytest.mark.parametrize(
    ("name", "label"),
    (
        ("right_ascension_277.5", "18:30"),
        ("declination_0", "+00:00"),
        ("declination_-15.5", "-15:30"),
    ),
)
def test_equatorial_labels_use_shared_sexagesimal_formats(name, label):
    formatter = AtlasChartStyle().as_publication_style()._coordinate_label
    assert formatter(name) == label


@pytest.mark.parametrize("path", EXAMPLES)
def test_canonical_examples_declare_four_semantic_grids(path):
    source = path.read_text(encoding="utf-8")

    assert "generate_celestial_sphere(" in source
    assert "draw_chart_view_from_arguments(" in source
    assert "sky.add_" not in source
