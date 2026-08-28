"""Current nonstellar catalogue contracts."""

# Contracts consolidated from test_milestone26_nonstellar.py.
"""Milestone 26 tests for the NonStellar catalogue layer."""

from types import SimpleNamespace

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.table import Table
from astropy.time import Time

from wenu.geometry.spherical import SphericalCurves
from wenu.objects.astronomical_object import AstronomicalObject
from wenu.objects.nonstellar import NonStellar
from wenu.sky.celestial_sphere import CelestialSphere


@pytest.fixture
def catalogue(tmp_path):
    table = Table()
    table["name"] = ["M 1", "M 31", "M 42"]
    table["ra"] = [83.633, 10.685, 83.822]
    table["dec"] = [22.014, 41.269, -5.391]
    table["dimension"] = ["6 x 4", "190X60", "85"]
    table["vmag"] = [8.4, 3.4, 4.0]
    table["object_type"] = ["SNR", "Galaxy", "Nebula"]
    table["pa"] = [30.0, np.nan, np.nan]
    path = tmp_path / "messier.ecsv"
    table.write(path, format="ascii.ecsv")
    return path


@pytest.fixture
def observer():
    location = EarthLocation.from_geodetic(
        lon=-71.5 * u.deg,
        lat=-33.0 * u.deg,
        height=52.0 * u.m,
    )
    frame = AltAz(
        obstime=Time("2026-08-16T01:00:00"),
        location=location,
    )
    return SimpleNamespace(altaz_frame=frame)


def test_nonstellar_is_the_single_catalogue_layer():
    assert issubclass(NonStellar, AstronomicalObject)


def test_dimension_parser():
    assert NonStellar.parse_dimension("26 X 14") == (26.0, 14.0)
    assert NonStellar.parse_dimension("80") == (80.0, 80.0)
    major, minor = NonStellar.parse_dimension("")
    assert np.isnan(major)
    assert np.isnan(minor)


def test_load_normalizes_heasarc_fields(catalogue, observer):
    layer = NonStellar(observer, samples=36)
    result = layer.load(filename=catalogue)
    assert list(result["identifier"]) == ["M 1", "M 31", "M 42"]
    assert result["major_axis_arcmin"][1] == 190.0
    assert result["minor_axis_arcmin"][1] == 60.0
    assert result["position_angle_deg"][0] == 30.0


def test_geometry_is_closed_and_transformed(catalogue, observer):
    layer = NonStellar(observer, samples=36)
    layer.load(filename=catalogue)
    geometry = layer.spherical_geometry(observer)
    assert isinstance(geometry, SphericalCurves)
    assert len(geometry) == 3
    assert np.all(geometry.closed)
    assert all(len(curve) == 36 for curve in geometry.lon_deg)
    assert np.all(np.isfinite(geometry.lon_deg[0]))
    assert geometry.metadata["coordinate_system"] == "altaz"
    assert geometry.metadata["semantic_entity_keys"] == (
        "M 1", "M 31", "M 42"
    )
    assert geometry.metadata["semantic_entity_display_names"] == (
        "M 1", "M 31", "M 42"
    )
    assert geometry.metadata["semantic_entity_categories"] == (
        "supernova_remnants", "galaxies", "nebulae"
    )


@pytest.mark.parametrize(
    ("object_type", "identifier", "category"),
    (
        ("Galaxy", None, "galaxies"),
        ("S", None, "galaxies"),
        ("E", None, "galaxies"),
        ("E?", None, "galaxies"),
        ("IR", None, "galaxies"),
        ("Open Cluster", None, "open_clusters"),
        ("OC", None, "open_clusters"),
        ("GC", None, "globular_clusters"),
        ("GB", None, "globular_clusters"),
        ("Planetary Nebula", None, "planetary_nebulae"),
        ("PL", None, "planetary_nebulae"),
        ("SNR", None, "supernova_remnants"),
        ("DI", "M 1", "supernova_remnants"),
        ("DI", "M 8", "nebulae"),
        ("Emission Nebula", None, "nebulae"),
        ("H II region", None, "nebulae"),
        ("Unclassified", None, "other_objects"),
        (None, None, "other_objects"),
    ),
)
def test_catalog_object_types_use_shared_astronomical_categories(
    object_type, identifier, category
):
    assert NonStellar.semantic_category(
        object_type,
        identifier=identifier,
    ) == category


def test_unknown_position_angle_does_not_invent_orientation():
    center = SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg)
    outline = NonStellar._ellipse(center, 16.0, 4.0, np.nan, 72)
    separations = center.separation(outline).to_value(u.arcmin)
    assert np.ptp(separations) < 1.0e-10
    assert separations[0] == pytest.approx(4.0)


def test_selection(catalogue, observer):
    layer = NonStellar(observer, samples=24)
    layer.load(filename=catalogue)
    geometry = layer.spherical_geometry(
        observer,
        selected=["M 31"],
    )
    assert list(geometry.ids) == ["M 31"]
    assert geometry.metadata["semantic_entity_keys"] == ("M 31",)
    assert geometry.metadata["semantic_entity_display_names"] == ("M 31",)
    assert geometry.metadata["semantic_entity_categories"] == (
        "galaxies",
    )


def test_outline_sampling_is_render_local_and_bounded(catalogue, observer):
    layer = NonStellar(observer, samples=36)
    layer.load(filename=catalogue)

    reduced = layer.spherical_geometry(observer, samples=18)
    complete = layer.spherical_geometry(observer)

    assert all(len(curve) == 18 for curve in reduced.lon_deg)
    assert all(len(curve) == 36 for curve in complete.lon_deg)
    assert layer.samples == 36
    with pytest.raises(ValueError, match="at least 12"):
        layer.spherical_geometry(observer, samples=11)
    with pytest.raises(ValueError, match="maximum sampling quality"):
        layer.spherical_geometry(observer, samples=37)


def test_outline_selections_share_one_quality_specific_cache(
    catalogue, observer, monkeypatch
):
    layer = NonStellar(observer, samples=36)
    layer.load(filename=catalogue)
    calls = []

    def transform(
        table,
        resolved,
        *,
        samples,
        minimum_size_arcmin,
    ):
        calls.append((len(table), samples, minimum_size_arcmin))
        return (
            tuple(np.full(samples, index) for index in range(len(table))),
            tuple(np.full(samples, -index) for index in range(len(table))),
        )

    monkeypatch.setattr(layer, "_transform_outline_table", transform)
    first = layer.spherical_geometry(
        observer,
        selected=["M 31"],
        samples=18,
        minimum_size_arcmin=2.0,
    )
    second = layer.spherical_geometry(
        observer,
        selected=["M 42", "M 1"],
        samples=18,
        minimum_size_arcmin=2.0,
    )

    assert first.ids.tolist() == ["M 31"]
    assert second.ids.tolist() == ["M 1", "M 42"]
    assert calls == [(3, 18, 2.0)]
    assert len(layer._observed_outline_cache) == 1
    cached = next(iter(layer._observed_outline_cache.values()))
    assert all(
        values.flags.writeable is False
        for coordinate in cached
        for values in coordinate
    )


def test_outline_quality_and_reload_select_distinct_realizations(
    catalogue, observer, monkeypatch
):
    layer = NonStellar(observer, samples=36)
    layer.load(filename=catalogue)
    calls = []

    def transform(
        table,
        resolved,
        *,
        samples,
        minimum_size_arcmin,
    ):
        calls.append((samples, minimum_size_arcmin))
        values = tuple(np.zeros(samples) for _ in table)
        return values, values

    monkeypatch.setattr(layer, "_transform_outline_table", transform)
    for samples, minimum in ((18, None), (36, None), (36, 2.0)):
        layer.spherical_geometry(
            observer,
            samples=samples,
            minimum_size_arcmin=minimum,
        )

    assert calls == [(18, None), (36, None), (36, 2.0)]
    assert len(layer._observed_outline_cache) == 3

    layer.load(filename=catalogue)
    assert layer._observed_outline_cache == {}


def test_celestial_sphere_helper_loads_and_registers(
    catalogue,
    observer,
):
    sky = CelestialSphere(observer)
    layer = sky.add_nonstellar(filename=catalogue, samples=24)
    assert sky.nonstellar is layer
    assert layer in sky.layers

