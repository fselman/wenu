"""Offline admission and nominal rectilinear open-cluster state provider.

Source lookup remains a separate model. This owner transports a density-mode
centre using its core mean motion; it does not reconstruct a historical cluster
or certify physical accuracy. No acquisition, observer or graphics dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path

import numpy as np
import astropy
from astropy import units as u
from astropy.coordinates import (CartesianDifferential, CartesianRepresentation,
                                 SphericalCosLatDifferential, SphericalRepresentation)
from astropy.table import Table
from astropy.time import Time

from wenu_kernel.records import (
    CatalogueRef, CatalogueSnapshot, ExternalId, ModelAdmission, ModelRef,
    ObjectKey, ObjectRecord, ProviderDescriptor, ProviderKey, ReferenceSpec,
    ResourceRef, TimePoint, TimeSpan, UncertaintyChannel, UncertaintyEvidence,
)


def _canonical_digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()


# Compatibility row name; object-independent SI solution type.
from wenu.astrometric_state import (
    SpaceMotionRow as ClusterMotionRow, RectilinearAstrometricProvider,
    validate_space_motion_domain, _NUMERICAL_RAD,
)


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
        solution = ClusterMotionRow(identifier, epoch, position, velocity, None)
        validate_space_motion_domain(solution, coverage)
        rows.append(solution)
    from io import StringIO
    stream = StringIO()
    copied.write(stream, format='ascii.ecsv')
    record = dict(source_metadata=metadata,
                  derived_table_sha256=sha256(stream.getvalue().encode()).hexdigest(),
                  unavailable={row.identifier: row.unavailable_reason for row in rows if row.unavailable_reason})
    return ClusterMotionCatalogue(tuple(rows), stream.getvalue(),
        json.dumps(record, sort_keys=True, allow_nan=False), coverage)


class ClusterMotionProvider(RectilinearAstrometricProvider):
    """Nominal model with provider-owned angular certificates; physical error unknown."""
    def __init__(self, catalogue, *, representation="direction"):
        if type(catalogue) is not ClusterMotionCatalogue:
            raise ValueError('An admitted immutable cluster catalogue is required.')
        if representation not in ('direction','cartesian'):
            raise ValueError('Unsupported cluster state representation.')
        cartesian = representation == 'cartesian'
        meta = catalogue.to_record()['source_metadata']
        key = ProviderKey('wenu.cluster-motion.cartesian' if cartesian else 'wenu.cluster-motion', '1')
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
        if cartesian:
            model = ModelRef('cluster-centre-rectilinear-cartesian','1',
                _canonical_digest((identity,meta['policies'],
                    'exact binary64 SI rectilinear PV; final position rounding/1',
                    astropy.__version__,np.__version__)),(resource,))
        facts = meta['astrometry']
        frame = ReferenceSpec(facts['frame'], facts['origin'], 'nominal-astrometric', representation, 'm,m/s' if cartesian else 'rad',
            'density-mode centre transported by core mean motion; no additional light-time correction; unknown physical error')
        capabilities = (('cartesian_state','batch_evaluation') if cartesian else
                        ('epoch_direction', 'batch_evaluation', 'direction_reuse_bound'))
        records = tuple(ObjectRecord(k, (ExternalId(meta['namespace'], meta['edition'], row.identifier),),
            'open-cluster', () if row.source_epoch is None else (row.source_epoch,),
            ('unavailable_motion',) if row.unavailable_reason else capabilities, (meta['provenance'],))
            for k, row in zip(keys, catalogue.rows))
        self._catalogue = CatalogueSnapshot(reference, records)
        self._admission = ModelAdmission(reference, model, frame,
            tuple(k for k, row in zip(keys, catalogue.rows) if row.unavailable_reason is None), capabilities, coverage)
        self._descriptor = ProviderDescriptor(key, (reference,), (self._admission,),
            ('offline Cartesian full-model PV; no temporal reuse or certified accuracy' if cartesian else
             'offline nominal propagation and interactive certified reuse; no default chart adoption'))
        self._evidence = UncertaintyEvidence(*(
            UncertaintyChannel('not_evaluated', None, 'rad', meaning)
            for meaning in ('cluster-centre measurement', 'centre/rectilinear model error')),
            UncertaintyChannel('bounded', _NUMERICAL_RAD, 'rad', 'angular_separation'))
        self._reuse_method = ModelRef('cluster-rectilinear-cone', '1',
            _canonical_digest(('exact-binary64-rational-cone/1', _NUMERICAL_RAD)), (resource,))

        velocity_evidence = None
        if cartesian:
            def unknown(unit,measurement):
                return UncertaintyEvidence(
                    UncertaintyChannel('not_evaluated',None,unit,measurement),
                    UncertaintyChannel('not_evaluated',None,unit,'nominal centre/rectilinear model error'),
                    UncertaintyChannel('not_evaluated',None,unit,'euclidean_norm'))
            self._evidence = unknown('m','cluster-centre position measurement')
            velocity_evidence = unknown('m/s','cluster-mean velocity measurement')
            self._reuse_method = None
        super().__init__(tuple(self._lookup.items()), descriptor=self._descriptor,
            catalogue=self._catalogue, admission=self._admission, evidence=self._evidence,
            reuse_method=self._reuse_method,velocity_evidence=velocity_evidence)
