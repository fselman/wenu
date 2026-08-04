"""Regression tests for atlas catalogue density and grid labels."""

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
    assert flat._coordinate_label("right_ascension_270") == "18h"
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
    assert [label.get_text() for label in labels] == ["18h", "+0°"]
    assert labels[0].get_position()[1] < -0.9
    assert labels[1].get_position()[0] < -0.9
    plt.close(figure)


def test_atlas_example_uses_curated_catalogue_subsets_and_global_grid():
    source = open(
        "tests/fixtures/example_regressions/atlas_style.py",
        encoding="utf-8",
    ).read()
    assert "add_open_clusters(selected=OPEN_CLUSTERS)" in source
    assert "add_planetary_nebulae(selected=PLANETARY_NEBULAE)" in source
    assert "ra=tuple(range(0, 360, 15))" in source
    assert "dec=tuple(range(-75, 76, 15))" in source
