"""Stellar adapters for native lookup and explicit full/angular nominal motion.

The original native adapter remains a lookup; the separate explicit nominal
admission delegates to the existing object-independent SI motion engine.
A time-independent lookup is not a zero-proper-motion model. This adapter's
native-catalogue reference never advertises epoch_direction, physical accuracy,
temporal reuse, distance or velocity. Coverage describes lookup availability,
not validity of a requested-epoch astrometric prediction.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
from hashlib import sha256
from math import cos, sin, pi, isfinite

from wenu_kernel.errors import InvalidQuery, UnsupportedCapability
from wenu_kernel.records import ReferenceSpec, TimePoint, UnboundedCoverage
from wenu.catalogue_state import (
    CatalogueDirectionProvider, catalogue_direction_angles as native_stellar_angles,
    catalogue_direction_states,
)

from wenu.astrometric_state import (
    SpaceMotionRow, AngularMotionRow, RectilinearAstrometricProvider, validate_space_motion_domain,
    _NUMERICAL_RAD,
)
from wenu.stellar_enrichment import StellarEnrichmentSnapshot, encode, decode
from wenu_kernel.records import (
    CatalogueRef, CatalogueSnapshot, ExternalId, ModelAdmission, ModelRef,
    ObjectKey, ObjectRecord, ProviderDescriptor, ProviderKey, ResourceRef,
    TimeSpan, UncertaintyChannel, UncertaintyEvidence,
)

NATIVE_STELLAR_REFERENCE = ReferenceSpec(
    "icrs", "solar-system-barycenter", "native-catalogue", "direction", "rad",
    "unpropagated source directions; no requested-epoch astrometry",
)


class LegacyNativeStellarProvider(CatalogueDirectionProvider):
    """Compatibility facade for the admitted source-epoch stellar lookup."""

    def __init__(self, rows, *, namespace, source_epoch, provenance,
                 catalogue_edition="materialized-input/1", reference=NATIVE_STELLAR_REFERENCE):
        if type(source_epoch) is not TimePoint:
            raise InvalidQuery("an explicit source epoch is required")
        if reference != NATIVE_STELLAR_REFERENCE:
            raise UnsupportedCapability("Only admitted native ICRS reference semantics are supported.")
        super().__init__(rows, namespace=namespace, source_epoch=source_epoch,
            provenance=provenance, catalogue_edition=catalogue_edition,
            reference=reference, capability="native_direction", semantic_type="star",
            provider_id="wenu.legacy-native-stars:" + namespace,
            resource_id="derived-native-stellar-table:" + namespace,
            model_id="unpropagated-native-stars", coverage=UnboundedCoverage(source_epoch.scale))


def native_stellar_states(rows, *, namespace, source_epoch, provenance, catalogue_edition="materialized-input/1",
                          reference=NATIVE_STELLAR_REFERENCE):
    """Query the real kernel at the source epoch; close all owned scope state.

    Empty tables require no query. No global registry/session survives this
    call; published immutable rows remain valid after cleanup.
    """
    provider = LegacyNativeStellarProvider(rows, namespace=namespace,
                                         source_epoch=source_epoch, provenance=provenance,
                                         catalogue_edition=catalogue_edition, reference=reference)
    return catalogue_direction_states(provider, source_epoch)





def _stellar_epoch(jyear, scale):
    """Julian-year definition, not time-scale conversion or a source default."""
    day = Fraction(2451545) + (Fraction(jyear) - 2000) * Fraction('365.25')
    whole = (day + Fraction(1, 2)).__floor__()
    small = float(day - whole)
    if small == .5:
        whole, small = whole + 1, -.5
    return TimePoint(whole, small, scale)


def _stellar_digest(value):
    return sha256(encode(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class StellarMotionCatalogue:
    """Explicit nominal model derived from an unchanged immutable source snapshot.

    All original objects remain present. Missing inputs do not acquire a model;
    Hip2 and original-1997 fallbacks remain source records for later admission.
    The source snapshot is retained verbatim, including uncertainties and flags.
    """
    source: StellarEnrichmentSnapshot
    coverage: TimeSpan
    distance_policy: str
    radial_velocity_policy: str
    motion_policy: str = 'full-input-rectilinear'
    rows: tuple[SpaceMotionRow | AngularMotionRow, ...] = field(init=False)
    metadata_json: bytes = field(init=False)

    def __post_init__(self):
        if type(self.source) is not StellarEnrichmentSnapshot:
            raise ValueError('A validated immutable stellar source snapshot is required.')
        if type(self.coverage) is not TimeSpan or self.coverage.start.scale != 'tcb':
            raise ValueError('An explicit finite TCB nominal model domain is required.')
        angular = self.motion_policy == 'proper-motion-angular'
        if self.motion_policy not in ('full-input-rectilinear', 'proper-motion-angular'):
            raise ValueError('Unsupported stellar motion policy.')
        expected_policies = ('not-used', 'not-used') if angular else (
            'positive-parallax-reciprocal', 'spectroscopic-proxy')
        if (self.distance_policy, self.radial_velocity_policy) != expected_policies:
            raise ValueError('Unsupported explicit stellar distance/radial-velocity policy.')
        row_type = AngularMotionRow if angular else SpaceMotionRow
        meta = self.source.metadata
        facts = meta['gaia_reference']
        # These are supported conventions; their actual values are read from the
        # validated source metadata, never inferred from a filename or HIP name.
        if (facts['frame'], facts['origin'], facts['epoch_scale'],
                facts['right_ascension_motion']) != (
                'icrs', 'solar-system-barycenter', 'tcb', 'mu_alpha*cos(delta)'):
            raise ValueError('Unqualified Gaia astrometric conventions.')
        sources = {r['source_id']: r for r in self.source.records('gaia_sources_v1.jsonl')}
        rows = []
        for star in self.source.records():
            hip = star['identity']['identifier']
            link = star['published_association']
            if link is None:
                rows.append(row_type(hip, None, None, None, 'no_published_gaia_association'))
                continue
            src = sources[link['source_id']]
            epoch = _stellar_epoch(src['ref_epoch'], facts['epoch_scale'])
            fields = (('ra', 'dec', 'pmra', 'pmdec') if angular else
                      ('ra', 'dec', 'parallax', 'pmra', 'pmdec', 'radial_velocity'))
            for name in fields:
                value = src.get(name)
                if value is not None and (type(value) not in (int, float) or not isfinite(value)):
                    raise ValueError('Invalid Gaia model parameter: ' + name)
            reason = None
            if src.get('astrometric_params_solved') not in (31, 95):
                reason = ('gaia_position_only' if src.get('astrometric_params_solved') == 3
                          else 'unsupported_gaia_solution')
            else:
                missing = [name for name in fields if src.get(name) is None]
                if missing:
                    reason = 'missing_gaia_' + ','.join(missing)
                elif not angular and src['parallax'] <= 0:
                    reason = 'nonpositive_gaia_parallax'
            if reason:
                rows.append(row_type(hip, epoch, None, None, reason))
                continue
            # Explicit source-unit admission. A spectroscopic RV is retained as
            # a nominal kinematic proxy, without binary/systemic corrections.
            expected = {'ra':'deg', 'dec':'deg', 'parallax':'mas',
                        'pmra':'mas / yr', 'pmdec':'mas / yr', 'radial_velocity':'km / s'}
            if angular:
                expected = {k: v for k, v in expected.items() if k in fields}
            if any(meta['gaia_column_units'].get(k) != v for k, v in expected.items()):
                raise ValueError('Unsupported Gaia angular-model units.' if angular else 'Unsupported Gaia full-model units.')
            # IAU exact au in metres; parsec = 648000/pi au; Julian year =
            # 365.25 SI days. These are unit definitions, not catalogue facts.
            mas_to_rad = pi / (180 * 3600 * 1000)
            if not angular:
                distance = 149597870700.0 / (src['parallax'] * mas_to_rad)
            ra, dec = src['ra'] * pi/180, src['dec'] * pi/180
            u = (cos(dec)*cos(ra), cos(dec)*sin(ra), sin(dec))
            east, north = (-sin(ra), cos(ra), 0.), (-sin(dec)*cos(ra), -sin(dec)*sin(ra), cos(dec))
            pma, pmd = (src[k] * mas_to_rad / (365.25 * 86400) for k in ('pmra', 'pmdec'))
            if angular:
                derivative = tuple(pma*a + pmd*d for a, d in zip(east, north))
                row = AngularMotionRow(hip, epoch, u, derivative, None)
            else:
                rv = src['radial_velocity'] * 1000
                position = tuple(distance*x for x in u)
                velocity = tuple(rv*x + distance*(pma*a + pmd*d) for x, a, d in zip(u, east, north))
                row = SpaceMotionRow(hip, epoch, position, velocity, None)
            validate_space_motion_domain(row, self.coverage)
            rows.append(row)
        policies = {'distance': self.distance_policy, 'radial_velocity': self.radial_velocity_policy,
                    'parallax_zero_point': 'none', 'light_time': 'no-additional-correction',
                    'binaries': 'no-orbit-or-systemic-correction', 'physical_accuracy': 'not-evaluated',
                    'source_to_si_error': 'not-evaluated', 'covariance_propagation': 'not-implemented'}
        if angular:
            del policies['source_to_si_error']
            policies['source_to_angular_error'] = 'not-evaluated'
            policies.update(motion='normalized-tangent-angular', perspective='omitted',
                            observer_parallax='unavailable', distance='not-used', radial_velocity='not-used')
        record = {'schema':('wenu-stellar-angular-motion-admission/1' if angular else
                            'wenu-stellar-motion-admission/1'),
            'source_manifest_sha256':sha256(self.source.manifest).hexdigest(),
            'original_baseline':meta['baseline'], 'association_ledger_sha256':meta['association_ledger_sha256'],
            'gaia_reference':facts, 'policies':policies,
            'coverage': [[t.jd1, t.jd2, t.scale] for t in (self.coverage.start, self.coverage.stop)],
            ('angular_solutions_sha256' if angular else 'si_solutions_sha256'):_stellar_digest([(r.identifier,
                None if r.source_epoch is None else [r.source_epoch.jd1, r.source_epoch.jd2, r.source_epoch.scale],
                r.direction if angular else r.position_m,
                r.tangent_per_s if angular else r.velocity_m_s, r.unavailable_reason) for r in rows]),
            'counts':{'retained_objects':len(rows), ('angular_models' if angular else 'full_input_models'):sum(r.unavailable_reason is None for r in rows),
                'unavailable_by_reason':dict(Counter(r.unavailable_reason for r in rows if r.unavailable_reason))}}
        object.__setattr__(self, 'rows', tuple(rows))
        object.__setattr__(self, 'metadata_json', encode(record))

    def to_record(self):
        return decode(self.metadata_json)


def admit_stellar_motion(source, *, coverage, distance_policy, radial_velocity_policy):
    """Opt in to one explicit full-input nominal model; no active layer changes."""
    return StellarMotionCatalogue(source, coverage, distance_policy, radial_velocity_policy)


def admit_stellar_angular_motion(source, *, coverage):
    """Opt in to measured-PM angular extrapolation, without distance/RV inference.

    Missing-PM rows remain unavailable. The original source is never rewritten.
    A finite nominal TCB domain is required; physical model error stays unknown.
    """
    return StellarMotionCatalogue(source, coverage, 'not-used', 'not-used', 'proper-motion-angular')


class StellarMotionProvider(RectilinearAstrometricProvider):
    """Stellar source adapter to the shared, separately typed affine engine."""
    def __init__(self, catalogue, *, representation='direction'):
        if type(catalogue) is not StellarMotionCatalogue:
            raise ValueError('An admitted immutable stellar motion catalogue is required.')
        if representation not in ('direction', 'cartesian'):
            raise ValueError('Unsupported stellar motion representation.')
        cartesian = representation == 'cartesian'
        angular = catalogue.motion_policy == 'proper-motion-angular'
        if angular and cartesian:
            raise ValueError('Angular stellar motion has no admitted Cartesian distance or velocity.')
        meta = catalogue.source.metadata
        record = catalogue.to_record()
        identity = _stellar_digest(record)
        namespace, edition = meta['baseline']['catalogue'], meta['baseline']['edition']
        key = ProviderKey('wenu.stellar-motion' + ('.angular' if angular else '.cartesian' if cartesian else ''), '1')
        provenance = ('Immutable stellar source manifest SHA-256 ' + record['source_manifest_sha256'],
                      'Explicit nominal rectilinear model; source/physical/input-conversion errors unknown')
        if angular:
            provenance = (provenance[0], 'Explicit normalized tangent angular model; perspective/parallax omitted; unknown physical error')
        resource = ResourceRef('stellar-angular-motion-inputs' if angular else 'stellar-motion-inputs', '1', identity, catalogue.coverage,
            'caller-declared nominal domain; not certified physical validity', provenance)
        keys = tuple(ObjectKey(namespace + ':' + row.identifier) for row in catalogue.rows)
        reference = CatalogueRef(key, (resource,), _stellar_digest([k.value for k in keys]))
        model = ModelRef('stellar-rectilinear' + ('-cartesian' if cartesian else ''), '1',
            _stellar_digest((identity, 'source-spherical-SI/1', 'shared-exact-binary64-SI-rectilinear/1',
                             _NUMERICAL_RAD if not cartesian else None)), (resource,))
        if angular:
            model = ModelRef('stellar-angular-tangent', '1',
                _stellar_digest((identity, 'source-spherical-angular/1',
                    'shared-exact-binary64-angular-affine/1', _NUMERICAL_RAD)), (resource,))
        frame = ReferenceSpec(meta['gaia_reference']['frame'], meta['gaia_reference']['origin'],
            'nominal-astrometric', representation, 'm,m/s' if cartesian else 'rad',
            'normalized tangent angular approximation; perspective/parallax omitted; no physical distance/RV' if angular else
            'catalogue astrometry; reciprocal positive parallax; spectroscopic RV proxy; no additional light time')
        caps = (('cartesian_state', 'batch_evaluation') if cartesian else
                ('epoch_direction', 'batch_evaluation', 'direction_reuse_bound'))
        objects = []
        for objkey, row, star in zip(keys, catalogue.rows, catalogue.source.records(), strict=True):
            ids = [ExternalId(namespace, edition, row.identifier)]
            if star['published_association']:
                link = star['published_association']
                ids.append(ExternalId(link['catalogue'], link['release'], link['source_id']))
                if link['release'] != meta['gaia_reference']['release']:
                    bridge = link['equivalent_dr3_identity']
                    ids.append(ExternalId(link['catalogue'], bridge['release'], bridge['source_id']))
            objects.append(ObjectRecord(objkey, tuple(ids), 'star',
                () if row.source_epoch is None else (row.source_epoch,),
                ('unavailable_motion',) if row.unavailable_reason else caps, provenance))
        snapshot = CatalogueSnapshot(reference, tuple(objects))
        admission = ModelAdmission(reference, model, frame,
            tuple(k for k, row in zip(keys, catalogue.rows) if row.unavailable_reason is None),
            caps, catalogue.coverage)
        descriptor = ProviderDescriptor(key, (reference,), (admission,),
            'explicit offline stellar angular motion; no default/chart/observer adoption' if angular else
            'explicit offline full-input stellar motion; no default/chart/observer adoption')
        if cartesian:
            def unknown(unit, measurement):
                return UncertaintyEvidence(*(UncertaintyChannel('not_evaluated', None, unit, meaning)
                    for meaning in (measurement, 'nominal rectilinear model', 'euclidean_norm')))
            evidence = unknown('m', 'stellar position measurement and source-to-SI conversion')
            velocity_evidence = unknown('m/s', 'stellar velocity measurement and source-to-SI conversion')
            reuse = None
        else:
            evidence = UncertaintyEvidence(
                UncertaintyChannel('not_evaluated', None, 'rad',
                    'stellar measurement and source-to-angular conversion' if angular else
                    'stellar measurement and source-to-SI conversion'),
                UncertaintyChannel('not_evaluated', None, 'rad',
                    'normalized tangent approximation; perspective omitted' if angular else 'nominal rectilinear model'),
                UncertaintyChannel('bounded', _NUMERICAL_RAD, 'rad', 'angular_separation'))
            velocity_evidence = None
            reuse = ModelRef('stellar-angular-tangent-cone' if angular else 'stellar-rectilinear-cone', '1',
                            _stellar_digest(('exact-binary64-rational-cone/1', _NUMERICAL_RAD)), (resource,))
        super().__init__(tuple(zip(keys, catalogue.rows)), descriptor=descriptor, catalogue=snapshot,
                         admission=admission, evidence=evidence, reuse_method=reuse,
                         velocity_evidence=velocity_evidence)
