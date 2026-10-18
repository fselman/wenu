"""SI state variant, velocity availability and full-model query contracts."""

from dataclasses import FrozenInstanceError, replace
from math import nextafter
import unittest

from wenu_kernel import Kernel
from wenu_kernel.errors import (
    AccuracyUnavailable, InvalidProviderResult, InvalidQuery, OutsideCoverage,
    ProviderEvaluationError, TimeConversionUnavailable, UnsupportedCapability,
)
from wenu_kernel.records import AccuracyRequest, CartesianState, ObjectKey, SessionPolicy, StateBatch
from wenu_kernel.reuse import direction_anchor_identity
from synthetic_providers import (
    CARTESIAN_REFERENCE, EPOCH, REFERENCE, FixedDirections, SyntheticCartesian, shifted,
)


class CartesianTests(unittest.TestCase):
    def setUp(self):
        self.provider = SyntheticCartesian()
        self.kernel = Kernel(references=(CARTESIAN_REFERENCE, REFERENCE))
        self.kernel.register(self.provider, ownership="borrowed")
        self.session = self.kernel.open_session(SessionPolicy((self.provider.reference,)))

    def tearDown(self):
        self.session.close()
        self.kernel.close()

    def test_full_model_si_values_order_and_identical_query_cache(self):
        times = (shifted(EPOCH, 1), EPOCH)
        objects = tuple(reversed(self.provider.objects))
        query = self.provider.query(times=times, objects=objects, require_velocity=True)
        result = self.session.evaluate(query)
        self.assertEqual([(r.time, r.object_key) for r in result.states], [(t, o) for t in times for o in objects])
        self.assertEqual(result.states[0].position_m, (173801.0, 2000.0, 3000.0))
        self.assertEqual(result.states[0].velocity_m_s, (2.0, 0.0, 0.0))
        self.assertTrue(result.states[0].velocity_available)
        self.assertIsNone(result.states[0].source_epoch)
        self.assertIs(result, self.session.evaluate(query))
        self.assertEqual(self.provider.calls["evaluate"], 1)

    def test_unknown_velocity_is_none_and_required_velocity_refused_before_propagation(self):
        provider = SyntheticCartesian("position-only", velocity_available=False)
        self.kernel.register(provider, ownership="borrowed")
        with self.kernel.open_session(SessionPolicy((provider.reference,))) as session:
            result = session.evaluate(provider.query())
            self.assertIsNone(result.states[0].velocity_m_s)
            self.assertIsNone(result.states[0].velocity_evidence)
            self.assertFalse(result.states[0].velocity_available)
            self.assertEqual(provider.snapshot.objects[0].source_epochs, ())
            for query in (provider.query(require_velocity=True), provider.query(accuracy=AccuracyRequest(velocity_m_s=.1, metric="euclidean_norm"))):
                with self.assertRaises(UnsupportedCapability):
                    session.evaluate(query)
            self.assertEqual(provider.calls["evaluate"], 1)

    def test_accepted_velocity_request_cannot_silently_return_unknown(self):
        self.provider.fault = "missing_velocity"
        with self.assertRaises(InvalidProviderResult):
            self.session.evaluate(self.provider.query(require_velocity=True))
        self.provider.fault = None
        self.assertTrue(self.session.evaluate(self.provider.query(require_velocity=True)).states[0].velocity_available)
        self.assertEqual(self.provider.calls["evaluate"], 2)

    def test_position_and_velocity_have_independent_bounds_and_unknown_physical_error(self):
        accuracy = AccuracyRequest(position_m=.01, velocity_m_s=.001, metric="euclidean_norm")
        result = self.session.evaluate(self.provider.query(accuracy=accuracy))
        row = result.states[0]
        self.assertEqual(row.position_evidence.numerical.units, "m")
        self.assertEqual(row.velocity_evidence.numerical.units, "m/s")
        self.assertEqual(row.position_evidence.physical_model.status, "not_evaluated")
        for tight in (replace(accuracy, position_m=nextafter(.01, 0)), replace(accuracy, velocity_m_s=nextafter(.001, 0))):
            with self.subTest(tight=tight), self.assertRaises(AccuracyUnavailable):
                self.session.evaluate(self.provider.query(accuracy=tight))

    def test_statistical_or_unknown_error_does_not_satisfy_deterministic_bound(self):
        for fault, accuracy in (("unknown_position_error", AccuracyRequest(position_m=.1, metric="euclidean_norm")),
                                ("statistical_velocity", AccuracyRequest(velocity_m_s=.1, metric="euclidean_norm"))):
            self.provider.fault = fault
            with self.subTest(fault=fault), self.assertRaises(AccuracyUnavailable):
                self.session.evaluate(self.provider.query(accuracy=accuracy))

    def test_failed_batches_and_provenance_or_unit_mismatch_never_enter_cache(self):
        faults = ("reorder", "omit", "duplicate", "wrong_origin", "wrong_epoch", "wrong_anchor", "wrong_position_units", "wrong_velocity_units")
        for fault in faults:
            self.provider.fault = fault
            with self.subTest(fault=fault), self.assertRaises(InvalidProviderResult):
                self.session.evaluate(self.provider.query())
        self.provider.fault = None
        self.session.evaluate(self.provider.query())
        self.assertEqual(self.provider.calls["evaluate"], len(faults) + 1)

    def test_cartesian_query_rejects_angular_meaning_and_unimplemented_reuse(self):
        for changes in ({"accuracy": AccuracyRequest(angular_rad=.1)},
                        {"accuracy": AccuracyRequest(position_m=1)},
                        {"evaluation_policy": "bounded_reuse"}):
            with self.subTest(changes=changes), self.assertRaises(UnsupportedCapability):
                self.session.evaluate(self.provider.query(**changes))
        self.assertEqual(self.provider.calls["evaluate"], 0)

    def test_vectors_and_evidence_are_immutable_after_buffer_and_owner_changes(self):
        result = self.session.evaluate(self.provider.query())
        for values in self.provider.buffers:
            values[:] = [999, 999, 999]
        self.session.close()
        self.kernel.close()
        self.assertEqual(result.states[0].position_m, (1000.0, 2000.0, 3000.0))
        self.assertEqual(result.states[0].velocity_m_s, (2.0, 0.0, 0.0))
        with self.assertRaises(FrozenInstanceError):
            result.states[0].position_m = (0, 0, 0)

    def test_constructor_rejects_nonfinite_vectors_wrong_units_and_fake_velocity_evidence(self):
        row = self.provider.evaluate(self.provider.query()).states[0]
        for vector in ([1, 2], [float("nan"), 0, 0], [True, 0, 0], [float("inf"), 0, 0]):
            for field in ("position_m", "velocity_m_s"):
                with self.subTest(field=field, vector=vector), self.assertRaises(InvalidQuery):
                    replace(row, **{field: vector})
        with self.assertRaises(InvalidQuery):
            replace(row, reference=replace(row.reference, units="km,km/s"))
        with self.assertRaises(InvalidQuery):
            replace(row, velocity_m_s=None)
        with self.assertRaises(InvalidQuery):
            replace(row, velocity_evidence=None)
        with self.assertRaises(InvalidQuery):
            self.provider.query(require_velocity=1)

    def test_zero_velocity_is_known_and_not_equivalent_to_absence(self):
        row = self.provider.evaluate(self.provider.query()).states[0]
        zero = replace(row, position_m=[0, 0, 0], velocity_m_s=[0, 0, 0])
        unknown = replace(row, velocity_m_s=None, velocity_evidence=None)
        self.assertTrue(zero.velocity_available)
        self.assertEqual(zero.position_m, (0.0, 0.0, 0.0))
        self.assertFalse(unknown.velocity_available)
        self.assertNotEqual(zero, unknown)

    def test_frame_origin_and_si_units_require_explicit_admission(self):
        teme = replace(CARTESIAN_REFERENCE, frame_id="teme", origin_id="earth")
        provider = SyntheticCartesian("teme", reference=teme)
        with self.assertRaises(UnsupportedCapability):
            self.kernel.register(provider, ownership="borrowed")
        with Kernel(references=(teme,)) as kernel:
            kernel.register(provider, ownership="borrowed")
            with kernel.open_session(SessionPolicy((provider.reference,))) as session:
                result = session.evaluate(provider.query())
                self.assertEqual(result.states[0].reference, teme)
        wrong_units = SyntheticCartesian("kilometres", reference=replace(CARTESIAN_REFERENCE, units="km,km/s"))
        with Kernel(references=(wrong_units.native_reference,)) as kernel:
            with self.assertRaises(UnsupportedCapability):
                kernel.register(wrong_units, ownership="borrowed")
        incompatible = SyntheticCartesian("wrong-capabilities")
        admission = incompatible.descriptor.admissions[0]
        incompatible.descriptor = replace(incompatible.descriptor, admissions=(replace(admission, capabilities=("native_direction",)),))
        with self.assertRaises(UnsupportedCapability):
            self.kernel.register(incompatible, ownership="borrowed")

    def test_coverage_and_time_basis_fail_before_numerical_backend(self):
        for time, error in ((shifted(self.provider.coverage.stop, 1), OutsideCoverage),
                            (replace(EPOCH, scale="tdb"), TimeConversionUnavailable)):
            with self.subTest(time=time), self.assertRaises(error):
                self.session.evaluate(self.provider.query(times=(time,)))
        self.assertEqual(self.provider.calls["evaluate"], 0)

    def test_cartesian_evaluation_does_not_invoke_direction_provider(self):
        direction = FixedDirections("unrelated-direction")
        self.kernel.register(direction, ownership="borrowed")
        before = direction.calls.copy()
        self.session.evaluate(self.provider.query())
        self.assertEqual(direction.calls, before)
        with self.assertRaises(InvalidQuery):
            direction_anchor_identity(self.provider.evaluate(self.provider.query(objects=(self.provider.objects[0],))))

    def test_backend_error_keeps_cause_and_retry_can_succeed(self):
        self.provider.fault = "backend"
        with self.assertRaises(ProviderEvaluationError) as caught:
            self.session.evaluate(self.provider.query())
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.provider.fault = None
        self.session.evaluate(self.provider.query())
        self.assertEqual(self.provider.calls["evaluate"], 2)

    def test_declared_source_epoch_is_preserved_and_cannot_be_hidden(self):
        provider = SyntheticCartesian("epoch-bearing", source_epoch=EPOCH)
        self.kernel.register(provider, ownership="borrowed")
        with self.kernel.open_session(SessionPolicy((provider.reference,))) as session:
            result = session.evaluate(provider.query())
            self.assertEqual(result.states[0].source_epoch, EPOCH)
            provider.source_epoch = None  # Constructed bad backend drops frozen provenance.
            with self.assertRaises(InvalidProviderResult):
                session.evaluate(provider.query(times=(shifted(EPOCH, 1),)))
        direction = FixedDirections("source-direction")
        with self.assertRaises(InvalidQuery):
            replace(direction.snapshot.objects[0], source_epochs=())

    def test_direction_state_cannot_supply_velocity_or_enter_cartesian_batch(self):
        direction = FixedDirections("angular")
        self.kernel.register(direction, ownership="borrowed")
        with self.kernel.open_session(SessionPolicy((direction.reference,))) as session:
            with self.assertRaises(UnsupportedCapability):
                session.evaluate(direction.query(require_velocity=True))
            self.assertEqual(direction.calls["evaluate"], 0)
        query = self.provider.query()
        valid = self.provider.evaluate(query)
        angular = direction.evaluate(direction.query())
        mixed = StateBatch(query, (valid.states[0], replace(angular.states[1], object_key=self.provider.objects[1])))
        original = self.provider.evaluate
        self.provider.evaluate = lambda request: mixed
        with self.assertRaises(InvalidProviderResult):
            self.session.evaluate(query)
        self.provider.evaluate = original
        self.assertTrue(all(type(row) is CartesianState for row in self.session.evaluate(query).states))


if __name__ == "__main__":
    unittest.main()
