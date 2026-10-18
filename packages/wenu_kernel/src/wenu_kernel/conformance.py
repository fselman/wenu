"""Reusable stdlib provider contract tests, shipped in the SDK wheel.

No concrete provider, test fixture, acquisition route or science oracle is
imported here. Provider packages supply fresh offline cases and honest activity
and buffer-mutation hooks. Run one case per admitted model/reference/subset.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Callable
import unittest

from .errors import InvalidQuery, TimeConversionUnavailable, UnknownObject, UnsupportedCapability
from .kernel import Kernel
from .providers import StateProvider
from .records import (
    CapabilityDecision, ObjectKey, SessionPolicy, StateQuery, exact,
)
from .reuse import validate_certificate, validate_reuse_plan


@dataclass(frozen=True, slots=True)
class ProviderActivity:
    """Owner instrumentation, including hidden numerical work in metadata calls.

    evaluations counts full state computations, not only public method entries;
    certifications counts bound computations; closes counts close invocations.
    Counters must be monotonic. Inspection must not change provider state.
    """

    evaluations: int
    certifications: int
    closes: int

    def __post_init__(self):
        for value in (self.evaluations, self.certifications, self.closes):
            if type(value) is not int or value < 0:
                raise InvalidQuery("activity counters must be nonnegative integers")


@dataclass(frozen=True, slots=True)
class ProviderCase:
    provider: StateProvider
    query: StateQuery
    probe: StateQuery
    activity: Callable[[], ProviderActivity]
    mutate_buffers: Callable[[], None]
    reuse_query: StateQuery | None = None

    def __post_init__(self):
        exact(self.query, StateQuery)
        exact(self.probe, StateQuery)
        if not callable(self.activity) or not callable(self.mutate_buffers):
            raise InvalidQuery("provider case requires activity and buffer mutation hooks")
        if self.query.times == self.probe.times or len(self.query.times) < 2:
            raise InvalidQuery("case needs a multi-time query and a distinct probe")
        if not set(self.probe.times) - set(self.query.times):
            raise InvalidQuery("probe must include an additional evaluation time")
        for query in (self.query, self.probe):
            if query.evaluation_policy != "full_model" or query.coverage is not None:
                raise InvalidQuery("base conformance queries must request full-model samples")
            if (query.catalogue, query.model, query.reference, query.objects) != (
                    self.query.catalogue, self.query.model, self.query.reference, self.query.objects):
                raise InvalidQuery("probe must preserve catalogue/model/reference/object binding")
        if self.reuse_query is not None:
            exact(self.reuse_query, StateQuery)
            reuse = self.reuse_query
            if (reuse.catalogue, reuse.model, reuse.reference, reuse.objects) != (
                    self.query.catalogue, self.query.model, self.query.reference, self.query.objects):
                raise InvalidQuery("reuse case must preserve the base scientific binding")
            if reuse.evaluation_policy != "bounded_reuse" or reuse.accuracy.angular_rad is None:
                raise InvalidQuery("reuse case needs an explicit angular bound")
            if len(reuse.times) < 2:
                raise InvalidQuery("reuse case must exercise multiple times")


class ProviderConformance:
    """Mix with unittest.TestCase and implement make_case() -> ProviderCase.

    Each invocation must create an independent, open provider with identical
    immutable scientific bindings. Hooks stay in the provider's own test code.
    All tests execute; unadvertised optional operations are checked as absent
    or refused, while advertised reuse requires an executable supplied case.
    Science accuracy, certificate interval proofs and real-resource validity
    remain provider-owned obligations; this kit cannot establish those proofs.
    """

    def make_case(self) -> ProviderCase:
        raise NotImplementedError

    def _activity(self, case):
        value = case.activity()
        self.assertIs(type(value), ProviderActivity)
        return value

    def _open_case(self, *, ownership="owned", reproducibility="reproducible"):
        case = self.make_case()
        self.assertIs(type(case), ProviderCase)
        # Failed registration does not transfer ownership. Cleanup must still
        # release the caller-created provider without hiding the first failure.
        caller_owned = [True]
        self.addCleanup(lambda: case.provider.close() if caller_owned[0] else None)
        descriptor = case.provider.describe()
        references = tuple(dict.fromkeys(a.reference for a in descriptor.admissions))
        kernel = Kernel(references=references)
        self.addCleanup(kernel.close)
        kernel.register(case.provider, ownership=ownership)
        caller_owned[0] = ownership != "owned"
        session = kernel.open_session(SessionPolicy((case.query.catalogue,), reproducibility=reproducibility))
        self.addCleanup(session.close)
        admissions = [a for a in descriptor.admissions if (
            a.catalogue == case.query.catalogue and a.model == case.query.model
            and a.reference == case.query.reference and set(case.query.objects) <= set(a.objects))]
        self.assertEqual(len(admissions), 1)
        admission = admissions[0]
        needs_reuse = "direction_reuse_bound" in admission.capabilities
        self.assertEqual(case.reuse_query is not None, needs_reuse,
                         "advertised reuse needs a supplied executable case")
        return case, kernel, session, admission

    def test_conformance_metadata_is_pure_and_bound(self):
        case, _, session, _ = self._open_case()
        before = self._activity(case)
        descriptor = case.provider.describe()
        snapshot = case.provider.catalogue(case.query.catalogue)
        frozen = deepcopy((descriptor, snapshot))
        for query in (case.query, case.probe):
            decision = case.provider.supports(query)
            self.assertIs(type(decision), CapabilityDecision)
            self.assertTrue(decision.supported, "conformance samples must be admitted")
        self.assertEqual(before, self._activity(case), "metadata performed numerical work or closed a resource")
        self.assertEqual(snapshot, session.catalogue(case.query.catalogue))
        self.assertEqual((case.provider.describe(), case.provider.catalogue(case.query.catalogue)), frozen)

    def test_conformance_order_identity_and_exact_cache(self):
        case, _, session, _ = self._open_case()
        before = self._activity(case)
        result = session.evaluate(case.query)
        self.assertEqual(result.query, case.query)
        self.assertEqual(tuple((r.time, r.object_key) for r in result.states),
                         tuple((t, obj) for t in case.query.times for obj in case.query.objects))
        after = self._activity(case)
        self.assertGreater(after.evaluations, before.evaluations, "activity hook did not observe evaluation")
        self.assertIs(session.evaluate(case.query), result)
        self.assertEqual(self._activity(case), after)
        # Reverse both axes; the provider may not sort logical requests.
        reverse = replace(case.query, times=tuple(reversed(case.query.times)),
                          objects=tuple(reversed(case.query.objects)))
        reversed_result = session.evaluate(reverse)
        lookup = {(r.time, r.object_key): r for r in result.states}
        self.assertEqual(reversed_result.states,
                         tuple(lookup[t, obj] for t in reverse.times for obj in reverse.objects))

    def test_conformance_fresh_warm_and_request_order(self):
        case, _, session, admission = self._open_case()
        first = session.evaluate(case.query)
        probe = session.evaluate(case.probe)
        other, _, fresh, _ = self._open_case()
        self.assertEqual((case.query, case.probe), (other.query, other.probe),
                         "case factories must preserve exact scientific bindings")
        self.assertIsNot(case.provider, other.provider, "factory reused a live provider")
        self.assertEqual(fresh.evaluate(other.probe), probe)
        self.assertEqual(fresh.evaluate(other.query), first)
        self.assertEqual(session.evaluate(case.query), first)
        if "static_direction" in admission.capabilities:
            vectors = {}
            for row in first.states + probe.states:
                self.assertEqual(row.vector, vectors.setdefault(row.object_key, row.vector),
                                 "static direction changed with evaluation time")

    def test_conformance_publication_and_owned_lifetime(self):
        case, kernel, session, _ = self._open_case()
        result = session.evaluate(case.query)
        snapshot = session.catalogue(case.query.catalogue)
        saved = deepcopy((result, snapshot))
        case.mutate_buffers()
        self.assertEqual((result, snapshot), saved)
        before = self._activity(case)
        session.close()
        kernel.close()
        self.assertEqual(self._activity(case).closes, before.closes + 1)
        kernel.close()
        session.close()
        self.assertEqual(self._activity(case).closes, before.closes + 1)
        self.assertEqual((result, snapshot), saved, "published data changed after close")

    def test_conformance_borrowed_lifetime(self):
        case, kernel, session, _ = self._open_case(ownership="borrowed")
        result = session.evaluate(case.query)
        saved = deepcopy(result)
        before = self._activity(case)
        session.close()
        kernel.close()
        self.assertEqual(self._activity(case).closes, before.closes)
        self.assertEqual(result, saved)

    def test_conformance_invalid_selection_never_evaluates(self):
        case, _, session, _ = self._open_case()
        records = session.catalogue(case.query.catalogue).objects
        keys = {r.key for r in records}
        absent = ObjectKey("wenu-conformance:absent")
        while absent in keys:
            absent = ObjectKey(absent.value + "-absent")
        before = self._activity(case)
        with self.assertRaises(UnknownObject):
            session.evaluate(replace(case.query, objects=(absent,)))
        target = "tdb" if case.query.times[0].scale != "tdb" else "tt"
        with self.assertRaises(TimeConversionUnavailable):
            session.evaluate(replace(case.query, times=tuple(replace(t, scale=target) for t in case.query.times)))
        self.assertEqual(self._activity(case), before)

    def test_conformance_direction_certificate_contract(self):
        case, _, session, admission = self._open_case(reproducibility="interactive_bounded")
        if case.reuse_query is None:
            anchor = session.evaluate(replace(case.query, objects=case.query.objects[:1], times=case.query.times[:1]))
            with self.assertRaises(UnsupportedCapability):
                case.provider.certify(anchor.query, anchor)
            return
        query = case.reuse_query
        anchor_query = replace(query, evaluation_policy="full_model", coverage=None,
                               objects=query.objects[:1], times=query.times[:1])
        anchor = session.evaluate(anchor_query)
        request = replace(query, objects=query.objects[:1], times=query.times[:1], coverage=None)
        before = self._activity(case)
        cert = case.provider.certify(request, anchor)
        after = self._activity(case)
        self.assertEqual(after.evaluations, before.evaluations, "certification propagated another state")
        self.assertGreater(after.certifications, before.certifications,
                           "activity hook did not observe certification")
        self.assertEqual(after.closes, before.closes)
        validate_certificate(cert, anchor, admission)
        self.assertEqual(case.provider.certify(request, anchor), cert)
        result = session.evaluate(query)
        self.assertTrue(result.reuse_certificates, "declared reuse case produced no certificates")
        saved = deepcopy(result)
        session.evaluate(case.probe)
        self.assertEqual(result, saved)

    def test_conformance_canonical_planning_and_results(self):
        case, _, session, admission = self._open_case()
        if "canonical_direction_reuse" not in admission.capabilities:
            # A planner is optional; no operation is imposed on this provider.
            result = session.evaluate(case.reuse_query or case.query)
            self.assertIsNone(result.reuse_plan)
            self.assertTrue(all(row.anchor_time == row.time for row in result.states),
                            "default non-planning provider used an arbitrary warm anchor")
            return
        query = case.reuse_query
        before = self._activity(case)
        plan = case.provider.plan_reuse(query)
        validate_reuse_plan(plan, query, admission)
        self.assertEqual(case.provider.plan_reuse(query), plan)
        self.assertEqual(self._activity(case), before, "planning performed numerical work or closed a resource")
        cold = session.evaluate(query)
        self.assertIsNotNone(cold.reuse_plan, "canonical conformance query fell back instead of exercising planning")
        other, _, fresh, _ = self._open_case()
        self.assertEqual(other.reuse_query, query)
        self.assertIsNot(other.provider, case.provider)
        fresh.evaluate(other.probe)
        reverse = replace(query, times=tuple(reversed(query.times)), objects=tuple(reversed(query.objects)))
        fresh.evaluate(reverse)
        self.assertEqual(fresh.evaluate(other.reuse_query), cold,
                         "canonical output depends on warmness or request order")


def provider_suite(factory: Callable[[], ProviderCase], *, name: str) -> unittest.TestSuite:
    """Build one independent suite for a factory, usable in unittest.load_tests.

    The descriptive name identifies the model/reference case in test reports.
    No provider is created during construction/discovery of this suite.
    """
    if not callable(factory) or type(name) is not str or not name.isidentifier():
        raise InvalidQuery("suite requires a case factory and identifier name")
    case_type = type(name, (ProviderConformance, unittest.TestCase),
                     {"make_case": staticmethod(factory), "__module__": __name__})
    return unittest.defaultTestLoader.loadTestsFromTestCase(case_type)
