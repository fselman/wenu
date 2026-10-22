#!/usr/bin/env python3
"""Explicit resumable capture of missing Gaia parameters and Hipparcos-2.

Raw source capture only. Run the separate offline audit to report availability.
No automatic retries, matching, propagation or production catalogue changes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import gzip
import json
from pathlib import Path
import tempfile
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
import xml.etree.ElementTree as ET

from astropy.table import Table, vstack

import gaia_crossmatch_audit as audit

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'docs/developer/data/stellar_astrometry_acquisition_v1.json'
ENDPOINT = 'https://gea.esac.esa.int/tap-server/tap'
CAP = 64 * 1024 * 1024
TOTAL_CAP = 512 * 1024 * 1024
BATCH = 500


def digest(raw):
    return {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def association_digest(rows):
    return sha256(canonical([{'hip': r['hip'], 'original': r['original'],
        'published_association': r['published_association']} for r in rows])).hexdigest()


def atomic_write(path, raw):
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.' + path.name, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(raw)
            stream.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def read_bounded(stream, cap=CAP):
    raw = stream.read(cap + 1)
    audit.require(len(raw) <= cap, 'Response exceeds byte cap')
    return raw


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Redirect refused; review the provider route')


def request(url, data=None):
    req = Request(url, data=None if data is None else urlencode(data).encode(),
        headers={'User-Agent': 'Wenu-stellar-astrometry/1', 'Accept-Encoding': 'identity'})
    # No retry: HTTP 429/503/Retry-After and DNS/timeouts stop this invocation.
    with build_opener(NoRedirect()).open(req, timeout=60) as response:
        audit.require(response.status == 200 and response.geturl() == url,
                      'Unexpected provider response')
        raw = read_bounded(response)
        length = response.headers.get('Content-Length')
        audit.require(length is None or int(length) == len(raw), 'Truncated provider response')
        return raw, {'url': url, 'status': 200, 'method': 'GET' if data is None else 'POST',
            'utc': datetime.now(timezone.utc).isoformat(),
            'content_type': response.headers.get('Content-Type'),
            'last_modified': response.headers.get('Last-Modified'),
            'etag': response.headers.get('ETag')}


def votable(raw):
    root = ET.fromstring(raw)
    status = [e.attrib.get('value') for e in root.iter()
              if e.tag.split('}')[-1] == 'INFO' and e.attrib.get('name') == 'QUERY_STATUS']
    audit.require(bool(status) and all(s == 'OK' for s in status),
                  'Missing/failed/overflow TAP QUERY_STATUS')
    return Table.read(BytesIO(raw), format='votable')


def query(sql, maxrec):
    return request(ENDPOINT + '/sync', dict(REQUEST='doQuery', LANG='ADQL',
        FORMAT='votable', MAXREC=str(maxrec), QUERY=sql))


def validate_gaia(table, ids, columns, reference):
    audit.require(table.colnames == columns, 'Gaia column schema differs')
    returned = [audit.identifier(x) for x in table['source_id']]
    audit.require(len(set(returned)) == len(returned) and set(returned) == set(ids),
                  'Gaia returned duplicate, foreign or missing IDs')
    list(audit.table_rows(table, ('source_id', 'solution_id')))
    audit.check_units(table, {'ra': 'deg', 'dec': 'deg', 'ref_epoch': 'yr',
        'parallax': 'mas', 'pmra': 'mas/yr', 'pmdec': 'mas/yr',
        'ra_error': 'mas', 'dec_error': 'mas', 'parallax_error': 'mas',
        'pmra_error': 'mas/yr', 'pmdec_error': 'mas/yr',
        'radial_velocity': 'km/s', 'radial_velocity_error': 'km/s'})
    epoch = reference['epoch']
    audit.require(reference['frame'] == 'icrs' and reference['origin'] == 'solar-system-barycenter'
                  and epoch['format'] == 'jyear' and epoch['scale'] == 'tcb',
                  'Unsupported Gaia source reference')
    audit.require(all(audit.scalar(x) == epoch['value'] for x in table['ref_epoch']),
                  'Unexpected Gaia reference epoch')


def validate_metadata(raw, columns):
    table = votable(raw)
    audit.require(table.colnames == ['column_name', 'datatype', 'unit', 'ucd', 'description'],
                  'Gaia metadata schema differs')
    returned = [str(v) for v in table['column_name']]
    audit.require(len(returned) == len(set(returned)) and set(returned) == set(columns),
                  'Missing/duplicate Gaia column metadata')
    for row in table:
        if str(row['column_name']) in ('source_id', 'solution_id'):
            audit.require(str(row['datatype']).lower() in ('long', 'bigint', 'int8'),
                          'Gaia identifier metadata is not integer')


def verify_product(root, name, record):
    audit.require(Path(name).name == name and name not in ('.', '..'), 'Unsafe product path')
    raw = (root / name).read_bytes()
    audit.require(digest(raw) == record, 'Changed capture product: ' + name)
    return raw


def verified_report(root, contract):
    payload = (root / 'audit_manifest_v3.json').read_bytes()
    manifest = json.loads(payload)
    audit.require(manifest.get('schema') == 'wenu-gaia-candidate-audit/3'
                  and manifest.get('complete') is True, 'Incomplete v3 association report')
    audit.require({'hip_review_v3.jsonl', 'summary_v3.json', 'published_associations_v3.jsonl'}
                  <= manifest['products'].keys(), 'Missing v3 report products')
    for name, record in manifest['products'].items():
        verify_product(root, name, record)
    rows = [json.loads(line) for line in (root / 'hip_review_v3.jsonl').read_text().splitlines()]
    ids = [r['hip'] for r in rows]
    audit.require(all(type(i) is str and i.isascii() and i.isdigit() and int(i) > 0 for i in ids),
                  'Invalid retained HIP identifiers')
    baseline = contract['baseline']
    audit.require(len(ids) == len(set(ids)) == baseline['rows']
        and sha256(('\n'.join(ids) + '\n').encode()).hexdigest() == baseline['ordered_hip_ids_sha256'],
        'Association report membership differs')
    photometry = [[int(r['hip']), 'missing' if r['original']['magnitude'] is None
                   else float(r['original']['magnitude']).hex()] for r in rows]
    audit.require(sha256(json.dumps(photometry, separators=(',', ':')).encode()).hexdigest()
                  == baseline['hip_magnitude_pairs_sha256'], 'Report visual photometry differs')
    summary = json.loads((root / 'summary_v3.json').read_text())
    ledger = [r['published_association'] for r in rows if r['published_association'] is not None]
    audit.require(ledger == [json.loads(line) for line in
        (root / 'published_associations_v3.jsonl').read_text().splitlines()], 'Association ledger differs')
    audit.require(len(ledger) == summary['retained_published_associations'], 'Association count differs')
    for row in rows:
        a = row['published_association']
        if a is None:
            continue
        sid = a['source_id']
        audit.require(type(sid) is str and sid.isascii() and sid.isdigit() and int(sid) > 0
                      and a['hip'] == row['hip'] and a['catalogue'] == 'Gaia', 'Invalid Gaia identity')
        if a['release'] == 'EDR3':
            bridge = a['equivalent_dr3_identity']
            audit.require(bridge['release'] == 'DR3' and bridge['source_id'] == sid
                and bridge['bridge']['policy'] == 'ESA-explicit-identical-source-list',
                'Missing explicit EDR3/DR3 bridge')
        else:
            audit.require(a['release'] == 'DR3', 'Unsupported association release')
    return rows, summary, sha256(payload).hexdigest()


def plan(rows, sources, columns, cache_digest, profile_payload):
    known = {audit.identifier(x) for x in sources['source_id']}
    required = {r['published_association']['source_id'] for r in rows if r['published_association']}
    return {'schema': 'wenu-stellar-astrometry-plan/1',
        'association_sha256': association_digest(rows), 'download_manifest_sha256': cache_digest,
        'profile_sha256': sha256(profile_payload).hexdigest(), 'columns': columns,
        'required_ids': sorted(required, key=int), 'missing_ids': sorted(required - known, key=int),
        'reused_source_ids': sorted(required & known, key=int), 'batch_size': BATCH,
        'endpoint': ENDPOINT}


def capture(output, identity, profile, *, transport=request, tap=query):
    """Checkpoint only complete validated products; resume identical plans only."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    plan_path = output / 'capture_plan_v1.json'
    if plan_path.exists():
        audit.require(plan_path.read_bytes() == canonical(identity), 'Capture plan differs')
    else:
        audit.require(not list(output.iterdir()), 'Unknown capture directory; choose a new path')
        atomic_write(plan_path, canonical(identity))
    products, receipts = {}, {}

    def obtain(name, loader, validator):
        receipt_path = output / (name + '.receipt.json')
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
            raw = verify_product(output, name, receipt['product'])
        else:
            raw, http = loader()
            validator(raw)
            audit.require(sum(v['bytes'] for v in products.values()) + len(raw) <= TOTAL_CAP,
                          'Capture total byte cap exceeded')
            receipt = {'product': digest(raw), 'http': http}
            atomic_write(output / name, raw)
            atomic_write(receipt_path, canonical(receipt))
        validator(raw)
        products[name], receipts[name] = digest(raw), receipt
        audit.require(sum(v['bytes'] for v in products.values()) <= TOTAL_CAP,
                      'Capture total byte cap exceeded')
        return raw

    for resource in profile['hipparcos2']['resources']:
        def validate(raw, spec=resource):
            audit.require(digest(raw) == {k: spec[k] for k in ('bytes', 'sha256')},
                          'Hipparcos-2 source identity differs')
        obtain(resource['filename'], lambda spec=resource: transport(spec['url']), validate)
    compressed = (output / 'hip2.dat.gz').read_bytes()
    with gzip.GzipFile(fileobj=BytesIO(compressed)) as stream:
        expanded = read_bounded(stream)
    audit.require(digest(expanded) == profile['hipparcos2']['expanded_table'],
                  'Expanded Hipparcos-2 source differs')
    audit.parse_hipparcos2(expanded, (output / 'ReadMe').read_bytes(), profile['hipparcos2'])
    atomic_write(output / 'hip2.dat', expanded)
    products['hip2.dat'] = digest(expanded)

    columns = identity['columns']
    names = ','.join("'" + c + "'" for c in columns)
    metadata_sql = ('SELECT column_name,datatype,unit,ucd,description FROM TAP_SCHEMA.columns '
                    "WHERE table_name='gaiadr3.gaia_source' AND column_name IN (" + names + ')')
    obtain('gaia_column_metadata_v1.vot', lambda: tap(metadata_sql, len(columns)+1),
           lambda raw: validate_metadata(raw, columns))

    missing, batches = identity['missing_ids'], []
    audit.require(len(missing) <= 118218 and (len(missing)+BATCH-1)//BATCH <= 128,
                  'Acquisition workload exceeds local cap')
    for offset in range(0, len(missing), BATCH):
        ids = missing[offset:offset+BATCH]
        sql = ('SELECT ' + ','.join(columns) + ' FROM gaiadr3.gaia_source WHERE source_id IN ('
               + ','.join(ids) + ') ORDER BY source_id')
        name = 'gaia_' + sha256(sql.encode()).hexdigest() + '.vot'
        def load(sql=sql, n=len(ids)):
            raw, receipt = tap(sql, n+1)
            return raw, dict(receipt, query=sql)
        obtain(name, load, lambda raw, ids=ids: validate_gaia(votable(raw), ids, columns,
                                                           profile['gaia']['reference']))
        batches.append({'filename': name, 'ids': ids, 'query': sql})
        print(f'Gaia parameter batch {offset//BATCH+1}/{(len(missing)+BATCH-1)//BATCH} verified', flush=True)
    manifest = {'schema': 'wenu-stellar-astrometry-capture/1', 'complete': True,
        'identity': identity, 'products': products, 'receipts': receipts, 'batches': batches}
    atomic_write(output / 'source_manifest_v1.json', canonical(manifest))
    return manifest


def verify_capture(root, identity, profile):
    payload = (root / 'source_manifest_v1.json').read_bytes()
    manifest = json.loads(payload)
    audit.require(manifest.get('schema') == 'wenu-stellar-astrometry-capture/1'
        and manifest.get('complete') is True and manifest['identity'] == identity,
        'Incomplete or differently bound astrometry capture')
    audit.require({'ReadMe', 'hip2.dat.gz', 'hip2.dat', 'gaia_column_metadata_v1.vot'}
                  <= manifest['products'].keys(), 'Missing astrometry products')
    audit.require(sum(v['bytes'] for v in manifest['products'].values()) <= TOTAL_CAP,
                  'Capture total byte cap exceeded')
    for name, record in manifest['products'].items():
        verify_product(root, name, record)
    for resource in profile['hipparcos2']['resources']:
        audit.require(manifest['products'][resource['filename']] ==
            {k: resource[k] for k in ('bytes', 'sha256')}, 'Hipparcos-2 source identity differs')
    validate_metadata((root / 'gaia_column_metadata_v1.vot').read_bytes(), identity['columns'])
    hips = audit.parse_hipparcos2((root / 'hip2.dat').read_bytes(),
        (root / 'ReadMe').read_bytes(), profile['hipparcos2'])
    tables, actual_ids = [], []
    for batch in manifest['batches']:
        audit.require(batch['filename'] == 'gaia_' + sha256(batch['query'].encode()).hexdigest() + '.vot',
                      'Batch query identity differs')
        table = votable((root / batch['filename']).read_bytes())
        validate_gaia(table, batch['ids'], identity['columns'], profile['gaia']['reference'])
        actual_ids.extend(batch['ids'])
        tables.append(table)
    audit.require(actual_ids == identity['missing_ids'], 'Missing/duplicate capture batches')
    extra = list(audit.table_rows(vstack(tables, metadata_conflicts='error'),
                  ('source_id', 'solution_id'))) if tables else []
    return hips, extra, {'astrometry_manifest_sha256': sha256(payload).hexdigest(),
                         'products': manifest['products'], 'identity': identity, 'profile': profile}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--association-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    data = ROOT / 'docs/developer/data'
    contract = json.loads((data / 'stellar_enrichment_contract_v1.json').read_bytes())
    policy = (data / 'gaia_dr3_acquisition_policy_v1.json').read_bytes()
    manifest, cache_receipt = audit.verify_cache(args.cache, contract, policy)
    rows, summary, report_digest = verified_report(args.association_report, contract)
    audit.require(summary['provenance']['download_manifest_sha256'] ==
                  cache_receipt['download_manifest_sha256'], 'Report/cache binding differs')
    sources = Table.read(args.cache / audit.PRODUCTS[2], format='ascii.ecsv')
    columns = manifest['identity']['columns']
    audit.require(sources.colnames == columns, 'Primary column schema differs')
    profile_payload = PROFILE.read_bytes()
    profile = json.loads(profile_payload)
    validate_gaia(sources, [audit.identifier(x) for x in sources['source_id']], columns,
                  profile['gaia']['reference'])
    approved = [c for group in json.loads(policy)['source_column_groups'].values() for c in group]
    audit.require(set(columns) <= set(approved), 'Unreviewed Gaia column request')
    identity = plan(rows, sources, columns, cache_receipt['download_manifest_sha256'], profile_payload)
    print(json.dumps({'required_associated_sources': len(identity['required_ids']),
        'reused_source_rows': len(identity['reused_source_ids']),
        'source_rows_to_fetch': len(identity['missing_ids']), 'association_manifest_sha256': report_digest}), flush=True)
    capture(args.output, identity, profile)
    verify_capture(args.output, identity, profile)
    print('ASTROMETRY SOURCE READY:', args.output.resolve())


if __name__ == '__main__':
    main()
