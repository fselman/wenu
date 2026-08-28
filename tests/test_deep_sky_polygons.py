"""Current deep sky polygons contracts."""

# Contracts consolidated from test_milestone29_galaxy_polygons.py.
"""Milestone 29 tests for galaxy polygon geometry."""

from types import SimpleNamespace

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time

from wenu.geometry.spherical import SphericalCurves, SphericalPolygons
from wenu.objects.galaxies import Galaxies
from wenu.objects.nonstellar import NonStellar


@pytest.fixture(scope="module")
def observer():
    location = EarthLocation.from_geodetic(
        lon=-71.5 * u.deg,
        lat=-33.0 * u.deg,
        height=52.0 * u.m,
    )
    return SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-08-16T01:00:00"),
            location=location,
        )
    )


@pytest.mark.integration
def test_galaxies_emit_polygons(observer):
    layer = Galaxies(observer, samples=36)
    layer.load()
    geometry = layer.spherical_geometry(
        observer,
        selected=["NGC5128"],
    )
    assert isinstance(geometry, SphericalPolygons)
    assert len(geometry) == 1
    assert geometry.ids.tolist() == ["NGC5128"]
    assert len(geometry.lon_deg[0]) == 36
    assert geometry.metadata["catalog"] == "galaxies"


@pytest.mark.integration
def test_nonstellar_messier_geometry_remains_curves(observer):
    layer = NonStellar(observer, samples=24)
    layer.load()
    geometry = layer.spherical_geometry(
        observer,
        selected=["M31"],
    )
    assert isinstance(geometry, SphericalCurves)


def test_position_angle_zero_places_major_axis_north_south():
    center = SkyCoord(ra=120.0 * u.deg, dec=-30.0 * u.deg)
    outline = Galaxies._ellipse(
        center,
        major=60.0,
        minor=20.0,
        position_angle=0.0,
        samples=72,
    )
    first_bearing = center.position_angle(outline[0]).to_value(u.deg)
    quarter_bearing = center.position_angle(
        outline[18]
    ).to_value(u.deg)
    seam_distance = min(
        abs(first_bearing),
        abs(first_bearing - 360.0),
    )
    assert seam_distance == pytest.approx(0.0, abs=1.0e-8)
    assert quarter_bearing == pytest.approx(90.0, abs=1.0e-8)
    assert center.separation(outline[0]).to_value(
        u.arcmin
    ) == pytest.approx(30.0)
    assert center.separation(outline[18]).to_value(
        u.arcmin
    ) == pytest.approx(10.0)


def test_position_angle_ninety_places_major_axis_east_west():
    center = SkyCoord(ra=120.0 * u.deg, dec=-30.0 * u.deg)
    outline = Galaxies._ellipse(
        center,
        major=60.0,
        minor=20.0,
        position_angle=90.0,
        samples=72,
    )
    first_bearing = center.position_angle(outline[0]).to_value(u.deg)
    assert first_bearing == pytest.approx(90.0, abs=1.0e-8)
    assert center.separation(outline[0]).to_value(
        u.arcmin
    ) == pytest.approx(30.0)


def test_minimum_size_preserves_axis_ratio():
    center = SkyCoord(ra=120.0 * u.deg, dec=-30.0 * u.deg)
    outline = Galaxies._ellipse(
        center,
        major=4.0,
        minor=2.0,
        position_angle=25.0,
        samples=72,
        minimum_size_arcmin=8.0,
    )
    separations = center.separation(outline).to_value(u.arcmin)
    assert np.max(separations) == pytest.approx(8.0)
    assert np.min(separations) == pytest.approx(4.0)


@pytest.mark.integration
def test_magellanic_clouds_produce_no_polygons(observer):
    layer = Galaxies(observer, samples=24)
    layer.load()
    geometry = layer.spherical_geometry(
        observer,
        selected=["NGC0292", "ESO056-115"],
    )
    assert isinstance(geometry, SphericalPolygons)
    assert len(geometry) == 0
