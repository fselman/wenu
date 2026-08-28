"""Current open clusters contracts."""

# Contracts consolidated from test_milestone37b_open_clusters.py.
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
from wenu.objects.open_clusters import OpenClusters
from wenu.projections import StereographicProjection
from wenu.rendering import MatplotlibRenderer
from wenu.rendering.symbols import DEFAULT_SYMBOLS
from wenu.resources import nonstellar_catalog_path


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


def test_packaged_open_cluster_catalogue():
    path = nonstellar_catalog_path("open_clusters")
    assert path.is_file()
    layer = OpenClusters(observer())
    table = layer.load()
    assert len(table) == 1931
    assert "IC 2602" in set(table["identifier"])
    assert "NGC 4755" in set(table["identifier"])


def test_requested_order_and_metadata_are_preserved():
    layer = OpenClusters(
        observer(),
        selected=["NGC 4755", "IC 2602"],
    )
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert isinstance(geometry, SphericalPoints)
    assert geometry.ids.tolist() == ["NGC 4755", "IC 2602"]
    assert geometry.metadata["symbol"] == "open_cluster"
    assert "apparent_diameter_arcmin" in geometry.metadata


def test_open_cluster_coordinates_are_vectorized_and_finite():
    layer = OpenClusters(
        observer(),
        selected=["IC 2391", "NGC 3532", "NGC 2516"],
    )
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert len(geometry) == 3
    assert np.all(np.isfinite(geometry.lon_deg))
    assert np.all(np.isfinite(geometry.lat_deg))


def test_empty_selection_returns_empty_points():
    layer = OpenClusters(observer(), selected=["not-a-cluster"])
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert isinstance(geometry, SphericalPoints)
    assert len(geometry) == 0


def test_sequential_open_cluster_selections_share_observed_catalogue():
    layer = OpenClusters(observer())
    layer.load()

    first = layer.spherical_geometry(
        layer.observer,
        selected=["IC 2602"],
    )
    second = layer.spherical_geometry(
        layer.observer,
        selected=["NGC 4755"],
    )

    assert first.ids.tolist() == ["IC 2602"]
    assert second.ids.tolist() == ["NGC 4755"]
    assert len(layer._observed_point_cache) == 1


def test_open_cluster_symbol_is_dotted_circumference():
    marker = DEFAULT_SYMBOLS.open_cluster
    assert isinstance(marker, Path)
    assert np.max(np.abs(marker.vertices)) <= 1.0
    assert np.count_nonzero(marker.codes == Path.MOVETO) == 12


def test_publication_style_uses_symbol_library_and_optional_labels():
    layer = _HashableLayer()
    sky = SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_cloud_isophotes={},
        galaxies=None,
        supernova_remnants=None,
        planetary_nebulae=None,
        globular_clusters=None,
        open_clusters=layer,
        constellation_lines=None,
        constellation_labels=None,
        constellation_boundaries=None,
        points=None,
        layers=(layer,),
    )
    style = PublicationStyle(open_cluster_symbol_size=81.0)
    render = style.layer_options(sky)[layer]["render"]
    assert render["style"]["marker"] is DEFAULT_SYMBOLS.open_cluster
    assert render["style"]["s"] == 81.0
    assert render["draw_labels"] is False


def test_selected_clusters_render_as_one_path_collection():
    layer = OpenClusters(
        observer(),
        selected=["IC 2602", "NGC 4755"],
    )
    layer.load()
    spherical = layer.spherical_geometry(layer.observer)
    projected = StereographicProjection().project_geometry(spherical)
    fig, ax = plt.subplots()
    artists = MatplotlibRenderer(ax).draw(
        projected,
        style={
            "marker": DEFAULT_SYMBOLS.open_cluster,
            "s": 64.0,
            "facecolors": "white",
            "edgecolors": "white",
        },
    )
    assert len(artists) == 1
    assert isinstance(artists[0], PathCollection)
    assert len(artists[0].get_offsets()) == 2
    plt.close(fig)