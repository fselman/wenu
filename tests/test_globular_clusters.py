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


def test_half_light_diameter_uses_declared_radius_units():
    source = Table({"name": ["synthetic"], "ra": [10.], "dec": [-20.]})
    source["half_light_radius"] = [120.] * u.arcsec
    source["core_radius"] = [30.] * u.arcsec
    layer = GlobularClusters(None)
    table = layer._normalize(source)
    assert table["half_light_radius"][0] == 2.
    assert table["core_radius"][0] == .5
    assert table["major_axis_arcmin"][0] == 4.
    assert table["minor_axis_arcmin"][0] == 4.
    assert table["half_light_radius"].unit == u.arcmin
    source["half_light_radius"].unit = u.m
    with pytest.raises(ValueError):
        layer._normalize(source)


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
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu.geometry.spherical import SphericalPoints
    points = layer.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None, labels_only=True)
    assert isinstance(points, SphericalPoints)
    assert points.metadata['major_axis_arcmin'].tolist() == [6.34,10.0]
    assert len(points) == 2 and len(layer.catalog) == 2


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


def test_globular_returned_kernel_centres_drive_native_and_warm_observed_routes(catalogue, observer, monkeypatch):
    from dataclasses import replace
    from astropy.coordinates import SkyCoord
    from wenu.catalogue_state import _unit_direction
    from wenu_kernel import KernelSession
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    layer = GlobularClusters(observer, samples=12, magnitude_limit=5.); layer.load(filename=catalogue)
    record = layer.catalogue_metadata.to_record()
    original = layer.source_catalog.copy(copy_data=True)
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    selected = ['NGC 5139']
    layer.spherical_centers(observer, selected=selected)
    layer.spherical_geometry(observer, selected=selected)
    evaluate, seen = KernelSession.evaluate, []
    def shift(session, query):
        batch = evaluate(session, query); seen.append(batch)
        return replace(batch, states=tuple(replace(s, vector=_unit_direction(35., -10.)) for s in batch.states))
    monkeypatch.setattr(KernelSession, 'evaluate', shift)
    points = layer.position()
    assert list(points.ids) == ['NGC 104', 'NGC 5139']
    np.testing.assert_allclose(points.lon_deg, 35.)
    labels = layer.realize(context, None, selected=selected, labels_only=True)
    np.testing.assert_allclose(labels.lon_deg, [35.])
    outline = layer.realize(context, None, selected=selected)
    expected = layer._ellipse(SkyCoord(ra=35.*u.deg, dec=-10.*u.deg), 10., 10., np.nan, 12)
    np.testing.assert_allclose(outline.lon_deg[0], expected.icrs.ra.deg)
    horizontal = layer.spherical_centers(observer, selected=selected)
    np.testing.assert_allclose(horizontal.lon_deg, [SkyCoord(ra=35.*u.deg, dec=-10.*u.deg).transform_to(observer.altaz_frame).az.deg])
    observed = layer.spherical_geometry(observer, selected=selected)
    np.testing.assert_allclose(observed.lon_deg[0], expected.transform_to(observer.altaz_frame).az.deg)
    assert observed.names.tolist() == ['omega Cen']
    assert observed.metadata['size_definition'] == 'half_light_diameter'
    assert observed.metadata['half_light_radius'].tolist() == [5.]
    assert len(seen) == 5  # One query per consumer, including warm observation.
    assert layer.catalogue_metadata.to_record() == record
    for name in original.colnames:
        np.testing.assert_array_equal(original[name], layer.source_catalog[name])


@pytest.mark.parametrize('failure', ('kernel', 'lookup'))
def test_packaged_globular_warm_routes_refuse_without_source_fallback(observer, monkeypatch, failure):
    from wenu_kernel import KernelSession
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    layer = GlobularClusters(observer, samples=12); layer.load()
    record = layer.require_catalogue_lookup_metadata().to_record()
    assert layer.admission_missing_fields
    with pytest.raises(ValueError, match='Incomplete nonstellar metadata'):
        layer.require_complete_metadata()
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    actions = (layer.position, lambda: layer.realize(context, None, labels_only=True),
               lambda: layer.realize(context, None),
               lambda: layer.spherical_centers(observer), lambda: layer.spherical_geometry(observer))
    for action in actions:
        action()
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic globular refusal')
    if failure == 'kernel':
        monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    else:
        monkeypatch.setattr(layer, 'require_catalogue_lookup_metadata', refuse)
    for action in actions:
        with pytest.raises(RuntimeError, match='globular refusal'):
            action()
    assert layer.catalogue_metadata.to_record() == record


def test_globular_provider_keeps_own_identity_and_unknown_physical_facts():
    from wenu_kernel.records import TimePoint
    from wenu.catalogue_state import catalogue_direction_states
    layer = GlobularClusters(None); layer.load()
    record = layer.catalogue_metadata.to_record()
    rows = tuple((str(r['identifier']), float(r['ra_deg']), float(r['dec_deg'])) for r in layer.catalog)
    provider = layer._direction_provider(rows, 'tt')
    descriptor = provider.describe()
    admission = descriptor.admissions[0]
    assert 'catalogue_lookup' in admission.capabilities
    assert 'globular' in admission.model.model_id
    states = catalogue_direction_states(provider, TimePoint(0, 0, 'tt'))
    assert len(states) == len(rows)
    assert all(state.source_epoch is None for state in states)
    assert record['epoch'] is None and record['origin'] is None
    assert admission.reference.origin_id == 'legacy-unverified-origin'
