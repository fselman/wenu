"""Import and test-collection barriers execute without astronomy dependencies."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

import wenu_kernel


class IsolationTests(unittest.TestCase):
    def test_sdk_import_with_site_packages_disabled(self):
        root = str(Path(wenu_kernel.__file__).resolve().parent.parent)
        code = """
import json, sys
sys.path.insert(0, ROOT)
import wenu_kernel
from wenu_kernel import records, errors, time, time_adapters, conformance
for forbidden in ('wenu', 'numpy', 'astropy', 'matplotlib', 'skyfield', 'sgp4', 'pandas', 'spiceypy'):
    assert not any(name == forbidden or name.startswith(forbidden + '.') for name in sys.modules), forbidden
print(json.dumps(wenu_kernel.__all__))
""".replace("ROOT", repr(root))
        result = subprocess.run([sys.executable, "-I", "-S", "-c", code],
                                capture_output=True, text=True, check=True)
        self.assertIn("Kernel", json.loads(result.stdout))

    def test_external_consumer_uses_shipped_kit_without_repository_fixtures(self):
        root = str(Path(wenu_kernel.__file__).resolve().parent.parent)
        code = r'''
import io, sys, unittest
sys.path.insert(0, SDK_ROOT)
from dataclasses import replace
from wenu_kernel.conformance import ProviderActivity, ProviderCase, provider_suite
from wenu_kernel.errors import UnsupportedCapability
from wenu_kernel.records import (
    AccuracyRequest, CapabilityDecision, CatalogueRef, CatalogueSnapshot,
    DirectionState, ModelAdmission, ModelRef, ObjectKey, ObjectRecord,
    ProviderDescriptor, ProviderKey, ReferenceSpec, ResourceRef, StateBatch,
    StateQuery, TimePoint, TimeSpan, UncertaintyChannel, UncertaintyEvidence,
)

class ConsumerProvider:
    # Entirely constructed data owned by this external consumer; no imports
    # from the repository's synthetic provider or test helpers.
    def __init__(self, capability="native_direction"):
        epoch = TimePoint(2451545, 0, "tt")
        span = TimeSpan(replace(epoch, jd1=2451544), replace(epoch, jd1=2451547))
        key = ProviderKey("external-fixture", "1")
        resource = ResourceRef("external-fixture", "1", "1"*64, span, "offline", ("constructed",))
        self.catalogue_ref = CatalogueRef(key, (resource,), "2"*64)
        self.model = ModelRef("external-fixture:fixed", "1", "3"*64, (resource,))
        self.reference = ReferenceSpec("icrs", "ssb", "geometric", "direction", "rad", "external:none")
        self.objects = (ObjectKey("external:a"), ObjectKey("external:b"))
        caps = (capability, "batch_evaluation")
        self.source_epochs = {obj: (None if capability == "catalogue_lookup" and i == 0 else epoch)
                              for i, obj in enumerate(self.objects)}
        self.snapshot = CatalogueSnapshot(self.catalogue_ref, tuple(
            ObjectRecord(obj, (), "constructed", (() if self.source_epochs[obj] is None else (epoch,)),
                         caps, ("constructed",)) for obj in self.objects))
        admission = ModelAdmission(self.catalogue_ref, self.model, self.reference, self.objects, caps, span)
        self.descriptor = ProviderDescriptor(key, (self.catalogue_ref,), (admission,), "local:immutable")
        self.evaluations = self.closes = 0
        self.buffers = []
        self.epoch = epoch

    def describe(self):
        return self.descriptor

    def catalogue(self, reference):
        return self.snapshot

    def supports(self, query):
        return CapabilityDecision(True, "constructed supported sample")

    def evaluate(self, query):
        self.evaluations += 1
        numeric = UncertaintyChannel("bounded", 0, "rad", "angular_separation")
        unknown = UncertaintyChannel("not_evaluated", None, "rad", "unknown")
        evidence = UncertaintyEvidence(unknown, unknown, numeric)
        rows = []
        for time in query.times:
            for obj in query.objects:
                buffer = [1, 0, 0]
                self.buffers.append(buffer)
                rows.append(DirectionState(obj, time, self.source_epochs[obj], time, self.reference, buffer, evidence))
        return StateBatch(query, rows)

    def certify(self, query, anchor):
        raise UnsupportedCapability("no angular certificate capability")

    def close(self):
        self.closes += 1

def make_case(capability="native_direction"):
    p = ConsumerProvider(capability)
    query = StateQuery(p.catalogue_ref, p.model, tuple(reversed(p.objects)),
                       (replace(p.epoch, jd2=.1), p.epoch), p.reference, AccuracyRequest())
    probe = replace(query, times=(replace(p.epoch, jd1=p.epoch.jd1+1),))
    def mutate():
        for buffer in p.buffers:
            buffer[:] = [999, 999, 999]
    return ProviderCase(p, query, probe, lambda: ProviderActivity(p.evaluations, 0, p.closes), mutate)

suite = provider_suite(make_case, name="IndependentConsumer")
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
assert result.wasSuccessful(), result.errors + result.failures
assert result.testsRun == 8 and not result.skipped
lookup_suite = provider_suite(lambda: make_case("catalogue_lookup"), name="IndependentLookupConsumer")
lookup_result = unittest.TextTestRunner(stream=io.StringIO()).run(lookup_suite)
assert lookup_result.wasSuccessful(), lookup_result.errors + lookup_result.failures
assert lookup_result.testsRun == 8 and not lookup_result.skipped
for forbidden in ("wenu", "numpy", "astropy", "matplotlib", "skyfield", "sgp4",
                  "synthetic_providers", "test_sessions", "test_conformance"):
    assert not any(n == forbidden or n.startswith(forbidden + ".") for n in sys.modules), forbidden
print("Independent consumer: 8 shipped conformance checks passed")
print("Independent lookup consumer: 8 shipped conformance checks passed")
'''.replace("SDK_ROOT", repr(root))
        result = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", code],
                                capture_output=True, text=True, check=True, cwd="/tmp")
        self.assertIn("8 shipped conformance checks passed", result.stdout)
        self.assertIn("Independent lookup consumer: 8 shipped conformance checks passed", result.stdout)

    def test_local_provider_gate_collects_without_wenu_or_backends(self):
        # Ordinary unittest discovery is the package gate; no pytest plugin or
        # root Wenu imports are needed even to enumerate its tests.
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent))
        self.assertGreater(suite.countTestCases(), 0)
        self.assertEqual(unittest.defaultTestLoader.errors, [])
        for forbidden in ("wenu", "numpy", "astropy", "matplotlib", "skyfield", "sgp4"):
            self.assertFalse(any(n == forbidden or n.startswith(forbidden + ".") for n in sys.modules))


if __name__ == "__main__":
    unittest.main()
