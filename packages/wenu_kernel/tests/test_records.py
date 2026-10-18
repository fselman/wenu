"""Typed time, immutable publication and scientific query admission faults."""

from dataclasses import FrozenInstanceError, replace
from math import nextafter
import unittest

from wenu_kernel.errors import InvalidQuery, TimeConversionUnavailable
from wenu_kernel.records import (
    AccuracyRequest, CatalogueSnapshot, DirectionState, ExternalId, ObjectKey,
    SessionPolicy, TimePoint, TimeSpan, UnboundedCoverage, UncertaintyChannel,
)
from synthetic_providers import EPOCH, FixedDirections, REFERENCE


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.provider = FixedDirections("fixed")

    def test_time_preserves_sub_single_jd_float_precision(self):
        a = TimePoint(2451545, 0.0, "tt")
        b = TimePoint(2451545.0, 1e-12, "tt")
        self.assertNotEqual(a, b)
        self.assertEqual(a.jd1 + a.jd2, b.jd1 + b.jd2)
        self.assertEqual(TimePoint(-1000000, -0.5, "tt").jd1, -1000000)
        self.assertEqual(TimePoint(0, -0.0, "tt"), TimePoint(0, 0, "tt"))

    def test_time_rejects_noncanonical_nonfinite_bool_and_civil_scales(self):
        for args in ((True, 0, "tt"), (1.2, 0, "tt"), (1, True, "tt"),
                     (1, float("nan"), "tt"), (1, float("inf"), "tt"),
                     (1, 0.5, "tt"), (1, -0.51, "tt"), (1, 0, "utc"), (1, 0, "ut1")):
            with self.subTest(args=args), self.assertRaises(InvalidQuery):
                TimePoint(*args)

    def test_interval_is_closed_and_does_not_relabel_time_scales(self):
        end = replace(EPOCH, jd2=0.25)
        span = TimeSpan(EPOCH, end)
        self.assertTrue(span.contains(EPOCH))
        self.assertTrue(span.contains(end))
        self.assertFalse(span.contains(replace(end, jd2=nextafter(0.25, 1))))
        with self.assertRaises(TimeConversionUnavailable):
            span.contains(replace(end, scale="tdb"))
        with self.assertRaises(InvalidQuery):
            TimeSpan(end, EPOCH)
        self.assertTrue(UnboundedCoverage("tt").contains(TimePoint(-5000000, 0, "tt")))

    def test_snapshot_severs_mutable_sequence_aliases(self):
        source = list(self.provider.snapshot.objects)
        snapshot = CatalogueSnapshot(self.provider.reference, source)
        source.clear()
        self.assertEqual(len(snapshot.objects), 2)
        with self.assertRaises(FrozenInstanceError):
            snapshot.objects[0].key = ObjectKey("other:key")
        with self.assertRaises(InvalidQuery):
            CatalogueSnapshot(self.provider.reference, [snapshot.objects[0]] * 2)

    def test_identifiers_and_missing_data_are_not_coerced(self):
        gaia = ExternalId("Gaia", "DR3", "9223372036854775807")
        self.assertEqual(gaia.identifier, "9223372036854775807")
        with self.assertRaises(InvalidQuery):
            ExternalId("Gaia", "DR3", 9223372036854775807)
        with self.assertRaises(InvalidQuery):
            UncertaintyChannel("not_evaluated", 0, "rad", "unknown")
        with self.assertRaises(InvalidQuery):
            replace(REFERENCE, equinox=EPOCH)

    def test_queries_reject_empty_duplicate_and_uncovered_samples(self):
        for changes in ({"objects": ()}, {"times": ()},
                        {"objects": self.provider.objects * 2}, {"times": (EPOCH, EPOCH)},
                        {"coverage": TimeSpan(replace(EPOCH, jd2=.1), replace(EPOCH, jd2=.2))}):
            with self.subTest(changes=changes), self.assertRaises(InvalidQuery):
                self.provider.query(**changes)

    def test_unsupported_accuracy_and_policy_are_explicit(self):
        for value in (0, -1, True, float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(InvalidQuery):
                AccuracyRequest(angular_rad=value)
        with self.assertRaises(InvalidQuery):
            SessionPolicy((self.provider.reference,), fallback_policy="guess")

    def test_direction_neither_normalizes_bad_data_nor_publishes_aliases(self):
        row = self.provider.evaluate(self.provider.query()).states[0]
        for vector in ([0, 0, 0], [1, 1, 0], [float("nan"), 0, 1], [True, 0, 0]):
            with self.subTest(vector=vector), self.assertRaises(InvalidQuery):
                replace(row, vector=vector)
        source = [1, 0, 0]
        row = replace(row, vector=source)
        source[0] = 99
        self.assertEqual(row.vector, (1.0, 0.0, 0.0))

    def test_mutable_subclasses_cannot_enter_snapshot(self):
        class MutableKey(ObjectKey):
            pass
        with self.assertRaises(InvalidQuery):
            replace(self.provider.snapshot.objects[0], key=MutableKey("mutable:key"))


if __name__ == "__main__":
    unittest.main()
