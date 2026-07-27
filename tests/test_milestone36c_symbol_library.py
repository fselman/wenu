from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time
from matplotlib.collections import PathCollection
from matplotlib.path import Path

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
    assert isinstance(marker, Path)
    assert marker is library.planetary_nebula
    assert np.max(np.abs(marker.vertices)) == 1.0
    assert np.count_nonzero(marker.codes == Path.MOVETO) == 5


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
