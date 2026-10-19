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


def test_signed_green_designations_have_distinct_semantic_keys(
    tmp_path,
    observer,
):
    table = Table()
    table["identifier"] = ["G024.7-00.6", "G024.7+00.6"]
    table["ra_deg"] = [279.679, 278.542]
    table["dec_deg"] = [-7.533, -7.083]
    table["major_axis_arcmin"] = [15.0, 30.0]
    table["minor_axis_arcmin"] = [15.0, 15.0]
    path = tmp_path / "signed-snr.ecsv"
    table.write(path, format="ascii.ecsv")

    layer = SupernovaRemnants(observer)
    layer.load(filename=path)
    geometry = layer.spherical_geometry(observer)

    assert geometry.metadata["semantic_entity_keys"] == (
        "G024.7_minus_00.6",
        "G024.7_plus_00.6",
    )
    assert geometry.metadata["semantic_entity_display_names"] == (
        "G024.7-00.6",
        "G024.7+00.6",
    )


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


def test_snr_returned_centres_drive_selected_native_and_warm_observed_geometry(catalogue, observer, monkeypatch):
    from dataclasses import replace
    from astropy.coordinates import SkyCoord
    from wenu.catalogue_state import _unit_direction
    from wenu_kernel import KernelSession
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    layer = SupernovaRemnants(observer, selected=['G184.6-5.8'], samples=12)
    layer.load(filename=catalogue)
    original = layer.source_catalog.copy(copy_data=True)
    record = layer.catalogue_metadata.to_record()
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    layer.spherical_centers(observer, selected=['G184.6-5.8'])
    layer.spherical_geometry(observer)
    values = {'G184.6-5.8': (35., -10.), 'G263.9-3.3': (75., 15.)}
    evaluate, calls = KernelSession.evaluate, []
    def shift(session, query):
        batch = evaluate(session, query); calls.append(batch)
        return replace(batch, states=tuple(replace(s, vector=_unit_direction(
            *values[s.object_key.value.rsplit(':', 1)[-1]])) for s in batch.states))
    monkeypatch.setattr(KernelSession, 'evaluate', shift)
    native = layer.position()
    np.testing.assert_allclose(native.lon_deg, [35., 75.])
    assert list(native.ids) == ['G184.6-5.8', 'G263.9-3.3']
    labels = layer.realize(context, None, labels_only=True)
    assert list(labels.ids) == ['G184.6-5.8']
    np.testing.assert_allclose(labels.lon_deg, [35.])
    assert labels.metadata['semantic_entity_keys'] == ('G184.6_minus_5.8',)
    outline = layer.realize(context, None)
    expected = layer._ellipse(SkyCoord(ra=35.*u.deg, dec=-10.*u.deg), 7., 5., np.nan, 12)
    np.testing.assert_allclose(outline.lon_deg[0], expected.icrs.ra.deg)
    points = layer.spherical_centers(observer, selected=['G184.6-5.8'])
    np.testing.assert_allclose(points.lon_deg,
        [SkyCoord(ra=35.*u.deg, dec=-10.*u.deg).transform_to(observer.altaz_frame).az.deg])
    observed = layer.spherical_geometry(observer)
    np.testing.assert_allclose(observed.lon_deg[0], expected.transform_to(observer.altaz_frame).az.deg)
    assert observed.metadata['major_axis_arcmin'].tolist() == [7.]
    assert observed.metadata['minor_axis_arcmin'].tolist() == [5.]
    assert observed.metadata['flux_1ghz_jy'].tolist() == [1040.]
    assert observed.metadata['position_angle_available'] is False
    assert observed.metadata['flux_1ghz_is_optical_visibility'] is False
    assert len(calls) == 5  # One state query per consumer, including warm caches.
    assert layer.catalogue_metadata.to_record() == record
    for name in original.colnames:
        np.testing.assert_array_equal(original[name], layer.source_catalog[name])


@pytest.mark.parametrize('failure', ('kernel', 'lookup'))
def test_packaged_snr_routes_refuse_after_warm_centre_and_outline_caches(observer, monkeypatch, failure):
    from wenu_kernel import KernelSession
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    layer = SupernovaRemnants(observer, selected=['G263.9-03.3'], samples=12); layer.load()
    record = layer.require_catalogue_lookup_metadata().to_record()
    with pytest.raises(ValueError, match='Incomplete nonstellar metadata'):
        layer.require_complete_metadata()
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    actions = (layer.position, lambda: layer.realize(context, None),
        lambda: layer.realize(context, None, labels_only=True),
        lambda: layer.spherical_centers(observer), lambda: layer.spherical_geometry(observer))
    for action in actions:
        action()
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic SNR refusal')
    if failure == 'kernel':
        monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    else:
        monkeypatch.setattr(layer, 'require_catalogue_lookup_metadata', refuse)
    for action in actions:
        with pytest.raises(RuntimeError, match='SNR refusal'):
            action()
    assert layer.catalogue_metadata.to_record() == record


def test_snr_lookup_retains_310_source_identities_and_unknown_physical_facts():
    from wenu.catalogue_state import catalogue_direction_states
    from wenu_kernel.records import TimePoint
    layer = SupernovaRemnants(None); layer.load()
    record = layer.catalogue_metadata.to_record()
    rows = tuple((str(row['identifier']), float(row['ra_deg']), float(row['dec_deg'])) for row in layer.catalog)
    provider = layer._direction_provider(rows, 'tt')
    admission = provider.describe().admissions[0]
    assert 'supernova-remnant' in admission.model.model_id
    assert 'catalogue_lookup' in admission.capabilities
    assert admission.reference.origin_id == 'legacy-unverified-origin'
    states = catalogue_direction_states(provider, TimePoint(0, 0, 'tt'))
    assert len(states) == len(rows) == 310
    assert all(state.source_epoch is None for state in states)
    assert record['epoch'] is None and record['origin'] is None
