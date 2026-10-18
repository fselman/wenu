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


class TrackedProvider(bridge.LegacyNativeStellarProvider):
    def __init__(self, rows):
        self.work = self.closes = 0
        super().__init__(rows, namespace="synthetic", source_epoch=bridge.HIPPARCOS_SOURCE_EPOCH,
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
                       (bridge.HIPPARCOS_SOURCE_EPOCH, TimePoint(2451545, 0.0, "tt")),
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
            source_epoch=bridge.HIPPARCOS_SOURCE_EPOCH, provenance=("constructed analytic axes",))
        expected = ((1, 0, 0), (0, 1, 0), (-sqrt(6)/4, -sqrt(6)/4, -.5), (0, 0, 1))
        self.assertEqual(bridge.native_stellar_angles(states, rows),
                         tuple((lon, lat) for _, lon, lat in rows))
        for state, vector in zip(states, expected):
            self.assertEqual(state.source_epoch, bridge.HIPPARCOS_SOURCE_EPOCH)
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
        self.assertTrue(all(s.source_epoch == bridge.HIPPARCOS_SOURCE_EPOCH for s in states))
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
                           (bridge.HIPPARCOS_SOURCE_EPOCH,), admission.reference, AccuracyRequest())
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
                                source_epoch=bridge.HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",))
                else:
                    bridge.native_stellar_states([('a', 0., 0.)], namespace="synthetic",
                        source_epoch=bridge.HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",))
                self.assertEqual(created[-1].closes, 1)
                with self.assertRaises(ClosedSession):created[-1].describe()

    def test_failed_registration_and_empty_tables_retain_caller_cleanup(self):
        with patch.object(bridge.LegacyNativeStellarProvider, "close", autospec=True) as close:
            self.assertEqual(bridge.native_stellar_states([], namespace="synthetic",
                source_epoch=bridge.HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",)), ())
            self.assertEqual(close.call_count, 1)
        with patch.object(Kernel, "register", side_effect=RuntimeError("synthetic registration failure")), \
                patch.object(bridge.LegacyNativeStellarProvider, "close", autospec=True) as close:
            with self.assertRaisesRegex(RuntimeError, "registration failure"):
                bridge.native_stellar_states([('a', 0., 0.)], namespace="synthetic",
                    source_epoch=bridge.HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",))
            self.assertEqual(close.call_count, 1)


if __name__ == "__main__":
    unittest.main()
