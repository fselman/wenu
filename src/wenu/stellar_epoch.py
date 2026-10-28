"""Immutable exact-event stellar products, separate from sources and sessions.

Preparation evaluates admitted models. Reading validates data only: it neither
recreates providers nor advances an epoch. No chart, observer or acquisition API.
"""
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import os
import shutil
import tempfile

from wenu.stellar_enrichment import (
    PRODUCTS, StellarEnrichmentSnapshot, decode, encode, identity, require,
)
from wenu_kernel.errors import KernelError
from wenu_kernel.records import (
    CartesianState, DirectionState, ReferenceSpec, TimePoint, TimeSpan,
    UncertaintyChannel, UncertaintyEvidence,
)

SCHEMA = 'wenu-stellar-epoch/1'
SOURCE_FILES = ('source_manifest_v1.json',) + PRODUCTS
PAYLOADS = ('models.json', 'states.jsonl') + tuple('source/' + n for n in SOURCE_FILES)


def _keys(value, names):
    require(type(value) is dict and set(value) == set(names), 'Invalid stellar epoch fields')


def _time(value):
    _keys(value, ('jd1', 'jd2', 'scale'))
    return TimePoint(**value)


def _evidence(value):
    _keys(value, ('measurement', 'physical_model', 'numerical'))
    channels = []
    for name in ('measurement', 'physical_model', 'numerical'):
        item = value[name]
        _keys(item, ('status', 'value', 'units', 'meaning'))
        channels.append(UncertaintyChannel(**item))
    return UncertaintyEvidence(*channels)


def _state(value, *, cartesian=False):
    fields = ('object_key', 'time', 'source_epoch', 'anchor_time', 'reference')
    fields += (('position_m', 'velocity_m_s', 'position_evidence', 'velocity_evidence')
               if cartesian else ('vector', 'evidence', 'certificate_id'))
    _keys(value, fields)
    from wenu_kernel.records import ObjectKey
    _keys(value['object_key'], ('value',))
    _keys(value['reference'], ('frame_id', 'origin_id', 'status', 'representation', 'units', 'correction_policy', 'equinox'))
    common = (ObjectKey(**value['object_key']), _time(value['time']),
              None if value['source_epoch'] is None else _time(value['source_epoch']),
              _time(value['anchor_time']), ReferenceSpec(**value['reference']))
    if cartesian:
        return CartesianState(*common, value['position_m'], value['velocity_m_s'],
                              _evidence(value['position_evidence']),
                              None if value['velocity_evidence'] is None else _evidence(value['velocity_evidence']))
    return DirectionState(*common, value['vector'], _evidence(value['evidence']), value['certificate_id'])


def _code_identity():
    # Fixed owners, never imports or paths supplied by the product.
    from wenu import stellar_state, astrometric_state, stellar_enrichment
    from wenu_kernel import kernel, records
    modules = (stellar_state, astrometric_state, stellar_enrichment, kernel, records)
    result = {m.__name__: sha256(Path(m.__file__).read_bytes()).hexdigest() for m in modules}
    result['wenu.stellar_epoch'] = sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def _read(path):
    require(path.is_file() and not path.is_symlink(), 'Missing/nonregular epoch payload: ' + str(path))
    require(path.stat().st_size <= 1024**3, 'Epoch payload exceeds 1 GiB safety limit')
    return path.read_bytes()


def _lines(raw):
    require(raw.endswith(b'\n') and raw.strip(), 'Incomplete/empty state payload')
    from io import BytesIO
    for line in BytesIO(raw):
        require(bool(line.strip()), 'Empty state record')
        yield decode(line)


def _validate(source, manifest, models_raw, states_raw):
    from wenu.astrometric_state import AngularMotionRow, SpaceMotionRow, validate_space_motion_domain
    _keys(manifest, ('schema', 'complete', 'event', 'motion_identity', 'code_identity', 'products'))
    require(manifest['schema'] == SCHEMA and manifest['complete'] is True, 'Unsupported/incomplete stellar epoch')
    event = _time(manifest['event'])
    require(event.scale == 'tcb', 'Stellar epoch must retain TCB event')
    require(manifest['code_identity'] == _code_identity(), 'Stellar epoch code identity differs')
    motion = manifest['motion_identity']
    _keys(motion, ('epoch', 'model_order', 'models', 'source_manifest_sha256', 'input_document_sha256'))
    require(_time(motion['epoch']) == event and
            motion['source_manifest_sha256'] == sha256(source.manifest).hexdigest(), 'Epoch source/event binding differs')
    digest = motion['input_document_sha256']
    require(digest is None or (type(digest) is str and len(digest) == 64 and
            all(c in '0123456789abcdef' for c in digest)), 'Invalid motion document identity')
    originals = tuple(source.records())
    ids = tuple(r['identity']['identifier'] for r in originals)
    models = decode(models_raw)
    require(type(models) is list and models and len(models) == len(motion['models']), 'Missing epoch models')
    require(motion['model_order'] == [m['policy'] for m in motion['models']] and
            len(set(motion['model_order'])) == len(models), 'Invalid model order')
    lookups = []
    for model, declared in zip(models, motion['models'], strict=True):
        _keys(model, ('admission', 'kind', 'coefficients', 'references'))
        _keys(declared, ('policy', 'identity_sha256', 'admission'))
        admission = model['admission']
        require(admission == declared['admission'] and sha256(encode(admission)).hexdigest() ==
                declared['identity_sha256'], 'Epoch model admission identity differs')
        policy = declared['policy']
        full = policy == 'full-input-rectilinear'
        require(policy in ('full-input-rectilinear', 'proper-motion-angular', 'hipparcos2-angular-fallback') and
                model['kind'] == ('cartesian-affine' if full else 'angular-affine'), 'Invalid epoch model representation')
        require(admission['source_manifest_sha256'] == motion['source_manifest_sha256'], 'Wrong model source')
        coverage = TimeSpan(*(TimePoint(*t) for t in admission['coverage']))
        require(coverage.contains(event), 'Epoch outside admitted domain')
        coefficients = model['coefficients']
        require(type(coefficients) is list and [r['identifier'] for r in coefficients] == list(ids), 'Wrong coefficient HIP order')
        values = []
        rows = {}
        for row in coefficients:
            _keys(row, ('identifier', 'source_epoch', 'initial', 'derivative', 'unavailable_reason'))
            epoch = None if row['source_epoch'] is None else TimePoint(*row['source_epoch'])
            typed = (SpaceMotionRow if full else AngularMotionRow)(row['identifier'], epoch,
                row['initial'], row['derivative'], row['unavailable_reason'])
            validate_space_motion_domain(typed, coverage)
            rows[row['identifier']] = row
            values.append([row['identifier'], row['source_epoch'], row['initial'], row['derivative'], row['unavailable_reason']])
        key = 'si_solutions_sha256' if full else 'angular_solutions_sha256'
        require(sha256(encode(values)).hexdigest() == admission[key], 'Original coefficients differ from admission')
        references = model['references']
        _keys(references, ('direction', 'cartesian') if full else ('direction',))
        for representation, record in references.items():
            reference = ReferenceSpec(**record)
            require(reference.frame_id == 'icrs' and reference.origin_id == 'solar-system-barycenter'
                    and reference.status == 'nominal-astrometric' and reference.equinox is None
                    and reference.representation == representation and reference.units ==
                    ('rad' if representation == 'direction' else 'm,m/s'), 'Invalid model reference')
        lookups.append(rows)
    namespace = source.metadata['baseline']['catalogue']
    count = 0
    for count, (record, hip) in enumerate(zip(_lines(states_raw), ids, strict=True), 1):
        _keys(record, ('identifier', 'model_index', 'status', 'reasons', 'direction', 'cartesian'))
        require(record['identifier'] == hip, 'Wrong state HIP order')
        reasons = []
        chosen = None
        for i, rows in enumerate(lookups):
            reason = rows[hip]['unavailable_reason']
            if reason is None:
                chosen = i
                break
            reasons.append(motion['model_order'][i] + ':' + reason)
        require(record['model_index'] == chosen and
                (chosen is None or type(record['model_index']) is int), 'Wrong model priority')
        require(record['reasons'] == reasons, 'Wrong model gap reasons')
        if chosen is None:
            require(record['status'] == 'unavailable' and record['direction'] is None and
                    record['cartesian'] is None, 'Gap advertises an evaluated state')
            continue
        require(record['status'] == 'evaluated', 'Available model lacks state')
        direction = _state(record['direction'])
        row = lookups[chosen][hip]
        source_event = None if row['source_epoch'] is None else TimePoint(*row['source_epoch'])
        full = models[chosen]['kind'] == 'cartesian-affine'
        require((record['cartesian'] is not None) == full, 'Invalid Cartesian capability')
        states = [direction] + ([_state(record['cartesian'], cartesian=True)] if full else [])
        for state in states:
            require(state.object_key.value == namespace + ':' + hip and
                    state.time == state.anchor_time == event and state.source_epoch == source_event and
                    state.reference.frame_id == 'icrs' and state.reference.origin_id == 'solar-system-barycenter' and
                    state.reference.status == 'nominal-astrometric' and
                    asdict(state.reference) == models[chosen]['references'][state.reference.representation],
                    'State identity/event/reference differs')
        require(direction.certificate_id is None, 'Exact epoch cannot advertise a temporal certificate')
    require(count == len(ids), 'Incomplete state population')


@dataclass(frozen=True, slots=True)
class StellarEpochCatalogue:
    """Validated immutable bytes; accessors return detached data, not live states."""
    source: StellarEnrichmentSnapshot
    manifest: bytes
    models_payload: bytes
    states_payload: bytes

    def __post_init__(self):
        require(type(self.source) is StellarEnrichmentSnapshot and
                all(type(b) is bytes for b in (self.manifest, self.models_payload, self.states_payload)),
                'Epoch catalogue requires immutable validated source/bytes')
        manifest = decode(self.manifest)
        _keys(manifest, ('schema', 'complete', 'event', 'motion_identity', 'code_identity', 'products'))
        require(type(manifest['products']) is dict, 'Invalid epoch payload inventory')
        payloads = {'models.json': self.models_payload, 'states.jsonl': self.states_payload,
                    'source/source_manifest_v1.json': self.source.manifest,
                    **{'source/' + n: b for n, b in self.source.products}}
        require(set(manifest['products']) == set(PAYLOADS) and all(
            identity(raw) == manifest['products'][name] for name, raw in payloads.items()), 'Epoch payload identity differs')
        try:
            _validate(self.source, manifest, self.models_payload, self.states_payload)
        except (KeyError, TypeError, OverflowError, KernelError) as error:
            raise ValueError('Invalid stellar epoch record') from error

    @property
    def instant(self):
        return _time(decode(self.manifest)['event'])

    def rows(self):
        return _lines(self.states_payload)

    def models(self):
        return decode(self.models_payload)

    def at(self, instant, identifiers=None):
        require(type(instant) is TimePoint and instant == self.instant, 'Exact saved TCB event required; advancement is not admitted')
        if identifiers is None:
            return tuple(self.rows())
        ids = tuple(identifiers)
        require(all(type(i) is str for i in ids) and len(ids) == len(set(ids)), 'Unique source HIP strings required')
        wanted = set(ids)
        found = {r['identifier']: r for r in self.rows() if r['identifier'] in wanted}
        require(set(found) == set(ids), 'Unknown epoch HIP')
        return tuple(found[i] for i in ids)


def load_stellar_epoch(directory, *, expected_manifest_sha256=None):
    """Read exact data only, with no provider construction, evaluation or network."""
    root = Path(directory)
    require(root.is_dir() and not root.is_symlink() and not (root/'source').is_symlink(), 'Invalid epoch directory')
    raw = _read(root/'manifest.json')
    if expected_manifest_sha256 is not None:
        require(sha256(raw).hexdigest() == expected_manifest_sha256, 'Epoch manifest identity differs')
    source = StellarEnrichmentSnapshot(tuple((n, _read(root/'source'/n)) for n in PRODUCTS),
                                      _read(root/'source/source_manifest_v1.json'))
    return StellarEpochCatalogue(source, raw, _read(root/'models.json'), _read(root/'states.jsonl'))


def prepare_stellar_epoch(request, destination):
    """Evaluate existing admitted models once; publish a validated new local bundle."""
    from wenu.stellar_state import (
        StellarMotionProvider, StellarMotionRequest, stellar_model_selection, stellar_motion_identity,
    )
    from wenu_kernel import Kernel
    from wenu_kernel.records import AccuracyRequest, SessionPolicy, StateQuery
    require(type(request) is StellarMotionRequest, 'An admitted stellar motion request is required')
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Epoch destination exists; choose a new revision')
    require(destination.parent.is_dir(), 'Epoch destination parent must exist')
    code = _code_identity()
    selection = stellar_model_selection(request)
    evaluated = {}
    references = [{} for _ in request.catalogues]
    for index, catalogue in enumerate(request.catalogues):
        chosen = tuple(hip for hip, selected, _ in selection if selected == index)
        for representation in ('direction', 'cartesian') if catalogue.motion_policy == 'full-input-rectilinear' else ('direction',):
            provider = StellarMotionProvider(catalogue, representation=representation)
            try:
                admission = provider.describe().admissions[0]
                references[index][representation] = asdict(admission.reference)
                if not chosen:
                    continue
                by_hip = {k.value.rsplit(':', 1)[1]: k for k in admission.objects}
                query = StateQuery(admission.catalogue, admission.model, tuple(by_hip[h] for h in chosen),
                    (request.instant,), admission.reference,
                    AccuracyRequest(metric='euclidean_norm') if representation == 'cartesian' else AccuracyRequest(),
                    require_velocity=representation == 'cartesian')
                with Kernel(references=(admission.reference,)) as kernel:
                    kernel.register(provider, ownership='borrowed')
                    with kernel.open_session(SessionPolicy((admission.catalogue,))) as session:
                        batch = session.evaluate(query)
                for hip, state in zip(chosen, batch.states, strict=True):
                    evaluated.setdefault(hip, {})[representation] = asdict(state)
            finally:
                provider.close()
    models = []
    for index, catalogue in enumerate(request.catalogues):
        full = catalogue.motion_policy == 'full-input-rectilinear'
        models.append(dict(admission=catalogue.to_record(), references=references[index], kind='cartesian-affine' if full else 'angular-affine',
            coefficients=[dict(identifier=r.identifier,
                source_epoch=None if r.source_epoch is None else [r.source_epoch.jd1, r.source_epoch.jd2, r.source_epoch.scale],
                initial=r.position_m if full else r.direction,
                derivative=r.velocity_m_s if full else r.tangent_per_s,
                unavailable_reason=r.unavailable_reason) for r in catalogue.rows]))
    source = request.catalogues[0].source
    stage = Path(tempfile.mkdtemp(prefix='.wenu-stellar-epoch-', dir=destination.parent))
    reserved = False
    try:
        (stage/'source').mkdir()
        for name, raw in source.products:
            (stage/'source'/name).write_bytes(raw)
        (stage/'source/source_manifest_v1.json').write_bytes(source.manifest)
        (stage/'models.json').write_bytes(encode(models))
        with (stage/'states.jsonl').open('wb') as output:
            for hip, selected, reasons in selection:
                state = evaluated.get(hip, {})
                output.write(encode(dict(identifier=hip, model_index=selected,
                    status='unavailable' if selected is None else 'evaluated', reasons=list(reasons),
                    direction=state.get('direction'), cartesian=state.get('cartesian'))) + b'\n')
        require(_code_identity() == code, 'Epoch code changed during preparation')
        manifest = encode(dict(schema=SCHEMA, complete=True, event=asdict(request.instant),
            motion_identity=stellar_motion_identity(request), code_identity=code,
            products={name: identity((stage/name).read_bytes()) for name in PAYLOADS}))
        (stage/'manifest.json').write_bytes(manifest)
        load_stellar_epoch(stage, expected_manifest_sha256=sha256(manifest).hexdigest())
        destination.mkdir()
        reserved = True
        (destination/'source').mkdir()
        for name in PAYLOADS:
            os.link(stage/name, destination/name)
        os.link(stage/'manifest.json', destination/'manifest.json')
        reserved = False
        return sha256(manifest).hexdigest()
    finally:
        if reserved:
            shutil.rmtree(destination)
        shutil.rmtree(stage)
