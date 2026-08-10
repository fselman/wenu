"""Milestone 45D semantic grid styles and canonical configuration."""

from dataclasses import replace
import importlib.util
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


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid_options(style, grid):
    return style.as_publication_style()._grid_options(grid)


@pytest.mark.parametrize("style", [ChartStyle(), CartoonChartStyle()])
def test_base_grid_lines_and_labels_share_semantic_colors(style):
    grids = (
        AltAzGrid(None),
        EquatorialGrid(None),
        EclipticGrid(None),
        GalacticGrid(None),
    )
    for grid in grids:
        options = grid_options(style, grid)["render"]
        expected = SEMANTIC_COLORS[grid.coordinate_system]
        assert options["style"]["color"] == expected
        assert options["label_style"]["color"] == expected


@pytest.mark.parametrize(
    "style",
    [atlas_chart_style("print"), cartoon_chart_style("print")],
)
def test_print_modes_subdue_altaz_without_changing_other_grid_defaults(style):
    assert style.grids.equatorial_color == "black"
    assert style.grids.altaz_color == "#707070"
    assert style.grids.ecliptic_color == "orange"
    assert style.grids.galactic_color == "blue"
    assert style.grids.coordinate_label_color is None


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


def built_sky(path):
    module = load(path)
    if path.stem == "regional_constellation_group":
        result = module.build_chart("summer-triangle")
    elif path.stem == "regional_constellation":
        result = module.build_chart("Cru")
    else:
        result = module.build_chart()
    return result[0]


@pytest.mark.parametrize("path", EXAMPLES)
def test_canonical_examples_declare_four_semantic_grids(path):
    source = path.read_text(encoding="utf-8")

    assert "sky.add_altaz_grid(" in source
    assert "sky.add_equatorial_grid(" in source
    assert "sky.add_ecliptic_grid(" in source
    assert "sky.add_galactic_grid(" in source


def test_canonical_grid_configuration_is_reference_free():
    sky = built_sky(EXAMPLES[0])
    grids = {
        layer.coordinate_system: layer
        for layer in sky.layers
        if hasattr(layer, "coordinate_system")
    }

    assert set(grids) == set(SEMANTIC_COLORS)
    assert grids["equatorial"].include_equator is False
    assert grids["ecliptic"].include_ecliptic is False
    assert grids["galactic"].include_plane is False
    assert grids["altaz"].include_horizon is False
    assert 0 not in grids["equatorial"].dec
    assert 0 not in grids["ecliptic"].latitude
    assert 0 not in grids["galactic"].latitude
    assert 0 not in grids["altaz"].altitude
