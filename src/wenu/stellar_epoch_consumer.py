"""Saved stellar query input, captured worker admission and position-view lifetime.

This adapter owns no propagation or rendering. Immutable product validation and
query policy remain in their existing owners; charts consume shared positions.
"""
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path

from wenu.stellar_enrichment import decode, encode, require
from wenu.stellar_epoch import StellarEpochCatalogue, load_stellar_epoch
from wenu.stellar_epoch_query import resolve_stellar_epoch
from wenu_kernel.records import TimePoint


@dataclass(frozen=True, slots=True)
class StellarEpochViewInput:
    catalogue: StellarEpochCatalogue
    instant: TimePoint
    reuse_window_julian_years: float
    resolution: object = field(init=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, 'resolution', resolve_stellar_epoch(self.catalogue,
            self.instant, reuse_window_julian_years=self.reuse_window_julian_years))

    def __reduce__(self):
        raise TypeError('Capture epoch execution input instead of transporting a resolved view')


def stellar_epoch_view_identity(request):
    require(type(request) is StellarEpochViewInput, 'An admitted epoch view input is required')
    receipt = request.resolution.receipt()
    motion = receipt['motion_identity']
    return dict(epoch=receipt['actual_position_event'], model_order=motion['model_order'],
        models=motion['models'], source_manifest_sha256=motion['source_manifest_sha256'],
        epoch_query=receipt)


@dataclass(frozen=True, slots=True)
class StellarEpochExecutionInput:
    """Small data-only binding; each worker loads and resolves once on admission."""
    document: bytes
    base_directory: str
    snapshot_sha256: str
    design_sha256: str
    integrity_sha256: str

    def _identity(self):
        return sha256(encode(dict(document_sha256=sha256(self.document).hexdigest(),
            base_directory=self.base_directory, snapshot_sha256=self.snapshot_sha256,
            design_sha256=self.design_sha256))).hexdigest()

    @classmethod
    def capture(cls, path, *, snapshot_sha256, design_sha256):
        path = Path(path).expanduser().resolve(strict=True)
        value = cls(path.read_bytes(), str(path.parent), snapshot_sha256, design_sha256, '')
        value = cls(value.document, value.base_directory, snapshot_sha256, design_sha256, value._identity())
        return value, value.admit(snapshot_sha256=snapshot_sha256, design_sha256=design_sha256)

    def admit(self, *, snapshot_sha256, design_sha256):
        require(type(self.document) is bytes and type(self.base_directory) is str,
                'Invalid captured epoch input')
        for value in (self.snapshot_sha256, self.design_sha256, self.integrity_sha256):
            require(type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value),
                    'Invalid captured epoch digest')
        require(snapshot_sha256 == self.snapshot_sha256 and design_sha256 == self.design_sha256
                and self.integrity_sha256 == self._identity(), 'Captured epoch input binding differs')
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib
        data = tomllib.loads(self.document.decode('utf-8'))
        require(set(data) == {'schema_version', 'document_kind', 'catalogue_directory',
            'manifest_sha256', 'instant', 'reuse_window_julian_years'}, 'Invalid epoch query document fields')
        require(type(data['schema_version']) is int and data['schema_version'] == 1
                and data['document_kind'] == 'wenu-stellar-epoch-query', 'Unsupported epoch query document')
        directory, digest = data['catalogue_directory'], data['manifest_sha256']
        require(type(directory) is str and bool(directory.strip()), 'Explicit epoch catalogue path required')
        require(type(digest) is str and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest),
                'Explicit epoch manifest SHA-256 required')
        instant = data['instant']
        require(type(instant) is dict and set(instant) == {'jd1', 'jd2', 'scale'}, 'Resolved epoch event required')
        catalogue = load_stellar_epoch(Path(self.base_directory)/Path(directory).expanduser(),
            expected_manifest_sha256=digest)
        return StellarEpochViewInput(catalogue, TimePoint(**instant), data['reuse_window_julian_years'])


class StellarEpochRealization:
    """Read-only position adapter with the existing stellar-view interface."""
    def __init__(self, request, source_table, source_metadata):
        import math
        import numpy as np
        from wenu.coordinates import CoordinateSpec, PositionStatus
        require(type(request) is StellarEpochViewInput, 'An admitted epoch view input is required')
        source = request.catalogue.source
        baseline, original = source.metadata['baseline'], source.metadata['original_metadata']
        require(all(source_metadata[k] == baseline[k] for k in ('catalogue', 'edition', 'source_sha256')),
                'Epoch/source catalogue binding differs')
        require(all(source_metadata[k] == original[k] for k in ('frame', 'origin', 'epoch'))
                and all(source_metadata['units'].get(k) == v for k, v in original['units'].items()),
                'Epoch/source reference or units differ')
        originals = {int(r['identity']['identifier']): r['original'] for r in source.records()}
        ids = tuple(int(i) for i in source_table.index)
        require(len(ids) == len(set(ids)) and set(ids) <= originals.keys(), 'Epoch/source identities differ')
        for hip, magnitude in zip(ids, source_table['magnitude'], strict=True):
            value = originals[hip]['magnitude']
            require((value is None and math.isnan(float(magnitude))) or
                    (value is not None and float(magnitude) == value), 'Epoch/source photometry differs')
        self.request = request
        self._closed = False
        self.query_calls = 0
        self._identity = stellar_epoch_view_identity(request)
        policies = self._identity['model_order']
        wanted = set(ids)
        self._positions, self._metadata = {}, {}
        for row in request.resolution.rows():
            hip = int(row['identifier'])
            if hip not in wanted:
                continue
            chosen = row['model_index']
            vector = None if row['direction'] is None else row['direction']['vector']
            if vector is None:
                position = (np.nan, np.nan)
            else:
                x, y, z = vector
                position = (np.degrees(np.arctan2(y, x)) % 360., np.degrees(np.arctan2(z, np.hypot(x, y))))
            self._positions[hip] = position
            self._metadata[hip] = (None if chosen is None else policies[chosen], row['status'],
                                   ';'.join(row['reasons']) if chosen is None else '')
        require(set(self._positions) == wanted, 'Epoch positions omit source identities')
        instant = self._identity['epoch']
        self.coordinate_spec = CoordinateSpec(frame='icrs', origin='solar-system-barycenter',
            position_status=PositionStatus.ASTROMETRIC,
            instant=f"JD({instant['jd1']},{float(instant['jd2']).hex()})", time_scale='tcb',
            provider='wenu saved stellar epoch', model='explicit saved epoch query',
            provenance=('stellar-epoch-manifest-sha256:'+request.resolution.receipt()['epoch_manifest_sha256'],
                        'Physical accuracy unknown; requested/actual events disclosed separately'))

    def close(self):
        self._closed = True
        self._positions.clear()
        self._metadata.clear()

    def _check(self):
        from wenu_kernel.errors import ClosedSession
        if self._closed:
            raise ClosedSession('stellar epoch view is closed')

    def positions(self, identifiers):
        import numpy as np
        self._check()
        self.query_calls += 1
        values = np.asarray([self._positions[int(i)] for i in identifiers], dtype=float).reshape(-1, 2)
        return values[:, 0], values[:, 1]

    def row_metadata(self, identifiers):
        import numpy as np
        self._check()
        values = [self._metadata[int(i)] for i in identifiers]
        return dict(stellar_motion_model=np.asarray([r[0] for r in values], dtype=object),
            stellar_motion_status=np.asarray([r[1] for r in values], dtype=object),
            stellar_motion_reason=np.asarray([r[2] for r in values], dtype=object))

    def report(self):
        from collections import Counter
        self._check()
        result = decode(encode(self._identity))
        result.update(model_counts=dict(Counter(r[0] or 'unavailable' for r in self._metadata.values())),
            public_position_queries=self.query_calls, sdk_batches_evaluated=0, exact_batch_reuses=0,
            physical_accuracy='unknown')
        return result
