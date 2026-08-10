"""Current supernova remnants contracts."""

# Contracts consolidated from test_milestone35b_supernova_remnants.py.
"""Milestone 35B tests for Galactic supernova remnants."""

from types import SimpleNamespace

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import AltAz, EarthLocation
from astropy.table import Table
from astropy.time import Time

from wenu.charts.styles import PublicationStyle
from wenu.geometry.spherical import SphericalCurves
from wenu.objects.nonstellar import NonStellar
from wenu.objects.supernova_remnants import SupernovaRemnants
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
            obstime=Time("2026-12-15T02:00:00"),
            location=location,
        )
    )


@pytest.fixture
def catalogue(tmp_path):
    table = Table()
    table["identifier"] = ["G184.6-5.8", "G263.9-3.3"]
    table["ra_deg"] = [83.633, 128.75]
    table["dec_deg"] = [22.017, -45.6]
    table["galactic_longitude_deg"] = [184.6, 263.9]
    table["galactic_latitude_deg"] = [-5.8, -3.3]
    table["major_axis_arcmin"] = [7.0, 255.0]
    table["minor_axis_arcmin"] = [5.0, 255.0]
    table["morphology"] = ["F", "C"]
    table["flux_1ghz_jy"] = [1040.0, 1750.0]
    table["flux_limit_flag"] = ["", ""]
    table["flux_uncertain"] = ["", "?"]
    table["spectral_index"] = [0.30, 0.40]
    table["spectral_index_flag"] = ["v", ""]
    table["alternate_names"] = ["Crab Nebula", "Vela"]
    path = tmp_path / "snr.ecsv"
    table.write(path, format="ascii.ecsv")
    return path


def test_supernova_remnants_specializes_nonstellar():
    assert issubclass(SupernovaRemnants, NonStellar)


def test_catalogue_resource_exists_after_download():
    resource = nonstellar_catalog_path("supernova_remnants")
    assert resource.is_file()


def test_catalogue_snapshot_contains_green_2024_rows():
    table = Table.read(nonstellar_catalog_path("supernova_remnants"))
    assert len(table) == 310
    assert "G184.6-05.8" in set(table["identifier"])
    assert "flux_1ghz_jy" in table.colnames


def test_normalization_preserves_radio_metadata(catalogue, observer):
    layer = SupernovaRemnants(observer, samples=48)
    table = layer.load(filename=catalogue)
    assert table["identifier"].tolist() == [
        "G184.6-5.8",
        "G263.9-3.3",
    ]
    assert table["morphology"].tolist() == ["F", "C"]
    assert table["flux_1ghz_jy"].tolist() == [1040.0, 1750.0]
    assert np.all(np.isnan(table["position_angle_deg"]))
    assert np.all(np.isnan(table["magnitude"]))


def test_geometry_uses_equal_area_circle_without_inventing_pa(
    catalogue,
    observer,
):
    layer = SupernovaRemnants(observer, samples=72)
    layer.load(filename=catalogue)
    geometry = layer.spherical_geometry(
        observer,
        selected=["G184.6-5.8"],
    )
    assert isinstance(geometry, SphericalCurves)
    assert geometry.closed.tolist() == [True]
    assert geometry.metadata["major_axis_arcmin"].tolist() == [7.0]
    assert geometry.metadata["minor_axis_arcmin"].tolist() == [5.0]
    assert geometry.metadata["position_angle_available"] is False
    assert geometry.metadata["flux_1ghz_is_optical_visibility"] is False
    assert "equal_area_circle" in geometry.metadata[
        "shape_representation"
    ]


def test_outline_sampling_can_be_reduced_per_render(catalogue, observer):
    layer = SupernovaRemnants(observer, samples=48)
    layer.load(filename=catalogue)

    reduced = layer.spherical_geometry(
        observer, selected=["G184.6-5.8"], samples=24
    )
    complete = layer.spherical_geometry(
        observer, selected=["G184.6-5.8"]
    )

    assert len(reduced.lon_deg[0]) == 24
    assert len(complete.lon_deg[0]) == 48


def test_sphere_helper_loads_and_registers(catalogue, observer):
    sky = CelestialSphere(observer)
    layer = sky.add_supernova_remnants(
        filename=catalogue,
        samples=48,
    )
    assert sky.supernova_remnants is layer
    assert layer in sky.layers


def test_publication_style_uses_named_snr_zorders(
    catalogue,
    observer,
):
    sky = CelestialSphere(observer)
    layer = sky.add_supernova_remnants(
        filename=catalogue,
        samples=48,
    )
    style = PublicationStyle(
        supernova_remnant_draw_labels=True,
    )
    render = style.layer_options(sky)[layer]["render"]
    assert render["style"]["zorder"] == layers.SUPERNOVA_REMNANTS
    assert (
        render["label_style"]["zorder"]
        == layers.SUPERNOVA_REMNANT_LABELS
    )
    assert render["style"]["linestyle"] == "--"


def test_snr_zorder_is_between_galaxies_and_stars():
    assert (
        layers.GALAXIES
        < layers.SUPERNOVA_REMNANTS
        < layers.STARS
    )
