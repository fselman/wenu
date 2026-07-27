from types import SimpleNamespace

import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time

from wenu.geometry.spherical import SphericalPoints
from wenu.objects.planetary_nebulae import PlanetaryNebulae
from wenu.resources import nonstellar_catalog_path


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


def test_packaged_planetary_nebula_catalogue_exists():
    path = nonstellar_catalog_path("planetary_nebulae")
    assert path.is_file()


def test_catalogue_loads_true_and_probable_objects():
    layer = PlanetaryNebulae(observer())
    table = layer.load()
    assert len(table) == 1143
    assert "PN G063.1+13.9" in set(table["identifier"])
    assert "PN G036.1-57.1" in set(table["identifier"])


def test_selection_is_case_insensitive():
    layer = PlanetaryNebulae(observer())
    layer.load()
    geometry = layer.spherical_geometry(
        layer.observer,
        selected=["pn g063.1+13.9"],
    )
    assert geometry.ids.tolist() == ["PN G063.1+13.9"]


def test_geometry_is_one_point_per_object():
    layer = PlanetaryNebulae(
        observer(),
        selected=["PN G063.1+13.9", "PN G036.1-57.1"],
        samples=72,
    )
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert isinstance(geometry, SphericalPoints)
    assert len(geometry) == 2
    assert np.all(np.isfinite(geometry.lon_deg))
    assert np.all(np.isfinite(geometry.lat_deg))


def test_catalogue_measurements_are_metadata_not_glyph_size():
    layer = PlanetaryNebulae(
        observer(),
        selected=["PN G036.1-57.1"],
    )
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert "major_axis_arcmin" in geometry.metadata
    assert "minor_axis_arcmin" in geometry.metadata
    assert geometry.metadata["geometry_kind"] == "cartographic_symbol"


def test_empty_selection_returns_empty_points():
    layer = PlanetaryNebulae(observer(), selected=["not-an-object"])
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert isinstance(geometry, SphericalPoints)
    assert len(geometry) == 0
