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
from contextlib import ExitStack
from hashlib import sha256
from math import cos, sin, pi, isfinite, isnan

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
class StellarMotionRequest:
    """Explicit ordered admitted models and one common nominal TCB event.

    This is stellar input, not a line/label or generic layer option. Availability
    selects models; a failed query never selects another model.
    """

    catalogues: tuple
    instant: TimePoint
    input_document_sha256: str | None = None

    def __post_init__(self):
        catalogues = tuple(self.catalogues)
        if not catalogues or any(type(c) is not StellarMotionCatalogue for c in catalogues):
            raise ValueError('Explicit admitted stellar catalogues are required.')
        if len({c.motion_policy for c in catalogues}) != len(catalogues):
            raise ValueError('Stellar model order must not contain duplicate models.')
        if type(self.instant) is not TimePoint or self.instant.scale != 'tcb':
            raise ValueError('A common resolved TCB event is required.')
        source = catalogues[0].source
        for catalogue in catalogues:
            if catalogue.source.manifest != source.manifest:
                raise ValueError('Stellar models must bind the same immutable source.')
            if not catalogue.coverage.contains(self.instant):
                raise ValueError('Stellar event lies outside a supplied model domain.')
        object.__setattr__(self, 'catalogues', catalogues)
        if self.input_document_sha256 is not None:
            value = self.input_document_sha256
            if (type(value) is not str or len(value) != 64
                    or any(c not in '0123456789abcdef' for c in value)):
                raise ValueError('Invalid stellar motion document SHA-256.')

    def __reduce__(self):
        raise TypeError('Stellar motion request transport is not admitted; bind it in the rendering process.')


def load_stellar_motion_request(path):
    """Admit one explicit local motion TOML through existing stellar models.

    This describes a nominal TCB event, never an observer clock or equinox.
    Paths are relative to the document. Source bytes are verified, not acquired.
    """
    from pathlib import Path
    document = Path(path).expanduser().resolve()
    return _load_stellar_motion_bytes(document.read_bytes(), document.parent)


def _load_stellar_motion_bytes(raw, base, *, source_directory=None):
    """One validation/admission path for a file and captured execution input."""
    from pathlib import Path
    try:
        import tomllib
    except ModuleNotFoundError:  # Python 3.10
        import tomli as tomllib
    from wenu.stellar_enrichment import load_stellar_enrichment
    values = tomllib.loads(raw.decode('utf-8'))
    required = {'schema_version', 'document_kind', 'source_directory',
                'source_manifest_sha256', 'target_jyear_tcb', 'models'}
    if values.keys() != required:
        raise ValueError('Stellar motion document has missing or unknown keys.')
    if (type(values['schema_version']) is not int or values['schema_version'] != 1
            or values['document_kind'] != 'wenu-stellar-motion-request'):
        raise ValueError('Unsupported stellar motion document schema.')
    digest = values['source_manifest_sha256']
    if (type(digest) is not str or len(digest) != 64
            or any(c not in '0123456789abcdef' for c in digest)):
        raise ValueError('An explicit source manifest SHA-256 is required.')
    directory = values['source_directory']
    if type(directory) is not str or not directory.strip():
        raise ValueError('An explicit local source directory is required.')

    def epoch(value):
        if type(value) not in (int, float):
            raise ValueError('TCB Julian epochs must be finite numbers.')
        try:
            if not isfinite(value):
                raise ValueError('TCB Julian epochs must be finite numbers.')
            return _stellar_epoch(value, 'tcb')
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError('Unsupported TCB Julian epoch.') from exc

    instant = epoch(values['target_jyear_tcb'])
    models = values['models']
    if type(models) is not list or not models:
        raise ValueError('An explicit nonempty ordered model list is required.')
    policies = set()
    admissions = []
    for model in models:
        required_model = {'motion_policy', 'start_jyear_tcb', 'stop_jyear_tcb',
                          'distance_policy', 'radial_velocity_policy'}
        if type(model) is not dict:
            raise ValueError('Each stellar model must be a TOML table.')
        policy = model.get('motion_policy')
        if type(policy) is not str or policy not in (
                'full-input-rectilinear', 'proper-motion-angular',
                'hipparcos2-angular-fallback'):
            raise ValueError('Unsupported stellar motion policy.')
        hip2 = policy == 'hipparcos2-angular-fallback'
        if hip2:
            required_model.add('epoch_policy')
        if model.keys() != required_model:
            raise ValueError('Stellar model has missing or unknown keys.')
        if policy in policies:
            raise ValueError('Duplicate stellar models are not admitted.')
        policies.add(policy)
        expected = (('positive-parallax-reciprocal', 'spectroscopic-proxy')
                    if policy == 'full-input-rectilinear' else ('not-used', 'not-used'))
        if (model['distance_policy'], model['radial_velocity_policy']) != expected:
            raise ValueError('Unsupported explicit stellar distance/radial-velocity policy.')
        if hip2 and model['epoch_policy'] != 'nominal-tcb-deferred-qualification':
            raise ValueError('An explicit nominal Hipparcos-2 epoch policy is required.')
        try:
            coverage = TimeSpan(epoch(model['start_jyear_tcb']), epoch(model['stop_jyear_tcb']))
        except InvalidQuery as exc:
            raise ValueError('Stellar model domain must be ordered.') from exc
        if not coverage.contains(instant):
            raise ValueError('Stellar event lies outside a supplied model domain.')
        admissions.append((model, coverage))

    source = load_stellar_enrichment(
        Path(base) / Path(directory).expanduser() if source_directory is None else source_directory,
                                    expected_manifest_sha256=digest)
    catalogues = tuple(StellarMotionCatalogue(source, coverage,
        model['distance_policy'], model['radial_velocity_policy'],
        model['motion_policy'], model.get('epoch_policy')) for model, coverage in admissions)
    return StellarMotionRequest(catalogues, instant, sha256(raw).hexdigest())


def stellar_motion_identity(request):
    """Science/input identity independent of process-local execution counters."""
    return dict(epoch=dict(jd1=request.instant.jd1, jd2=request.instant.jd2,
                           scale=request.instant.scale),
        model_order=[c.motion_policy for c in request.catalogues],
        models=[dict(policy=c.motion_policy, identity_sha256=_stellar_digest(c.to_record()),
                     admission=c.to_record()) for c in request.catalogues],
        source_manifest_sha256=sha256(request.catalogues[0].source.manifest).hexdigest(),
        input_document_sha256=request.input_document_sha256)


@dataclass(frozen=True, slots=True)
class StellarMotionExecutionInput:
    """Pinned data-only atlas transport; never an evaluated state or live session."""
    document: bytes
    source_directory: str
    snapshot_sha256: str
    design_sha256: str
    motion_identity_sha256: str
    integrity_sha256: str

    def _digest(self):
        return _stellar_digest([sha256(self.document).hexdigest(), self.source_directory,
            self.snapshot_sha256, self.design_sha256, self.motion_identity_sha256])

    @classmethod
    def capture(cls, path, *, snapshot_sha256, design_sha256):
        from pathlib import Path
        path = Path(path).expanduser().resolve()
        raw = path.read_bytes()
        request = _load_stellar_motion_bytes(raw, path.parent)
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib
        directory = (path.parent / Path(tomllib.loads(raw.decode('utf-8'))[
            'source_directory']).expanduser()).resolve()
        value = cls(raw, str(directory), snapshot_sha256, design_sha256,
                    _stellar_digest(stellar_motion_identity(request)), '')
        value = cls(raw, value.source_directory, snapshot_sha256, design_sha256,
                    value.motion_identity_sha256, value._digest())
        value._validate(snapshot_sha256, design_sha256)
        return value, request

    def _validate(self, snapshot_sha256, design_sha256):
        from pathlib import Path
        if (type(self.document) is not bytes or type(self.source_directory) is not str
                or not Path(self.source_directory).is_absolute()):
            raise ValueError('Invalid stellar execution input.')
        for digest in (self.snapshot_sha256, self.design_sha256,
                       self.motion_identity_sha256, self.integrity_sha256):
            if type(digest) is not str or len(digest) != 64 or any(
                    c not in '0123456789abcdef' for c in digest):
                raise ValueError('Invalid stellar execution digest.')
        if (self._digest() != self.integrity_sha256
                or self.snapshot_sha256 != snapshot_sha256
                or self.design_sha256 != design_sha256):
            raise ValueError('Stellar execution input identity mismatch.')

    def admit(self, *, snapshot_sha256, design_sha256):
        self._validate(snapshot_sha256, design_sha256)
        request = _load_stellar_motion_bytes(self.document, '.',
            source_directory=self.source_directory)
        if _stellar_digest(stellar_motion_identity(request)) != self.motion_identity_sha256:
            raise ValueError('Stellar execution model/source identity mismatch.')
        return request


class _StellarRealization:
    """Request-local SDK bridge owned by a realized Stars view."""

    def __init__(self, request, source_table, source_metadata):
        from wenu_kernel import Kernel
        from wenu_kernel.records import SessionPolicy
        from wenu.coordinates import CoordinateSpec, PositionStatus
        from wenu_kernel.errors import ClosedSession
        self._closed_error = ClosedSession
        self._scope = ExitStack()
        self._closed = False
        self.request = request
        self.query_calls = 0
        self._last_batches = {}
        self.sdk_batches_evaluated = 0
        self.exact_batch_reuses = 0
        self._groups = []
        self._ids = tuple(int(i) for i in source_table.index)
        self._index = {i: n for n, i in enumerate(self._ids)}
        self._models = [None] * len(self._ids)
        self._reasons = [[] for _ in self._ids]
        source = request.catalogues[0].source
        baseline = source.metadata['baseline']
        for field in ('catalogue', 'edition', 'source_sha256'):
            if source_metadata[field] != baseline[field]:
                raise ValueError('Stellar enrichment/source binding differs: ' + field)
        original_metadata = source.metadata['original_metadata']
        for field in ('frame', 'origin', 'epoch'):
            if source_metadata[field] != original_metadata[field]:
                raise ValueError('Stellar source reference differs: ' + field)
        if any(source_metadata['units'].get(k) != v
               for k, v in original_metadata['units'].items()):
            raise ValueError('Stellar source units differ from enrichment.')
        originals = {int(r['identity']['identifier']): r['original'] for r in source.records()}
        if len(self._ids) != len(self._index) or not set(self._ids) <= originals.keys():
            raise ValueError('Stellar source identities differ from enrichment.')
        for identifier, magnitude in zip(self._ids, source_table['magnitude']):
            value = originals[identifier]['magnitude']
            if not ((value is None and isnan(float(magnitude)))
                    or (value is not None and float(magnitude) == value)):
                raise ValueError('Stellar source photometry differs from enrichment.')
        instant = request.instant
        self.coordinate_spec = CoordinateSpec(
            frame='icrs', origin='solar-system-barycenter',
            position_status=PositionStatus.ASTROMETRIC,
            instant=f'JD({instant.jd1},{instant.jd2.hex()})', time_scale='tcb',
            provider='wenu stellar realization', model='explicit ordered nominal stellar models',
            provenance=('stellar-source-manifest-sha256:' + sha256(source.manifest).hexdigest(),
                        'Physical accuracy unknown; no guaranteed ancient-position accuracy') + tuple(
                            'stellar-model-sha256:' + _stellar_digest(c.to_record())
                            for c in request.catalogues))
        try:
            for catalogue in request.catalogues:
                rows = {int(row.identifier): row for row in catalogue.rows}
                chosen = []
                for n, identifier in enumerate(self._ids):
                    if self._models[n] is not None:
                        continue
                    row = rows[identifier]
                    if row.unavailable_reason is not None:
                        self._reasons[n].append(catalogue.motion_policy + ':' + row.unavailable_reason)
                    else:
                        chosen.append(identifier)
                        self._models[n] = catalogue.motion_policy
                if not chosen:
                    continue
                provider = StellarMotionProvider(catalogue)
                # Close even if registration or session creation fails.
                self._scope.callback(provider.close)
                admission = provider.describe().admissions[0]
                kernel = self._scope.enter_context(Kernel(references=(admission.reference,)))
                kernel.register(provider, ownership='borrowed')
                session = self._scope.enter_context(kernel.open_session(SessionPolicy((admission.catalogue,))))
                keys = {int(key.value.rsplit(':', 1)[1]): key for key in admission.objects}
                self._groups.append((session, admission, tuple(keys[i] for i in chosen), tuple(chosen)))
        except BaseException:
            self.close()
            raise

    def close(self):
        if not self._closed:
            self._closed = True
            try:
                self._scope.close()
            finally:
                self._groups.clear()
                self._last_batches.clear()

    def positions(self, identifiers):
        """Read actual SDK results, retaining source identity and explicit gaps."""
        import numpy as np
        from wenu_kernel.records import AccuracyRequest, StateQuery
        if self._closed:
            raise self._closed_error('stellar realization is closed')
        self.query_calls += 1
        ids = tuple(int(i) for i in identifiers)
        if not ids:
            return np.asarray([], dtype=float), np.asarray([], dtype=float)
        values = {}
        for session, admission, keys, hips in self._groups:
            query = StateQuery(admission.catalogue, admission.model, keys,
                (self.request.instant,), admission.reference, AccuracyRequest())
            batch = session.evaluate(query)
            if self._last_batches.get(admission.model) is batch:
                self.exact_batch_reuses += 1
            else:
                self.sdk_batches_evaluated += 1
                self._last_batches[admission.model] = batch
            # Query validation/order and exact-result reuse belong to the SDK.
            for state, hip in zip(batch.states, hips, strict=True):
                x, y, z = state.vector
                values[hip] = (np.degrees(np.arctan2(y, x)) % 360.,
                               np.degrees(np.arctan2(z, np.hypot(x, y))))
        angles = np.asarray([values.get(i, (np.nan, np.nan)) for i in ids], dtype=float).reshape(-1, 2)
        return angles[:, 0], angles[:, 1]

    def row_metadata(self, identifiers):
        import numpy as np
        indices = [self._index[int(i)] for i in identifiers]
        return dict(stellar_motion_model=np.asarray([self._models[n] for n in indices], dtype=object),
            stellar_motion_status=np.asarray(['evaluated' if self._models[n] else 'unavailable' for n in indices], dtype=object),
            stellar_motion_reason=np.asarray(['' if self._models[n] else ';'.join(self._reasons[n]) for n in indices], dtype=object))

    def report(self):
        result = dict(epoch=dict(jd1=self.request.instant.jd1, jd2=self.request.instant.jd2, scale='tcb'),
            model_order=[c.motion_policy for c in self.request.catalogues],
            models=[dict(policy=c.motion_policy, identity_sha256=_stellar_digest(c.to_record()),
                         admission=c.to_record()) for c in self.request.catalogues],
            source_manifest_sha256=sha256(self.request.catalogues[0].source.manifest).hexdigest(),
            model_counts=dict(Counter(m or 'unavailable' for m in self._models)),
            public_position_queries=self.query_calls,
            sdk_batches_evaluated=self.sdk_batches_evaluated,
            exact_batch_reuses=self.exact_batch_reuses, physical_accuracy='unknown')
        if self.request.input_document_sha256 is not None:
            result['input_document_sha256'] = self.request.input_document_sha256
        return result


@dataclass(frozen=True, slots=True)
class StellarMotionCatalogue:
    """Explicit nominal model derived from an unchanged immutable source snapshot.

    All original objects remain present. Missing inputs do not acquire a model;
    Hip2 fallback admission is separate; original-1997 lookup stays unchanged.
    The source snapshot is retained verbatim, including uncertainties and flags.
    """
    source: StellarEnrichmentSnapshot
    coverage: TimeSpan
    distance_policy: str
    radial_velocity_policy: str
    motion_policy: str = 'full-input-rectilinear'
    epoch_policy: str | None = None
    rows: tuple[SpaceMotionRow | AngularMotionRow, ...] = field(init=False)
    metadata_json: bytes = field(init=False)

    def __post_init__(self):
        if type(self.source) is not StellarEnrichmentSnapshot:
            raise ValueError('A validated immutable stellar source snapshot is required.')
        if type(self.coverage) is not TimeSpan or self.coverage.start.scale != 'tcb':
            raise ValueError('An explicit finite TCB nominal model domain is required.')
        hip2 = self.motion_policy == 'hipparcos2-angular-fallback'
        angular = self.motion_policy in ('proper-motion-angular', 'hipparcos2-angular-fallback')
        if self.motion_policy not in ('full-input-rectilinear', 'proper-motion-angular', 'hipparcos2-angular-fallback'):
            raise ValueError('Unsupported stellar motion policy.')
        expected_policies = ('not-used', 'not-used') if angular else (
            'positive-parallax-reciprocal', 'spectroscopic-proxy')
        if (self.distance_policy, self.radial_velocity_policy) != expected_policies:
            raise ValueError('Unsupported explicit stellar distance/radial-velocity policy.')
        if hip2:
            _admit_hipparcos2_fallback(self)
            return
        if self.epoch_policy is not None:
            raise ValueError('A nominal Hipparcos-2 epoch policy cannot relabel Gaia inputs.')
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


def _admit_hipparcos2_fallback(catalogue):
    """Source interpretation only; evaluation stays in the shared angular core."""
    if catalogue.epoch_policy != 'nominal-tcb-deferred-qualification':
        raise ValueError('Explicit nominal-TCB Hipparcos-2 epoch policy is required; see issue #326.')
    source = catalogue.source
    meta = source.metadata
    profile = meta['hipparcos2_profile']
    facts = profile['reference']
    epoch_fact = facts['epoch']
    if ((facts['frame'], facts['origin'], epoch_fact['format']) !=
            ('icrs', 'solar-system-barycenter', 'jyear')
            or epoch_fact['scale'] is not None
            or type(epoch_fact['value']) not in (int, float)
            or not isfinite(epoch_fact['value'])):
        raise ValueError('Unsupported Hipparcos-2 source convention; nominal policy does not replace a declared scale.')
    for name, unit in (('RArad','rad'), ('DErad','rad'), ('pmRA','mas/yr'), ('pmDE','mas/yr')):
        if profile['columns'][name]['unit'] != unit:
            raise ValueError('Unsupported Hipparcos-2 angular unit: ' + name)
    epoch = _stellar_epoch(epoch_fact['value'], 'tcb')
    if not catalogue.coverage.contains(epoch):
        raise ValueError('Hipparcos-2 nominal source epoch is outside the model domain.')
    hip_sources = {r['HIP']: r for r in source.records('hipparcos2_sources_v1.jsonl')}
    gaia_sources = {r['source_id']: r for r in source.records('gaia_sources_v1.jsonl')}
    rows = []
    for star in source.records():
        hip = star['identity']['identifier']
        link = star['published_association']
        gaia = None if link is None else gaia_sources[link['source_id']]
        # Fallback selection follows actual angular inputs, not parallax/RV or
        # the earlier full-input inventory preference. Published links survive.
        if (gaia is not None and gaia.get('astrometric_params_solved') in (31, 95)
                and all(gaia.get(k) is not None for k in ('ra','dec','pmra','pmdec'))):
            rows.append(AngularMotionRow(hip, None, None, None, 'gaia_angular_model_available'))
            continue
        src = hip_sources.get(hip)
        if src is None:
            rows.append(AngularMotionRow(hip, None, None, None, 'no_hipparcos2_source'))
            continue
        fields = ('RArad','DErad','pmRA','pmDE')
        missing = [k for k in fields if src.get(k) is None]
        if missing:
            rows.append(AngularMotionRow(hip, epoch, None, None, 'missing_hipparcos2_' + ','.join(missing)))
            continue
        if any(type(src[k]) not in (int, float) or not isfinite(src[k]) for k in fields):
            raise ValueError('Invalid Hipparcos-2 angular parameter.')
        ra, dec = src['RArad'], src['DErad']
        if not (0 <= ra < 2*pi and -pi/2 <= dec <= pi/2):
            raise ValueError('Hipparcos-2 angular position outside source range.')
        u = (cos(dec)*cos(ra), cos(dec)*sin(ra), sin(dec))
        east, north = (-sin(ra), cos(ra), 0.), (-sin(dec)*cos(ra), -sin(dec)*sin(ra), cos(dec))
        mas_to_rad = pi / (180 * 3600 * 1000)
        pma, pmd = (src[k] * mas_to_rad / (365.25 * 86400) for k in ('pmRA','pmDE'))
        derivative = tuple(pma*a + pmd*d for a,d in zip(east,north))
        row = AngularMotionRow(hip, epoch, u, derivative, None)
        validate_space_motion_domain(row, catalogue.coverage)
        rows.append(row)
    policies = dict(distance='not-used', radial_velocity='not-used',
        motion='normalized-tangent-angular', perspective='omitted', observer_parallax='unavailable',
        light_time='no-additional-correction', binaries='no-orbit-or-systemic-correction',
        acceleration='not-modelled', covariance_propagation='not-implemented',
        physical_accuracy='not-evaluated', source_to_angular_error='not-evaluated',
        epoch=catalogue.epoch_policy, time_convention_error='not-evaluated',
        follow_up='https://github.com/fselman/wenu/issues/326')
    record = dict(schema='wenu-stellar-hipparcos2-motion-admission/1',
        source_manifest_sha256=sha256(source.manifest).hexdigest(), original_baseline=meta['baseline'],
        association_ledger_sha256=meta['association_ledger_sha256'],
        hipparcos2_reference=facts,
        model_reference=dict(frame=facts['frame'], origin=facts['origin'], epoch_scale='tcb',
            epoch_value=epoch_fact['value'], right_ascension_motion='mu_alpha*cos(delta)',
            qualification='explicit nominal time convention; original epoch scale unresolved'),
        policies=policies,
        coverage=[[t.jd1,t.jd2,t.scale] for t in (catalogue.coverage.start,catalogue.coverage.stop)],
        angular_solutions_sha256=_stellar_digest([(r.identifier,
            None if r.source_epoch is None else [r.source_epoch.jd1,r.source_epoch.jd2,r.source_epoch.scale],
            r.direction,r.tangent_per_s,r.unavailable_reason) for r in rows]),
        counts=dict(retained_objects=len(rows), angular_models=sum(r.unavailable_reason is None for r in rows),
            unavailable_by_reason=dict(Counter(r.unavailable_reason for r in rows if r.unavailable_reason))))
    object.__setattr__(catalogue, 'rows', tuple(rows))
    object.__setattr__(catalogue, 'metadata_json', encode(record))


def admit_stellar_hipparcos2_motion(source, *, coverage, epoch_policy):
    """Opt in to separate angular fallback with an explicit nominal TCB policy.

    Source time-scale facts stay unchanged; this performs no TT/TCB conversion.
    Qualified Gaia angular inputs take precedence. No physical PV is inferred.
    """
    return StellarMotionCatalogue(source, coverage, 'not-used', 'not-used',
                                  'hipparcos2-angular-fallback', epoch_policy)


class StellarMotionProvider(RectilinearAstrometricProvider):
    """Stellar source adapter to the shared, separately typed affine engine."""
    def __init__(self, catalogue, *, representation='direction'):
        if type(catalogue) is not StellarMotionCatalogue:
            raise ValueError('An admitted immutable stellar motion catalogue is required.')
        if representation not in ('direction', 'cartesian'):
            raise ValueError('Unsupported stellar motion representation.')
        cartesian = representation == 'cartesian'
        hip2 = catalogue.motion_policy == 'hipparcos2-angular-fallback'
        angular = catalogue.motion_policy in ('proper-motion-angular', 'hipparcos2-angular-fallback')
        if angular and cartesian:
            raise ValueError('Angular stellar motion has no admitted Cartesian distance or velocity.')
        meta = catalogue.source.metadata
        record = catalogue.to_record()
        identity = _stellar_digest(record)
        namespace, edition = meta['baseline']['catalogue'], meta['baseline']['edition']
        key = ProviderKey('wenu.stellar-motion' + ('.hipparcos2-angular' if hip2 else '.angular' if angular else '.cartesian' if cartesian else ''), '1')
        provenance = ('Immutable stellar source manifest SHA-256 ' + record['source_manifest_sha256'],
                      'Explicit nominal rectilinear model; source/physical/input-conversion errors unknown')
        if angular:
            provenance = (provenance[0], 'Explicit normalized tangent angular model; perspective/parallax omitted; unknown physical error')
        if hip2:
            provenance += ('Hipparcos-2 source epoch on nominal TCB axis; original scale unresolved; time-convention error unknown; issue #326',)
        resource = ResourceRef('stellar-hipparcos2-angular-inputs' if hip2 else 'stellar-angular-motion-inputs' if angular else 'stellar-motion-inputs', '1', identity, catalogue.coverage,
            'caller-declared nominal domain; not certified physical validity', provenance)
        keys = tuple(ObjectKey(namespace + ':' + row.identifier) for row in catalogue.rows)
        reference = CatalogueRef(key, (resource,), _stellar_digest([k.value for k in keys]))
        model = ModelRef('stellar-rectilinear' + ('-cartesian' if cartesian else ''), '1',
            _stellar_digest((identity, 'source-spherical-SI/1', 'shared-exact-binary64-SI-rectilinear/1',
                             _NUMERICAL_RAD if not cartesian else None)), (resource,))
        if angular:
            model = ModelRef('stellar-hipparcos2-angular-tangent' if hip2 else 'stellar-angular-tangent', '1',
                _stellar_digest((identity, 'source-hipparcos2-angular/1' if hip2 else 'source-spherical-angular/1',
                    'shared-exact-binary64-angular-affine/1', _NUMERICAL_RAD)), (resource,))
        facts = record['model_reference'] if hip2 else meta['gaia_reference']
        frame = ReferenceSpec(facts['frame'], facts['origin'],
            'nominal-astrometric', representation, 'm,m/s' if cartesian else 'rad',
            'Hipparcos-2 normalized tangent; nominal TCB epoch/rate convention; unresolved original scale; issue #326; no physical PV' if hip2 else
            'normalized tangent angular approximation; perspective/parallax omitted; no physical distance/RV' if angular else
            'catalogue astrometry; reciprocal positive parallax; spectroscopic RV proxy; no additional light time')
        caps = (('cartesian_state', 'batch_evaluation') if cartesian else
                ('epoch_direction', 'batch_evaluation', 'direction_reuse_bound'))
        objects = []
        for objkey, row, star in zip(keys, catalogue.rows, catalogue.source.records(), strict=True):
            ids = [ExternalId(namespace, edition, row.identifier)]
            if hip2 and star['source_references']['hipparcos2'] is not None:
                profile = meta['hipparcos2_profile']
                ids.append(ExternalId(profile['catalogue'], profile['citation'], row.identifier))
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
            'explicit offline Hipparcos-2 angular fallback; nominal TCB; issue #326; no default adoption' if hip2 else
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
                    'Hipparcos-2 measurement, angular conversion and nominal time-convention uncertainty' if hip2 else
                    'stellar measurement and source-to-angular conversion' if angular else
                    'stellar measurement and source-to-SI conversion'),
                UncertaintyChannel('not_evaluated', None, 'rad',
                    'normalized tangent approximation; perspective omitted' if angular else 'nominal rectilinear model'),
                UncertaintyChannel('bounded', _NUMERICAL_RAD, 'rad', 'angular_separation'))
            velocity_evidence = None
            reuse = ModelRef('stellar-hipparcos2-angular-tangent-cone' if hip2 else 'stellar-angular-tangent-cone' if angular else 'stellar-rectilinear-cone', '1',
                            _stellar_digest(('exact-binary64-rational-cone/1', _NUMERICAL_RAD)), (resource,))
        super().__init__(tuple(zip(keys, catalogue.rows)), descriptor=descriptor, catalogue=snapshot,
                         admission=admission, evidence=evidence, reuse_method=reuse,
                         velocity_evidence=velocity_evidence)

