"""Current globular clusters contracts."""

# Contracts consolidated from test_milestone32_globular_clusters.py.
"""Milestone 32 tests for Galactic globular clusters."""

from types import SimpleNamespace

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import AltAz, EarthLocation
from astropy.table import Table
from astropy.time import Time

from wenu.charts.styles import PublicationStyle
from wenu.geometry.spherical import SphericalCurves
from wenu.objects.globular_clusters import GlobularClusters
from wenu.objects.nonstellar import NonStellar
from wenu.rendering import layers
from wenu.resources import nonstellar_catalog_path
from wenu.sky.celestial_sphere import CelestialSphere


@pytest.fixture
def observer():
    location = EarthLocation.from_geodetic(
        lon=-71.5 * u.deg,
        lat=-33.0 * u.deg,
        height=52.0 * u.m,
    )
    return SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-05-16T02:00:00"),
            location=location,
        )
    )


@pytest.fixture
def catalogue(tmp_path):
    table = Table()
    table["name"] = ["NGC 104", "NGC 5139", "NGC 6205"]
    table["alt_name"] = ["47 Tuc", "omega Cen", "M 13"]
    table["ra"] = [6.023, 201.697, 250.421]
    table["dec"] = [-72.081, -47.480, 36.460]
    table["vmag"] = [4.09, 3.68, 5.78]
    table["half_light_radius"] = [3.17, 5.00, 1.69]
    table["core_radius"] = [0.36, 2.37, 0.62]
    table["central_concentration"] = [2.07, 1.31, 1.53]
    table["metallicity"] = [-0.72, -1.53, -1.53]
    table["helio_distance"] = [4.5, 5.2, 7.1]
    path = tmp_path / "globulars.ecsv"
    table.write(path, format="ascii.ecsv")
    return path


def test_globular_clusters_specializes_nonstellar():
    assert issubclass(GlobularClusters, NonStellar)


def test_catalogue_resource_exists_after_download():
    assert nonstellar_catalog_path("globular_clusters").is_file()


def test_normalization_uses_half_light_diameter(catalogue, observer):
    layer = GlobularClusters(observer, magnitude_limit=5.0)
    table = layer.load(filename=catalogue)
    assert list(table["identifier"]) == ["NGC 104", "NGC 5139"]
    assert table["major_axis_arcmin"].tolist() == pytest.approx(
        [6.34, 10.0]
    )
    assert table["minor_axis_arcmin"].tolist() == pytest.approx(
        [6.34, 10.0]
    )
    assert np.all(np.isnan(table["position_angle_deg"]))


def test_geometry_is_circular_and_preserves_metadata(
    catalogue,
    observer,
):
    layer = GlobularClusters(observer, samples=48)
    layer.load(filename=catalogue)
    geometry = layer.spherical_geometry(
        observer,
        selected=["NGC 5139"],
    )
    assert isinstance(geometry, SphericalCurves)
    assert geometry.closed.tolist() == [True]
    assert geometry.names.tolist() == ["omega Cen"]
    assert geometry.metadata["size_definition"] == "half_light_diameter"
    assert geometry.metadata["half_light_radius"].tolist() == [5.0]
    assert geometry.metadata["metallicity"].tolist() == [-1.53]


def test_outline_sampling_can_be_reduced_per_render(catalogue, observer):
    layer = GlobularClusters(observer, samples=48)
    layer.load(filename=catalogue)

    reduced = layer.spherical_geometry(
        observer, selected=["NGC 5139"], samples=24
    )
    complete = layer.spherical_geometry(
        observer, selected=["NGC 5139"]
    )

    assert len(reduced.lon_deg[0]) == 24
    assert len(complete.lon_deg[0]) == 48


def test_sphere_helper_loads_and_registers(catalogue, observer):
    sky = CelestialSphere(observer)
    layer = sky.add_globular_clusters(
        filename=catalogue,
        magnitude_limit=6.0,
        samples=36,
    )
    assert sky.globular_clusters is layer
    assert layer in sky.layers


def test_publication_style_uses_named_cluster_zorders(
    catalogue,
    observer,
):
    sky = CelestialSphere(observer)
    cluster = sky.add_globular_clusters(
        filename=catalogue,
        samples=36,
    )
    style = PublicationStyle(
        globular_cluster_draw_labels=True,
    )
    render = style.layer_options(sky)[cluster]["render"]
    assert render["style"]["zorder"] == layers.GLOBULAR_CLUSTERS
    assert (
        render["label_style"]["zorder"]
        == layers.GLOBULAR_CLUSTER_LABELS
    )
    assert render["style"]["linestyle"] == "-"


def test_cluster_zorder_is_between_galaxies_and_stars():
    assert (
        layers.GALAXIES
        < layers.GLOBULAR_CLUSTERS
        < layers.STARS
    )

