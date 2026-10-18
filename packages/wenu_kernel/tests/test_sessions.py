"""Synthetic provider faults and registry/session composition/failure contracts."""

from dataclasses import replace
import unittest

from wenu_kernel import Kernel
from wenu_kernel.errors import (
    AccuracyUnavailable, ClosedSession, IncompatibleContract, InvalidProviderResult,
    InvalidQuery,
    OutsideCoverage, ProviderBusy, ProviderEvaluationError, ResourceMismatch,
    TimeConversionUnavailable, UnknownObject, UnsupportedCapability,
)
from wenu_kernel.records import AccuracyRequest, ObjectKey, SessionPolicy, TimePoint
from synthetic_providers import EPOCH, FixedDirections, MovingDirections, REFERENCE


class SyntheticProviderChecks:
    """Fixture-specific mutation/failure checks retained with their old test IDs.

    The portable provider gate is shipped in wenu_kernel.conformance; these
    synthetic hooks and numerical expectations are not part of that API.
    """

    def test_order_identity_and_identical_query_reuse(self):
        times = (replace(EPOCH, jd2=.1), EPOCH)
        query = self.provider.query(times=times, objects=tuple(reversed(self.provider.objects)))
        result = self.session.evaluate(query)
        self.assertEqual([(r.time, r.object_key) for r in result.states],
                         [(t, obj) for t in times for obj in query.objects])
        self.assertEqual(result.query, query)
        self.assertIs(result, self.session.evaluate(query))
        self.assertEqual(self.provider.calls["evaluate"], 1)

    def test_result_survives_buffer_mutation_session_and_provider_close(self):
        result = self.session.evaluate(self.provider.query())
        vectors = tuple(r.vector for r in result.states)
        for buffer in self.provider.buffers:
            buffer[:] = [999, 999, 999]
        self.session.close()
        self.kernel.close()
        self.assertEqual(tuple(r.vector for r in result.states), vectors)
        self.assertEqual(len(result.states), 2)

    def test_full_model_new_time_is_not_temporally_reused(self):
        a = self.session.evaluate(self.provider.query())
        b = self.session.evaluate(self.provider.query(times=(replace(EPOCH, jd1=EPOCH.jd1+1),)))
        self.assertEqual(self.provider.calls["evaluate"], 2)
        self.assertEqual(a.states[0].vector == b.states[0].vector, self.provider.rate == 0)

    def test_failed_batch_never_enters_exact_query_cache(self):
        for fault in ("reorder", "omit", "duplicate", "wrong_epoch", "wrong_anchor"):
            self.provider.fault = fault
            with self.subTest(fault=fault), self.assertRaises(InvalidProviderResult):
                self.session.evaluate(self.provider.query())
        self.provider.fault = None
        self.assertEqual(len(self.session.evaluate(self.provider.query()).states), 2)
        self.assertEqual(self.provider.calls["evaluate"], 6)

    def test_tighter_accuracy_never_uses_looser_result_or_statistical_claim(self):
        self.session.evaluate(self.provider.query())
        query = self.provider.query(accuracy=AccuracyRequest(angular_rad=1e-16))
        with self.assertRaises(AccuracyUnavailable):
            self.session.evaluate(query)
        query = replace(query, accuracy=AccuracyRequest(angular_rad=1e-12))
        for fault in ("statistical", "unknown_error"):
            self.provider.fault = fault
            with self.subTest(fault=fault), self.assertRaises(AccuracyUnavailable):
                self.session.evaluate(query)
        self.provider.fault = None
        self.session.evaluate(query)
        self.assertEqual(self.provider.calls["evaluate"], 5)


class FixedProviderTests(SyntheticProviderChecks, unittest.TestCase):
    def setUp(self):
        self.provider = FixedDirections("fixed")
        self.kernel = Kernel(references=(REFERENCE,))
        self.kernel.register(self.provider, ownership="owned")
        self.session = self.kernel.open_session(SessionPolicy((self.provider.reference,)))

    def tearDown(self):
        self.session.close()
        self.kernel.close()


class MovingProviderTests(FixedProviderTests):
    def setUp(self):
        self.provider = MovingDirections("moving")
        self.kernel = Kernel(references=(REFERENCE,))
        self.kernel.register(self.provider, ownership="owned")
        self.session = self.kernel.open_session(SessionPolicy((self.provider.reference,)))


class StaticDirectionTests(unittest.TestCase):
    def open_provider(self, provider, *, reproducibility="reproducible"):
        kernel = Kernel(references=(REFERENCE,))
        self.addCleanup(kernel.close)
        kernel.register(provider, ownership="owned")
        session = kernel.open_session(SessionPolicy((provider.reference,), reproducibility=reproducibility))
        self.addCleanup(session.close)
        return session

    def test_unknown_and_declared_epochs_stay_distinct_from_evaluation_time(self):
        from synthetic_providers import StaticDirections
        for source_epoch in (None, EPOCH):
            with self.subTest(source_epoch=source_epoch):
                provider = StaticDirections(source_epoch=source_epoch)
                session = self.open_provider(provider)
                times = (provider.coverage.start, provider.coverage.stop)
                result = session.evaluate(provider.query(times=times))
                for row in result.states:
                    self.assertEqual(row.source_epoch, source_epoch)
                    self.assertEqual(row.anchor_time, row.time)
                    self.assertEqual(row.evidence.physical_model.status, "not_evaluated")
                self.assertEqual(result.states[0].vector, result.states[2].vector)
                self.assertIs(session.evaluate(result.query), result)

    def test_epoch_dependent_models_cannot_omit_declared_epoch(self):
        for cls in (FixedDirections, MovingDirections):
            provider = cls("requires-epoch")
            session = self.open_provider(provider)
            evaluate = provider.evaluate
            def missing_epoch(query):
                batch = evaluate(query)
                return replace(batch, states=tuple(replace(row, source_epoch=None) for row in batch.states))
            provider.evaluate = missing_epoch
            with self.subTest(cls=cls), self.assertRaises(InvalidProviderResult):
                session.evaluate(provider.query())
            provider.evaluate = evaluate
            session.evaluate(provider.query())
            self.assertEqual(provider.calls["evaluate"], 2)

    def test_static_admission_cannot_also_claim_native_or_epoch_direction(self):
        from synthetic_providers import StaticDirections
        for capability in ("native_direction", "epoch_direction", "cartesian_state"):
            provider = StaticDirections()
            admission = provider.descriptor.admissions[0]
            provider.descriptor = replace(provider.descriptor, admissions=(replace(
                admission, capabilities=admission.capabilities + (capability,)),))
            kernel = Kernel(references=(REFERENCE,))
            self.addCleanup(kernel.close)
            with self.subTest(capability=capability), self.assertRaises(UnsupportedCapability):
                kernel.register(provider, ownership="owned")
            self.assertEqual(provider.calls["close"], 0)
            provider.close()

    def test_source_epoch_mismatch_fails_whole_batch_and_does_not_cache(self):
        from synthetic_providers import StaticDirections
        for source_epoch, wrong_epoch in ((None, EPOCH), (EPOCH, None), (EPOCH, replace(EPOCH, jd1=1))):
            provider = StaticDirections(source_epoch=source_epoch)
            session = self.open_provider(provider)
            evaluate = provider.evaluate
            def corrupt(query):
                batch = evaluate(query)
                return replace(batch, states=batch.states[:-1] + (replace(batch.states[-1], source_epoch=wrong_epoch),))
            provider.evaluate = corrupt
            with self.subTest(source_epoch=source_epoch), self.assertRaises(InvalidProviderResult):
                session.evaluate(provider.query())
            provider.evaluate = evaluate
            session.evaluate(provider.query())
            self.assertEqual(provider.calls["evaluate"], 2)

    def test_static_coverage_scale_and_error_limits_still_apply(self):
        from synthetic_providers import StaticDirections
        provider = StaticDirections()
        session = self.open_provider(provider)
        for query, error in ((provider.query(times=(TimePoint(1, 0, "tt"),)), OutsideCoverage),
                             (provider.query(times=(replace(EPOCH, scale="tdb"),)), TimeConversionUnavailable)):
            with self.subTest(error=error), self.assertRaises(error):
                session.evaluate(query)
        self.assertEqual(provider.calls["evaluate"], 0)
        with self.assertRaises(AccuracyUnavailable):
            session.evaluate(provider.query(accuracy=AccuracyRequest(angular_rad=1e-16)))
        # Constancy alone does not authorize a temporal cache or certificate.
        session.evaluate(provider.query())
        session.evaluate(provider.query(times=(replace(EPOCH, jd2=.1),)))
        self.assertEqual(provider.calls["evaluate"], 3)

    def test_certified_static_reuse_keeps_unknown_source_epoch_and_original_anchor(self):
        from synthetic_providers import CertifiedStaticDirections
        from wenu_kernel.reuse import direction_anchor_identity
        for reproducibility in ("reproducible", "interactive_bounded"):
            provider = CertifiedStaticDirections()
            session = self.open_provider(provider, reproducibility=reproducibility)
            query = provider.query(accuracy=AccuracyRequest(angular_rad=1e-10), evaluation_policy="bounded_reuse")
            first = session.evaluate(query)
            later = session.evaluate(replace(query, times=(replace(EPOCH, jd2=.1),)))
            self.assertEqual(provider.calls["evaluate"], 1)
            self.assertTrue(all(row.source_epoch is None for row in later.states))
            self.assertEqual(tuple(row.anchor_time for row in later.states),
                             tuple(row.anchor_time for row in first.states))
            self.assertTrue(later.reuse_certificates)
            full = replace(query, evaluation_policy="full_model", objects=query.objects[:1], coverage=None)
            anchor = session.evaluate(full)
            declared = replace(anchor, states=(replace(anchor.states[0], source_epoch=EPOCH),))
            self.assertNotEqual(direction_anchor_identity(anchor), direction_anchor_identity(declared))


class CatalogueLookupTests(unittest.TestCase):
    """Closest owner: StaticDirectionTests; protect honest incomplete-source lookup."""

    open_provider = StaticDirectionTests.open_provider

    def test_mixed_source_epochs_are_preserved_and_new_queries_reach_provider(self):
        from synthetic_providers import CatalogueLookupDirections
        provider = CatalogueLookupDirections()
        session = self.open_provider(provider)
        first = session.evaluate(provider.query())
        later = session.evaluate(provider.query(times=(replace(EPOCH, jd2=.1),)))
        self.assertEqual(tuple(row.source_epoch for row in first.states), (None, EPOCH))
        self.assertEqual(tuple(row.source_epoch for row in later.states), (None, EPOCH))
        self.assertEqual(tuple(row.vector for row in first.states), tuple(row.vector for row in later.states))
        self.assertEqual(provider.calls['evaluate'], 2)
        self.assertIs(session.evaluate(later.query), later)

    def test_lookup_cannot_advertise_other_models_or_temporal_certificates(self):
        from synthetic_providers import CatalogueLookupDirections
        for extra in ('native_direction', 'epoch_direction', 'static_direction', 'cartesian_state',
                      'direction_reuse_bound', 'canonical_direction_reuse'):
            provider = CatalogueLookupDirections()
            self.addCleanup(provider.close)
            admission = provider.descriptor.admissions[0]
            provider.descriptor = replace(provider.descriptor, admissions=(replace(admission,
                capabilities=admission.capabilities + (extra,)),))
            kernel = Kernel(references=(REFERENCE,))
            self.addCleanup(kernel.close)
            with self.subTest(extra=extra), self.assertRaises(UnsupportedCapability):
                kernel.register(provider, ownership='owned')
            self.assertEqual(provider.calls['close'], 0)

    def test_accuracy_velocity_and_interval_requests_refuse_before_evaluation(self):
        from synthetic_providers import CatalogueLookupDirections
        provider = CatalogueLookupDirections()
        session = self.open_provider(provider)
        variants = (
            dict(accuracy=AccuracyRequest(angular_rad=1e-6)),
            dict(accuracy=AccuracyRequest(position_m=1)),
            dict(accuracy=AccuracyRequest(velocity_m_s=1)),
            dict(accuracy=AccuracyRequest(metric='another-metric')),
            dict(require_velocity=True), dict(coverage=provider.coverage),
            dict(accuracy=AccuracyRequest(angular_rad=1e-6), evaluation_policy='bounded_reuse'),
        )
        for changes in variants:
            with self.subTest(changes=changes), self.assertRaises(UnsupportedCapability):
                session.evaluate(provider.query(**changes))
        self.assertEqual(provider.calls['evaluate'], 0)

    def test_known_or_unknown_epoch_corruption_never_enters_cache(self):
        from synthetic_providers import CatalogueLookupDirections
        for index, wrong in ((0, EPOCH), (1, None), (1, replace(EPOCH, jd1=1))):
            provider = CatalogueLookupDirections()
            session = self.open_provider(provider)
            evaluate = provider.evaluate
            def corrupt(query):
                batch = evaluate(query)
                rows = list(batch.states)
                rows[index] = replace(rows[index], source_epoch=wrong)
                return replace(batch, states=rows)
            provider.evaluate = corrupt
            with self.subTest(index=index, wrong=wrong), self.assertRaises(InvalidProviderResult):
                session.evaluate(provider.query())
            provider.evaluate = evaluate
            self.assertEqual(len(session.evaluate(provider.query()).states), 2)
            self.assertEqual(provider.calls['evaluate'], 2)

    def test_lookup_keeps_explicit_scale_and_coverage_limits(self):
        from synthetic_providers import CatalogueLookupDirections
        provider = CatalogueLookupDirections()
        session = self.open_provider(provider)
        for query, error in ((provider.query(times=(TimePoint(1, 0, 'tt'),)), OutsideCoverage),
                             (provider.query(times=(replace(EPOCH, scale='tdb'),)), TimeConversionUnavailable)):
            with self.subTest(error=error), self.assertRaises(error):
                session.evaluate(query)
        self.assertEqual(provider.calls['evaluate'], 0)

    def test_lookup_cannot_publish_known_physical_epoch_accuracy(self):
        from synthetic_providers import CatalogueLookupDirections
        provider = CatalogueLookupDirections()
        session = self.open_provider(provider)
        evaluate = provider.evaluate
        def corrupt(query):
            batch = evaluate(query)
            row = batch.states[-1]
            physical = replace(row.evidence.physical_model, status='bounded', value=0)
            row = replace(row, evidence=replace(row.evidence, physical_model=physical))
            return replace(batch, states=batch.states[:-1] + (row,))
        provider.evaluate = corrupt
        with self.assertRaises(InvalidProviderResult):
            session.evaluate(provider.query())
        provider.evaluate = evaluate
        session.evaluate(provider.query())
        self.assertEqual(provider.calls['evaluate'], 2)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.fixed = FixedDirections("fixed")
        self.moving = MovingDirections("moving")
        self.kernel = Kernel(references=(REFERENCE,))

    def test_session_freezes_bindings_and_only_queries_named_provider(self):
        self.kernel.register(self.fixed, ownership="borrowed")
        with self.kernel.open_session(SessionPolicy((self.fixed.reference,))) as old:
            self.kernel.register(self.moving, ownership="borrowed")
            with self.assertRaises(ResourceMismatch):
                old.evaluate(self.moving.query())
        with self.kernel.open_session(SessionPolicy((self.fixed.reference, self.moving.reference))) as session:
            before = self.fixed.calls.copy()
            query = self.moving.query(times=(TimePoint(EPOCH.jd1+1, 0, "tt"),))
            result = session.evaluate(query)
            self.assertAlmostEqual(result.states[0].vector[0], 0, places=14)
            self.assertAlmostEqual(result.states[0].vector[1], 1, places=14)
            self.assertEqual(self.fixed.calls, before)
        self.kernel.close()
        self.assertEqual(self.fixed.calls["close"], 0)

    def test_busy_guards_and_exactly_once_owned_close(self):
        key = self.kernel.register(self.fixed, ownership="owned")
        a = self.kernel.open_session(SessionPolicy((self.fixed.reference,)))
        b = self.kernel.open_session(SessionPolicy((self.fixed.reference,)))
        a.close()
        a.close()
        with self.assertRaises(ProviderBusy):
            self.kernel.unregister(key)
        with self.assertRaises(ProviderBusy):
            self.kernel.close()
        b.close()
        self.kernel.close()
        self.kernel.close()
        self.assertEqual(self.fixed.calls["close"], 1)
        with self.assertRaises(ClosedSession):
            b.catalogue(self.fixed.reference)
        with self.assertRaises(ClosedSession):
            self.kernel.register(self.moving, ownership="borrowed")

    def test_failed_registration_does_not_take_ownership(self):
        self.fixed.descriptor = replace(self.fixed.descriptor, key=replace(self.fixed.key, contract_version="wrong"),
                                        catalogues=(replace(self.fixed.reference, provider=replace(self.fixed.key, contract_version="wrong")),),
                                        admissions=())
        with self.assertRaises(IncompatibleContract):
            self.kernel.register(self.fixed, ownership="owned")
        self.kernel.close()
        self.assertEqual(self.fixed.calls["close"], 0)

    def test_duplicate_identity_cannot_replace_live_provider(self):
        key = self.kernel.register(self.fixed, ownership="borrowed")
        other = FixedDirections("fixed")
        with self.assertRaises(ResourceMismatch):
            self.kernel.register(other, ownership="owned")
        self.kernel.unregister(key)
        self.assertEqual(other.calls["close"], 0)

    def test_unregistered_reference_and_future_capabilities_fail_closed(self):
        empty = Kernel(references=())
        with self.assertRaises(UnsupportedCapability):
            empty.register(self.fixed, ownership="owned")
        admission = self.fixed.descriptor.admissions[0]
        self.fixed.descriptor = replace(self.fixed.descriptor, admissions=(replace(admission, capabilities=("cartesian_reuse_bound",)),))
        with self.assertRaises(UnsupportedCapability):
            self.kernel.register(self.fixed, ownership="borrowed")

    def test_failed_open_rolls_back_all_session_leases(self):
        self.kernel.register(self.fixed, ownership="owned")
        self.kernel.register(self.moving, ownership="owned")
        self.moving.fault = "catalogue"
        with self.assertRaises(ProviderEvaluationError) as caught:
            self.kernel.open_session(SessionPolicy((self.fixed.reference, self.moving.reference)))
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.moving.fault = None
        self.kernel.close()
        self.assertEqual(self.fixed.calls["close"], 1)
        self.assertEqual(self.moving.calls["close"], 1)

    def test_wrong_catalogue_digest_is_rejected(self):
        self.kernel.register(self.fixed, ownership="borrowed")
        self.fixed.fault = "wrong_catalogue"
        with self.assertRaises(InvalidProviderResult):
            self.kernel.open_session(SessionPolicy((self.fixed.reference,)))
        self.kernel.close()

    def test_backend_failure_preserves_cause_and_session_recovers(self):
        self.kernel.register(self.fixed, ownership="borrowed")
        with self.kernel.open_session(SessionPolicy((self.fixed.reference,))) as session:
            self.fixed.fault = "backend"
            with self.assertRaises(ProviderEvaluationError) as caught:
                session.evaluate(self.fixed.query())
            self.assertIsInstance(caught.exception.__cause__, RuntimeError)
            self.fixed.fault = None
            session.evaluate(self.fixed.query())
            self.assertEqual(self.fixed.calls["evaluate"], 2)
            with self.assertRaises(AttributeError):
                caught.exception.code = "different"

    def test_unsupported_unknown_object_reference_coverage_and_scale_before_evaluation(self):
        self.kernel.register(self.fixed, ownership="borrowed")
        with self.kernel.open_session(SessionPolicy((self.fixed.reference,))) as session:
            cases = [({"objects": (ObjectKey("absent:key"),)}, UnknownObject),
                     ({"times": (TimePoint(1, 0, "tt"),)}, OutsideCoverage),
                     ({"times": (replace(EPOCH, scale="tdb"),)}, TimeConversionUnavailable),
                     ({"reference": replace(REFERENCE, frame_id="unknown")}, UnsupportedCapability),
                     ({"evaluation_policy": "bounded_reuse"}, InvalidQuery),
                     ({"accuracy": AccuracyRequest(position_m=1)}, UnsupportedCapability)]
            for changes, error in cases:
                with self.subTest(changes=changes), self.assertRaises(error):
                    session.evaluate(self.fixed.query(**changes))
            self.assertEqual(self.fixed.calls["evaluate"], 0)

    def test_provider_refusal_never_becomes_empty_success(self):
        self.kernel.register(self.fixed, ownership="borrowed")
        with self.kernel.open_session(SessionPolicy((self.fixed.reference,))) as session:
            self.fixed.fault = "unsupported"
            with self.assertRaises(UnsupportedCapability):
                session.evaluate(self.fixed.query())
            self.assertEqual(self.fixed.calls["evaluate"], 0)

    def test_close_failure_remains_explicit_and_retryable(self):
        key = self.kernel.register(self.fixed, ownership="owned")
        self.fixed.fault = "close"
        with self.assertRaises(ProviderEvaluationError):
            self.kernel.unregister(key)
        self.fixed.fault = None
        self.kernel.unregister(key)
        self.kernel.close()
        self.assertEqual(self.fixed.calls["close"], 2)


if __name__ == "__main__":
    unittest.main()
