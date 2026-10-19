"""Offline admission and nominal rectilinear open-cluster state provider.

Source lookup remains a separate model. This owner transports a density-mode
centre using its core mean motion; it does not reconstruct a historical cluster
or certify physical accuracy. No acquisition, observer or graphics dependency.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum, isfinite, sqrt
from pathlib import Path

import numpy as np
import astropy
from astropy import units as u
from astropy.coordinates import (CartesianDifferential, CartesianRepresentation,
                                 SphericalCosLatDifferential, SphericalRepresentation)
from astropy.table import Table
from astropy.time import Time

from wenu_kernel.errors import (AccuracyUnavailable, ClosedSession, InvalidQuery,
                                ResourceMismatch, UnsupportedCapability)
from wenu_kernel.records import (
    AccuracyRequest, CapabilityDecision, CatalogueRef, CatalogueSnapshot,
    DirectionState, ExternalId, ModelAdmission, ModelRef, ObjectKey, ObjectRecord,
    ProviderDescriptor, ProviderKey, ReferenceSpec, ResourceRef, StateBatch,
    StateQuery, TimePoint, TimeSpan, UncertaintyChannel, UncertaintyEvidence,
)
from wenu_kernel.reuse import direction_anchor_identity, make_certificate


def _canonical_digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()


def _seconds(time, epoch):
    if time.scale != epoch.scale:
        raise InvalidQuery('Explicit time conversion is required.')
    return fsum((time.jd1 - epoch.jd1, time.jd2, -epoch.jd2)) * u.day.to(u.s)


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
class ClusterMotionRow:
    identifier: str
    source_epoch: TimePoint | None
    position_m: tuple[float, float, float] | None
    velocity_m_s: tuple[float, float, float] | None
    unavailable_reason: str | None

    def __post_init__(self):
        if not isinstance(self.identifier, str) or not self.identifier.strip() or self.identifier.strip() != self.identifier:
            raise ValueError('Invalid cluster identity.')
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


@dataclass(frozen=True, slots=True)
class ClusterMotionCatalogue:
    """Copied solutions and source evidence; no caller-owned mutable buffers."""
    rows: tuple[ClusterMotionRow, ...]
    source_ecsv: str
    metadata_json: str
    coverage: TimeSpan

    def __post_init__(self):
        rows = tuple(self.rows)
        if (any(type(row) is not ClusterMotionRow for row in rows)
                or len({row.identifier for row in rows}) != len(rows)
                or type(self.coverage) is not TimeSpan
                or not isinstance(self.source_ecsv, str) or not isinstance(self.metadata_json, str)):
            raise ValueError('Invalid immutable cluster motion catalogue.')
        object.__setattr__(self, 'rows', rows)

    def source_table(self):
        return Table.read(self.source_ecsv.splitlines(), format='ascii.ecsv')

    def to_record(self):
        return json.loads(self.metadata_json)


def load_cluster_motion(companion_path, metadata_path, *, coverage):
    """Admit explicit source/qualification files; never change an active layer."""
    data = Path(companion_path).read_bytes()
    metadata_bytes = Path(metadata_path).read_bytes()
    metadata = json.loads(metadata_bytes)
    source_digest = sha256(data).hexdigest()
    if source_digest != metadata['companion_sha256']:
        raise ValueError('Cluster astrometry bytes do not match qualification.')
    table = Table.read(data.decode('utf-8').splitlines(), format='ascii.ecsv')
    admitted = admit_cluster_motion(table, metadata, coverage=coverage)
    record = admitted.to_record()
    record['input_companion_sha256'] = source_digest
    record['input_metadata_sha256'] = sha256(metadata_bytes).hexdigest()
    return ClusterMotionCatalogue(admitted.rows, data.decode('utf-8'),
        json.dumps(record, sort_keys=True, allow_nan=False), coverage)


def admit_cluster_motion(table, metadata, *, coverage):
    """Validate metadata/units before publishing immutable nominal solutions.

    Constructed inputs use the same schema but must declare their provenance.
    Missing rows stay in the catalogue with explicit reasons, never zero motion.
    """
    if type(coverage) is not TimeSpan:
        raise ValueError('An explicit finite nominal model domain is required.')
    metadata = json.loads(json.dumps(metadata, allow_nan=False))
    required = {'schema', 'astrometry', 'namespace', 'edition', 'provenance', 'source_name',
                'selected_catalogue_sha256', 'source_spec_digest', 'policies', 'columns'}
    if (type(metadata) is not dict or not required.issubset(metadata)
            or metadata.get('schema') != 'wenu-cluster-motion-admission/1'):
        raise ValueError('Unsupported cluster motion metadata.')
    facts = metadata['astrometry']
    if (type(facts) is not dict or not {'frame', 'origin', 'ra_motion_convention',
                                      'epoch_scale', 'epoch_label'}.issubset(facts)
            or not isinstance(facts['epoch_label'], str) or not facts['epoch_label'].strip()):
        raise ValueError('Missing explicit cluster astrometry declarations.')
    if (facts['frame'] != 'icrs' or facts['origin'] != 'solar-system-barycenter'
            or facts['ra_motion_convention'] != 'mu_alpha_star'
            or facts['epoch_scale'] != 'tcb'):
        raise ValueError('Unsupported cluster astrometry convention.')
    for field in ('namespace', 'edition', 'provenance', 'source_name'):
        if not isinstance(metadata.get(field), str) or not metadata[field].strip():
            raise ValueError('Missing cluster source identity/provenance.')
    if table.meta.get('selected_catalogue_sha256') != metadata['selected_catalogue_sha256']:
        raise ValueError('Cluster selection identity does not match qualification.')
    if _canonical_digest(table.meta.get('astrometry_source')) != metadata['source_spec_digest']:
        raise ValueError('Cluster source facts do not match qualification.')
    if metadata['policies'] != {
            'distance': 'declared-source-estimator', 'radial_velocity': 'spectroscopic-proxy',
            'centre': 'density-mode-transported-by-core-mean',
            'physical_accuracy': 'not-evaluated', 'light_time': 'no-additional-correction'}:
        raise ValueError('Unsupported cluster motion model policy.')
    epoch = Time(facts['epoch_label'], scale=facts['epoch_scale'])
    # Astropy permits +0.5; the SDK canonical split uses [-0.5, +0.5).
    carry = int(epoch.jd2 >= 0.5)
    epoch = TimePoint(int(epoch.jd1) + carry, float(epoch.jd2) - carry, epoch.scale)
    if not coverage.contains(epoch):
        raise ValueError('Nominal model domain must include its source epoch.')
    names = metadata['columns']
    roles = {'identifier', 'source', 'ra', 'dec', 'distance', 'pm_ra', 'pm_dec', 'rv'}
    if (type(names) is not dict or set(names) != roles
            or any(not isinstance(name, str) or not name for name in names.values())
            or len(set(names.values())) != len(names)
            or not set(names.values()).issubset(table.colnames)):
        raise ValueError('Required cluster astrometry columns are missing.')
    dimensions = dict(ra=u.rad, dec=u.rad, distance=u.m,
                      pm_ra=u.rad/u.s, pm_dec=u.rad/u.s, rv=u.m/u.s)
    for role, unit in dimensions.items():
        declared = table[names[role]].unit
        if declared is None or not declared.is_equivalent(unit):
            raise ValueError('Missing or incompatible cluster astrometry unit: ' + role)
    copied = table.copy(copy_data=True)
    identifiers = list(map(str, copied[names['identifier']]))
    if (any(np.ma.is_masked(x) for x in copied[names['identifier']])
            or any(not x or x.strip() != x for x in identifiers)
            or len(set(identifiers)) != len(identifiers)):
        raise ValueError('Cluster identifiers must be present and unique.')
    rows = []
    for row, identifier in zip(copied, identifiers):
        if np.ma.is_masked(row[names['source']]) or row[names['source']] != metadata['source_name']:
            rows.append(ClusterMotionRow(identifier, None, None, None, 'unqualified centre epoch/source'))
            continue
        values = {}
        for role, unit in dimensions.items():
            value = row[names[role]]
            if not np.ma.is_masked(value):
                value = (float(value) * copied[names[role]].unit).to_value(unit)
                if not isfinite(value):
                    raise ValueError('Non-finite unmasked cluster astrometry: ' + role)
                values[role] = value
        if ('dec' in values and not -np.pi/2 <= values['dec'] <= np.pi/2
                or 'distance' in values and values['distance'] <= 0):
            raise ValueError('Invalid cluster latitude/distance.')
        if len(values) != len(dimensions):
            missing = ','.join(sorted(set(dimensions) - values.keys()))
            rows.append(ClusterMotionRow(identifier, epoch, None, None, 'missing ' + missing))
            continue
        # Astropy owns the spherical differential, including pole-safe mu*cosdec.
        spherical = SphericalRepresentation(values['ra']*u.rad, values['dec']*u.rad,
            values['distance']*u.m, differentials=SphericalCosLatDifferential(
                values['pm_ra']*u.rad/u.s, values['pm_dec']*u.rad/u.s, values['rv']*u.m/u.s))
        cartesian = spherical.represent_as(CartesianRepresentation, CartesianDifferential)
        position = tuple(map(float, cartesian.xyz.to_value(u.m)))
        velocity = tuple(map(float, cartesian.differentials['s'].d_xyz.to_value(u.m/u.s)))
        # Refuse a domain passing numerically through the observer origin.
        speed2 = fsum(x*x for x in velocity)
        if speed2:
            closest = -fsum(p*v for p, v in zip(position, velocity))/speed2
            lower, upper = (_seconds(t, epoch) for t in (coverage.start, coverage.stop))
            closest = min(max(closest, lower), upper)
            radius = sqrt(fsum((p+closest*v)**2 for p, v in zip(position, velocity)))
            if radius <= 64*np.finfo(float).eps*values['distance']:
                raise ValueError('Nominal model domain intersects a singular centre trajectory.')
        rows.append(ClusterMotionRow(identifier, epoch, position, velocity, None))
    from io import StringIO
    stream = StringIO()
    copied.write(stream, format='ascii.ecsv')
    record = dict(source_metadata=metadata,
                  derived_table_sha256=sha256(stream.getvalue().encode()).hexdigest(),
                  unavailable={row.identifier: row.unavailable_reason for row in rows if row.unavailable_reason})
    return ClusterMotionCatalogue(tuple(rows), stream.getvalue(),
        json.dumps(record, sort_keys=True, allow_nan=False), coverage)


class ClusterMotionProvider:
    """Nominal model with provider-owned angular certificates; physical error unknown."""
    def __init__(self, catalogue):
        if type(catalogue) is not ClusterMotionCatalogue:
            raise ValueError('An admitted immutable cluster catalogue is required.')
        self._catalogue_data = catalogue
        self._rows = {row.identifier: row for row in catalogue.rows}
        self._closed = False
        meta = catalogue.to_record()['source_metadata']
        key = ProviderKey('wenu.cluster-motion', '1')
        coverage = catalogue.coverage
        identity = _canonical_digest((catalogue.metadata_json, tuple(
            (x.identifier, x.position_m, x.velocity_m_s) for x in catalogue.rows),
            (coverage.start.jd1, coverage.start.jd2, coverage.stop.jd1, coverage.stop.jd2, coverage.start.scale)))
        resource = ResourceRef('qualified-cluster-motion', meta['edition'], identity,
            coverage, 'explicit nominal model domain; no certified physical validity', (meta['provenance'],))
        keys = tuple(ObjectKey(meta['namespace'] + ':' + row.identifier) for row in catalogue.rows)
        self._lookup = dict(zip(keys, catalogue.rows))
        reference = CatalogueRef(key, (resource,), _canonical_digest([x.value for x in keys]))
        model = ModelRef('cluster-centre-rectilinear', '2', _canonical_digest((identity, meta['policies'],
            'Astropy spherical differential; SI rectilinear update; exact-rational cone/1',
            _NUMERICAL_RAD, astropy.__version__, np.__version__)), (resource,))
        facts = meta['astrometry']
        frame = ReferenceSpec(facts['frame'], facts['origin'], 'nominal-astrometric', 'direction', 'rad',
            'density-mode centre transported by core mean motion; no additional light-time correction; unknown physical error')
        capabilities = ('epoch_direction', 'batch_evaluation', 'direction_reuse_bound')
        records = tuple(ObjectRecord(k, (ExternalId(meta['namespace'], meta['edition'], row.identifier),),
            'open-cluster', () if row.source_epoch is None else (row.source_epoch,),
            ('unavailable_motion',) if row.unavailable_reason else capabilities, (meta['provenance'],))
            for k, row in zip(keys, catalogue.rows))
        self._catalogue = CatalogueSnapshot(reference, records)
        self._admission = ModelAdmission(reference, model, frame,
            tuple(k for k, row in zip(keys, catalogue.rows) if row.unavailable_reason is None), capabilities, coverage)
        self._descriptor = ProviderDescriptor(key, (reference,), (self._admission,),
            'offline nominal propagation and interactive certified reuse; no default chart adoption')
        self._evidence = UncertaintyEvidence(*(
            UncertaintyChannel('not_evaluated', None, 'rad', meaning)
            for meaning in ('cluster-centre measurement', 'centre/rectilinear model error')),
            UncertaintyChannel('bounded', _NUMERICAL_RAD, 'rad', 'angular_separation'))
        self._reuse_method = ModelRef('cluster-rectilinear-cone', '1',
            _canonical_digest(('exact-binary64-rational-cone/1', _NUMERICAL_RAD)), (resource,))

    def _check(self):
        if self._closed:
            raise ClosedSession('Cluster motion provider is closed.')

    def describe(self):
        self._check()
        return self._descriptor

    def catalogue(self, reference):
        self._check()
        if reference != self._catalogue.reference:
            raise ResourceMismatch('Cluster catalogue binding mismatch.')
        return self._catalogue

    def supports(self, query):
        self._check()
        if type(query) is not StateQuery:
            return CapabilityDecision(False, 'A typed state query is required.')
        a = self._admission
        if (query.catalogue, query.model, query.reference) != (a.catalogue, a.model, a.reference):
            return CapabilityDecision(False, 'Cluster model/reference binding mismatch.')
        for key in query.objects:
            row = self._lookup.get(key)
            if row is None or row.unavailable_reason:
                return CapabilityDecision(False, key.value + ': ' + ('unknown object' if row is None else row.unavailable_reason))
        if any(t.scale != a.coverage.start.scale for t in query.times):
            return CapabilityDecision(False, 'Explicit time conversion is required.')
        if any(not a.coverage.contains(t) for t in query.times):
            return CapabilityDecision(False, 'Outside admitted nominal model domain.')
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
                dt = _seconds(time, row.source_epoch)
                position = np.asarray(row.position_m) + dt*np.asarray(row.velocity_m_s)
                norm = sqrt(fsum(float(x)*float(x) for x in position))
                if not isfinite(norm) or norm == 0:
                    raise ValueError('Undefined nominal cluster direction.')
                vector = tuple(float(x)/norm for x in position)
                if not _inside_cone(vector, _exact_position(row, time), _NUMERICAL_RAD):
                    raise AccuracyUnavailable('Computed direction fails its exact numerical bound.')
                states.append(DirectionState(key, time, row.source_epoch, time,
                    query.reference, vector, self._evidence))
        return StateBatch(query, tuple(states))

    def certify(self, query, anchor):
        self._check()
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
