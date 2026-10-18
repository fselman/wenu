"""Native lookup adapter contracts; constructed rows, not catalogue accuracy."""
from dataclasses import replace
from math import sqrt
import unittest
from unittest.mock import patch

from wenu_kernel import Kernel
from wenu_kernel.conformance import ProviderActivity, ProviderCase, ProviderConformance
from wenu_kernel.errors import ClosedSession, InvalidQuery, UnsupportedCapability
from wenu_kernel.records import AccuracyRequest, SessionPolicy, StateQuery, TimePoint
from wenu import stellar_state as bridge
import json
import pandas as pd
import pytest
from stellar_catalogue_fixtures import native_table
from wenu.stellar_catalogue import (
    METADATA_KEY, StellarCatalogueMetadata, ingest_stellar_catalogue,
    source_stellar_metadata, stellar_table_metadata,
)

# Explicit synthetic fixture epoch, not a production catalogue default.
HIPPARCOS_SOURCE_EPOCH = TimePoint(2448349, 0.0625, 'tt')


def test_catalogue_metadata_controls_kernel_and_all_native_outputs(monkeypatch, tmp_path):
    from wenu.objects.stars import Stars
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu_kernel import KernelSession
    stars = Stars(None)
    table = native_table(pd.DataFrame(dict(ra_degrees=[15., 30.], dec_degrees=[20., 25.],
                                         magnitude=[1., 2.]), index=[100, 200]), epoch=2016.)
    record = table.attrs[METADATA_KEY]
    record['edition'] = 'synthetic-2016'
    record['provenance'] = ['independent synthetic metadata']
    record['source_metadata']['extra_source_field'] = ['preserve', {'nested': 42}]
    table = ingest_stellar_catalogue(table, StellarCatalogueMetadata.from_record(record)).table
    stars.source_catalog = stars.catalog = table
    seen = []
    evaluate = KernelSession.evaluate
    def capture(session, query):
        result = evaluate(session, query)
        seen.append(result)
        return result
    monkeypatch.setattr(KernelSession, 'evaluate', capture)
    from wenu.sky.constellation_lines import ConstellationLines
    from wenu.sky.constellation_labels import ConstellationLabels
    graph = tmp_path / 'synthetic.fab'
    graph.write_text('Ari 2 100 200\n')
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    outputs = (stars.position(), stars.native_positions([100]), stars.realize(context, None),
               ConstellationLines(stars, filename=graph).realize(context, None),
               ConstellationLabels(stars, min_stars=1).realize(context, None),
               ConstellationLabels(stars, selected={'ZZZ'}).realize(context, None))
    for output in outputs:
        assert output.coordinate_spec.epoch == 'J2016'
        assert output.coordinate_spec.provenance == ('independent synthetic metadata',)
    metadata = stellar_table_metadata(table)
    assert all(batch.states[0].source_epoch == metadata.source_epoch for batch in seen)
    assert metadata.source_epoch == TimePoint(2457389., 0., 'tt')
    assert metadata.to_record() == record
    record['epoch']['value'] = 1900.
    assert metadata.epoch_label == 'J2016'


@pytest.mark.parametrize('field', ('epoch', 'frame', 'origin', 'units', 'edition', 'provenance', 'source_sha256'))
def test_catalogue_missing_required_metadata_is_refused(field):
    table = native_table(pd.DataFrame(dict(ra_degrees=[15.], dec_degrees=[20.]), index=[100]))
    record = table.attrs[METADATA_KEY]
    del record[field]
    with pytest.raises(ValueError, match='metadata'):
        StellarCatalogueMetadata.from_record(record)


@pytest.mark.parametrize('fault', ('missing_epoch', 'epoch_mismatch', 'missing_unit', 'duplicate_id', 'wrong_frame', 'wrong_angle_unit', 'source_epoch_conflict', 'missing_time_scale'))
def test_catalogue_inconsistent_astrometry_is_refused(fault):
    table = native_table(pd.DataFrame(dict(ra_degrees=[15., 30.], dec_degrees=[20., 25.]), index=[100, 200]))
    record = table.attrs[METADATA_KEY]
    if fault == 'missing_epoch': table = table.drop(columns=['epoch_year'])
    if fault == 'epoch_mismatch': table.loc[200, 'epoch_year'] = 2000.
    if fault == 'missing_unit': del record['units']['epoch_year']
    if fault == 'duplicate_id': table.index = [100, 100]
    if fault == 'wrong_frame': record['frame'] = 'fk5'
    if fault == 'wrong_angle_unit': record['units']['ra_degrees'] = 'rad'
    if fault == 'source_epoch_conflict': record['source_metadata']['reference_epoch_jd'] = 2451545.
    if fault == 'missing_time_scale': del record['epoch']['scale']
    with pytest.raises(ValueError):
        ingest_stellar_catalogue(table, StellarCatalogueMetadata.from_record(record))


def test_catalogue_source_identity_checked_before_publication(tmp_path, monkeypatch):
    from wenu.objects.stars import Stars
    table = native_table(pd.DataFrame(dict(ra_degrees=[15.], dec_degrees=[20.]), index=[100]))
    stars = Stars(None)
    stars.source_catalog = stars.catalog = table
    path = tmp_path / 'custom.dat'
    path.write_bytes(b'wrong bytes')
    def forbidden(*args):
        raise AssertionError('Unidentified source reached the parser')
    monkeypatch.setattr('wenu.objects.stars.hipparcos.load_dataframe', forbidden)
    with pytest.raises(ValueError, match='Source bytes differ'):
        stars.load(filename=path, metadata=table.attrs[METADATA_KEY])
    assert stars.source_catalog is stars.catalog is table
    bare = table.copy(); bare.attrs.clear()
    with pytest.raises(ValueError, match='ingest it before use'):
        stellar_table_metadata(bare)


def test_catalogue_sidecar_and_unknown_source_metadata_are_preserved(tmp_path):
    from hashlib import sha256
    table = native_table(pd.DataFrame(dict(ra_degrees=[15.], dec_degrees=[20.]), index=[100]))
    record = table.attrs[METADATA_KEY]
    payload = b'explicit custom catalogue bytes'
    record['source_sha256'] = sha256(payload).hexdigest()
    record['source_metadata']['publication'] = {'doi': 'synthetic:fixture'}
    path = tmp_path / 'custom.dat'
    path.with_name(path.name + '.metadata.json').write_text(json.dumps(record))
    metadata = source_stellar_metadata('hipparcos', payload, path)
    normalized = ingest_stellar_catalogue(table, metadata)
    assert normalized.table.attrs[METADATA_KEY] == record
    assert normalized.metadata.to_record() == record


class TrackedProvider(bridge.LegacyNativeStellarProvider):
    def __init__(self, rows):
        self.work = self.closes = 0
        super().__init__(rows, namespace="synthetic", source_epoch=HIPPARCOS_SOURCE_EPOCH,
                         provenance=("constructed native lookup fixture",))

    def _direction(self, key):
        self.work += 1
        return super()._direction(key)

    def close(self):
        self.closes += 1
        super().close()


def make_case():
    source = [["a", 0.0, 0.0], ["b", 90.0, 30.0]]
    provider = TrackedProvider(source)
    admission = provider.describe().admissions[0]
    # Different sample times test a static LOOKUP, never epoch propagation.
    query = StateQuery(admission.catalogue, admission.model, admission.objects,
                       (HIPPARCOS_SOURCE_EPOCH, TimePoint(2451545, 0.0, "tt")),
                       admission.reference, AccuracyRequest())
    probe = replace(query, times=(TimePoint(2460000, 0.0, "tt"),))

    def mutate():
        source[0][1] = 180.0
        source.append(["c", 45.0, 0.0])

    return ProviderCase(provider, query, probe,
                        lambda: ProviderActivity(provider.work, 0, provider.closes), mutate)


class TestNativeStellarConformance(ProviderConformance, unittest.TestCase):
    make_case = staticmethod(make_case)


class TestNativeStellarAdapter(unittest.TestCase):
    def test_analytic_vectors_source_epoch_and_unknown_uncertainty(self):
        rows = [("a", 0.0, 0.0), ("b", 90.0, 0.0), ("c", 225.0, -30.0), ("d", 0.0, 90.0)]
        states = bridge.native_stellar_states(rows, namespace="synthetic",
            source_epoch=HIPPARCOS_SOURCE_EPOCH, provenance=("constructed analytic axes",))
        expected = ((1, 0, 0), (0, 1, 0), (-sqrt(6)/4, -sqrt(6)/4, -.5), (0, 0, 1))
        self.assertEqual(bridge.native_stellar_angles(states, rows),
                         tuple((lon, lat) for _, lon, lat in rows))
        for state, vector in zip(states, expected):
            self.assertEqual(state.source_epoch, HIPPARCOS_SOURCE_EPOCH)
            self.assertEqual(state.time, state.source_epoch)
            self.assertEqual(state.source_epoch.jd1 + state.source_epoch.jd2,
                             2451545.0 - 8.75 * 365.25)
            self.assertEqual(state.source_epoch.scale, "tt")
            self.assertEqual(state.reference.status, "native-catalogue")
            for actual, target in zip(state.vector, vector):
                self.assertAlmostEqual(actual, target, delta=1e-15)
            for channel in (state.evidence.measurement, state.evidence.physical_model, state.evidence.numerical):
                self.assertEqual((channel.status, channel.value), ("not_evaluated", None))

    def test_fixed_lookup_cannot_claim_motion_accuracy_or_certification(self):
        case = make_case(); provider = case.provider
        self.addCleanup(provider.close)
        admission = provider.describe().admissions[0]
        self.assertNotIn("epoch_direction", admission.capabilities)
        self.assertIn("native_direction", admission.capabilities)
        states = provider.evaluate(case.query).states
        self.assertEqual(states[0].vector, states[2].vector)
        self.assertTrue(all(s.source_epoch == HIPPARCOS_SOURCE_EPOCH for s in states))
        for query in (replace(case.query, accuracy=AccuracyRequest(angular_rad=1e-6)),
                      replace(case.query, evaluation_policy="bounded_reuse"),
                      replace(case.query, require_velocity=True)):
            with self.subTest(query=query):
                self.assertFalse(provider.supports(query).supported)
                with self.assertRaises(UnsupportedCapability):provider.evaluate(query)

    def test_input_change_changes_binding_and_original_buffers_do_not_alias(self):
        source = [["a", 12.0, -34.0]]
        first = TrackedProvider(source); original = first.describe()
        admission = original.admissions[0]
        query = StateQuery(admission.catalogue, admission.model, admission.objects,
                           (HIPPARCOS_SOURCE_EPOCH,), admission.reference, AccuracyRequest())
        before = first.evaluate(query)
        source[0][1] = 56.0
        second = TrackedProvider(source)
        self.addCleanup(first.close);self.addCleanup(second.close)
        self.assertEqual(first.describe(), original)
        self.assertNotEqual(original.catalogues, second.describe().catalogues)
        self.assertEqual(first.evaluate(query), before)
        self.assertEqual(first.work, 2)
        self.assertEqual(second.work, 0)

    def test_invalid_rows_do_not_fabricate_kernel_states(self):
        for rows in ([('a', float('nan'), 0.0)], [('a', 0.0, 91.0)],
                     [('a', True, 0.0)], [('a', 0.0, 0.0), ('a', 1.0, 0.0)]):
            with self.subTest(rows=rows), self.assertRaises(InvalidQuery):
                TrackedProvider(rows)

    def test_owned_service_closes_once_after_success_and_evaluation_failure(self):
        created = []
        original = bridge.LegacyNativeStellarProvider
        class Provider(original):
            def __init__(self, *args, **kwargs):
                self.closes = 0; created.append(self);super().__init__(*args, **kwargs)
            def close(self):self.closes += 1;super().close()
        for fail in (False, True):
            with self.subTest(fail=fail), patch.object(bridge, "LegacyNativeStellarProvider", Provider):
                if fail:
                    with patch.object(Provider, "evaluate", side_effect=RuntimeError("synthetic backend failure")):
                        with self.assertRaisesRegex(Exception, "evaluate failed"):
                            bridge.native_stellar_states([('a', 0., 0.)], namespace="synthetic",
                                source_epoch=HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",))
                else:
                    bridge.native_stellar_states([('a', 0., 0.)], namespace="synthetic",
                        source_epoch=HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",))
                self.assertEqual(created[-1].closes, 1)
                with self.assertRaises(ClosedSession):created[-1].describe()

    def test_failed_registration_and_empty_tables_retain_caller_cleanup(self):
        with patch.object(bridge.LegacyNativeStellarProvider, "close", autospec=True) as close:
            self.assertEqual(bridge.native_stellar_states([], namespace="synthetic",
                source_epoch=HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",)), ())
            self.assertEqual(close.call_count, 1)
        with patch.object(Kernel, "register", side_effect=RuntimeError("synthetic registration failure")), \
                patch.object(bridge.LegacyNativeStellarProvider, "close", autospec=True) as close:
            with self.assertRaisesRegex(RuntimeError, "registration failure"):
                bridge.native_stellar_states([('a', 0., 0.)], namespace="synthetic",
                    source_epoch=HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",))
            self.assertEqual(close.call_count, 1)


if __name__ == "__main__":
    unittest.main()
