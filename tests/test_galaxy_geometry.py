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
        centres=None,
    ):
        assert centres is not None
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


def _synthetic_kernel_galaxies(tmp_path, *, epoch=None):
    from astropy.table import Table
    source = Table(dict(name=['synthetic'], ra_deg=[10.], dec_deg=[-20.],
                        major_axis_arcmin=[2.], minor_axis_arcmin=[1.], position_angle_deg=[30.]))
    source.meta = dict(catalog='synthetic', release='synthetic-v1', coordinate_frame='ICRS',
                       coordinate_origin='solar-system-barycenter',
                       documentation_url='https://example.invalid/synthetic')
    if epoch is not None:
        source.meta.update(coordinate_epoch=epoch, coordinate_epoch_scale='tt')
    for name in source.colnames:
        if name.endswith('_deg'): source[name].unit = 'deg'
        elif name.endswith('_arcmin'): source[name].unit = 'arcmin'
    path = tmp_path/'kernel-galaxy.ecsv'
    source.write(path, overwrite=True)
    layer = Galaxies(None, samples=12)
    layer.load(filename=path, require_complete_metadata=True)
    return layer


@pytest.mark.parametrize('epoch', (None, 'J2016.0'))
def test_galaxy_kernel_queries_preserve_optional_epoch_and_actual_requested_time(tmp_path, monkeypatch, epoch):
    from wenu_kernel import KernelSession
    from wenu_kernel.records import TimePoint
    layer = _synthetic_kernel_galaxies(tmp_path, epoch=epoch)
    before = layer.catalogue_metadata.document_json
    seen = []
    evaluate = KernelSession.evaluate
    def capture(session, query):
        result = evaluate(session, query)
        seen.append((session.catalogue(query.catalogue), result))
        return result
    monkeypatch.setattr(KernelSession, 'evaluate', capture)
    for year in (-10000., 10000.):
        time = Time(year, format='jyear', scale='tt')
        points = layer.position(time)
        snapshot, batch = seen[-1]
        assert batch.query.times == (TimePoint(float(time.jd1), float(time.jd2), 'tt'),)
        assert snapshot.objects[0].capabilities == ('static_direction', 'batch_evaluation')
        expected = None if epoch is None else TimePoint(2457389, 0, 'tt')
        assert batch.states[0].source_epoch == expected
        assert batch.states[0].time == batch.states[0].anchor_time == batch.query.times[0]
        assert batch.states[0].evidence.physical_model.status == 'not_evaluated'
        np.testing.assert_array_equal(points.lon_deg, [10.])
        assert points.metadata['catalogue_admission'] == layer.catalogue_metadata.to_record()
    assert layer.catalogue_metadata.document_json == before


def test_galaxy_kernel_returned_vectors_drive_every_centre_and_outline_route(tmp_path, monkeypatch):
    from dataclasses import replace
    from astropy.coordinates import SkyCoord
    from wenu_kernel import KernelSession
    from wenu.catalogue_state import _unit_direction
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    layer = _synthetic_kernel_galaxies(tmp_path)
    evaluate = KernelSession.evaluate
    calls = []
    def shifted(session, query):
        batch = evaluate(session, query)
        calls.append(query)
        return replace(batch, states=tuple(replace(row, vector=_unit_direction(35., -10.))
                                          for row in batch.states))
    monkeypatch.setattr(KernelSession, 'evaluate', shifted)
    np.testing.assert_allclose(layer.position().lon_deg, [35.], atol=1e-12)
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    labels = layer.realize(context, None, labels_only=True)
    np.testing.assert_allclose(labels.lon_deg, [35.], atol=1e-12)
    expected = layer._ellipse(SkyCoord(ra=35.*u.deg, dec=-10.*u.deg), 2., 1., 30., 12)
    native = layer.realize(context, None)
    np.testing.assert_allclose(native.lon_deg[0], expected.icrs.ra.deg, atol=1e-12)
    current_observer = observer()
    centres = layer.spherical_centers(current_observer)
    horizontal = SkyCoord(ra=35.*u.deg, dec=-10.*u.deg).transform_to(current_observer.altaz_frame)
    np.testing.assert_allclose(centres.lon_deg, [horizontal.az.deg], atol=1e-10)
    observed = layer.spherical_geometry(current_observer)
    expected_horizontal = expected.transform_to(current_observer.altaz_frame)
    np.testing.assert_allclose(observed.lon_deg[0], expected_horizontal.az.deg, atol=1e-10)
    assert len(calls) == 5
    np.testing.assert_array_equal(layer.catalog['ra_deg'], [10.])


@pytest.mark.parametrize('route', ('position', 'native-outlines', 'native-labels', 'observed-centres', 'observed-outlines'))
def test_galaxy_kernel_refusal_has_no_direct_catalogue_fallback(tmp_path, monkeypatch, route):
    from wenu_kernel import KernelSession
    from wenu_kernel.errors import UnsupportedCapability
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    layer = _synthetic_kernel_galaxies(tmp_path)
    def refuse(*args):
        raise UnsupportedCapability('synthetic galaxy refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    with pytest.raises(UnsupportedCapability, match='synthetic galaxy refusal'):
        if route == 'position': layer.position()
        elif route.startswith('native'):
            layer.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None, labels_only=route=='native-labels')
        elif route == 'observed-centres': layer.spherical_centers(observer())
        else: layer.spherical_geometry(observer())


def test_packaged_galaxy_kernel_reference_keeps_unknown_source_origin_explicit(monkeypatch):
    from wenu_kernel import KernelSession
    layer = Galaxies(None); layer.load()
    source_record = layer.catalogue_metadata.to_record()
    seen = []
    evaluate = KernelSession.evaluate
    def capture(session, query):
        seen.append(query)
        return evaluate(session, query)
    monkeypatch.setattr(KernelSession, 'evaluate', capture)
    points = layer.position()
    assert source_record['origin'] is None
    assert seen[0].reference.origin_id == 'legacy-unverified-origin'
    assert seen[0].reference.status == 'legacy-unverified-catalogue-encoding'
    assert points.coordinate_spec.model == 'legacy-unverified-catalogue-encoding'
    assert points.metadata['catalogue_admission'] == source_record
    assert layer.admission_missing_fields
    with pytest.raises(ValueError): layer.require_complete_metadata()


def test_galaxy_provider_passes_shipped_kernel_conformance(tmp_path):
    from dataclasses import replace
    import io
    import unittest
    from wenu_kernel.conformance import ProviderActivity, ProviderCase, provider_suite
    from wenu_kernel.records import AccuracyRequest, StateQuery, TimePoint
    layer = _synthetic_kernel_galaxies(tmp_path)
    def factory():
        rows = [['synthetic', 10., -20.]]
        provider = layer._direction_provider(rows, 'tt')
        admission = provider.describe().admissions[0]
        query = StateQuery(admission.catalogue, admission.model, admission.objects,
            (TimePoint(-1000000, 0, 'tt'), TimePoint(3000000, 0, 'tt')),
            admission.reference, AccuracyRequest())
        probe = replace(query, times=(TimePoint(4000000, 0, 'tt'),))
        counts = {'evaluate': 0, 'close': 0}
        evaluate, close = provider.evaluate, provider.close
        def measured(query):
            counts['evaluate'] += 1
            return evaluate(query)
        def cleanup():
            counts['close'] += 1
            return close()
        provider.evaluate, provider.close = measured, cleanup
        def mutate():
            rows[0][1] = 99.
        return ProviderCase(provider, query, probe,
            lambda: ProviderActivity(counts['evaluate'], 0, counts['close']), mutate)
    result = unittest.TextTestRunner(stream=io.StringIO()).run(provider_suite(factory, name='GalaxyStaticContract'))
    assert result.wasSuccessful(), result.errors + result.failures
    assert result.testsRun == 8 and not result.skipped


def test_galaxy_unknown_epoch_scale_remains_provenance_without_blocking_lookup(tmp_path, monkeypatch):
    layer = _synthetic_kernel_galaxies(tmp_path, epoch='J2016.0')
    # Source may preserve an unqualified date, but the SDK cannot invent its scale.
    from astropy.table import Table
    path = tmp_path/'kernel-galaxy.ecsv'
    table = Table.read(path)
    del table.meta['coordinate_epoch_scale']
    table.write(path, overwrite=True)
    layer.load(filename=path)
    assert layer.catalogue_metadata.to_record()['epoch'] == 'J2016.0'
    assert layer.catalogue_metadata.to_record()['epoch_scale'] is None
    from wenu_kernel import KernelSession
    evaluate, seen = KernelSession.evaluate, []
    def capture(session, query):
        batch = evaluate(session, query)
        seen.extend(batch.states)
        return batch
    monkeypatch.setattr(KernelSession, 'evaluate', capture)
    points = layer.position()
    np.testing.assert_array_equal(points.lon_deg, [10.])
    assert seen and all(state.source_epoch is None for state in seen)
    assert points.metadata['catalogue_admission']['epoch'] == 'J2016.0'
    assert points.metadata['catalogue_admission']['epoch_scale'] is None


def test_galaxy_warm_observed_caches_follow_changed_kernel_centres(tmp_path, monkeypatch):
    from dataclasses import replace
    from astropy.coordinates import SkyCoord
    from wenu_kernel import KernelSession
    from wenu.catalogue_state import _unit_direction
    layer = _synthetic_kernel_galaxies(tmp_path)
    resolved = observer()
    old_points = layer.spherical_centers(resolved)
    old_outline = layer.spherical_geometry(resolved)
    evaluate, calls = KernelSession.evaluate, []
    def shift(session, query):
        calls.append(query)
        batch = evaluate(session, query)
        return replace(batch, states=tuple(replace(state, vector=_unit_direction(35., -10.)) for state in batch.states))
    monkeypatch.setattr(KernelSession, 'evaluate', shift)
    points = layer.spherical_centers(resolved)
    outline = layer.spherical_geometry(resolved)
    assert len(calls) == 2  # One state query per path, no second outline evaluation.
    horizontal = SkyCoord(ra=35.*u.deg, dec=-10.*u.deg).transform_to(resolved.altaz_frame)
    expected = layer._ellipse(SkyCoord(ra=35.*u.deg, dec=-10.*u.deg), 2., 1., 30., 12).transform_to(resolved.altaz_frame)
    np.testing.assert_allclose(points.lon_deg, [horizontal.az.deg], atol=1e-10)
    np.testing.assert_allclose(outline.lon_deg[0], expected.az.deg, atol=1e-10)
    assert not np.allclose(old_points.lon_deg, points.lon_deg)
    assert not np.allclose(old_outline.lon_deg[0], outline.lon_deg[0])
    layer.spherical_centers(resolved); layer.spherical_geometry(resolved)
    assert len(calls) == 4
    assert len(layer._observed_point_cache) == len(layer._observed_outline_cache) == 2
    np.testing.assert_array_equal(layer.catalog['ra_deg'], [10.])


@pytest.mark.parametrize('failure', ('kernel', 'lookup'))
@pytest.mark.parametrize('route', ('position', 'native-outlines', 'native-labels', 'observed-centres', 'observed-outlines'))
def test_galaxy_warm_routes_refuse_failed_lookup_or_kernel_without_fallback(tmp_path, monkeypatch, failure, route):
    from wenu_kernel import KernelSession
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    layer = _synthetic_kernel_galaxies(tmp_path)
    resolved = observer()
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    actions = {'position': lambda: layer.position(),
        'native-outlines': lambda: layer.realize(context, None),
        'native-labels': lambda: layer.realize(context, None, labels_only=True),
        'observed-centres': lambda: layer.spherical_centers(resolved),
        'observed-outlines': lambda: layer.spherical_geometry(resolved)}
    actions[route]()
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic galaxy admission refusal')
    if failure == 'kernel':
        monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    else:
        monkeypatch.setattr(layer, 'require_catalogue_lookup_metadata', refuse)
    with pytest.raises(RuntimeError, match='galaxy admission refusal'):
        actions[route]()


def test_packaged_galaxy_routes_apply_lookup_admission_without_qualifying_physical_gaps(monkeypatch):
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    layer = Galaxies(None, samples=12); layer.load()
    before = layer.catalogue_metadata.to_record()
    validate, seen = layer.require_catalogue_lookup_metadata, []
    def capture():
        seen.append(True)
        return validate()
    monkeypatch.setattr(layer, 'require_catalogue_lookup_metadata', capture)
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    layer.position()
    layer.realize(context, None, selected=['NGC5128'], labels_only=True)
    layer.realize(context, None, selected=['NGC5128'])
    layer.spherical_centers(observer(), selected=['NGC5128'])
    layer.spherical_geometry(observer(), selected=['NGC5128'])
    assert len(seen) == 5
    assert before == layer.catalogue_metadata.to_record()
    assert before['frame'] is None and before['origin'] is None
    with pytest.raises(ValueError, match='Incomplete nonstellar metadata'):
        layer.require_complete_metadata()
