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
