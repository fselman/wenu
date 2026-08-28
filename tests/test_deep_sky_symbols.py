"""Current deep sky symbols contracts."""

# Contracts consolidated from test_milestone26_nonstellar_symbols.py.
"""Tests for visible NonStellar symbols and label options."""

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import SkyCoord

from wenu.coordinates import GENERIC_SPHERICAL_SPEC

from wenu.charts.styles import PublicationStyle
from wenu.objects.nonstellar import NonStellar


def test_minimum_symbol_size_preserves_axis_ratio():
    center = SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg)
    outline = NonStellar._ellipse(
        center,
        8.0,
        4.0,
        35.0,
        144,
        minimum_size_arcmin=30.0,
    )
    separation = center.separation(outline).to_value(u.arcmin)
    assert np.min(separation) == pytest.approx(15.0, rel=2.0e-3)
    assert np.max(separation) == pytest.approx(30.0, rel=2.0e-3)


def test_true_angular_size_remains_available():
    center = SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg)
    outline = NonStellar._ellipse(
        center,
        8.0,
        4.0,
        35.0,
        144,
        minimum_size_arcmin=None,
    )
    separation = center.separation(outline).to_value(u.arcmin)
    assert np.min(separation) == pytest.approx(2.0, rel=2.0e-3)
    assert np.max(separation) == pytest.approx(4.0, rel=2.0e-3)


def test_nonstellar_labels_are_optional_and_small_by_default():
    style = PublicationStyle()
    assert style.nonstellar_draw_labels is False
    assert style.nonstellar_label_fontsize < style.label_fontsize
    assert style.nonstellar_minimum_size_arcmin > 0.0

# Contracts consolidated from test_milestone30_galaxy_rendering.py.
"""Milestone 30 tests for filled galaxy polygon preparation/rendering."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from wenu.geometry.projected import (
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.geometry.spherical import SphericalPolygons
from wenu.rendering import layers
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.rendering.preparation import (
    clip_polygons_to_latitude,
)


def polygon_collections():
    spherical = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([0.0, 1.0, 1.0, 0.0],),
        lat_deg=([-1.0, -1.0, 1.0, 1.0],),
        names=["test"],
        metadata={
            "magnitude": np.asarray([10.0]),
            "catalog": "galaxies",
        },
    )
    projected = ProjectedPolygons(
        items=[
            ProjectedPolygon(
                x=[-1.0, 1.0, 1.0, -1.0],
                y=[-1.0, -1.0, 1.0, 1.0],
                name="test",
            )
        ],
        metadata={
            "magnitude": np.asarray([10.0]),
            "catalog": "galaxies",
        },
    )
    return spherical, projected


def test_filled_polygon_latitude_clipping_preserves_polygon_semantics():
    spherical, projected = polygon_collections()
    clipped = clip_polygons_to_latitude(
        spherical,
        projected,
        minimum=0.0,
    )
    assert isinstance(clipped, ProjectedPolygons)
    assert len(clipped) == 1
    assert clipped[0].name == "test"
    assert np.min(clipped[0].y) == pytest.approx(0.0)
    assert np.max(clipped[0].y) == pytest.approx(1.0)
    assert clipped.metadata["magnitude"].tolist() == [10.0]
    assert clipped.metadata["catalog"] == "galaxies"


def test_filled_polygon_clipping_removes_invisible_polygon():
    spherical, projected = polygon_collections()
    clipped = clip_polygons_to_latitude(
        spherical,
        projected,
        minimum=2.0,
    )
    assert isinstance(clipped, ProjectedPolygons)
    assert len(clipped) == 0
    assert clipped.metadata["magnitude"].size == 0


def test_complete_sphere_polygon_clipping_is_an_identity():
    spherical, _ = polygon_collections()
    projected = ProjectedPolygons(items=[])

    assert clip_polygons_to_latitude(
        spherical, projected, minimum=-90.0
    ) is projected


def test_renderer_draws_fill_and_continuous_outline_separately():
    _, projected = polygon_collections()
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    artists = renderer.draw(
        projected,
        polygon_fill_style={
            "facecolor": "gold",
            "face_alpha": 0.25,
            "zorder": layers.GALAXY_FILLS,
        },
        polygon_outline_style={
            "edgecolor": "cyan",
            "edge_alpha": 0.8,
            "linewidth": 1.2,
            "linestyle": "-",
            "zorder": layers.GALAXIES,
        },
    )
    try:
        assert len(artists) == 2
        fill, outline = artists
        assert fill.get_facecolor()[3] == pytest.approx(0.25)
        assert fill.get_edgecolor()[3] == pytest.approx(0.0)
        assert fill.get_zorder() == layers.GALAXY_FILLS
        assert outline.get_edgecolor()[3] == pytest.approx(0.8)
        assert outline.get_facecolor()[3] == pytest.approx(0.0)
        assert outline.get_linestyle() == "-"
        assert outline.get_zorder() == layers.GALAXIES
    finally:
        plt.close(figure)


def test_renderer_supports_outline_without_fill():
    _, projected = polygon_collections()
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    artists = renderer.draw(
        projected,
        polygon_outline_style={
            "edgecolor": "white",
            "edge_alpha": 0.9,
            "facecolor": "none",
            "linestyle": "-",
            "zorder": layers.GALAXIES,
        },
    )
    try:
        assert len(artists) == 1
        assert artists[0].get_facecolor()[3] == pytest.approx(0.0)
        assert artists[0].get_edgecolor()[3] == pytest.approx(0.9)
    finally:
        plt.close(figure)


def test_combined_polygon_style_supports_independent_alpha():
    _, projected = polygon_collections()
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    artists = renderer.draw(
        projected,
        style={
            "edgecolor": "red",
            "facecolor": "blue",
            "edge_alpha": 0.7,
            "face_alpha": 0.15,
            "zorder": layers.GALAXIES,
        },
    )
    try:
        assert len(artists) == 1
        assert artists[0].get_edgecolor()[3] == pytest.approx(0.7)
        assert artists[0].get_facecolor()[3] == pytest.approx(0.15)
    finally:
        plt.close(figure)


def test_global_alpha_cannot_override_independent_polygon_alpha():
    _, projected = polygon_collections()
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    try:
        with pytest.raises(ValueError, match="cannot be combined"):
            renderer.draw(
                projected,
                style={
                    "edgecolor": "white",
                    "alpha": 0.5,
                    "edge_alpha": 0.8,
                },
            )
    finally:
        plt.close(figure)


def test_named_galaxy_zorders_have_required_order():
    assert layers.MILKY_WAY < layers.GALAXY_FILLS
    assert layers.GALAXY_FILLS < layers.BOUNDARIES
    assert layers.CONSTELLATIONS < layers.GALAXIES
    assert layers.GALAXIES < layers.STARS
    assert layers.GALAXY_LABELS == layers.LABELS

# Contracts consolidated from test_milestone31_galaxy_styles.py.
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
    spherical = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
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
    assert mask["zorder"] > layers.MILKY_WAY
    assert mask["zorder"] > layers.GALAXY_FILLS
    assert mask["zorder"] > layers.GALAXIES
    assert mask["zorder"] > layers.GALAXY_LABELS




def test_requested_visual_regions_are_declared():
    regions = galaxy_regions_module().REGIONS

    assert regions["centaurus-crux-musca"].constellations == (
        "Cen",
        "Cru",
        "Mus",
    )
    assert regions["virgo-coma"].constellations == ("Vir", "Com")

# Contracts consolidated from test_milestone36c_symbol_library.py.
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time
from matplotlib.collections import PathCollection
from matplotlib.path import Path as MatplotlibPath

from wenu.charts.styles import PublicationStyle
from wenu.geometry.spherical import SphericalPoints
from wenu.objects.planetary_nebulae import PlanetaryNebulae
from wenu.projections import StereographicProjection
from wenu.rendering import MatplotlibRenderer
from wenu.rendering.symbols import DEFAULT_SYMBOLS, SymbolLibrary


class _HashableLayer:
    pass


def observer():
    return SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-07-27T02:00:00"),
            location=EarthLocation.from_geodetic(
                lon=-70.65 * u.deg,
                lat=-33.45 * u.deg,
            ),
        )
    )


def test_symbol_library_exposes_normalized_planetary_nebula():
    library = SymbolLibrary()
    marker = library["planetary_nebula"]
    assert isinstance(marker, MatplotlibPath)
    assert marker is library.planetary_nebula
    assert np.max(np.abs(marker.vertices)) == 1.0
    assert np.count_nonzero(marker.codes == MatplotlibPath.MOVETO) == 5


def test_planetary_nebulae_are_vectorized_points():
    layer = PlanetaryNebulae(
        observer(),
        selected=["PN G063.1+13.9", "PN G036.1-57.1"],
    )
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert isinstance(geometry, SphericalPoints)
    assert len(geometry) == 2
    assert geometry.metadata["symbol"] == "planetary_nebula"
    assert geometry.ids.tolist() == [
        "PN G063.1+13.9",
        "PN G036.1-57.1",
    ]


def test_style_uses_one_custom_marker_collection():
    layer = PlanetaryNebulae(
        observer(),
        selected=["PN G063.1+13.9"],
    )
    layer.load()
    spherical = layer.spherical_geometry(layer.observer)
    projection = StereographicProjection()
    projected = projection.project_geometry(spherical)
    sky = SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_cloud_isophotes={},
        galaxies=None,
        supernova_remnants=None,
        globular_clusters=None,
        planetary_nebulae=layer,
        constellation_lines=None,
        constellation_labels=None,
        constellation_boundaries=None,
        points=None,
        layers=(layer,),
    )
    style = PublicationStyle()
    options = style.layer_options(sky)[layer]
    assert options["render"]["style"]["marker"] is (
        DEFAULT_SYMBOLS.planetary_nebula
    )
    assert options["render"]["draw_labels"] is False

    fig, ax = plt.subplots()
    artists = MatplotlibRenderer(ax).draw(
        projected,
        **options["render"],
    )
    assert len(artists) == 1
    assert isinstance(artists[0], PathCollection)
    assert len(artists[0].get_offsets()) == 1
    plt.close(fig)


def test_symbol_size_is_style_controlled_not_catalogue_diameter():
    style = PublicationStyle(planetary_nebula_symbol_size=81.0)
    layer = _HashableLayer()
    sky = SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_cloud_isophotes={},
        galaxies=None,
        supernova_remnants=None,
        globular_clusters=None,
        planetary_nebulae=layer,
        constellation_lines=None,
        constellation_labels=None,
        constellation_boundaries=None,
        points=None,
        layers=(layer,),
    )
    render = style.layer_options(sky)[layer]["render"]
    assert render["style"]["s"] == 81.0

# Contracts consolidated from test_milestone40h_ellipse_callback_repair.py.
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

from wenu.charts.legend import _legend_ellipse


def test_ellipse_factory_accepts_matplotlib_keyword_contract():
    figure, ax = plt.subplots()
    try:
        original = Ellipse(
            (0.0, 0.0),
            width=1.0,
            height=0.5,
            facecolor="red",
        )
        result = _legend_ellipse(
            legend=ax.legend([], []),
            orig_handle=original,
            xdescent=0.0,
            ydescent=0.0,
            width=20.0,
            height=7.0,
            fontsize=10.0,
        )
        assert isinstance(result, Ellipse)
        assert result.width > result.height
    finally:
        plt.close(figure)

# Contracts consolidated from test_milestone40i_visual_galaxy_ellipse_repair.py.
import importlib.util
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse


def load_example():
    path = Path("tests/fixtures/example_regressions/stellar_magnitude_legend.py")
    specification = importlib.util.spec_from_file_location(
        "stellar_magnitude_legend_example_repaired",
        path,
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_visual_uses_separate_stars_and_objects_legends(tmp_path):
    module = load_example()
    destination = tmp_path / "reference.png"
    figure, _, object_legend, result = module.draw_reference(
        destination,
        dpi=80,
    )
    assert destination.is_file()
    assert object_legend.get_title().get_text() == "Objects"
    assert result.artist.get_title().get_text() == "Stars"
    assert object_legend is not result.artist
    plt.close(figure)


def test_plotted_stars_do_not_obscure_the_stars_legend():
    module = load_example()
    figure, ax, _, result = module.draw_reference()
    figure.canvas.draw()
    legend_box = result.artist.get_window_extent(
        figure.canvas.get_renderer()
    )
    star_collection = ax.collections[0]
    display_points = ax.transData.transform(
        star_collection.get_offsets()
    )
    assert not any(
        legend_box.contains(float(x), float(y))
        for x, y in display_points
    )
    plt.close(figure)


def test_object_legend_galaxy_handle_is_elliptical():
    module = load_example()
    figure, _, object_legend, _ = module.draw_reference()
    handles = object_legend.legend_handles
    assert len(handles) == 1
    assert isinstance(handles[0], Ellipse)
    assert handles[0].width > handles[0].height
    assert handles[0].get_facecolor()[-1] > 0.0
    plt.close(figure)