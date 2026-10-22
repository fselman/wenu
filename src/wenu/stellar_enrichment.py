"""Immutable, data-only multi-edition stellar input snapshots.

No catalogue acquisition, state provider, distance inference or propagation.
The source-native loader remains in stellar_catalogue; this codec preserves
linked editions and explicit gaps without admitting a physical model.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path

PRODUCTS = ('metadata_v1.json', 'stars_v1.jsonl', 'gaia_sources_v1.jsonl',
            'hipparcos2_sources_v1.jsonl', 'candidate_evidence_v1.jsonl')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON field: ' + key)
        result[key] = value
    return result


def _constant(value):
    raise ValueError('Non-finite JSON value: ' + value)


def _floating(value):
    result = float(value)
    require(isfinite(result), 'Non-finite JSON number')
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=_object, parse_constant=_constant, parse_float=_floating)


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def identity(raw):
    return {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}


def _id(value):
    require(type(value) is str and value.isascii() and value.isdigit()
            and int(value) > 0 and str(int(value)) == value, 'Invalid decimal-string identifier')
    return value


def _records(raw):
    rows = [decode(line) for line in raw.splitlines()]
    require(all(type(row) is dict for row in rows), 'Snapshot records must be JSON objects')
    return rows


def _number(value):
    return value is None or type(value) in (int, float)


@dataclass(frozen=True, slots=True)
class StellarEnrichmentSnapshot:
    """Validated immutable bytes; iterators return detached records on each read."""
    products: tuple
    manifest: bytes

    def __post_init__(self):
        require(type(self.products) is tuple and all(type(p) is tuple and len(p) == 2
                and type(p[0]) is str and type(p[1]) is bytes for p in self.products)
                and type(self.manifest) is bytes, 'Snapshot requires immutable product bytes')
        require(tuple(name for name, _ in self.products) == PRODUCTS, 'Unknown snapshot product schema')
        document = decode(self.manifest)
        require(type(document) is dict and document.get('schema') == 'wenu-stellar-enrichment-snapshot/1'
                and document.get('complete') is True and set(document['products']) == set(PRODUCTS),
                'Incomplete/unknown stellar snapshot')
        raw = dict(self.products)
        for name, payload in self.products:
            require(identity(payload) == document['products'][name], 'Snapshot product digest differs: ' + name)
        metadata = decode(raw[PRODUCTS[0]])
        require(type(metadata) is dict and metadata.get('schema') == 'wenu-stellar-enrichment-metadata/1'
                and metadata.get('row_schema') == 'wenu-stellar-enrichment/1'
                and metadata.get('model_admission') == 'none', 'Unsupported enrichment metadata')
        baseline = metadata['baseline']
        require(len(metadata['original_columns']) == len(set(metadata['original_columns']))
                and set(metadata['required_preserved_columns']) <= set(metadata['original_columns']),
                'Required original columns missing or duplicated')
        require(metadata['original_metadata']['source_sha256'] == baseline['source_sha256'],
                'Original source identity differs')
        for key in ('catalogue', 'edition'):
            require(metadata['original_metadata'][key] == baseline[key], 'Original edition differs')
        original_reference = metadata['original_metadata']
        require(original_reference['frame'] == 'icrs'
                and original_reference['origin'] == 'solar-system-barycenter'
                and original_reference['epoch']['format'] == 'jyear'
                and original_reference['epoch']['scale'] in ('tt', 'tcb', 'tdb'),
                'Unsupported original source reference')
        for key, expected in {'ra_degrees':'deg','dec_degrees':'deg','ra_hours':'hourangle',
                              'ra_mas_per_year':'mas/yr','dec_mas_per_year':'mas/yr',
                              'parallax_mas':'mas','epoch_year':'Julian year','magnitude':'mag'}.items():
            if key in metadata['original_columns']:
                require(original_reference['units'].get(key) == expected,
                        'Unsupported original source unit: ' + key)
        reference = metadata['gaia_reference']
        require(reference['frame'] == 'icrs' and reference['origin'] == 'solar-system-barycenter'
                and reference['epoch_scale'] == 'tcb' and reference['release'] == 'DR3'
                and reference['right_ascension_motion'] == 'mu_alpha*cos(delta)',
                'Unsupported Gaia source reference')
        units = metadata['gaia_column_units']
        require(set(units) == set(metadata['gaia_columns']), 'Missing Gaia unit metadata')
        for key, expected in {'ra':'deg', 'dec':'deg', 'ref_epoch':'yr', 'parallax':'mas',
                              'pmra':'mas / yr', 'pmdec':'mas / yr'}.items():
            require(units.get(key) == expected, 'Unsupported Gaia column unit: ' + key)
        for key, expected in {'ra_error':'mas','dec_error':'mas','parallax_error':'mas',
                              'pmra_error':'mas / yr','pmdec_error':'mas / yr',
                              'radial_velocity':'km / s','radial_velocity_error':'km / s'}.items():
            if key in metadata['gaia_columns']:
                require(units.get(key) == expected, 'Unsupported Gaia column unit: ' + key)
        require(metadata['original_metadata']['units'].get('magnitude') == 'mag',
                'Original visual magnitude unit missing')
        hip_profile = metadata['hipparcos2_profile']
        href = hip_profile['reference']
        require(href['frame'] == 'icrs' and href['origin'] == 'solar-system-barycenter'
                and href['epoch']['format'] == 'jyear'
                and href['epoch']['scale'] in (None, 'tt', 'tcb', 'tdb'), 'Unsupported Hip2 reference')
        for key, expected in {'RArad':'rad','DErad':'rad','Plx':'mas',
                              'pmRA':'mas/yr','pmDE':'mas/yr'}.items():
            require(hip_profile['columns'][key]['unit'] == expected, 'Unsupported Hip2 unit: ' + key)
        stars = _records(raw[PRODUCTS[1]])
        gaia = _records(raw[PRODUCTS[2]])
        hip2 = _records(raw[PRODUCTS[3]])
        candidates = _records(raw[PRODUCTS[4]])
        members = [_id(r['identity']['identifier']) for r in stars]
        require(len(members) == len(set(members)) == baseline['rows'], 'Snapshot membership differs')
        require(sha256(('\n'.join(members) + '\n').encode()).hexdigest()
                == baseline['ordered_hip_ids_sha256'], 'Snapshot membership order differs')
        population = set(members)
        gaia_ids = [_id(s['source_id']) for s in gaia]
        require(len(set(gaia_ids)) == len(gaia_ids), 'Duplicate Gaia snapshot source')
        source_map = dict(zip(gaia_ids, gaia))
        for source in gaia:
            _id(source['solution_id'])
            require(set(source) == set(metadata['gaia_columns']), 'Gaia source column schema differs')
            require(all(_number(source[k]) for k in ('ra','dec','ref_epoch','pmra','pmdec','parallax')),
                    'Invalid Gaia parameter encoding')
            require(source['ref_epoch'] == reference['expected_ref_epoch'], 'Gaia epoch differs')
            require(source['ra'] is None or 0 <= source['ra'] < 360, 'Invalid Gaia longitude')
            require(source['dec'] is None or abs(source['dec']) <= 90, 'Invalid Gaia latitude')
        hids = [_id(r['HIP']) for r in hip2]
        require(len(hids) == len(set(hids)) and set(hids) <= population, 'Duplicate/foreign Hip2 entry')
        hip2_map = dict(zip(hids, hip2))
        for row in hip2:
            native = row['original_record_ascii'].encode('ascii')
            require(len(native) == metadata['hipparcos2_profile']['record_length']
                    and sha256(native).hexdigest() == row['record_sha256']
                    and str(int(native[:6])) == row['HIP'], 'Hip2 original record differs')
            for name, spec in metadata['hipparcos2_profile']['columns'].items():
                field = native[spec['first_byte']-1:spec['last_byte']].strip()
                if name == 'HIP':
                    value = str(int(field))
                elif name == 'UW':
                    value = [float(native[i:i+7]) for i in
                             range(spec['first_byte']-1, spec['last_byte'], 7)]
                elif spec['kind'] == 'integer':
                    value = int(field)
                else:
                    value = float(field) if field else None
                require(value == row[name], 'Hip2 parsed field differs from original bytes: ' + name)
        pairs = set()
        by_hip = defaultdict(set)
        referenced = set()
        for row in candidates:
            pair = (_id(row['hip']), _id(row['source_id']))
            require(pair[0] in population and pair[1] in source_map and pair not in pairs,
                    'Duplicate/foreign candidate identity')
            pairs.add(pair)
            by_hip[pair[0]].add(pair[1])
            referenced.add(pair[1])
        magnitudes, choices = [], Counter()
        original_digest, association_digest = sha256(), sha256()
        associations = 0
        for row in stars:
            key = row['identity']['identifier']
            require(row['schema'] == metadata['row_schema']
                    and row['identity'] == {'catalogue':baseline['catalogue'], 'edition':baseline['edition'],
                                           'identifier':key, 'component':None}, 'Membership identity differs')
            original = row['original']
            require(set(original) == set(metadata['original_columns']) and original['hip'] == key,
                    'Original source columns/identity differ')
            if 'epoch_year' in original:
                require(original['epoch_year'] == original_reference['epoch']['value'],
                        'Original row epoch differs')
            for name in ('ra_degrees','dec_degrees','ra_mas_per_year','dec_mas_per_year','parallax_mas'):
                if name in original:
                    require(_number(original[name]), 'Invalid original numeric field: ' + name)
            require(original.get('ra_degrees') is None or 0 <= original['ra_degrees'] < 360,
                    'Original longitude outside domain')
            require(original.get('dec_degrees') is None or abs(original['dec_degrees']) <= 90,
                    'Original latitude outside domain')
            original_digest.update(encode(original)+b'\n')
            association_digest.update(encode({'hip':key,'association':row['published_association']})+b'\n')
            value = original['magnitude']
            require(_number(value), 'Invalid visual magnitude')
            magnitudes.append([int(key), 'missing' if value is None else float(value).hex()])
            require(row['adopted_solution'] is None, 'Snapshot cannot adopt an astrometric model')
            require(row['input_availability']['model_adopted'] is False,
                    'Source availability cannot adopt a model')
            require(all(_id(sid) in source_map for sid in row['candidates'])
                    and len(row['candidates']) == len(set(row['candidates'])), 'Invalid candidate references')
            require(by_hip[key] <= set(row['candidates']),
                    'Missing per-HIP candidate evidence')
            association = row['published_association']
            source = None
            if association is not None:
                sid = _id(association['source_id'])
                require(association['catalogue'] == 'Gaia' and association['hip'] == key
                        and sid in source_map and sid in row['candidates'], 'Invalid published association')
                require(association['release'] in ('DR3','EDR3'), 'Unsupported associated Gaia release')
                if association['release'] == 'EDR3':
                    bridge = association['equivalent_dr3_identity']
                    require(bridge['release'] == 'DR3' and bridge['source_id'] == sid
                            and bridge['bridge']['policy'] == 'ESA-explicit-identical-source-list',
                            'Missing EDR3/DR3 identity bridge')
                source = source_map[sid]
                referenced.add(sid)
                associations += 1
            require(row['match_status'] == ('identified' if association else 'unmatched'),
                    'Association status differs')
            require(row['source_references'] == {'gaia':association['source_id'] if association else None,
                    'hipparcos2':key if key in hip2_map else None}, 'Source row references differ')
            full = source is not None and source.get('astrometric_params_solved') in (31,95)
            full = full and all(source.get(k) is not None for k in ('ra','dec','ref_epoch','parallax','pmra','pmdec'))
            hrow = hip2_map.get(key)
            hfull = hrow is not None and all(hrow.get(k) is not None for k in ('RArad','DErad','Plx','pmRA','pmDE'))
            choice = 'gaia' if full else 'hipparcos2' if hfull else 'original_1997_lookup'
            require(row['input_availability']['preferred_available_input'] == choice,
                    'Fallback availability differs')
            choices[choice] += 1
            expected_photometry = ({k:v for k,v in source.items() if k.startswith('phot_')}
                                   if source else None)
            require(row['foreign_photometry'] == expected_photometry, 'Foreign photometry differs')
        require(set(gaia_ids) == referenced, 'Unreferenced or missing Gaia snapshot sources')
        require(original_digest.hexdigest() == metadata['original_rows_sha256'],
                'Original loaded source fields differ')
        require(association_digest.hexdigest() == metadata['association_ledger_sha256'],
                'Published association ledger differs')
        require(sha256(json.dumps(magnitudes, separators=(',', ':')).encode()).hexdigest()
                == baseline['hip_magnitude_pairs_sha256'], 'Original visual photometry differs')
        counts = {'retained_hip_rows':len(stars), 'published_associations':associations,
                  'gaia_source_rows':len(gaia), 'hipparcos2_rows':len(hip2),
                  'candidate_pairs':len(candidates), 'preferred_available_inputs':dict(choices)}
        require(counts == metadata['counts'], 'Snapshot coverage counts differ')

    @property
    def metadata(self):
        return decode(self.products[0][1])

    def records(self, product='stars_v1.jsonl'):
        require(product in PRODUCTS[1:], 'Unknown snapshot record product')
        payload = dict(self.products)[product]
        for line in payload.splitlines():
            yield decode(line)


def load_stellar_enrichment(directory, *, expected_manifest_sha256=None):
    """Read and verify a self-contained local snapshot; never acquire anything."""
    root = Path(directory)
    manifest = (root / 'source_manifest_v1.json').read_bytes()
    if expected_manifest_sha256 is not None:
        require(sha256(manifest).hexdigest() == expected_manifest_sha256, 'Snapshot manifest identity differs')
    # Names are fixed by this schema, never taken from untrusted manifest paths.
    return StellarEnrichmentSnapshot(tuple((name, (root/name).read_bytes()) for name in PRODUCTS), manifest)
