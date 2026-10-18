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
                angle = self.angular_rate(key) * ((time.jd1 - EPOCH.jd1) + (time.jd2 - EPOCH.jd2))
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

    def angular_rate(self, key):
        return self.rate

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


def shifted(time, days):
    """Toy fixture date arithmetic, retaining the small binary fraction."""
    from fractions import Fraction
    from math import floor
    fraction = Fraction(time.jd2) + Fraction(days)
    carry = floor(fraction + Fraction(1, 2))
    small = float(fraction - carry)
    if small == 0.5:
        carry += 1
        small = -0.5
    return TimePoint(time.jd1 + carry, small, time.scale)


class CertifiedDirections(SyntheticDirections):
    """Constructed circular motions with conservative rational interval bounds.

    Each source has its own motion/range. The declared numerical anchor floor
    is fixture evidence, not an astrometric accuracy measurement.
    """

    capability = "epoch_direction"

    def __init__(self, name="certified"):
        super().__init__(name)
        caps = (self.capability, "batch_evaluation", "direction_reuse_bound")
        self.model = replace(self.model, configuration_digest=digest("circular:2^-10,2^-20"))
        self.snapshot = replace(self.snapshot, objects=tuple(replace(o, capabilities=caps)
                                                            for o in self.snapshot.objects))
        admission = replace(self.descriptor.admissions[0], model=self.model, capabilities=caps)
        self.descriptor = replace(self.descriptor, admissions=(admission,))
        self.calls["certify"] = 0
        self.evaluated_objects = []
        self.certificate_fault = None
        self.fail_certificate_object = None

    def angular_rate(self, key):
        return 2.0 ** (-10 if key == self.objects[0] else -20)

    def evaluate(self, query):
        self.evaluated_objects.extend((t, o) for t in query.times for o in query.objects)
        return super().evaluate(query)

    def certify(self, query, anchor):
        from fractions import Fraction
        from math import inf, nextafter
        from wenu_kernel.errors import AccuracyUnavailable
        from wenu_kernel.reuse import make_certificate, direction_anchor_identity, certificate_identity
        self.calls["certify"] += 1
        fault = self.certificate_fault if (self.fail_certificate_object is None
                or anchor.states[0].object_key == self.fail_certificate_object) else None
        if fault == "unavailable":
            raise AccuracyUnavailable("constructed provider cannot bound this interval")
        if fault == "unsupported":
            raise UnsupportedCapability("constructed certificate not available")
        if fault == "backend":
            raise RuntimeError("constructed certificate backend failure")
        if fault == "none":
            return None
        row = anchor.states[0]
        width = 2.0 ** (-8 if row.object_key == self.objects[0] else -2)
        start, stop = shifted(row.anchor_time, -width), shifted(row.anchor_time, width)
        start = max((start, self.coverage.start), key=TimeSpan.key)
        stop = min((stop, self.coverage.stop), key=TimeSpan.key)
        elapsed = max(abs(Fraction(t.jd1 - row.anchor_time.jd1)
                          + Fraction(t.jd2) - Fraction(row.anchor_time.jd2)) for t in (start, stop))
        error = Fraction(row.evidence.numerical.value) + Fraction(self.angular_rate(row.object_key)) * elapsed
        maximum = nextafter(float(error), inf)
        method = ModelRef(self.key.provider_id + ":constant-angular-speed-bound", "1",
                          digest("constructed-rational-outward-bound"), self.model.dependencies)
        cert = make_certificate(catalogue=query.catalogue, model=query.model,
                                anchor_identity=direction_anchor_identity(anchor),
                                objects=query.objects, reference=query.reference,
                                validity=TimeSpan(start, stop), metric="angular_separation",
                                maximum_error=maximum, method=method)
        if fault == "identity":
            object.__setattr__(cert, "identity", "0" * 64)
        elif fault == "anchor":
            cert = replace(cert, anchor_identity="0" * 64)
        elif fault == "model":
            cert = replace(cert, model=replace(cert.model, configuration_digest="0" * 64))
        elif fault == "catalogue":
            cert = replace(cert, catalogue=replace(cert.catalogue, membership_digest="0" * 64))
        elif fault == "objects":
            cert = replace(cert, objects=(ObjectKey("other:object"),))
        elif fault == "reference":
            cert = replace(cert, reference=replace(cert.reference, correction_policy="other"))
        elif fault == "metric":
            cert = replace(cert, metric="wrong-metric")
        elif fault == "anchor_error":
            cert = replace(cert, maximum_error=0)
        elif fault == "scale":
            cert = replace(cert, validity=TimeSpan(replace(start, scale="tdb"), replace(stop, scale="tdb")))
        elif fault == "outside_resource":
            cert = replace(cert, validity=TimeSpan(TimePoint(1, 0, "tt"), stop))
        elif fault == "omitted_anchor":
            cert = replace(cert, validity=TimeSpan(shifted(row.time, .1), shifted(row.time, .2)))
        elif fault == "method_resource":
            foreign = replace(self.model.dependencies[0], sha256="0" * 64)
            cert = replace(cert, method=replace(cert.method, dependencies=(foreign,)))
        return cert if fault == "identity" else replace(cert, identity=certificate_identity(cert))


class CanonicalDirections(CertifiedDirections):
    """Constructed deterministic binary date cells, not a real motion model."""

    def __init__(self, name="canonical"):
        super().__init__(name)
        caps = self.descriptor.admissions[0].capabilities + ("canonical_direction_reuse",)
        self.snapshot = replace(self.snapshot, objects=tuple(replace(o, capabilities=caps) for o in self.snapshot.objects))
        self.descriptor = replace(self.descriptor, admissions=(replace(self.descriptor.admissions[0], capabilities=caps),))
        self.plan_fault = None

    def plan_reuse(self, query):
        from fractions import Fraction
        from math import floor
        from wenu_kernel.errors import AccuracyUnavailable
        from wenu_kernel.records import AnchorSelection
        from wenu_kernel.reuse import make_reuse_plan, reuse_plan_identity
        fault = self.plan_fault
        if fault == "unavailable":
            raise AccuracyUnavailable("constructed canonical schedule unavailable")
        if fault == "unsupported":
            raise UnsupportedCapability("constructed canonical schedule unsupported")
        if fault == "backend":
            raise RuntimeError("constructed planning failure")
        if fault == "none":
            return None
        anchors = []
        for time in query.times:
            for obj in query.objects:
                width = Fraction(1, 256 if obj == self.objects[0] else 4)
                elapsed = Fraction(time.jd1 - EPOCH.jd1) + Fraction(time.jd2) - Fraction(EPOCH.jd2)
                index = floor(elapsed / width + Fraction(1, 2))
                anchor = shifted(EPOCH, index * width)
                anchor = max((anchor, self.coverage.start), key=TimeSpan.key)
                anchor = min((anchor, self.coverage.stop), key=TimeSpan.key)
                anchors.append(AnchorSelection(obj, time, anchor))
        method = ModelRef(self.key.provider_id + ":binary-cells", "1", digest("nearest binary cells; ties advance"), self.model.dependencies)
        plan = make_reuse_plan(query, anchors, method)
        if fault == "query":
            plan = replace(plan, query=replace(query, accuracy=AccuracyRequest(angular_rad=2e-5)))
        elif fault == "omit":
            plan = replace(plan, anchors=plan.anchors[:-1])
        elif fault == "order":
            plan = replace(plan, anchors=tuple(reversed(plan.anchors)))
        elif fault == "outside":
            plan = replace(plan, anchors=(replace(plan.anchors[0], anchor_time=TimePoint(1, 0, "tt")),) + plan.anchors[1:])
        elif fault == "scale":
            plan = replace(plan, anchors=(replace(plan.anchors[0], anchor_time=replace(EPOCH, scale="tdb")),) + plan.anchors[1:])
        elif fault == "method_resource":
            resource = replace(self.model.dependencies[0], sha256="0" * 64)
            plan = replace(plan, method=replace(plan.method, dependencies=(resource,)))
        plan = replace(plan, identity=reuse_plan_identity(plan))
        return replace(plan, identity="0" * 64) if fault == "identity" else plan
