"""Exercise the shipped kit and prove it rejects faulty provider cases.

The closest existing tests are the synthetic provider checks in test_sessions.
Those fixture-specific failure oracles remain intact; this owner validates the
distributable harness against every currently implemented state capability.
"""

from dataclasses import replace
import io
import unittest

from wenu_kernel.conformance import ProviderActivity, ProviderCase, provider_suite
from wenu_kernel.errors import InvalidQuery
from wenu_kernel.records import AccuracyRequest
from synthetic_providers import (
    CanonicalDirections, CertifiedDirections, FixedDirections, MovingDirections,
    SyntheticCartesian, StaticDirections, CertifiedStaticDirections, CatalogueLookupDirections, EPOCH,
)


def make_factory(cls, name, **options):
    def factory():
        provider = cls(name, **options)
        query = provider.query(times=(replace(EPOCH, jd2=2**-10), EPOCH),
                               objects=tuple(reversed(provider.objects)))
        probe = replace(query, times=(replace(EPOCH, jd2=.01), replace(EPOCH, jd2=.02)))
        caps = provider.describe().admissions[0].capabilities
        reuse = (replace(query, accuracy=AccuracyRequest(angular_rad=1e-5), evaluation_policy="bounded_reuse")
                 if "direction_reuse_bound" in caps else None)

        def activity():
            return ProviderActivity(provider.calls["evaluate"], provider.calls.get("certify", 0), provider.calls["close"])

        def mutate_buffers():
            for buffer in provider.buffers:
                buffer[:] = [999, 999, 999]

        return ProviderCase(provider, query, probe, activity, mutate_buffers, reuse)
    return factory


FACTORIES = (
    ("FixedContract", make_factory(FixedDirections, "kit-fixed")),
    ("MovingContract", make_factory(MovingDirections, "kit-moving")),
    ("CertifiedContract", make_factory(CertifiedDirections, "kit-certified")),
    ("CanonicalContract", make_factory(CanonicalDirections, "kit-canonical")),
    ("CartesianContract", make_factory(SyntheticCartesian, "kit-cartesian")),
    ("PositionOnlyContract", make_factory(SyntheticCartesian, "kit-position-only", velocity_available=False)),
    ("StaticContract", make_factory(StaticDirections, "kit-static")),
    ("CertifiedStaticContract", make_factory(CertifiedStaticDirections, "kit-certified-static")),
    ("CatalogueLookupContract", make_factory(CatalogueLookupDirections, "kit-lookup")),
    ("UnknownEpochLookupContract", make_factory(CatalogueLookupDirections, "kit-undated", epochs=(None, None))),
)


def run_suite(factory, name="FaultyContract"):
    # Capture expected failures; an expected failing nested suite must not
    # write alarming tracebacks into the outer successful acceptance gate.
    return unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(provider_suite(factory, name=name))


class HarnessTests(unittest.TestCase):
    def assert_rejects(self, factory, expected_test):
        result = run_suite(factory)
        failures = result.failures + result.errors
        self.assertTrue(failures, "conformance accepted a deliberately faulty provider")
        self.assertTrue(any(expected_test in test.id() for test, _ in failures),
                        [test.id() for test, _ in failures])
        self.assertFalse(result.skipped)

    def test_suite_discovery_does_not_construct_provider(self):
        def factory():
            self.fail("provider constructed during discovery")
        suite = provider_suite(factory, name="LazyContract")
        self.assertEqual(suite.countTestCases(), 8)

    def test_case_and_activity_require_usable_instrumentation(self):
        case = FACTORIES[0][1]()
        try:
            for value in (-1, True, 1.5):
                with self.assertRaises(InvalidQuery):
                    ProviderActivity(value, 0, 0)
            for changes in ({"query": replace(case.query, times=case.query.times[:1])},
                            {"probe": case.query}, {"activity": None}, {"mutate_buffers": None},
                            {"probe": replace(case.query, times=tuple(reversed(case.query.times)))},
                            {"reuse_query": case.query}):
                with self.subTest(changes=changes), self.assertRaises(InvalidQuery):
                    replace(case, **changes)
            for name in ("", "bad-name", "123", None):
                with self.assertRaises(InvalidQuery):
                    provider_suite(FACTORIES[0][1], name=name)
        finally:
            case.provider.close()

    def test_fault_wrong_order_is_detected_by_shipped_gate(self):
        def factory():
            case = FACTORIES[0][1]()
            case.provider.fault = "reorder"
            return case
        self.assert_rejects(factory, "order_identity_and_exact_cache")

    def test_failed_metadata_setup_closes_caller_owned_provider(self):
        created = []
        def factory():
            case = FACTORIES[0][1]()
            created.append(case.provider)
            case.provider.describe = lambda: None
            return case
        result = run_suite(factory)
        self.assertEqual(len(result.errors), 8)
        self.assertEqual(len(created), 8)
        self.assertTrue(all(p.calls["close"] == 1 for p in created))

    def test_fault_metadata_propagation_is_detected(self):
        def factory():
            case = FACTORIES[0][1]()
            supports = case.provider.supports
            def impure(query):
                case.provider.evaluate(query)
                return supports(query)
            case.provider.supports = impure
            return case
        self.assert_rejects(factory, "metadata_is_pure_and_bound")

    def test_fault_warm_state_changes_output_is_detected(self):
        def factory():
            case = FACTORIES[0][1]()
            evaluate = case.provider.evaluate
            def history_dependent(query):
                batch = evaluate(query)
                if case.provider.calls["evaluate"] > 1:
                    row = replace(batch.states[0], vector=(0, 0, 1))
                    batch = replace(batch, states=(row,)+batch.states[1:])
                return batch
            case.provider.evaluate = history_dependent
            return case
        self.assert_rejects(factory, "fresh_warm_and_request_order")

    def test_fault_static_direction_changes_with_time_is_detected(self):
        def factory():
            case = make_factory(StaticDirections, "fault-static")()
            case.provider.rate = 1.0
            return case
        self.assert_rejects(factory, "fresh_warm_and_request_order")

    def test_fault_unobserved_evaluation_is_detected(self):
        def factory():
            case = FACTORIES[0][1]()
            return replace(case, activity=lambda: ProviderActivity(0, 0, 0))
        self.assert_rejects(factory, "order_identity_and_exact_cache")

    def test_fault_lookup_uses_query_time_to_move_source_direction_is_detected(self):
        def factory():
            case = make_factory(CatalogueLookupDirections, "fault-lookup")()
            case.provider.rate = 1.0
            return case
        self.assert_rejects(factory, "fresh_warm_and_request_order")

    def test_fault_missing_advertised_reuse_case_is_detected(self):
        def factory():
            return replace(FACTORIES[2][1](), reuse_query=None)
        self.assert_rejects(factory, "direction_certificate_contract")

    def test_fault_invalid_certificate_is_detected(self):
        def factory():
            case = FACTORIES[2][1]()
            case.provider.certificate_fault = "model"
            return case
        self.assert_rejects(factory, "direction_certificate_contract")

    def test_fault_planning_propagates_is_detected(self):
        def factory():
            case = FACTORIES[3][1]()
            planner = case.provider.plan_reuse
            def impure(query):
                case.provider.evaluate(replace(query, evaluation_policy="full_model", coverage=None))
                return planner(query)
            case.provider.plan_reuse = impure
            return case
        self.assert_rejects(factory, "canonical_planning_and_results")


def load_tests(loader, tests, pattern):
    for name, factory in FACTORIES:
        tests.addTests(provider_suite(factory, name=name))
    return tests


if __name__ == "__main__":
    unittest.main()
