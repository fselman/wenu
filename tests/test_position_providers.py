"""Milestone 49B.3 native astronomical position-provider contracts."""

import numpy as np
import pandas as pd
import pytest
from astropy.table import Table

from wenu.geometry import SphericalPoints
from wenu.objects.galaxies import Galaxies
from wenu.objects.globular_clusters import GlobularClusters
from wenu.objects.nonstellar import NonStellar
from wenu.objects.open_clusters import OpenClusters
from wenu.objects.planetary_nebulae import PlanetaryNebulae
from wenu.objects.stars import Stars
from wenu.objects.supernova_remnants import SupernovaRemnants
from wenu.positions import PositionProvider
from wenu.sky.horizon import HorizonReference


def test_stars_provide_static_native_icrs_positions(monkeypatch):
    from wenu_kernel import KernelSession
    from wenu.stellar_state import HIPPARCOS_SOURCE_EPOCH
    calls = []
    evaluate = KernelSession.evaluate
    def capture(session, query):
        calls.append(query)
        return evaluate(session, query)
    monkeypatch.setattr(KernelSession, 'evaluate', capture)
    stars = Stars(None, catalog="hipparcos")
    stars.catalog = pd.DataFrame(
        {
            "ra_hours": [1.0, 2.0],
            "dec_degrees": [-30.0, 45.0],
            "magnitude": [1.5, 2.5],
        },
        index=[100, 200],
    )

    geometry = stars.position("2026-08-28T00:00:00")

    assert isinstance(stars, PositionProvider)
    assert isinstance(geometry, SphericalPoints)
    np.testing.assert_allclose(geometry.lon_deg, [15.0, 30.0])
    np.testing.assert_allclose(geometry.lat_deg, [-30.0, 45.0])
    assert geometry.ids.tolist() == [100, 200]
    assert geometry.coordinate_spec.frame == "icrs"
    assert geometry.coordinate_spec.origin == "solar-system-barycenter"
    assert geometry.coordinate_spec.instant is None
    assert geometry.coordinate_spec.epoch == "J1991.25"
    assert len(calls) == 1 and calls[0].times == (HIPPARCOS_SOURCE_EPOCH,)
    assert tuple(key.value for key in calls[0].objects) == ('hipparcos:100', 'hipparcos:200')


def _native_star_source():
    """Synthetic source: faint and missing-coordinate rows exceed marker selection."""
    stars = Stars(None, magnitude_limit=2)
    stars.source_catalog = pd.DataFrame(dict(ra_degrees=[15., 30., np.nan],
        ra_hours=[1., 2., np.nan], dec_degrees=[-30., 45., 0.],
        magnitude=[1., 9., 3.], is_variable=[False, True, False]), index=[100, 200, 300])
    stars.catalog = stars.source_catalog.iloc[:1].copy()
    return stars


def test_native_id_query_keeps_faint_rows_missing_coordinates_and_source_order(monkeypatch):
    from wenu_kernel import KernelSession
    stars = _native_star_source()
    source, active = stars.source_catalog.copy(deep=True), stars.catalog.copy(deep=True)
    queries = []
    evaluate = KernelSession.evaluate
    def capture(session, query):
        queries.append(query)
        return evaluate(session, query)
    monkeypatch.setattr(KernelSession, 'evaluate', capture)
    points = stars.native_positions([300, 200, 100, 404])
    np.testing.assert_array_equal(points.ids, [100, 200, 300])
    np.testing.assert_array_equal(points.lon_deg, [15., 30., np.nan])
    np.testing.assert_array_equal(points.metadata['magnitude'], [1., 9., 3.])
    np.testing.assert_array_equal(points.metadata['is_variable'], [False, True, False])
    assert len(queries) == 1
    assert tuple(key.value for key in queries[0].objects) == ('hipparcos:100', 'hipparcos:200')
    assert points.coordinate_spec.epoch == 'J1991.25' and points.coordinate_spec.instant is None
    pd.testing.assert_frame_equal(source, stars.source_catalog)
    pd.testing.assert_frame_equal(active, stars.catalog)


def test_native_position_uses_authoritative_degree_encoding_when_both_columns_exist():
    stars = _native_star_source()
    # A derived hours column must not replace the source's degree encoding.
    stars.source_catalog.loc[100, 'ra_hours'] = np.nextafter(1., np.inf)
    stars.catalog = stars.source_catalog.iloc[:1].copy()
    before = stars.catalog.copy(deep=True)
    direct, selected = stars.position(), stars.native_positions([100])
    np.testing.assert_array_equal(direct.lon_deg, [15.])
    np.testing.assert_array_equal(selected.lon_deg, direct.lon_deg)
    assert direct.coordinate_spec == selected.coordinate_spec
    pd.testing.assert_frame_equal(before, stars.catalog)


@pytest.mark.parametrize('route', ('position', 'native_positions'))
def test_native_position_routes_use_returned_kernel_direction_and_propagate_failure(monkeypatch, route):
    from dataclasses import replace
    from wenu_kernel import KernelSession
    stars = _native_star_source()
    evaluate = KernelSession.evaluate
    def quarter_turn(session, query):
        batch = evaluate(session, query)
        return replace(batch, states=tuple(replace(state,
            vector=(-state.vector[1], state.vector[0], state.vector[2])) for state in batch.states))
    def query():
        return stars.position('2026-08-28T00:00:00') if route == 'position' else stars.native_positions([100])
    monkeypatch.setattr(KernelSession, 'evaluate', quarter_turn)
    np.testing.assert_allclose(query().lon_deg, [105.], rtol=0, atol=1e-12)
    def fail(*args):
        raise RuntimeError('synthetic native state refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', fail)
    with pytest.raises(RuntimeError, match='native state refusal'):
        query()


def test_native_id_query_empty_absent_and_unloaded_policies(monkeypatch):
    from wenu_kernel import KernelSession
    stars = _native_star_source()
    def forbidden(*args):
        raise AssertionError('An empty selection must not query the kernel')
    monkeypatch.setattr(KernelSession, 'evaluate', forbidden)
    assert len(stars.native_positions([])) == len(stars.native_positions([404])) == 0
    with pytest.raises(RuntimeError, match='catalogue has not been loaded'):
        Stars(None).native_positions([100])


def test_nonstellar_catalogues_provide_native_centres_not_morphology():
    objects = NonStellar(None, catalog="messier")
    objects.catalog = Table(
        {
            "identifier": ["M1", "M31"],
            "ra_deg": [83.633, 10.685],
            "dec_deg": [22.014, 41.269],
            "magnitude": [8.4, 3.4],
        }
    )

    geometry = objects.position()

    assert isinstance(objects, PositionProvider)
    np.testing.assert_allclose(geometry.lon_deg, [83.633, 10.685])
    np.testing.assert_allclose(geometry.lat_deg, [22.014, 41.269])
    assert geometry.names.tolist() == ["M1", "M31"]
    assert geometry.coordinate_spec.frame == "icrs"


def test_open_clusters_provide_selected_native_centres():
    clusters = OpenClusters(None, selected=("NGC 2516",))
    clusters.catalog = Table(
        {
            "identifier": ["NGC 2516", "NGC 3532"],
            "ra_deg": [119.5, 166.4],
            "dec_deg": [-60.8, -58.7],
            "apparent_diameter_arcmin": [30.0, 50.0],
            "object_type": ["Open Cluster", "Open Cluster"],
        }
    )

    geometry = clusters.position()

    assert isinstance(clusters, PositionProvider)
    assert geometry.ids.tolist() == ["NGC 2516"]
    np.testing.assert_allclose(geometry.lon_deg, [119.5])
    np.testing.assert_allclose(geometry.lat_deg, [-60.8])


def test_nonstellar_subclasses_share_the_centre_provider_boundary():
    assert Galaxies.position is NonStellar.position
    assert GlobularClusters.position is NonStellar.position
    assert PlanetaryNebulae.position is NonStellar.position
    assert SupernovaRemnants.position is NonStellar.position


def test_constructed_reference_geometry_is_not_a_position_provider():
    assert not isinstance(HorizonReference(), PositionProvider)


@pytest.mark.parametrize(
    "provider",
    (Stars(None), NonStellar(None), OpenClusters(None)),
)
def test_unloaded_providers_reject_position_requests(provider):
    with pytest.raises(RuntimeError, match="catalogue has not been loaded"):
        provider.position()
