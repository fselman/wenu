"""Object-independent nominal space-motion directions and angular certificates.

Adapters qualify source astrometry, construct immutable SI rows and bind SDK
identities/evidence. This engine knows no catalogue, stellar/object family,
observer, projection or renderer. Its initial model requires complete PV inputs.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from math import fsum, isfinite, sqrt
from sys import float_info
from wenu_kernel.errors import (AccuracyUnavailable, ClosedSession, InvalidQuery,
                                ResourceMismatch, UnsupportedCapability)
from wenu_kernel.records import (
    CapabilityDecision, CatalogueSnapshot, CartesianState, DirectionState, ModelAdmission,
    ModelRef, ObjectKey, ProviderDescriptor, StateBatch, StateQuery, TimePoint,
    TimeSpan, UncertaintyEvidence,
)
from wenu_kernel.reuse import direction_anchor_identity, make_certificate

def _seconds(time, epoch):
    if time.scale != epoch.scale:
        raise InvalidQuery('Explicit time conversion is required.')
    return fsum((time.jd1 - epoch.jd1, time.jd2, -epoch.jd2)) * 86400.0


# Algorithm contracts, not catalogue data. The bound is verified for each vector
# against exact arithmetic on the admitted binary64 SI solution and split time.
_NUMERICAL_RAD = 2.0**-40


def _day(time):
    return Fraction(time.jd1) + Fraction(time.jd2)


def _exact_position(row, time):
    if time.scale != row.source_epoch.scale:
        raise InvalidQuery('Explicit time conversion is required.')
    dt = (_day(time) - _day(row.source_epoch)) * 86400
    return tuple(Fraction(p) + dt*Fraction(v)
                 for p, v in zip(row.position_m, row.velocity_m_s))


def _inside_cone(vector, position, angular_rad):
    """Exact sufficient test for angular separation <= angular_rad <= 1 rad.

    Positive dot keeps the angle acute. 4*sin(angle)^2 <= tolerance^2
    implies angle <= 2*sin(angle) <= tolerance. No libm inverse-trig
    rounding enters admission. A circular cone of half-angle < pi/2 is convex;
    checking both endpoints bounds every position on a rectilinear segment.
    """
    w = tuple(Fraction(x) for x in vector)
    dot = sum(a*b for a, b in zip(w, position))
    cross = (w[1]*position[2]-w[2]*position[1],
             w[2]*position[0]-w[0]*position[2],
             w[0]*position[1]-w[1]*position[0])
    return (dot > 0 and 4*sum(x*x for x in cross)
            <= Fraction(angular_rad)**2*sum(x*x for x in w)*sum(x*x for x in position))


def _midpoint(first, second):
    day = (_day(first) + _day(second))/2
    whole = (day + Fraction(1, 2)).numerator // (day + Fraction(1, 2)).denominator
    fraction = float(day - whole)
    if fraction >= .5:
        whole += 1
        fraction -= 1
    return TimePoint(whole, fraction, first.scale)


@dataclass(frozen=True, slots=True)
class SpaceMotionRow:
    identifier: str
    source_epoch: TimePoint | None
    position_m: tuple[float, float, float] | None
    velocity_m_s: tuple[float, float, float] | None
    unavailable_reason: str | None

    def __post_init__(self):
        if not isinstance(self.identifier, str) or not self.identifier.strip() or self.identifier.strip() != self.identifier:
            raise ValueError('Invalid astrometric identity.')
        if self.source_epoch is not None and type(self.source_epoch) is not TimePoint:
            raise ValueError('Invalid source epoch.')
        if self.unavailable_reason is not None:
            if not isinstance(self.unavailable_reason, str) or not self.unavailable_reason:
                raise ValueError('Unavailable rows require a reason.')
            if self.position_m is not None or self.velocity_m_s is not None:
                raise ValueError('Unavailable rows cannot advertise a space-motion solution.')
        else:
            if self.source_epoch is None:
                raise ValueError('Space motion requires a source epoch.')
            for name in ('position_m', 'velocity_m_s'):
                values = tuple(map(float, getattr(self, name)))
                if len(values) != 3 or not all(isfinite(v) for v in values):
                    raise ValueError('Space-motion vectors must be finite triples.')
                object.__setattr__(self, name, values)




def validate_space_motion_domain(row, coverage):
    """Reject scale/epoch gaps and a rectilinear domain crossing the origin."""
    if type(coverage) is not TimeSpan:
        raise ValueError('An explicit finite nominal model domain is required.')
    if row.unavailable_reason is not None:
        return
    if row.source_epoch.scale != coverage.start.scale or not coverage.contains(row.source_epoch):
        raise ValueError('Source epoch is outside the explicit model domain/scale.')
    distance = sqrt(fsum(p*p for p in row.position_m))
    speed2 = fsum(v*v for v in row.velocity_m_s)
    closest = 0.
    if speed2:
        closest = -fsum(p*v for p,v in zip(row.position_m,row.velocity_m_s))/speed2
        lower, upper = (_seconds(t,row.source_epoch) for t in (coverage.start,coverage.stop))
        closest = min(max(closest,lower),upper)
    radius = sqrt(fsum((p+closest*v)**2 for p,v in zip(row.position_m,row.velocity_m_s)))
    if not isfinite(radius) or radius <= 64*float_info.epsilon*distance:
        raise ValueError('Nominal model domain intersects a singular centre trajectory.')


class RectilinearAstrometricProvider:
    """One engine for qualified SI solutions of any object type.

    Semantic types are carried by supplied ObjectRecords and never dispatch
    numerical work. The adapter owns all source/model identity and error meaning.
    Direction or Cartesian output uses the same complete-PV nominal model.
    """
    def __init__(self, rows, *, descriptor, catalogue, admission, evidence, reuse_method=None,
                 velocity_evidence=None):
        pairs = tuple(rows)
        if (type(descriptor) is not ProviderDescriptor or type(catalogue) is not CatalogueSnapshot
                or type(admission) is not ModelAdmission or type(evidence) is not UncertaintyEvidence
                or admission not in descriptor.admissions
                or admission.catalogue != catalogue.reference
                or catalogue.reference not in descriptor.catalogues
                or (admission.reference.representation,admission.reference.units) not in (
                    ('direction','rad'),('cartesian','m,m/s'))
                or type(admission.coverage) is not TimeSpan):
            raise ValueError('Inconsistent astrometric provider bindings.')
        if any(type(key) is not ObjectKey or type(row) is not SpaceMotionRow for key,row in pairs):
            raise ValueError('Astrometric rows require typed immutable keys and SI solutions.')
        lookup = dict(pairs)
        direction = admission.reference.representation == 'direction'
        capabilities = ({'epoch_direction','batch_evaluation','direction_reuse_bound'} if direction
                        else {'cartesian_state','batch_evaluation'})
        if (len(lookup) != len(pairs) or set(lookup) != {row.key for row in catalogue.objects}
                or set(admission.objects) != {key for key,row in pairs if row.unavailable_reason is None}
                or set(admission.capabilities) != capabilities):
            raise ValueError('Inconsistent astrometric objects or capabilities.')
        if direction:
            if (type(reuse_method) is not ModelRef or velocity_evidence is not None
                    or evidence.numerical.status != 'bounded' or evidence.numerical.value != _NUMERICAL_RAD
                    or evidence.numerical.units != 'rad' or evidence.numerical.meaning != 'angular_separation'):
                raise ValueError('Inconsistent direction numerical evidence.')
        else:
            if reuse_method is not None or type(velocity_evidence) is not UncertaintyEvidence:
                raise ValueError('Cartesian admission needs separate velocity evidence and no direction reuse.')
            for supplied,unit in ((evidence,'m'),(velocity_evidence,'m/s')):
                if any(channel.status != 'not_evaluated' or channel.units != unit
                       for channel in (supplied.measurement,supplied.physical_model,supplied.numerical)):
                    raise ValueError('Cartesian error bounds are not yet admitted; retain unknown SI channels.')
                if supplied.numerical.meaning != 'euclidean_norm':
                    raise ValueError('Cartesian numerical metric must be euclidean_norm.')
        for row in lookup.values():
            validate_space_motion_domain(row, admission.coverage)
        self._lookup = lookup
        self._descriptor, self._catalogue, self._admission = descriptor, catalogue, admission
        self._evidence, self._reuse_method = evidence, reuse_method
        self._velocity_evidence = velocity_evidence
        self._closed = False

    def _check(self):
        if self._closed:
            raise ClosedSession('Astrometric provider is closed.')

    def describe(self):
        self._check()
        return self._descriptor

    def catalogue(self, reference):
        self._check()
        if reference != self._catalogue.reference:
            raise ResourceMismatch('Astrometric catalogue binding mismatch.')
        return self._catalogue

    def supports(self, query):
        self._check()
        if type(query) is not StateQuery:
            return CapabilityDecision(False, 'A typed state query is required.')
        a = self._admission
        if (query.catalogue, query.model, query.reference) != (a.catalogue, a.model, a.reference):
            return CapabilityDecision(False, 'Astrometric model/reference binding mismatch.')
        for key in query.objects:
            row = self._lookup.get(key)
            if row is None or row.unavailable_reason:
                return CapabilityDecision(False, key.value + ': ' + ('unknown object' if row is None else row.unavailable_reason))
        if any(t.scale != a.coverage.start.scale for t in query.times):
            return CapabilityDecision(False, 'Explicit time conversion is required.')
        if any(not a.coverage.contains(t) for t in query.times):
            return CapabilityDecision(False, 'Outside admitted nominal model domain.')
        if a.reference.representation == 'cartesian':
            if (query.evaluation_policy != 'full_model' or query.coverage is not None
                    or query.accuracy.metric != 'euclidean_norm'
                    or any(value is not None for value in (query.accuracy.angular_rad,
                        query.accuracy.position_m,query.accuracy.velocity_m_s))):
                return CapabilityDecision(False, 'Cartesian full-model output only; no bounds or temporal reuse.')
            return CapabilityDecision(True, 'Nominal SI position and velocity; unknown physical/numerical error.')
        if (query.accuracy.position_m is not None or query.accuracy.velocity_m_s is not None
                or query.accuracy.metric != 'angular_separation'
                or query.evaluation_policy != 'full_model'
                or query.require_velocity or query.coverage is not None):
            return CapabilityDecision(False, 'Direction full-model evaluation only; kernel owns temporal reuse.')
        if query.accuracy.angular_rad is not None and query.accuracy.angular_rad < _NUMERICAL_RAD:
            return CapabilityDecision(False, 'Requested tolerance is below the verified numerical floor.')
        return CapabilityDecision(True, 'Nominal centre propagation; unknown physical accuracy.')

    def evaluate(self, query):
        decision = self.supports(query)
        if not decision.supported:
            raise UnsupportedCapability(decision.reason)
        states = []
        for time in query.times:
            for key in query.objects:
                row = self._lookup[key]
                if query.reference.representation == 'cartesian':
                    # Exact binary64 SI model and split-JD elapsed time; round only
                    # the final coordinates. This is not source/physical accuracy.
                    position = tuple(float(value) for value in _exact_position(row,time))
                    states.append(CartesianState(key,time,row.source_epoch,time,
                        query.reference,position,row.velocity_m_s,self._evidence,self._velocity_evidence))
                    continue
                dt = _seconds(time, row.source_epoch)
                position = tuple(p + dt*v for p, v in zip(row.position_m, row.velocity_m_s))
                norm = sqrt(fsum(float(x)*float(x) for x in position))
                if not isfinite(norm) or norm == 0:
                    raise ValueError('Undefined nominal astrometric direction.')
                vector = tuple(float(x)/norm for x in position)
                if not _inside_cone(vector, _exact_position(row, time), _NUMERICAL_RAD):
                    raise AccuracyUnavailable('Computed direction fails its exact numerical bound.')
                states.append(DirectionState(key, time, row.source_epoch, time,
                    query.reference, vector, self._evidence))
        return StateBatch(query, tuple(states))

    def certify(self, query, anchor):
        self._check()
        if self._admission.reference.representation == 'cartesian':
            raise UnsupportedCapability('Cartesian temporal certificates are not admitted.')
        if type(query) is not StateQuery or query.evaluation_policy != 'bounded_reuse':
            raise UnsupportedCapability('Certificate requires an explicit bounded-reuse query.')
        tolerance = query.accuracy.angular_rad
        if tolerance is None or tolerance < _NUMERICAL_RAD:
            raise AccuracyUnavailable('Requested tolerance is below the verified numerical floor.')
        if len(query.objects) != 1 or len(query.times) != 1:
            raise UnsupportedCapability('Certificates require one original object/time anchor.')
        probe = replace(query, evaluation_policy='full_model', coverage=None)
        if not self.supports(probe).supported:
            raise UnsupportedCapability('Unsupported certificate query binding or capability.')
        identity = direction_anchor_identity(anchor)
        if (replace(anchor.query, times=query.times, accuracy=query.accuracy) != probe
                or anchor.states[0].reference != query.reference):
            raise ResourceMismatch('Certificate anchor/query binding mismatch.')
        state = anchor.states[0]
        row = self._lookup[query.objects[0]]
        if (not self._admission.coverage.contains(state.anchor_time)
                or state.source_epoch != row.source_epoch or state.evidence != self._evidence
                or not _inside_cone(state.vector, _exact_position(row, state.anchor_time), _NUMERICAL_RAD)):
            raise AccuracyUnavailable('Anchor does not satisfy this model numerical bound.')
        # The endpoints are checked against the actual stored vector, so the
        # total bound includes its original approximation error, not just drift.
        bound = min(tolerance, 1.0)
        def admitted(time):
            return _inside_cone(state.vector, _exact_position(row, time), bound)
        if query.coverage is not None:
            points = (query.coverage.start, query.coverage.stop, state.anchor_time)
            start, stop = min(points, key=_day), max(points, key=_day)
            if (not self._admission.coverage.contains(start)
                    or not self._admission.coverage.contains(stop)
                    or not admitted(start) or not admitted(stop)):
                raise AccuracyUnavailable('Requested interval exceeds the admitted angular cone/domain.')
        else:
            def endpoint(candidate):
                # Halving sacrifices maximum interval size, never the bound.
                while not admitted(candidate):
                    closer = _midpoint(candidate, state.anchor_time)
                    if closer == candidate or closer == state.anchor_time:
                        return state.anchor_time
                    candidate = closer
                return candidate
            start = endpoint(self._admission.coverage.start)
            stop = endpoint(self._admission.coverage.stop)
        return make_certificate(catalogue=query.catalogue, model=query.model,
            anchor_identity=identity, objects=query.objects, reference=query.reference,
            validity=TimeSpan(start, stop), metric='angular_separation',
            maximum_error=bound, method=self._reuse_method)

    def close(self):
        self._closed = True
