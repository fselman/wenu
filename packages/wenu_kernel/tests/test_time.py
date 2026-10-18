"""Time admission, provenance and precision; no astronomy backend required.

Closest existing faults: test_records.RecordTests time precision/scale cases.
These retain that validation and test explicit conversion as a separate owner.
TT/TAI offsets use the USNO definition; the Decimal oracle is independent of
the adapter's Fraction normalization. Constructed adapters test envelopes only.
"""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext
from math import inf, nextafter
import unittest

from wenu_kernel import Kernel
from wenu_kernel.errors import (
    AccuracyUnavailable, IncompatibleContract, InvalidProviderResult,
    InvalidQuery, OutsideCoverage, ProviderEvaluationError,
    ResourceMismatch, TimeConversionUnavailable,
)
from wenu_kernel.records import (
    ModelRef, ResourceRef, SessionPolicy, TimePoint, TimeSpan, UnboundedCoverage,
)
from wenu_kernel.time import TimeConversion, TimeConversionAdmission, TimeService
from wenu_kernel.time_adapters import TaiTtAdapter
from synthetic_providers import FixedDirections, REFERENCE


def domain(scale="tai"):
    return TimeSpan(TimePoint(2400000, 0, scale), TimePoint(2600000, 0, scale))


def service(adapter):
    return TimeService((adapter,), admissions=(adapter.describe(),))


class ConstructedAdapter:
    """Deliberately synthetic TT->TDB offset; NOT a relativistic authority."""

    def __init__(self, admission=None):
        self.admission = admission or TimeConversionAdmission(
            "tt", "tdb", domain("tt"), ModelRef("synthetic:time", "1", "1"*64, ()),
            1e-6, ("CONSTRUCTED fixed offset; contract fixture only",),
        )
        self.calls = 0
        self.fault = None

    def describe(self):
        return self.admission

    def convert(self, time, target_scale):
        self.calls += 1
        if self.fault == "backend":
            raise RuntimeError("synthetic backend failure")
        if self.fault == "unavailable":
            raise TimeConversionUnavailable("synthetic missing authority", time=time)
        row = TimeConversion(time, replace(time, scale=target_scale, jd2=time.jd2 + 1e-8),
                             self.admission.model, 1e-8, self.admission.provenance)
        changes = {
            "source": {"source": replace(time, jd1=time.jd1+1)},
            "scale": {"target": replace(row.target, scale="tcb")},
            "model": {"model": replace(row.model, configuration_digest="2"*64)},
            "provenance": {"provenance": ("unadmitted policy",)},
            "bound": {"numerical_error_s": nextafter(self.admission.maximum_error_s, inf)},
        }
        if self.fault == "type":
            return object()
        return replace(row, **changes.get(self.fault, {}))


class TimeTests(unittest.TestCase):
    def test_identity_preserves_exact_small_part_and_has_no_adapter(self):
        for scale in ("tai", "tt", "tdb", "tcb"):
            original = TimePoint(-5000000, 1e-12, scale)
            row = TimeService().convert(original, scale, maximum_error_s=0)
            self.assertIs(row.source, original)
            self.assertIs(row.target, original)
            self.assertEqual(row.numerical_error_s, 0)
            self.assertEqual(row.model.model_id, "wenu.time:identity")

    def test_missing_pair_civil_scales_and_bad_precision_fail_explicitly(self):
        time = TimePoint(2451545, 0, "tt")
        for target in ("tai", "tdb", "tcb"):
            with self.assertRaises(TimeConversionUnavailable):
                TimeService().convert(time, target)
        for target in ("utc", "ut1", "TT", None):
            with self.assertRaises(InvalidQuery):
                TimeService().convert(time, target)
        for bound in (-1, True, float("nan"), inf):
            with self.assertRaises(InvalidQuery):
                TimeService().convert(time, "tt", maximum_error_s=bound)
        with self.assertRaises(InvalidQuery):
            TimeService().convert((2451545, 0, "tt"), "tt")

    def test_tai_tt_matches_usno_j2000_definition_both_directions(self):
        # USNO: J2000 TT 12:00 = TAI 11:59:27.816. Decimal is an
        # independent oracle and never uses a large binary64 sum.
        with localcontext() as ctx:
            ctx.prec = 90
            for source, sign in (("tai", 1), ("tt", -1)):
                row = service(TaiTtAdapter(domain(source))).convert(TimePoint(2451545, 0, source),
                                                                  "tt" if sign == 1 else "tai")
                expected = Decimal(sign) * Decimal("32.184") / Decimal(86400)
                residual = abs(Decimal.from_float(row.target.jd2) - expected) * Decimal(86400)
                self.assertLessEqual(residual, Decimal.from_float(row.numerical_error_s))
                self.assertLess(row.numerical_error_s, 1e-11)
                self.assertNotEqual(row.target.jd2, row.source.jd2)
                self.assertEqual(row.model.model_id, "wenu.time:tt-tai")

    def test_small_offsets_survive_at_large_jd(self):
        converter = service(TaiTtAdapter(domain()))
        a = converter.convert(TimePoint(2451545, 0, "tai"), "tt")
        b = converter.convert(TimePoint(2451545, 1e-12, "tai"), "tt")
        self.assertNotEqual(a.target, b.target)
        self.assertEqual(a.target.jd1 + a.target.jd2, b.target.jd1 + b.target.jd2)

    def test_conversion_is_independent_of_order_and_other_requests(self):
        converter = service(TaiTtAdapter(domain()))
        times = tuple(TimePoint(2451545, value, "tai") for value in (-.5, 0, 1e-12, .4999))
        cold = {time: converter.convert(time, "tt") for time in times}
        warm = {time: converter.convert(time, "tt") for time in reversed(times)}
        self.assertEqual(cold, warm)
        other = service(TaiTtAdapter(domain()))
        self.assertEqual(cold, {time: other.convert(time, "tt") for time in times})

    def test_day_rollovers_and_negative_days_have_outward_error_bounds(self):
        with localcontext() as ctx:
            ctx.prec = 90
            # Negative days are an explicitly admitted algebraic test domain,
            # not evidence that atomic time existed in antiquity.
            for scale, sign in (("tai", 1), ("tt", -1)):
                adapter = TaiTtAdapter(TimeSpan(TimePoint(-10000000, 0, scale),
                                               TimePoint(3000000, 0, scale)))
                converter = service(adapter)
                for day in (-1000000, 0, 2451545):
                    for fraction in (-.5, nextafter(-.5, 0), -.4997, 0, 1e-12,
                                     .4997, .4996275, -.4996275, nextafter(.5, 0)):
                        with self.subTest(scale=scale, day=day, fraction=fraction):
                            source = TimePoint(day, fraction, scale)
                            row = converter.convert(source, adapter.describe().target_scale)
                            expected = (Decimal(day) + Decimal.from_float(source.jd2)
                                        + Decimal(sign)*Decimal("32.184")/Decimal(86400))
                            actual = Decimal(row.target.jd1) + Decimal.from_float(row.target.jd2)
                            residual = abs(actual-expected)*Decimal(86400)
                            self.assertLessEqual(residual, Decimal.from_float(row.numerical_error_s))
                            self.assertLessEqual(row.numerical_error_s, adapter.describe().maximum_error_s)
                            self.assertTrue(-.5 <= row.target.jd2 < .5)

    def test_round_trip_preserves_instant_with_composed_numerical_budget(self):
        out = service(TaiTtAdapter(domain()))
        back = service(TaiTtAdapter(domain("tt")))
        with localcontext() as ctx:
            ctx.prec = 90
            for fraction in (-.5, 0, 1e-12, .4999):
                source = TimePoint(2451545, fraction, "tai")
                first = out.convert(source, "tt")
                second = back.convert(first.target, "tai")
                residual = abs((Decimal(second.target.jd1-source.jd1)
                                + Decimal.from_float(second.target.jd2)
                                - Decimal.from_float(source.jd2))*Decimal(86400))
                budget = (Decimal.from_float(first.numerical_error_s)
                          + Decimal.from_float(second.numerical_error_s))
                self.assertLessEqual(residual, budget)

    def test_requested_bound_equal_and_one_ulp_tighter(self):
        converter = service(TaiTtAdapter(domain()))
        time = TimePoint(2451545, 0, "tai")
        row = converter.convert(time, "tt")
        self.assertGreater(row.numerical_error_s, 0)
        self.assertEqual(converter.convert(time, "tt", maximum_error_s=row.numerical_error_s), row)
        with self.assertRaises(AccuracyUnavailable):
            converter.convert(time, "tt", maximum_error_s=nextafter(row.numerical_error_s, 0))

    def test_interval_closed_and_outside_rejected_before_backend(self):
        adapter = ConstructedAdapter()
        converter = service(adapter)
        for time in (adapter.admission.validity.start, adapter.admission.validity.stop):
            self.assertEqual(converter.convert(time, "tdb").source, time)
        calls = adapter.calls
        for time in (TimePoint(2399999, .4999, "tt"), TimePoint(2600000, 1e-20, "tt")):
            with self.assertRaises(OutsideCoverage):
                converter.convert(time, "tdb")
        self.assertEqual(adapter.calls, calls)

    def test_resource_coverage_checked_and_hash_bound(self):
        resource = ResourceRef("synthetic:table", "1", "a"*64,
                               TimeSpan(TimePoint(2451545, 0, "tt"), TimePoint(2451546, 0, "tt")),
                               "local-only", ("CONSTRUCTED",))
        adapter = ConstructedAdapter()
        adapter.admission = replace(adapter.admission,
                                    model=replace(adapter.admission.model, dependencies=(resource,)))
        converter = service(adapter)
        row = converter.convert(resource.coverage.start, "tdb")
        self.assertEqual(row.model.dependencies, (resource,))
        with self.assertRaises(OutsideCoverage):
            converter.convert(TimePoint(2451544, 0, "tt"), "tdb")
        self.assertEqual(adapter.calls, 1)
        adapter.admission = replace(adapter.admission, model=replace(adapter.admission.model,
            dependencies=(replace(resource, sha256="b"*64),)))
        with self.assertRaises(InvalidProviderResult):
            converter.convert(resource.coverage.start, "tdb")

    def test_explicit_allowlist_and_exact_contract_required(self):
        adapter = ConstructedAdapter()
        with self.assertRaises(ResourceMismatch):
            TimeService((adapter,))
        with self.assertRaises(ResourceMismatch):
            TimeService(admissions=(adapter.describe(),))
        with self.assertRaises(ResourceMismatch):
            TimeService((adapter,), admissions=(replace(adapter.describe(), maximum_error_s=2e-6),))
        for version in ("wenu.kernel/2.0", "wenu.kernel/0.9"):
            adapter.admission = replace(adapter.admission, contract_version=version)
            with self.assertRaises(IncompatibleContract):
                service(adapter)

    def test_duplicate_pairs_and_bad_adapter_descriptors_are_atomic(self):
        a = ConstructedAdapter()
        b = ConstructedAdapter(replace(a.admission, model=replace(a.admission.model, version="2")))
        with self.assertRaises(InvalidQuery):
            TimeService((a, b), admissions=(a.describe(), b.describe()))
        with self.assertRaises(InvalidQuery):
            TimeService((a,), admissions=(a.describe(), a.describe()))
        with self.assertRaises(IncompatibleContract):
            TimeService((object(),))
        a.describe = lambda: object()
        with self.assertRaises(InvalidProviderResult):
            TimeService((a,))
        self.assertEqual(a.calls, 0)

    def test_no_conversion_chaining_or_fallback(self):
        tai_tt = TaiTtAdapter(domain())
        tt_tdb = ConstructedAdapter()
        converter = TimeService((tai_tt, tt_tdb), admissions=(tai_tt.describe(), tt_tdb.describe()))
        with self.assertRaises(TimeConversionUnavailable):
            converter.convert(TimePoint(2451545, 0, "tai"), "tdb")
        self.assertEqual(tt_tdb.calls, 0)

    def test_malformed_results_fail_and_recovery_does_not_reuse_failed_output(self):
        adapter = ConstructedAdapter()
        converter = service(adapter)
        time = TimePoint(2451545, 0, "tt")
        for fault in ("type", "source", "scale", "model", "provenance", "bound"):
            adapter.fault = fault
            with self.subTest(fault=fault), self.assertRaises(InvalidProviderResult):
                converter.convert(time, "tdb")
        adapter.fault = None
        row = converter.convert(time, "tdb")
        self.assertEqual(adapter.calls, 7)
        self.assertEqual(row.source, time)

    def test_backend_cause_and_typed_failure_are_preserved(self):
        adapter = ConstructedAdapter()
        converter = service(adapter)
        time = TimePoint(2451545, 0, "tt")
        adapter.fault = "backend"
        with self.assertRaises(ProviderEvaluationError) as caught:
            converter.convert(time, "tdb")
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.assertEqual(caught.exception.time, time)
        adapter.fault = "unavailable"
        with self.assertRaises(TimeConversionUnavailable):
            converter.convert(time, "tdb")

    def test_records_copy_buffers_and_results_survive_caller_changes(self):
        adapter = ConstructedAdapter()
        provenance = list(adapter.admission.provenance)
        adapter.admission = replace(adapter.admission, provenance=provenance)
        adapters, allowed = [adapter], [adapter.describe()]
        converter = TimeService(adapters, admissions=allowed)
        adapters.clear()
        allowed.clear()
        provenance.clear()
        row = converter.convert(TimePoint(2451545, 0, "tt"), "tdb")
        with self.assertRaises(FrozenInstanceError):
            row.target = row.source
        self.assertTrue(row.provenance)
        builtin = TaiTtAdapter(domain())
        with self.assertRaises(FrozenInstanceError):
            builtin._admission = adapter.admission

    def test_invalid_admission_and_result_values_fail_at_construction(self):
        admission = ConstructedAdapter().admission
        for changes in ({"source_scale": "utc"}, {"target_scale": "tt"},
                        {"validity": domain("tai")}, {"maximum_error_s": -1},
                        {"maximum_error_s": True}, {"maximum_error_s": inf},
                        {"provenance": ()}, {"model": object()}):
            with self.subTest(changes=changes), self.assertRaises(InvalidQuery):
                replace(admission, **changes)
        resource = ResourceRef("synthetic:wrong-scale", "1", "a"*64,
                               UnboundedCoverage("tdb"), "local", ("CONSTRUCTED",))
        with self.assertRaises(InvalidQuery):
            replace(admission, model=replace(admission.model, dependencies=(resource,)))
        with self.assertRaises(InvalidQuery):
            TaiTtAdapter(UnboundedCoverage("tai"))
        with self.assertRaises(InvalidQuery):
            TaiTtAdapter(domain("tdb"))
        original = service(TaiTtAdapter(domain())).convert(TimePoint(2451545, 0, "tai"), "tt")
        for value in (True, -1, inf, float("nan")):
            with self.assertRaises(InvalidQuery):
                replace(original, numerical_error_s=value)

    def test_state_query_keeps_same_scale_policy_and_other_providers_idle(self):
        provider = FixedDirections("fixed")
        kernel = Kernel(references=(REFERENCE,))
        kernel.register(provider, ownership="borrowed")
        with kernel.open_session(SessionPolicy((provider.reference,))) as session:
            time = TimePoint(2451545, 0, "tai")
            with self.assertRaises(TimeConversionUnavailable):
                session.evaluate(provider.query(times=(time,)))
            converter = service(TaiTtAdapter(domain()))
            converted = converter.convert(time, "tt")
            self.assertEqual(provider.calls["evaluate"], 0)
            batch = session.evaluate(provider.query(times=(converted.target,)))
            self.assertEqual(batch.states[0].time, converted.target)
            self.assertEqual(provider.calls["evaluate"], 1)
        kernel.close()


if __name__ == "__main__":
    unittest.main()
