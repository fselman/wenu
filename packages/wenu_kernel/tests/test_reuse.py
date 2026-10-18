"""Certificate trust boundary, interval/error admission and selective reuse."""

from dataclasses import FrozenInstanceError, replace
from math import atan2, hypot, nextafter
import unittest

from wenu_kernel import Kernel
from wenu_kernel.errors import (
    AccuracyUnavailable, InvalidProviderResult, InvalidQuery, OutsideCoverage,
    ProviderEvaluationError, UnsupportedCapability,
)
from wenu_kernel.records import AccuracyRequest, SessionPolicy, StateBatch, TimeSpan
from wenu_kernel.reuse import direction_anchor_identity, certificate_identity
from synthetic_providers import CertifiedDirections, CanonicalDirections, EPOCH, FixedDirections, REFERENCE, shifted


class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.provider = CertifiedDirections()
        self.kernel = Kernel(references=(REFERENCE,))
        self.kernel.register(self.provider, ownership="borrowed")
        self.session = self.kernel.open_session(SessionPolicy(
            (self.provider.reference,), reproducibility="interactive_bounded"))

    def tearDown(self):
        self.session.close()
        self.kernel.close()

    def query(self, time=EPOCH, **changes):
        return self.provider.query(times=(time,), accuracy=AccuracyRequest(angular_rad=1e-5),
                                   evaluation_policy="bounded_reuse", **changes)

    def test_reuse_retains_catalogue_epoch_anchor_and_reported_bound(self):
        anchor = self.session.evaluate(self.query())
        before = self.provider.calls.copy()
        time = shifted(EPOCH, .001)
        result = self.session.evaluate(self.query(time))
        self.assertEqual(self.provider.calls, before)
        self.assertEqual(result.query.times, (time,))
        for a, row in zip(anchor.states, result.states):
            self.assertEqual(row.source_epoch, EPOCH)
            self.assertEqual(row.anchor_time, EPOCH)
            self.assertEqual(row.time, time)
            self.assertEqual(row.vector, a.vector)
            cert = next(c for c in result.reuse_certificates if c.identity == row.certificate_id)
            self.assertEqual(row.evidence.numerical.value, cert.maximum_error)
            self.assertGreater(row.evidence.numerical.value, a.evidence.numerical.value)
            self.assertEqual(row.evidence.physical_model.status, "not_evaluated")

    def test_only_expired_object_is_reevaluated_and_another_provider_is_untouched(self):
        fixed = FixedDirections("fixed")
        self.kernel.register(fixed, ownership="borrowed")
        self.session.evaluate(self.query())
        self.provider.evaluated_objects.clear()
        fixed_before = fixed.calls.copy()
        time = shifted(EPOCH, .01)
        result = self.session.evaluate(self.query(time))
        self.assertEqual(self.provider.evaluated_objects, [(time, self.provider.objects[0])])
        self.assertIsNone(result.states[0].certificate_id)
        self.assertIsNotNone(result.states[1].certificate_id)
        self.assertEqual(fixed.calls, fixed_before)

    def test_closed_interval_and_exact_error_equality_do_not_admit_one_ulp_outside(self):
        first = self.session.evaluate(self.query(objects=(self.provider.objects[0],)))
        cert = first.reuse_certificates[0]
        query = replace(self.query(cert.validity.stop, objects=cert.objects),
                        accuracy=AccuracyRequest(angular_rad=cert.maximum_error))
        before = self.provider.calls["evaluate"]
        result = self.session.evaluate(query)
        self.assertEqual(result.states[0].certificate_id, cert.identity)
        self.assertEqual(self.provider.calls["evaluate"], before)
        outside = replace(cert.validity.stop, jd2=nextafter(cert.validity.stop.jd2, .5))
        self.session.evaluate(replace(query, times=(outside,)))
        self.assertEqual(self.provider.calls["evaluate"], before + 1)
        tighter = replace(self.query(cert.validity.start, objects=cert.objects),
                          accuracy=AccuracyRequest(angular_rad=nextafter(cert.maximum_error, 0)))
        self.assertIsNone(self.session.evaluate(tighter).states[0].certificate_id)

    def test_reuse_chain_never_resets_error_or_moves_original_anchor(self):
        first = self.session.evaluate(self.query())
        a = self.session.evaluate(self.query(shifted(EPOCH, .001)))
        b = self.session.evaluate(self.query(shifted(EPOCH, .002)))
        for x, y in zip(a.states, b.states):
            self.assertEqual(x.anchor_time, EPOCH)
            self.assertEqual(x.certificate_id, y.certificate_id)
            self.assertEqual(x.evidence.numerical, y.evidence.numerical)
        self.assertEqual(self.provider.calls["evaluate"], 1)
        scalar = replace(a.query, evaluation_policy="full_model", objects=(a.states[0].object_key,))
        with self.assertRaises(InvalidQuery):
            direction_anchor_identity(StateBatch(scalar, (a.states[0],)))

    def test_tighter_and_full_model_queries_evaluate_instead_of_relaxing_bound(self):
        self.session.evaluate(self.query())
        time = shifted(EPOCH, .001)
        tight = replace(self.query(time), accuracy=AccuracyRequest(angular_rad=1e-12))
        result = self.session.evaluate(tight)
        self.assertTrue(all(r.certificate_id is None for r in result.states))
        self.assertTrue(all(r.evidence.numerical.value <= 1e-12 for r in result.states))
        full = self.session.evaluate(replace(self.query(shifted(EPOCH, .002)), evaluation_policy="full_model"))
        self.assertTrue(all(r.certificate_id is None for r in full.states))
        self.assertEqual(full.reuse_certificates, ())

    def test_reproducible_policy_uses_model_independent_of_warmness_and_request_order(self):
        def run(order):
            with self.kernel.open_session(SessionPolicy((self.provider.reference,))) as session:
                return {time: session.evaluate(self.query(time)) for time in order}
        times = (EPOCH, shifted(EPOCH, .001), shifted(EPOCH, .002))
        a = run(times)
        b = run(tuple(reversed(times)))
        self.assertEqual(a, b)
        self.assertTrue(all(row.certificate_id is None for batch in a.values() for row in batch.states))

    def test_same_available_certificates_use_total_order_independent_of_insertion(self):
        anchors = (EPOCH, shifted(EPOCH, 2**-9))
        def run(order):
            with self.kernel.open_session(SessionPolicy(
                    (self.provider.reference,), reproducibility="interactive_bounded")) as session:
                for time in order:
                    tight = replace(self.query(time, objects=(self.provider.objects[0],)),
                                    accuracy=AccuracyRequest(angular_rad=1e-12))
                    session.evaluate(tight)
                return session.evaluate(self.query(shifted(EPOCH, 2**-10), objects=(self.provider.objects[0],)))
        a, b = run(anchors), run(tuple(reversed(anchors)))
        self.assertEqual(a, b)
        self.assertEqual(a.states[0].anchor_time, EPOCH)

    def test_numerical_separation_from_model_is_within_reported_total_bound(self):
        self.session.evaluate(self.query())
        time = shifted(EPOCH, .003)
        result = self.session.evaluate(self.query(time))
        exact = self.provider.evaluate(replace(self.query(time), evaluation_policy="full_model"))
        for a, b in zip(result.states, exact.states):
            x, y = a.vector, b.vector
            cross = (x[1]*y[2]-x[2]*y[1], x[2]*y[0]-x[0]*y[2], x[0]*y[1]-x[1]*y[0])
            angle = atan2(hypot(*cross), sum(i*j for i, j in zip(x, y)))
            self.assertLessEqual(angle, a.evidence.numerical.value + b.evidence.numerical.value)

    def test_whole_interval_is_checked_even_when_sample_fits(self):
        self.session.evaluate(self.query())
        time = shifted(EPOCH, .001)
        interval = TimeSpan(shifted(EPOCH, -.01), shifted(EPOCH, .01))
        with self.assertRaises(AccuracyUnavailable):
            self.session.evaluate(self.query(time, objects=(self.provider.objects[0],), coverage=interval))
        fitting = TimeSpan(shifted(EPOCH, -.003), shifted(EPOCH, .003))
        result = self.session.evaluate(self.query(time, objects=(self.provider.objects[0],), coverage=fitting))
        self.assertIsNotNone(result.states[0].certificate_id)

    def test_corrupt_provider_certificates_fail_closed_and_publish_no_cache(self):
        faults = ("identity", "anchor", "model", "catalogue", "objects", "reference",
                  "metric", "anchor_error", "scale", "outside_resource", "omitted_anchor",
                  "method_resource", "none")
        for fault in faults:
            with self.subTest(fault=fault):
                self.provider.certificate_fault = fault
                with self.assertRaises(InvalidProviderResult):
                    self.session.evaluate(self.query())
        self.provider.certificate_fault = None
        result = self.session.evaluate(self.query())
        self.assertEqual(self.provider.calls["evaluate"], len(faults) + 1)
        self.assertEqual(len(result.reuse_certificates), 2)

    def test_failure_after_first_certificate_rolls_back_both_caches(self):
        self.provider.certificate_fault = "backend"
        self.provider.fail_certificate_object = self.provider.objects[1]
        with self.assertRaises(ProviderEvaluationError):
            self.session.evaluate(self.query())
        self.provider.certificate_fault = None
        self.session.evaluate(self.query())
        self.assertEqual(self.provider.calls["evaluate"], 2)
        self.assertEqual(self.provider.calls["certify"], 4)

    def test_uncertifiable_provider_falls_back_but_explicit_interval_must_fail(self):
        self.provider.certificate_fault = "unavailable"
        first = self.session.evaluate(self.query())
        self.assertEqual(first.reuse_certificates, ())
        self.assertTrue(all(r.certificate_id is None for r in first.states))
        with self.assertRaises(AccuracyUnavailable):
            self.session.evaluate(self.query(coverage=TimeSpan(EPOCH, shifted(EPOCH, .001))))

    def test_model_without_reuse_capability_still_evaluates_requested_bound(self):
        fixed = FixedDirections("no-certificates")
        self.kernel.register(fixed, ownership="borrowed")
        with self.kernel.open_session(SessionPolicy((fixed.reference,), reproducibility="interactive_bounded")) as session:
            query = fixed.query(evaluation_policy="bounded_reuse", accuracy=AccuracyRequest(angular_rad=1e-5))
            result = session.evaluate(query)
            self.assertEqual(result.reuse_certificates, ())
            with self.assertRaises(AccuracyUnavailable):
                session.evaluate(replace(query, coverage=TimeSpan(EPOCH, shifted(EPOCH, .001))))

    def test_outside_resource_never_uses_temporal_cache(self):
        self.session.evaluate(self.query())
        with self.assertRaises(OutsideCoverage):
            self.session.evaluate(self.query(shifted(self.provider.coverage.stop, 1)))

    def test_certificate_and_digest_are_immutable_and_meaning_sensitive(self):
        result = self.session.evaluate(self.query())
        cert = result.reuse_certificates[0]
        self.assertEqual(cert.identity, certificate_identity(cert))
        with self.assertRaises(FrozenInstanceError):
            cert.maximum_error = 0
        self.assertNotEqual(certificate_identity(replace(cert, maximum_error=nextafter(cert.maximum_error, 1))), cert.identity)
        for value in (-1, float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(InvalidQuery):
                replace(cert, maximum_error=value)

    def test_whole_query_interval_outside_resource_fails_before_evaluation(self):
        query = self.query(coverage=TimeSpan(shifted(self.provider.coverage.start, -1), EPOCH))
        with self.assertRaises(OutsideCoverage):
            self.session.evaluate(query)
        self.assertEqual(self.provider.calls["evaluate"], 0)

    def test_certificate_cannot_exceed_separate_model_or_resource_interval(self):
        for owner in ("model", "resource"):
            with self.subTest(owner=owner):
                provider = CertifiedDirections("limited-" + owner)
                narrow = TimeSpan(shifted(EPOCH, -.001), shifted(EPOCH, .001))
                admission = provider.descriptor.admissions[0]
                if owner == "model":
                    admission = replace(admission, coverage=narrow)
                else:
                    resource = replace(provider.reference.resources[0], coverage=narrow)
                    provider.reference = replace(provider.reference, resources=(resource,))
                    provider.model = replace(provider.model, dependencies=(resource,))
                    provider.snapshot = replace(provider.snapshot, reference=provider.reference)
                    admission = replace(admission, catalogue=provider.reference, model=provider.model)
                provider.descriptor = replace(provider.descriptor, catalogues=(provider.reference,), admissions=(admission,))
                self.kernel.register(provider, ownership="borrowed")
                with self.kernel.open_session(SessionPolicy((provider.reference,), reproducibility="interactive_bounded")) as session:
                    query = provider.query(evaluation_policy="bounded_reuse", accuracy=AccuracyRequest(angular_rad=1e-5))
                    with self.assertRaises(InvalidProviderResult):
                        session.evaluate(query)

    def test_mixed_hit_miss_batch_keeps_requested_time_and_object_order(self):
        self.session.evaluate(self.query())
        times = (shifted(EPOCH, .01), shifted(EPOCH, .001))
        objects = tuple(reversed(self.provider.objects))
        query = replace(self.query(), times=times, objects=objects)
        result = self.session.evaluate(query)
        self.assertEqual([(r.time, r.object_key) for r in result.states],
                         [(time, obj) for time in times for obj in objects])
        self.assertEqual([r.certificate_id is None for r in result.states], [False, True, False, False])

    def test_certification_cannot_hide_a_too_large_full_model_error(self):
        self.session.evaluate(self.query())
        query = replace(self.query(shifted(EPOCH, .001)), accuracy=AccuracyRequest(angular_rad=1e-16))
        before = self.provider.calls["certify"]
        with self.assertRaises(AccuracyUnavailable):
            self.session.evaluate(query)
        self.assertEqual(self.provider.calls["certify"], before)

    def test_no_reuse_cache_crosses_sessions_and_published_provenance_survives_close(self):
        self.session.evaluate(self.query())
        query = self.query(shifted(EPOCH, .001))
        reused = self.session.evaluate(query)
        with self.kernel.open_session(SessionPolicy((self.provider.reference,), reproducibility="interactive_bounded")) as cold:
            fresh = cold.evaluate(query)
            self.assertTrue(all(row.certificate_id is None for row in fresh.states))
        identity = reused.reuse_certificates[0].identity
        self.session.close()
        self.kernel.close()
        self.assertEqual(reused.reuse_certificates[0].identity, identity)
        self.assertEqual(reused.states[0].anchor_time, EPOCH)


class CanonicalReuseTests(unittest.TestCase):
    def setUp(self):
        self.provider = CanonicalDirections()
        self.kernel = Kernel(references=(REFERENCE,))
        self.kernel.register(self.provider, ownership="borrowed")
        self.session = self.kernel.open_session(SessionPolicy((self.provider.reference,)))

    def tearDown(self):
        self.session.close()
        self.kernel.close()

    def query(self, time=EPOCH, **changes):
        return self.provider.query(times=(time,), accuracy=AccuracyRequest(angular_rad=1e-5),
                                   evaluation_policy="bounded_reuse", **changes)

    def test_cold_warm_reverse_order_and_different_batches_return_identical_rows(self):
        times = (shifted(EPOCH, .001), shifted(EPOCH, -.001), shifted(EPOCH, .01))
        forward = {t: self.session.evaluate(self.query(t)) for t in times}
        with self.kernel.open_session(SessionPolicy((self.provider.reference,))) as reverse:
            backward = {t: reverse.evaluate(self.query(t)) for t in reversed(times)}
        self.assertEqual(forward, backward)
        with self.kernel.open_session(SessionPolicy((self.provider.reference,))) as batch_session:
            batch = batch_session.evaluate(replace(self.query(), times=tuple(reversed(times))))
        for row in batch.states:
            match = next(r for r in forward[row.time].states if r.object_key == row.object_key)
            self.assertEqual(row, match)
        self.assertTrue(all(result.reuse_plan is not None for result in forward.values()))

    def test_same_cell_reuses_anchors_and_new_cell_updates_only_fast_object(self):
        first = self.session.evaluate(self.query(shifted(EPOCH, .001)))
        self.provider.evaluated_objects.clear()
        second = self.session.evaluate(self.query(shifted(EPOCH, .0015)))
        self.assertEqual(self.provider.evaluated_objects, [])
        self.assertEqual([r.anchor_time for r in first.states], [r.anchor_time for r in second.states])
        third = self.session.evaluate(self.query(shifted(EPOCH, .01)))
        self.assertEqual(self.provider.evaluated_objects, [(third.states[0].anchor_time, self.provider.objects[0])])
        self.assertEqual(third.states[1].anchor_time, EPOCH)

    def test_cell_boundary_uses_planned_anchor_even_when_previous_certificate_still_fits(self):
        before = shifted(EPOCH, nextafter(2**-9, 0))
        boundary = shifted(EPOCH, 2**-9)
        obj = self.provider.objects[0]
        a = self.session.evaluate(self.query(before, objects=(obj,)))
        self.assertTrue(a.reuse_certificates[0].validity.contains(boundary))
        b = self.session.evaluate(self.query(boundary, objects=(obj,)))
        self.assertEqual(a.states[0].anchor_time, EPOCH)
        self.assertEqual(b.states[0].anchor_time, shifted(EPOCH, 2**-8))
        self.assertEqual(self.provider.calls["evaluate"], 2)

    def test_plan_is_pure_deterministic_and_transitively_immutable(self):
        from wenu_kernel.reuse import make_reuse_plan, reuse_plan_identity
        query = self.query(shifted(EPOCH, .001))
        calls = self.provider.calls.copy()
        plan = self.provider.plan_reuse(query)
        self.assertEqual(plan, self.provider.plan_reuse(query))
        self.assertEqual(self.provider.calls, calls)
        self.assertEqual(self.provider.evaluated_objects, [])
        self.assertEqual(plan.identity, reuse_plan_identity(plan))
        values = list(plan.anchors)
        copied = make_reuse_plan(query, values, plan.method)
        values.clear()
        self.assertEqual(copied, plan)
        with self.assertRaises(FrozenInstanceError):
            plan.anchors[0].anchor_time = EPOCH

    def test_invalid_plans_fail_before_any_propagation(self):
        for fault in ("none", "query", "omit", "order", "outside", "scale", "method_resource", "identity"):
            self.provider.plan_fault = fault
            with self.subTest(fault=fault), self.assertRaises(InvalidProviderResult):
                self.session.evaluate(self.query(shifted(EPOCH, .001)))
        self.assertEqual(self.provider.calls["evaluate"], 0)
        self.provider.plan_fault = None
        self.assertIsNotNone(self.session.evaluate(self.query(shifted(EPOCH, .001))).reuse_plan)

    def test_backend_planning_failure_preserves_cause_and_never_falls_back(self):
        self.provider.plan_fault = "backend"
        with self.assertRaises(ProviderEvaluationError) as caught:
            self.session.evaluate(self.query())
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.assertEqual(self.provider.calls["evaluate"], 0)

    def test_unavailable_or_unsupported_plans_fall_back_to_actual_epoch_model(self):
        for index, fault in enumerate(("unavailable", "unsupported")):
            self.provider.plan_fault = fault
            result = self.session.evaluate(self.query(shifted(EPOCH, .001 + index * .0001)))
            with self.subTest(fault=fault):
                self.assertIsNone(result.reuse_plan)
                self.assertTrue(all(row.anchor_time == row.time and row.certificate_id is None for row in result.states))

    def test_too_tight_canonical_certificate_falls_back_without_relaxing_bound(self):
        self.session.evaluate(self.query(shifted(EPOCH, .001)))
        query = replace(self.query(shifted(EPOCH, .001)), accuracy=AccuracyRequest(angular_rad=1e-12))
        result = self.session.evaluate(query)
        self.assertIsNone(result.reuse_plan)
        self.assertTrue(all(row.evidence.numerical.value <= 1e-12 and row.time == row.anchor_time for row in result.states))

    def test_certificate_failure_rolls_back_all_new_canonical_anchors(self):
        self.provider.certificate_fault = "backend"
        self.provider.fail_certificate_object = self.provider.objects[1]
        query = self.query(shifted(EPOCH, .001))
        with self.assertRaises(ProviderEvaluationError):
            self.session.evaluate(query)
        self.assertEqual(len(self.provider.evaluated_objects), 2)
        self.provider.certificate_fault = None
        self.session.evaluate(query)
        self.assertEqual(len(self.provider.evaluated_objects), 4)

    def test_explicit_whole_interval_has_a_certificate_and_uncovered_interval_fails(self):
        obj = self.provider.objects[0]
        fitting = TimeSpan(shifted(EPOCH, -.002), shifted(EPOCH, .002))
        result = self.session.evaluate(self.query(shifted(EPOCH, .001), objects=(obj,), coverage=fitting))
        self.assertIsNotNone(result.reuse_plan)
        self.assertTrue(all(result.reuse_certificates[0].validity.contains(t) for t in (fitting.start, fitting.stop)))
        # A requested interval need not contain the provider's canonical anchor.
        narrow = TimeSpan(shifted(EPOCH, .0009), shifted(EPOCH, .0011))
        narrow_result = self.session.evaluate(self.query(shifted(EPOCH, .001), objects=(obj,), coverage=narrow))
        self.assertIsNotNone(narrow_result.reuse_plan)
        self.assertFalse(narrow.contains(narrow_result.states[0].anchor_time))
        too_wide = TimeSpan(shifted(EPOCH, -.01), shifted(EPOCH, .01))
        with self.assertRaises(AccuracyUnavailable):
            self.session.evaluate(self.query(shifted(EPOCH, .001), objects=(obj,), coverage=too_wide))

    def test_full_model_policy_never_uses_canonical_reuse(self):
        self.session.evaluate(self.query(shifted(EPOCH, .001)))
        result = self.session.evaluate(replace(self.query(shifted(EPOCH, .0015)), evaluation_policy="full_model"))
        self.assertIsNone(result.reuse_plan)
        self.assertTrue(all(row.certificate_id is None and row.time == row.anchor_time for row in result.states))

    def test_optional_capability_requires_a_planner_and_does_not_touch_other_provider(self):
        bad = CanonicalDirections("incomplete")
        bad.plan_reuse = None
        with self.assertRaises(UnsupportedCapability):
            self.kernel.register(bad, ownership="owned")
        self.assertEqual(bad.calls["close"], 0)
        fixed = FixedDirections("independent")
        self.kernel.register(fixed, ownership="borrowed")
        before = fixed.calls.copy()
        self.session.evaluate(self.query(shifted(EPOCH, .001)))
        self.assertEqual(fixed.calls, before)


if __name__ == "__main__":
    unittest.main()
