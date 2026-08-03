"""Milestone 31 tests for galaxy chart styles and masked regions."""

from types import SimpleNamespace
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu.charts.styles import PublicationStyle
from wenu.geometry.projected import (
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.geometry.spherical import SphericalPolygons
from wenu.rendering import layers


def galaxy_regions_module():
    """Load tests/fixtures/example_regressions/galaxy_regions.py without packaging examples."""
    path = (
        Path(__file__).resolve().parents[1]
        / "tests"
        / "fixtures"
        / "example_regressions"
        / "galaxy_regions.py"
    )
    spec = spec_from_file_location("wenu_example_galaxy_regions", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load example module: {path}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class HashableLayer:
    samples = 73


def fake_sky():
    galaxies = HashableLayer()
    return SimpleNamespace(
        stars=None,
        nonstellar=None,
        galaxies=galaxies,
        constellation_lines=None,
        constellation_labels=None,
        constellation_boundaries=None,
        points=None,
        layers=(galaxies,),
    )


def test_default_galaxy_style_is_outline_only_with_small_labels():
    sky = fake_sky()
    style = PublicationStyle()
    options = style.layer_options(sky)[sky.galaxies]
    render = options["render"]
    outline = render["polygon_outline_style"]
    assert "polygon_fill_style" not in render
    assert outline["linestyle"] == "-"
    assert outline["zorder"] == layers.GALAXIES
    assert render["draw_labels"] is False
    assert render["label_style"]["fontsize"] == 6.0
    assert (
        render["label_style"]["zorder"]
        == layers.GALAXY_LABELS
    )


def test_filled_style_uses_named_fill_zorder_and_independent_alpha():
    sky = fake_sky()
    style = PublicationStyle(
        galaxy_edge_color="cyan",
        galaxy_edge_alpha=0.8,
        galaxy_face_color="deepskyblue",
        galaxy_face_alpha=0.2,
    )
    render = style.layer_options(sky)[sky.galaxies]["render"]
    fill = render["polygon_fill_style"]
    outline = render["polygon_outline_style"]
    assert fill == {
        "facecolor": "deepskyblue",
        "face_alpha": 0.2,
        "zorder": layers.GALAXY_FILLS,
    }
    assert outline["edgecolor"] == "cyan"
    assert outline["edge_alpha"] == 0.8
    assert outline["zorder"] == layers.GALAXIES


def test_galaxy_style_uses_filled_polygon_clipping():
    sky = fake_sky()
    options = PublicationStyle().layer_options(sky)[sky.galaxies]
    spherical = SphericalPolygons(
        lon_deg=([0.0, 1.0, 1.0, 0.0],),
        lat_deg=([-1.0, -1.0, 1.0, 1.0],),
    )
    projected = ProjectedPolygons(
        items=[
            ProjectedPolygon(
                x=[-1.0, 1.0, 1.0, -1.0],
                y=[-1.0, -1.0, 1.0, 1.0],
            )
        ]
    )
    clipped = options["prepare"](spherical, projected)
    assert isinstance(clipped, ProjectedPolygons)
    assert len(clipped) == 1


def test_outside_mask_is_above_all_named_galaxy_layers():
    style = PublicationStyle(outside_mask_zorder=20.0)
    mask = style.outside_mask_style()
    assert mask["zorder"] > layers.GALAXY_FILLS
    assert mask["zorder"] > layers.GALAXIES
    assert mask["zorder"] > layers.GALAXY_LABELS


def test_virgo_coma_region_renders_galaxies_and_outside_mask():
    example = galaxy_regions_module()
    from wenu.rendering import MatplotlibRenderer

    region, _, sky, chart = example.build_region("virgo-coma")
    assert region.constellations == ("Vir", "Com")
    assert chart.outside_mask_constellations == ("Vir", "Com")

    figure, ax = plt.subplots(figsize=chart.figure_size(5.0))
    try:
        result = chart.render(
            sky,
            MatplotlibRenderer(ax),
            style=example.chart_style(filled=True),
        )
        galaxy_result = next(
            layer
            for layer in result.layers
            if layer.layer is sky.galaxies
        )
        assert isinstance(
            galaxy_result.projected,
            ProjectedPolygons,
        )
        assert galaxy_result.artists
        mask_artists = [
            patch
            for patch in ax.patches
            if patch.get_zorder() == 20.0
        ]
        assert len(mask_artists) == 1
    finally:
        plt.close(figure)


def test_requested_visual_regions_are_declared():
    regions = galaxy_regions_module().REGIONS

    assert regions["centaurus-crux-musca"].constellations == (
        "Cen",
        "Cru",
        "Mus",
    )
    assert regions["virgo-coma"].constellations == ("Vir", "Com")
