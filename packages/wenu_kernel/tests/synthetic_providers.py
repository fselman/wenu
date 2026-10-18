"""Constructed fixtures, not captured astronomy data or numerical oracles."""

from dataclasses import replace
from hashlib import sha256
from math import cos, sin, pi

from wenu_kernel.records import (
    AccuracyRequest, CapabilityDecision, CatalogueRef, CatalogueSnapshot,
    DirectionState, ExternalId, ModelAdmission, ModelRef, ObjectKey, ObjectRecord,
    ProviderDescriptor, ProviderKey, ReferenceSpec, ResourceRef, StateBatch,
    StateQuery, TimePoint, TimeSpan, UncertaintyChannel, UncertaintyEvidence,
)
from wenu_kernel.errors import UnsupportedCapability

REFERENCE = ReferenceSpec("icrs", "ssb", "geometric", "direction", "rad", "synthetic:none")
EPOCH = TimePoint(2451545, 0.0, "tt")


def digest(value):
    return sha256(value.encode()).hexdigest()


class SyntheticDirections:
    """Instrumentation is deliberately mutable; published records are not."""

    rate = 0.0
    capability = "native_direction"

    def __init__(self, name):
        self.key = ProviderKey(name, "synthetic-1")
        self.objects = (ObjectKey(name + ":a"), ObjectKey(name + ":b"))
        self.coverage = TimeSpan(TimePoint(2400000, 0, "tt"), TimePoint(2500000, 0, "tt"))
        resource = ResourceRef(name, "constructed-1", digest(name), self.coverage,
                               "offline:synthetic", ("constructed fixture; no observations",))
        self.reference = CatalogueRef(self.key, (resource,), digest(name + ":membership"))
        self.model = ModelRef(name + ":directions", "1", digest(str(self.rate)), (resource,))
        caps = (self.capability, "batch_evaluation")
        self.snapshot = CatalogueSnapshot(self.reference, tuple(
            ObjectRecord(key, (ExternalId(name, "1", str(i)),), "synthetic",
                         (EPOCH,), caps, ("constructed",)) for i, key in enumerate(self.objects)))
        admission = ModelAdmission(self.reference, self.model, REFERENCE,
                                   self.objects, caps, self.coverage)
        self.descriptor = ProviderDescriptor(self.key, (self.reference,), (admission,), "local:immutable")
        self.calls = {"catalogue": 0, "supports": 0, "evaluate": 0, "close": 0}
        self.fault = None
        self.buffers = []

    def describe(self):
        return self.descriptor

    def catalogue(self, reference):
        self.calls["catalogue"] += 1
        if self.fault == "catalogue":
            raise RuntimeError("synthetic catalogue failure")
        if self.fault == "wrong_catalogue":
            return replace(self.snapshot, reference=replace(reference, membership_digest="0" * 64))
        return self.snapshot

    def supports(self, query):
        self.calls["supports"] += 1
        return CapabilityDecision(self.fault != "unsupported", "synthetic decision")

    def evaluate(self, query):
        self.calls["evaluate"] += 1
        if self.fault == "backend":
            raise RuntimeError("synthetic numerical failure")
        states = []
        unknown = UncertaintyChannel("not_evaluated", None, "rad", "synthetic unknown")
        numerical = UncertaintyChannel("bounded", 2e-15, "rad", "angular_separation")
        if self.fault == "statistical":
            numerical = replace(numerical, status="statistical")
        if self.fault == "unknown_error":
            numerical = replace(numerical, status="not_evaluated", value=None)
        evidence = UncertaintyEvidence(unknown, unknown, numerical)
        for time in query.times:
            for key in query.objects:
                angle = self.rate * ((time.jd1 - EPOCH.jd1) + (time.jd2 - EPOCH.jd2))
                angle += self.objects.index(key) * 0.1
                vector = [cos(angle), sin(angle), 0.0]
                self.buffers.append(vector)
                row = DirectionState(key, time, EPOCH, time, REFERENCE, vector, evidence)
                if self.fault == "wrong_epoch":
                    row = replace(row, source_epoch=TimePoint(2451544, 0, "tt"))
                if self.fault == "wrong_anchor":
                    row = replace(row, anchor_time=TimePoint(2451544, 0, "tt"))
                states.append(row)
        if self.fault == "reorder":
            states.reverse()
        if self.fault == "omit":
            states.pop()
        if self.fault == "duplicate":
            states.append(states[0])
        return StateBatch(query, states)

    def certify(self, query, anchor):
        raise UnsupportedCapability("synthetic foundation has no reuse certificates")

    def close(self):
        self.calls["close"] += 1
        if self.fault == "close":
            raise RuntimeError("synthetic close failure")

    def query(self, **changes):
        return replace(StateQuery(self.reference, self.model, self.objects,
                                 (EPOCH,), REFERENCE, AccuracyRequest()), **changes)


class FixedDirections(SyntheticDirections):
    pass


class MovingDirections(SyntheticDirections):
    rate = pi / 2
    capability = "epoch_direction"
