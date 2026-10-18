"""Current galaxy geometry contracts."""

# Contracts consolidated from test_milestone28_galaxies.py.
"""Milestone 28 tests for the Galaxies domain layer."""

from types import SimpleNamespace

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time

from wenu import Galaxies
from wenu.geometry.spherical import SphericalPolygons
from wenu.objects.nonstellar import NonStellar
from wenu.sky.celestial_sphere import CelestialSphere


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


def test_static_galaxy_admission_does_not_require_a_measurement_epoch(tmp_path):
    """Synthetic ICRS directions: static model, no fabricated measurement date."""
    from astropy.table import Table
    from astropy.time import Time
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    source = Table(dict(name=['synthetic'], ra_deg=[10.], dec_deg=[-20.],
                        major_axis_arcmin=[2.], minor_axis_arcmin=[1.], position_angle_deg=[30.]))
    source.meta = dict(catalog='synthetic', release='synthetic-v1', coordinate_frame='ICRS',
                       coordinate_origin='solar-system-barycenter',
                       documentation_url='https://example.invalid/synthetic')
    source['catalogue_position_model'] = ['source-epoch']
    for name in source.colnames:
        if name.endswith('_deg'):
            source[name].unit = 'deg'
        elif name.endswith('_arcmin'):
            source[name].unit = 'arcmin'
    path = tmp_path/'static-galaxy.ecsv'
    source.write(path)
    layer = Galaxies(None)
    layer.load(filename=path, require_complete_metadata=True)
    assert layer.position_model == 'static-direction'
    assert layer.admission_missing_fields == ()
    assert layer.require_complete_metadata() is layer.catalogue_metadata
    assert layer.catalogue_metadata.require_complete(position_model='static-direction') is layer.catalogue_metadata
    with pytest.raises(ValueError, match='epoch'):
        layer.catalogue_metadata.require_complete()
    assert layer.catalogue_metadata.to_record()['epoch'] is None
    assert layer.catalogue_metadata.to_record()['epoch_scale'] is None
    assert layer.source_catalog['catalogue_position_model'].tolist() == ['source-epoch']
    positions = [layer.position(time) for time in Time([-10000., 2000., 10000.], format='jyear', scale='tt')]
    for points in positions:
        np.testing.assert_array_equal(points.lon_deg, [10.])
        np.testing.assert_array_equal(points.lat_deg, [-20.])
        assert points.coordinate_spec.epoch is None
        assert points.coordinate_spec.model == 'static-direction'
        assert points.metadata['catalogue_position_model'] == 'static-direction'
    native = layer.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None)
    assert native.coordinate_spec == positions[0].coordinate_spec
    assert native.metadata['catalogue_position_model'] == 'static-direction'
    # A supplied source epoch is retained as provenance; the model stays static.
    source.meta.update(coordinate_epoch='J2016.0', coordinate_epoch_scale='tt')
    source.write(path, overwrite=True)
    layer.load(filename=path, require_complete_metadata=True)
    assert layer.catalogue_metadata.to_record()['epoch'] == 'J2016.0'
    for time in Time([-10000., 10000.], format='jyear', scale='tt'):
        np.testing.assert_array_equal(layer.position(time).lon_deg, [10.])
        assert layer.position(time).coordinate_spec.model == 'static-direction'
    # Removing epoch requirements must not relax the other coordinate facts.
    source.meta.pop('coordinate_frame')
    source.write(path, overwrite=True)
    previous = layer.catalog
    with pytest.raises(ValueError, match='frame'):
        layer.load(filename=path, require_complete_metadata=True)
    assert layer.catalog is previous


def test_galaxies_is_a_nonstellar_specialization():
    assert issubclass(Galaxies, NonStellar)
    assert Galaxies.layer_name == "galaxies"


@pytest.mark.integration
def test_galaxy_catalogue_retains_openngc_metadata():
    layer = Galaxies(observer=None)
    catalogue = layer.load()
    assert len(catalogue) == 1058
    for name in (
        "b_magnitude",
        "v_magnitude",
        "selection_magnitude",
        "selection_band",
        "surface_brightness_b_mag_arcsec2",
        "morphology",
        "common_names",
        "identifiers",
        "rendering_class",
    ):
        assert name in catalogue.colnames
    assert np.max(catalogue["magnitude"]) <= 12.0


@pytest.mark.integration
def test_default_geometry_excludes_two_isophote_systems():
    layer = Galaxies(observer(), samples=24)
    layer.load()
    table = layer._geometry_table()
    assert len(table) == 1056
    assert set(table["rendering_class"]) == {"ellipse"}


@pytest.mark.integration
def test_magellanic_clouds_do_not_generate_ellipse_geometry():
    current_observer = observer()
    layer = Galaxies(current_observer, samples=24)
    layer.load()
    geometry = layer.spherical_geometry(
        current_observer,
        selected=["NGC0292", "ESO056-115"],
    )
    assert isinstance(geometry, SphericalPolygons)
    assert len(geometry) == 0


@pytest.mark.integration
def test_selected_galaxy_geometry_preserves_catalogue_metadata():
    current_observer = observer()
    layer = Galaxies(current_observer, samples=24)
    layer.load()
    geometry = layer.spherical_geometry(
        current_observer,
        selected=["NGC5128"],
    )
    assert isinstance(geometry, SphericalPolygons)
    assert len(geometry) == 1
    assert geometry.ids.tolist() == ["NGC5128"]
    assert len(geometry.lon_deg[0]) == 24
    # Polygon boundaries are implicitly closed; unlike curves,
    # SphericalPolygons intentionally has no ``closed`` attribute.
    assert not hasattr(geometry, "closed")
    assert geometry.metadata["selection_band"].tolist() == ["V"]
    assert geometry.metadata["rendering_class"].tolist() == ["ellipse"]
    assert geometry.metadata["morphology"][0]
    assert np.isfinite(
        geometry.metadata["surface_brightness_b_mag_arcsec2"][0]
    )


@pytest.mark.integration
def test_galaxy_outline_sampling_can_be_reduced_per_render():
    current_observer = observer()
    layer = Galaxies(current_observer, samples=24)
    layer.load()

    reduced = layer.spherical_geometry(
        current_observer,
        selected=["NGC5128"],
        samples=12,
    )
    complete = layer.spherical_geometry(
        current_observer,
        selected=["NGC5128"],
    )

    assert len(reduced.lon_deg[0]) == 12
    assert len(complete.lon_deg[0]) == 24
    assert layer.samples == 24


@pytest.mark.integration
def test_galaxy_selections_reuse_inherited_maximal_outline_cache(
    monkeypatch,
):
    current_observer = observer()
    layer = Galaxies(current_observer, samples=24)
    layer.load()
    calls = []

    def transform(
        table,
        resolved,
        *,
        samples,
        minimum_size_arcmin,
    ):
        calls.append(len(table))
        values = tuple(np.zeros(samples) for _ in table)
        return values, values

    monkeypatch.setattr(layer, "_transform_outline_table", transform)
    first = layer.spherical_geometry(
        current_observer, selected=["NGC5128"]
    )
    second = layer.spherical_geometry(
        current_observer, selected=["NGC0224"]
    )

    assert first.ids.tolist() == ["NGC5128"]
    assert second.ids.tolist() == ["NGC0224"]
    assert calls == [1056]


@pytest.mark.integration
def test_galaxies_and_messier_can_coexist_on_one_sky():
    sky = CelestialSphere(observer())
    messier = sky.add_nonstellar(samples=24)
    galaxies = sky.add_galaxies(samples=24)
    assert sky.nonstellar is messier
    assert sky.galaxies is galaxies
    assert messier is not galaxies
    assert messier in sky.layers
    assert galaxies in sky.layers
    assert messier.catalog_name == "messier"
    assert galaxies.catalog_name == "galaxies"
