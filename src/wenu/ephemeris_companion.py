"""Immutable exact-event geometric ephemeris data, separate from live resources.

Preparation borrows the existing offline ephemeris/SDK owners. Loading validates
data only, without importing a provider, reopening SPKs or evaluating an orbit.
"""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
import shutil
import tempfile

from wenu.ephemeris import EphemerisJulianDate, EphemerisStateRequest
from wenu_kernel.records import TimePoint, TimeSpan
from wenu_kernel.errors import KernelError

SCHEMA = 'wenu-ephemeris-companion/1'
POLICY = 'de440-then-de441-part1-then-part2/1'
REFERENCE = dict(frame='icrf', centre='0', status='geometric',
    coordinate_scale='tdb', position_unit='au', velocity_unit='au/day')
UNKNOWN_ERRORS = dict(measurement=None, physical_model=None, numerical=None)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _keys(value, names):
    _require(type(value) is dict and set(value) == set(names), 'Invalid companion fields')


def _encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, 'Duplicate JSON field')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def _digest(value):
    _require(type(value) is str and len(value) == 64 and
             all(c in '0123456789abcdef' for c in value), 'Invalid SHA-256')


def _strings(value):
    _require(type(value) is list and value and
             all(type(x) is str and x.strip() for x in value), 'Missing provenance')


def _time(value, scale):
    _keys(value, ('jd1', 'jd2', 'scale'))
    _require(value['scale'] == scale, 'Wrong companion time scale')
    event = TimePoint(**value)
    EphemerisJulianDate(event.jd1, event.jd2)
    return event


def _link(value, event):
    if value is None:
        return
    _keys(value, ('stellar_manifest_sha256', 'stellar_event', 'admission', 'conversion'))
    _digest(value['stellar_manifest_sha256'])
    source = _time(value['stellar_event'], 'tcb')
    from wenu.astrometric_coordinates import TcbTdbAdapter
    from wenu_kernel.time import TimeService
    admission = value['admission']
    _require(type(admission) is dict and 'validity' in admission, 'Missing time admission')
    domain = admission['validity']
    _keys(domain, ('start', 'stop'))
    adapter = TcbTdbAdapter(TimeSpan(_time(domain['start'], 'tcb'), _time(domain['stop'], 'tcb')))
    expected = _decode(_encode(asdict(adapter.describe())))
    _require(admission == expected, 'Unsupported time conversion admission')
    service = TimeService((adapter,), admissions=(adapter.describe(),))
    conversion = service.convert(source, 'tdb')
    _require(conversion.target == event and
             value['conversion'] == _decode(_encode(asdict(conversion))),
             'Time conversion receipt/event differs')


def _validate(manifest, raw):
    _keys(manifest, ('schema', 'complete', 'event', 'reference', 'selection',
                     'implementation', 'stellar_link', 'products'))
    _require(manifest['schema'] == SCHEMA and manifest['complete'] is True,
             'Unsupported/incomplete companion')
    event = _time(manifest['event'], 'tdb')
    _require(manifest['reference'] == REFERENCE, 'Wrong geometric reference/units')
    products = manifest['products']
    _keys(products, ('states.json',))
    _keys(products['states.json'], ('sha256', 'size_bytes'))
    _require(products['states.json'] == dict(sha256=sha256(raw).hexdigest(), size_bytes=len(raw)),
             'Companion payload identity differs')
    selection = manifest['selection']
    _keys(selection, ('model', 'part', 'path', 'sha256', 'coverage_jd', 'provenance',
                      'segments', 'policy', 'spatial_convention', 'axes_evidence'))
    _digest(selection['sha256'])
    _strings(selection['provenance'])
    _require((selection['model'], selection['part']) in
             (('DE440', 'full'), ('DE441', 'part-1'), ('DE441', 'part-2')) and
             selection['policy'] == POLICY and
             selection['spatial_convention'] == 'JPL TDB-compatible geometric ICRF' and
             selection['axes_evidence'] == 'SPK frame 1; JPL DE440/DE441 metadata explicitly admitted' and
             type(selection['path']) is str and Path(selection['path']).is_absolute(),
             'Invalid ephemeris model/part/convention')
    coverage = selection['coverage_jd']
    _require(type(coverage) is list and len(coverage) == 2 and
             all(type(x) in (int, float) and isfinite(x) for x in coverage) and
             coverage[0] < coverage[1], 'Invalid ephemeris coverage')
    from fractions import Fraction
    exact = Fraction(event.jd1) + Fraction(event.jd2)
    _require(coverage[0] <= exact <= coverage[1], 'Event outside selected coverage')
    segments = selection['segments']
    _require(type(segments) is list and segments, 'Missing SPK segment evidence')
    for segment in segments:
        _keys(segment, ('centre', 'target', 'frame', 'data_type', 'start_jd', 'end_jd'))
        _require(all(type(segment[k]) is int for k in ('centre', 'target', 'frame', 'data_type')) and
                 segment['frame'] == 1 and segment['data_type'] in (2, 3) and
                 all(type(segment[k]) in (int, float) and isfinite(segment[k])
                     for k in ('start_jd', 'end_jd')) and
                 segment['start_jd'] < segment['end_jd'], 'Invalid SPK segment')
    _require({(0, 3), (3, 399), (0, 10)} <=
             {(s['centre'], s['target']) for s in segments} and
             coverage == [max(s['start_jd'] for s in segments),
                          min(s['end_jd'] for s in segments)], 'Incomplete SPK path/coverage')
    implementation = manifest['implementation']
    _keys(implementation, ('sources', 'backends'))
    _keys(implementation['sources'], ('wenu.ephemeris', 'wenu.ephemeris_state',
        'wenu.skyfield_ephemeris', 'wenu.ephemeris_companion',
        'wenu_kernel.kernel', 'wenu_kernel.records'))
    for digest in implementation['sources'].values():
        _digest(digest)
    _keys(implementation['backends'], ('skyfield', 'jplephem', 'astropy', 'numpy'))
    _require(all(type(v) is str and v.strip() for v in implementation['backends'].values()),
             'Missing backend identity')
    _link(manifest['stellar_link'], event)
    rows = _decode(raw)
    _require(type(rows) is list and len(rows) == 2, 'Incomplete Earth/Sun companion')
    for target, row in zip(('399', '10'), rows, strict=True):
        _keys(row, ('target', 'centre', 'position_au', 'velocity_au_per_day',
                    'position_error_au', 'velocity_error_au_per_day', 'provenance'))
        _require(row['target'] == target and row['centre'] == '0', 'Wrong Earth/Sun identity')
        for field in ('position_au', 'velocity_au_per_day'):
            _require(type(row[field]) is list and len(row[field]) == 3 and
                     all(type(x) in (int, float) and isfinite(x) for x in row[field]),
                     'Invalid geometric PV')
        _require(row['position_error_au'] == UNKNOWN_ERRORS and
                 row['velocity_error_au_per_day'] == UNKNOWN_ERRORS,
                 'No ephemeris error certificate is admitted')
        _strings(row['provenance'])
        _require('returned kernel Cartesian state' in row['provenance'], 'Missing SDK transport evidence')


@dataclass(frozen=True, slots=True)
class EphemerisCompanion:
    """Validated immutable bytes; detached data-only exact-event access."""
    manifest: bytes
    states: bytes

    def __post_init__(self):
        _require(type(self.manifest) is bytes and type(self.states) is bytes,
                 'Immutable companion bytes required')
        try:
            _validate(_decode(self.manifest), self.states)
        except (KeyError, TypeError, OverflowError, KernelError) as error:
            raise ValueError('Invalid companion record') from error

    @property
    def instant(self):
        return _time(_decode(self.manifest)['event'], 'tdb')

    def at(self, instant, identifiers=('399', '10')):
        _require(type(instant) is TimePoint and instant == self.instant,
                 'Exact saved TDB event required; planetary reuse is not admitted')
        ids = tuple(identifiers)
        _require(all(type(i) is str and i in ('399', '10') for i in ids) and
                 len(set(ids)) == len(ids), 'Unique Earth/Sun NAIF identifiers required')
        rows = {r['target']: r for r in _decode(self.states)}
        return tuple(rows[i] for i in ids)


def load_ephemeris_companion(directory, *, expected_manifest_sha256=None):
    """Validate bytes only: no SPK, provider, network or stellar source needed."""
    root = Path(directory)
    _require(root.is_dir() and not root.is_symlink(), 'Invalid companion directory')
    def read(name):
        path = root/name
        _require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 1024**2,
                 'Missing/nonregular/oversize companion payload')
        return path.read_bytes()
    manifest = read('manifest.json')
    if expected_manifest_sha256 is not None:
        _digest(expected_manifest_sha256)
        _require(sha256(manifest).hexdigest() == expected_manifest_sha256,
                 'Companion manifest identity differs')
    return EphemerisCompanion(manifest, read('states.json'))


def prepare_ephemeris_companion(resources, instant, destination, *,
                                stellar_manifest=None, time_admission=None,
                                time_conversion=None):
    """Borrow validated open resources; evaluate Earth/Sun through the existing SDK.

    Optional linkage pins original stellar manifest bytes and an explicitly
    admitted TCB→TDB receipt. Accepted stellar products are never modified.
    """
    from wenu.skyfield_ephemeris import OfflineEphemerisResources
    from wenu.ephemeris_state import KernelEphemerisStateSource
    _require(type(resources) is OfflineEphemerisResources, 'Open pinned offline resources required')
    _require(type(instant) is TimePoint and instant.scale == 'tdb', 'Native TDB event required')
    event = EphemerisJulianDate(instant.jd1, instant.jd2)
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Companion destination exists; choose a new revision')
    _require(destination.parent.is_dir(), 'Companion parent must exist')
    link = None
    if stellar_manifest is not None:
        _require(type(stellar_manifest) is bytes and time_admission is not None and
                 time_conversion is not None, 'Stellar link requires manifest and conversion receipts')
        stellar = _decode(stellar_manifest)
        _require(stellar.get('schema') == 'wenu-stellar-epoch/1' and stellar.get('complete') is True,
                 'Invalid stellar manifest')
        link = _decode(_encode(dict(stellar_manifest_sha256=sha256(stellar_manifest).hexdigest(),
            stellar_event=stellar['event'], admission=asdict(time_admission),
            conversion=asdict(time_conversion))))
        _link(link, instant)
    else:
        _require(time_admission is None and time_conversion is None, 'Unlinked companion cannot claim a stellar receipt')
    source, selection = resources.select(event)
    routed = KernelEphemerisStateSource(source)
    rows = []
    for target in ('399', '10'):
        request = EphemerisStateRequest(target, '0', 'icrf', event, 'tdb')
        state = routed.state(request)
        _require(state.request == request and state.provider_target_id == target and
                 state.provider_centre_id == '0' and state.resource == source.resource and
                 state.resource.sha256 == selection['sha256'] and
                 (state.position_unit, state.velocity_unit) == ('au', 'au/day'),
                 'Ephemeris returned wrong identity/reference/units')
        rows.append(dict(target=target, centre='0', position_au=list(state.position),
            velocity_au_per_day=list(state.velocity), position_error_au=UNKNOWN_ERRORS.copy(),
            velocity_error_au_per_day=UNKNOWN_ERRORS.copy(), provenance=list(state.provenance)))
    raw = _encode(rows)
    from importlib import import_module, metadata
    names = ('wenu.ephemeris', 'wenu.ephemeris_state', 'wenu.skyfield_ephemeris',
             'wenu.ephemeris_companion', 'wenu_kernel.kernel', 'wenu_kernel.records')
    implementation = dict(sources={n: sha256(Path(import_module(n).__file__).read_bytes()).hexdigest()
                                   for n in names},
        backends={n: metadata.version(n) for n in ('skyfield', 'jplephem', 'astropy', 'numpy')})
    manifest = _encode(dict(schema=SCHEMA, complete=True, event=asdict(instant), reference=REFERENCE,
        selection=selection, implementation=implementation, stellar_link=link,
        products={'states.json': dict(sha256=sha256(raw).hexdigest(), size_bytes=len(raw))}))
    EphemerisCompanion(manifest, raw)
    stage = Path(tempfile.mkdtemp(prefix='.wenu-ephemeris-', dir=destination.parent))
    reserved = False
    try:
        (stage/'states.json').write_bytes(raw)
        (stage/'manifest.json').write_bytes(manifest)
        load_ephemeris_companion(stage, expected_manifest_sha256=sha256(manifest).hexdigest())
        destination.mkdir()
        reserved = True
        os.link(stage/'states.json', destination/'states.json')
        os.link(stage/'manifest.json', destination/'manifest.json')
        reserved = False
        return sha256(manifest).hexdigest()
    finally:
        if reserved:
            shutil.rmtree(destination)
        shutil.rmtree(stage)
