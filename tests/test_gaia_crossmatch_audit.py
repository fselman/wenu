"""Synthetic offline Gaia evidence admission/report tests; no provider calls."""
import importlib.util
import json
import math
from pathlib import Path
import socket
import sys
import gzip
from io import BytesIO
from types import ModuleType
from hashlib import sha256

import numpy as np
import pytest
from astropy.table import Table, MaskedColumn

SPEC = importlib.util.spec_from_file_location('gaia_audit', Path(__file__).parents[1] / 'tools/gaia_crossmatch_audit.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)
FETCH_SPEC = importlib.util.spec_from_file_location('fetch_kervella_catalogue',
    Path(__file__).parents[1] / 'tools/fetch_kervella_catalogue.py')
fetcher = importlib.util.module_from_spec(FETCH_SPEC)
FETCH_SPEC.loader.exec_module(fetcher)
sys.path.insert(0, str(Path(__file__).parents[1] / 'tools'))
import fetch_stellar_astrometry as stellar_fetch

HIP_METADATA = {'frame': 'icrs', 'origin': 'solar-system-barycenter',
                'epoch': {'value': 1991.25, 'format': 'jyear', 'scale': 'tt'}}
PROFILE = {'frame': 'icrs', 'origin': 'solar-system-barycenter',
           'epoch_scale': 'tcb', 'expected_ref_epoch': 2016.0}


def hip(i, **kwargs):
    return dict(hip=str(i), ra_degrees=10., dec_degrees=0., ra_mas_per_year=0.,
                dec_mas_per_year=0., magnitude=5., is_multiple=False, **kwargs)


def source(i, **kwargs):
    row = dict(source_id=str(i), solution_id='1', ref_epoch=2016., ra=10., dec=0.,
               pmra=0., pmdec=0., parallax=-1., radial_velocity=None)
    row.update(kwargs)
    return row


def pair(i, sid, **kwargs):
    return dict(original_ext_source_id=str(i), source_id=str(sid), xm_flag=0, **kwargs)


def evaluate(hips, best, neighbours, sources):
    return audit.audit(hips, best, neighbours, sources, HIP_METADATA, PROFILE, diagnostics=True)


def test_cardinality_shared_sources_and_unmatched_are_distinct():
    h = [hip(i) for i in range(1, 5)]
    h[1]['is_multiple'] = True
    best = [pair(1, 100), pair(2, 200), pair(3, 100)]
    n = best + [pair(2, 201)]
    s = [source(100), source(200), source(201)]
    before = json.dumps([h, best, n, s])
    summary, rows, candidates = evaluate(h, best, n, s)
    assert summary['categories'] == {'unmatched': 1, 'unique_candidate': 2, 'multiple_candidates': 1}
    assert summary['shared_gaia_sources'] == 1
    assert 'original_multiple_system' in rows[1]['review_reasons']
    assert 'component_identity_needs_review' not in rows[0]['review_reasons']
    assert rows[0]['pivot_evidence_present']
    assert not rows[3]['pivot_evidence_present']
    assert candidates[0]['shared_hip_ids'] == ['1', '3']
    assert [r['hip'] for r in rows] == ['1', '2', '3', '4']
    assert all(r['adopted_solution'] is None for r in rows + candidates)
    assert candidates[0]['gaia_source']['parallax'] == -1
    assert candidates[0]['gaia_source']['radial_velocity'] is None
    assert summary['adopted_astrometric_solutions'] == 0
    assert json.dumps([h, best, n, s]) == before


def test_missing_best_or_neighbourhood_is_reported_not_adopted():
    for b, n in [([pair(1, 100)], []), ([], [pair(1, 100)])]:
        _, rows, _ = evaluate([hip(1)], b, n, [source(100)])
        assert 'best_neighbourhood_inconsistent' in rows[0]['review_reasons']


@pytest.mark.parametrize('patch', [dict(pmra=None, pmdec=None), dict(ruwe=99.),
    dict(parallax=-10.), dict(ra=90.), dict(radial_velocity=None)])
def test_published_best_association_survives_quality_or_diagnostic_warnings(patch):
    h = hip(1)
    h['is_multiple'] = True
    summary, rows, candidates = evaluate([h], [pair(1, 100, number_of_neighbours=2)],
        [pair(1, 100), pair(1, 101)], [source(100, **patch), source(101)])
    assert summary['retained_published_associations'] == 1
    assert rows[0]['published_association']['source_id'] == '100'
    assert candidates[0]['decision'] == 'retained_published_association'
    assert candidates[1]['decision'] == 'neighbourhood_alternative'
    assert candidates[0]['best']['number_of_neighbours'] == 2
    assert rows[0]['adopted_solution'] is None


def test_neighbourhood_only_is_not_guessed_and_shared_best_links_survive():
    summary, rows, candidates = evaluate([hip(1), hip(2), hip(3)],
        [pair(1, 100), pair(2, 100)], [pair(1, 100), pair(2, 100), pair(3, 101)],
        [source(100), source(101)])
    assert summary['retained_published_associations'] == 2
    assert rows[2]['published_association'] is None
    assert summary['hip_without_published_association'] == 1
    assert summary['shared_gaia_sources'] == 1
    assert candidates[2]['decision'] == 'neighbourhood_alternative'


def test_conflicting_published_best_rows_are_not_arbitrarily_selected():
    with pytest.raises(ValueError, match='Contradictory published best'):
        evaluate([hip(1)], [pair(1, 100), pair(1, 101)],
                 [pair(1, 100), pair(1, 101)], [source(100), source(101)])


@pytest.mark.parametrize('fault', ['duplicate_pair', 'foreign_hip', 'missing_source', 'extra_source', 'duplicate_source'])
def test_identity_inconsistencies_stop(fault):
    b, n, s = [pair(1, 100)], [pair(1, 100)], [source(100)]
    if fault == 'duplicate_pair': n += n
    if fault == 'foreign_hip': n.append(pair(2, 100))
    if fault == 'missing_source': s = []
    if fault == 'extra_source': s.append(source(200))
    if fault == 'duplicate_source': s += s
    with pytest.raises(ValueError): evaluate([hip(1)], b, n, s)


@pytest.mark.parametrize('value', [1., True, None, np.ma.masked, '1', -1])
def test_integer_ids_never_admit_float_or_mask(value):
    with pytest.raises(ValueError): audit.identifier(value)


def test_large_integer_ids_and_masks_survive_ecsv(tmp_path):
    sid = 9007199254740993
    t = Table({'source_id': [sid], 'ruwe': MaskedColumn([2.], mask=[True])})
    path = tmp_path / 'raw.ecsv'
    t.write(path, format='ascii.ecsv')
    row = list(audit.table_rows(Table.read(path, format='ascii.ecsv'), ['source_id']))[0]
    assert row == {'source_id': str(sid), 'ruwe': None}
    assert audit.scalar(np.float64('nan')) is None
    with pytest.raises(ValueError): audit.scalar(float('inf'))


def test_common_epoch_oracles_and_missing_motion():
    # At the equator, the tangent-linear displacement is exactly atan(mu*dt).
    for dec in (0., 89.999, 90., -90.):
        original = audit.unit_direction(359.999, dec)
        moved = audit.unit_direction(359.999, dec, 1000., 0., 24.75)
        expected = math.atan(1000 * audit.MAS_RAD * 24.75) / audit.MAS_RAD / 1000
        assert audit.separation(original, moved) == pytest.approx(expected, abs=1e-8)
    h = hip(1)
    h['ra_mas_per_year'] = None
    _, _, rows = evaluate([h], [pair(1, 100)], [pair(1, 100)], [source(100, pmra=None)])
    assert rows[0]['separation_at_hip_epoch_arcsec'] is None
    assert rows[0]['separation_at_gaia_epoch_arcsec'] is None
    assert rows[0]['diagnostic_missing_input']


def test_nonzero_motion_reaches_both_common_epoch_diagnostics():
    h = hip(1)
    h['ra_mas_per_year'] = 1000.
    _, _, rows = evaluate([h], [pair(1, 100)], [pair(1, 100)], [source(100, pmra=1000.)])
    assert rows[0]['separation_at_hip_epoch_arcsec'] == pytest.approx(24.75, abs=0.001)
    assert rows[0]['separation_at_gaia_epoch_arcsec'] == pytest.approx(24.75, abs=0.001)


@pytest.mark.parametrize('patch', [{'ref_epoch': 2015.5}, {'ra': 360.}, {'dec': 91.}])
def test_bad_diagnostic_inputs_never_veto_published_association(patch):
    summary, hips, rows = evaluate([hip(1)], [pair(1, 100)], [pair(1, 100)], [source(100, **patch)])
    assert summary['retained_published_associations'] == 1
    assert hips[0]['published_association']['source_id'] == '100'
    assert rows[0]['diagnostic_status'].startswith('unavailable:')


def test_units_require_exact_semantics():
    t = Table({'ra': [1.]})
    with pytest.raises(ValueError): audit.check_units(t, {'ra': 'deg'})
    t['ra'].unit = 'rad'
    with pytest.raises(ValueError): audit.check_units(t, {'ra': 'deg'})
    t['ra'].unit = 'deg'
    audit.check_units(t, {'ra': 'deg'})


def test_publish_no_clobber_and_failure_cleanup(tmp_path):
    out = tmp_path / 'audit_v1'
    audit.publish(out, {}, [{'hip': '1', 'published_association': None}], [], {})
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    with pytest.raises(ValueError): audit.publish(out, {}, [], [], {})
    assert before == {p.name: p.read_bytes() for p in out.iterdir()}
    failed = tmp_path / 'failed_v1'
    with pytest.raises(ValueError): audit.publish(failed, {'bad': float('nan')}, [], [], {})
    assert not failed.exists()
    assert not list(tmp_path.glob('.failed_v1-*'))


@pytest.fixture
def cache(tmp_path):
    root = tmp_path / 'cache'
    root.mkdir()
    policy = b'{"synthetic": true}'
    baseline = {'rows': 1, 'source_sha256': 'a'*64,
                'ordered_hip_ids_sha256': sha256(b'1\n').hexdigest(),
                'hip_magnitude_pairs_sha256': sha256(json.dumps([[1, float(5.).hex()]], separators=(',', ':')).encode()).hexdigest()}
    contract = {'baseline': baseline}
    products = {}
    for name in audit.PRODUCTS:
        (root / name).write_bytes(b'synthetic')
        products[name] = {'sha256': sha256(b'synthetic').hexdigest(), 'bytes': 9}
    query = 'synthetic query, not provider data'
    endpoint = 'https://gea.esac.esa.int/tap-server/tap'
    key = sha256((endpoint+'\n'+query).encode()).hexdigest()
    (root / (key + '.vot')).write_bytes(b'synthetic')
    manifest = dict(schema='wenu-gaia-raw-download/1', complete=True, adopted_matches=0,
        identity=dict(release='Gaia DR3', endpoint=endpoint, rows=1,
                      source_sha256=baseline['source_sha256'], membership_sha256=baseline['ordered_hip_ids_sha256'],
                      policy_sha256=sha256(policy).hexdigest()), products=products,
        jobs={key: dict(query=query, filename=key+'.vot', sha256=sha256(b'synthetic').hexdigest(), bytes=9)})
    (root / 'download_manifest_v1.json').write_text(json.dumps(manifest))
    return root, contract, policy, manifest


@pytest.mark.parametrize('fault', ['none', 'product', 'raw', 'policy', 'membership', 'incomplete', 'path'])
def test_cache_identity_and_corruption(cache, fault):
    root, contract, policy, manifest = cache
    if fault == 'product': (root / audit.PRODUCTS[0]).write_bytes(b'changed!!')
    if fault == 'raw': next(root.glob('*.vot')).write_bytes(b'changed!!')
    if fault == 'policy': policy = b'different'
    if fault == 'membership': manifest['identity']['source_sha256'] = 'b'*64
    if fault == 'incomplete': manifest['complete'] = False
    if fault == 'path': manifest['products']['../escape'] = dict(bytes=0, sha256='x')
    (root / 'download_manifest_v1.json').write_text(json.dumps(manifest))
    if fault == 'none':
        assert audit.verify_cache(root, contract, policy)[1]['completed_raw_results_verified'] == 1
    else:
        with pytest.raises(ValueError): audit.verify_cache(root, contract, policy)


@pytest.mark.parametrize('supplement,coverage', [(False, False), (True, False), (True, True)])
def test_main_real_ecsv_to_report_offline(cache, tmp_path, monkeypatch, kervella_bundle,
                                         hip2_bundle, supplement, coverage):
    """Actual parser/publication path; Wenu source loading alone is synthetic."""
    import pandas as pd
    root, contract, policy, manifest = cache
    local = tmp_path / 'checkout'
    data = local / 'docs/developer/data'
    data.mkdir(parents=True)
    (data / 'stellar_enrichment_contract_v1.json').write_text(json.dumps(contract))
    (data / 'gaia_dr3_acquisition_policy_v1.json').write_bytes(policy)
    (data / 'gaia_dr3_audit_reference_v1.json').write_text(json.dumps(PROFILE))
    table = Table({'source_id': [9007199254740993], 'solution_id': [100],
                   'ref_epoch': [2016.], 'ra': [10.], 'dec': [0.], 'pmra': [0.], 'pmdec': [0.]})
    for name, unit in {'ref_epoch': 'yr', 'ra': 'deg', 'dec': 'deg', 'pmra': 'mas/yr', 'pmdec': 'mas/yr'}.items():
        table[name].unit = unit
    table.write(root / audit.PRODUCTS[2], format='ascii.ecsv', overwrite=True)
    candidate = Table({'source_id': [9007199254740993], 'original_ext_source_id': [1], 'xm_flag': [0]})
    for name in audit.PRODUCTS[:2]: candidate.write(root / name, format='ascii.ecsv', overwrite=True)
    Table({'column_name': table.colnames}).write(root / audit.PRODUCTS[3], format='ascii.ecsv', overwrite=True)
    for name in manifest['products']:
        raw = (root / name).read_bytes()
        manifest['products'][name] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    manifest['identity']['columns'] = table.colnames
    manifest['counts'] = dict(retained_hip_rows=1, gaia_source_rows=1,
                             hip_with_crossmatch_candidates=1, hip_without_crossmatch_candidates=0)
    (root / 'download_manifest_v1.json').write_text(json.dumps(manifest))
    (root / 'crossmatch_unmatched_hip_ids_v1.json').write_text('[]')
    h = hip(1)
    h.update(component_count=0, multiple_annex='', ccdm_id='', is_variable=False)
    metadata = dict(HIP_METADATA, source_sha256=contract['baseline']['source_sha256'],
        units={'ra_mas_per_year': 'mas/yr', 'dec_mas_per_year': 'mas/yr'})
    class Stars:
        def __init__(self, observer): pass
        def load(self):
            self.source_catalog = pd.DataFrame([{k:v for k,v in h.items() if k != 'hip'}], index=[1])
            self.catalogue_metadata = type('Metadata', (), {'to_record': lambda self: metadata})()
    fake = ModuleType('wenu.objects.stars')
    fake.Stars = Stars
    monkeypatch.setitem(sys.modules, 'wenu', ModuleType('wenu'))
    monkeypatch.setitem(sys.modules, 'wenu.objects', ModuleType('wenu.objects'))
    monkeypatch.setitem(sys.modules, 'wenu.objects.stars', fake)
    monkeypatch.setattr(audit, 'ROOT', local)
    monkeypatch.setattr(socket, 'socket', lambda *a, **k: pytest.fail('Unexpected network'))
    extra = []
    if supplement:
        raw, readme, kprofile, compressed = kervella_bundle
        profile_bytes = json.dumps(kprofile).encode()
        (data / 'kervella_association_source_v1.json').write_bytes(profile_bytes)
        capture = tmp_path / 'kervella_source'
        capture.mkdir()
        (capture / 'ReadMe').write_bytes(readme)
        (capture / 'tablea1.dat.gz').write_bytes(compressed)
        (capture / 'tablea1.dat').write_bytes(raw)
        products = {p.name: dict(bytes=p.stat().st_size, sha256=sha256(p.read_bytes()).hexdigest()) for p in capture.iterdir()}
        (capture / 'source_manifest_v1.json').write_text(json.dumps(dict(
            schema='wenu-kervella-source-capture/1', complete=True,
            profile_sha256=sha256(profile_bytes).hexdigest(), products=products)))
        monkeypatch.syspath_prepend(str(Path(__file__).parents[1] / 'tools'))
        extra = ['--kervella-source', str(capture)]
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    out = tmp_path / 'report_v1'
    if coverage:
        prior = tmp_path / 'prior_v3'
        audit.main(['--cache', str(root), '--output', str(prior), *extra])
        astrometry_profile, _, hreadme, hcompressed = hip2_bundle
        profile_payload = json.dumps(astrometry_profile).encode()
        (data / 'stellar_astrometry_acquisition_v1.json').write_bytes(profile_payload)
        rows, _, _ = stellar_fetch.verified_report(prior, contract)
        identity = stellar_fetch.plan(rows, table, table.colnames,
            sha256((root / 'download_manifest_v1.json').read_bytes()).hexdigest(), profile_payload)
        captured = tmp_path / 'astrometry_source'
        stellar_fetch.capture(captured, identity, astrometry_profile,
            transport=lambda url: ((hreadme if url.endswith('ReadMe') else hcompressed), {}),
            tap=lambda *a: (synthetic_vot(metadata_table(table.colnames)), {}))
        extra += ['--astrometry-source', str(captured)]
    audit.main(['--cache', str(root), '--output', str(out), *extra])
    version = 4 if coverage else 3 if supplement else 2
    summary = json.loads((out / f'summary_v{version}.json').read_text())
    assert summary['adopted_astrometric_solutions'] == 0 and summary['retained_hip_rows'] == 1
    row = json.loads((out / f'candidate_evidence_v{version}.jsonl').read_text())
    assert row['source_id'] == '9007199254740993'
    assert row['separation_at_hip_epoch_arcsec'] is None
    assert row['diagnostic_status'] == 'not_requested'
    assert summary['retained_published_associations'] == 1
    assert row['decision'] == 'retained_published_association'
    association = json.loads((out / f'published_associations_v{version}.jsonl').read_text())
    assert association['source_id'] == row['source_id']
    if supplement:
        assert summary['kervella_supplement']['statuses']['agreement'] == 1
        assert summary['kervella_supplement']['primary_associations_preserved']
    if coverage:
        assert summary['astrometric_coverage']['preferred_available_inputs'] == {'hipparcos2':1}
        reviewed = json.loads((out / 'hip_review_v4.jsonl').read_text())
        assert reviewed['astrometric_coverage']['hipparcos2_fallback_source']['HIP'] == '1'
    for name, record in json.loads((out / f'audit_manifest_v{version}.json').read_text())['products'].items():
        raw = (out / name).read_bytes()
        assert record == dict(sha256=sha256(raw).hexdigest(), bytes=len(raw))
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}


@pytest.fixture
def kervella_bundle():
    """Constructed fixed-width records, explicitly not real provider evidence."""
    columns = {
        'HIP': dict(first_byte=1, last_byte=6, unit='---', kind='identifier'),
        'GaiaDR2': dict(first_byte=8, last_byte=26, unit='---', kind='identifier'),
        'GaiaEDR3': dict(first_byte=28, last_byte=46, unit='---', kind='identifier'),
        'Vmag': dict(first_byte=112, last_byte=117, unit='mag', kind='number')}
    def record(hip, dr2, edr3, magnitude):
        raw = bytearray(b' ' * 650)
        for name, value in dict(HIP=hip, GaiaDR2=dr2, GaiaEDR3=edr3, Vmag=magnitude).items():
            spec = columns[name]
            raw[spec['first_byte']-1:spec['last_byte']] = str(value or '').rjust(spec['last_byte']-spec['first_byte']+1).encode()
        return bytes(raw)
    payload = b'\n'.join([record(1, 100, 9007199254740993, 5), record(2, 200, None, 6)]) + b'\n'
    description = 'Synthetic fixture\nByte-by-byte Description of file: tablea1.dat\n'
    for name, spec in columns.items():
        description += f" {spec['first_byte']}-{spec['last_byte']} A19 {spec['unit']} {name} Synthetic column\n"
    readme = description.encode()
    compressed = gzip.compress(payload, mtime=0)
    def identity(raw): return dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    profile = dict(rows=2, record_length=650, columns=columns,
        catalogue='synthetic-Kervella', citation='Synthetic fixture, not provider data',
        gaia_identity_bridge=dict(from_release='EDR3', to_release='DR3',
                                 policy='ESA-explicit-identical-source-list'),
        resources=[dict(filename=name, url='https://cdsarc.cds.unistra.fr/ftp/J/A+A/657/A7/'+name, **identity(raw))
                   for name, raw in [('ReadMe', readme), ('tablea1.dat.gz', compressed)]],
        expanded_table=identity(payload), transport_cap_bytes=100000, expanded_cap_bytes=100000)
    return payload, readme, profile, compressed


def test_kervella_exact_fixed_width_integer_and_blank_fields(kervella_bundle):
    payload, readme, profile, _ = kervella_bundle
    rows = audit.parse_kervella_table(payload, readme, profile)
    assert rows[0]['GaiaEDR3'] == '9007199254740993'
    assert rows[1]['GaiaEDR3'] is None and rows[1]['GaiaDR2'] == '200'
    assert rows[0]['source_row_number'] == 1


@pytest.mark.parametrize('fault', ['table_bytes', 'readme_bytes', 'layout', 'rows', 'length', 'duplicate', 'float_id'])
def test_kervella_malformed_source_refused(kervella_bundle, fault):
    payload, readme, profile, _ = kervella_bundle
    if fault == 'table_bytes': payload += b'x'
    if fault == 'readme_bytes': readme += b'x'
    if fault == 'layout': profile['columns']['GaiaEDR3']['first_byte'] = 29
    if fault == 'rows': profile['rows'] = 3
    if fault == 'length': profile['record_length'] = 649
    if fault in ('duplicate', 'float_id'):
        lines = payload.splitlines()
        if fault == 'duplicate': lines[1] = lines[0]
        else: lines[0] = b'1.0   ' + lines[0][6:]
        payload = b'\n'.join(lines) + b'\n'
        profile['expanded_table'] = dict(bytes=len(payload), sha256=sha256(payload).hexdigest())
    with pytest.raises(ValueError): audit.parse_kervella_table(payload, readme, profile)


def test_kervella_supplement_preserves_primary_conflicts_and_dr2_separation(kervella_bundle):
    _, _, profile, _ = kervella_bundle
    summary, hips, candidates = evaluate([hip(i) for i in range(1, 6)],
        [pair(1, 100), pair(2, 200)], [pair(1, 100), pair(2, 200)], [source(100), source(200)])
    before = json.dumps([summary, hips])
    rows = [dict(HIP='1', GaiaEDR3='999', GaiaDR2='10'),
            dict(HIP='2', GaiaEDR3='200', GaiaDR2=None),
            dict(HIP='3', GaiaEDR3='100', GaiaDR2=None),
            dict(HIP='4', GaiaEDR3=None, GaiaDR2='400'),
            dict(HIP='999', GaiaEDR3='9990', GaiaDR2=None)]
    result, output = audit.supplement_kervella(summary, hips, rows, profile)
    assert output[0]['published_association'] == hips[0]['published_association']
    assert output[0]['kervella_status'] == 'conflict_primary_preserved'
    assert output[1]['kervella_status'] == 'agreement'
    assert output[2]['published_association']['release'] == 'EDR3'
    assert output[2]['published_association']['source_id'] == '100'
    assert output[2]['association_status'] == 'supplemented'
    assert output[0]['association_status'] == 'primary_retained'
    assert output[3]['published_association'] is None
    assert output[3]['association_status'] == 'unassociated'
    assert output[4]['published_association'] is None
    assert result['retained_published_associations'] == 3
    assert result['kervella_supplement']['new_associations'] == 1
    assert result['kervella_supplement']['dr2_only_evidence'] == 1
    assert result['kervella_supplement']['shared_gaia_sources_after_supplement'] == 1
    assert result['kervella_supplement']['rows_outside_retained_hip_population'] == 1
    assert [r['hip'] for r in output] == [r['hip'] for r in hips]
    assert json.dumps([summary, hips]) == before
    assert sum(b['count'] for b in result['association_magnitude_histograms']['unassociated_after']['bins']) == 2


def test_kervella_bridge_and_duplicate_rows_refused(kervella_bundle):
    _, _, profile, _ = kervella_bundle
    summary, hips, _ = evaluate([hip(1)], [], [], [])
    row = dict(HIP='1', GaiaEDR3='100', GaiaDR2=None)
    with pytest.raises(ValueError, match='Duplicate Kervella'):
        audit.supplement_kervella(summary, hips, [row, row], profile)
    profile['gaia_identity_bridge']['from_release'] = 'DR2'
    with pytest.raises(ValueError, match='bridge'):
        audit.supplement_kervella(summary, hips, [row], profile)


def test_kervella_bounded_capture_reuse_corruption_and_publication(kervella_bundle, tmp_path):
    payload, readme, profile, compressed = kervella_bundle
    requests = []
    class Response(BytesIO):
        status = 200
        headers = {'Last-Modified': 'synthetic', 'Content-Type': 'application/octet-stream'}
        def geturl(self): return self.url
    def open_request(request, timeout):
        requests.append(request.full_url)
        response = Response(readme if request.full_url.endswith('/ReadMe') else compressed)
        response.url = request.full_url
        return response
    profile_bytes = json.dumps(profile).encode()
    directory = tmp_path / 'capture_v1'
    manifest = fetcher.fetch(directory, profile_bytes, open_request=open_request)
    assert manifest['complete'] is True and len(requests) == 2
    assert (directory / 'tablea1.dat').read_bytes() == payload
    assert fetcher.fetch(directory, profile_bytes, open_request=lambda *a, **k: pytest.fail('Unexpected repeat request')) == manifest
    (directory / 'tablea1.dat').write_bytes(b'changed')
    with pytest.raises(ValueError): fetcher.verify_capture(directory, profile_bytes)
    bad = tmp_path / 'bad_v1'
    profile['transport_cap_bytes'] = 1
    with pytest.raises(ValueError, match='byte budget'):
        fetcher.fetch(bad, json.dumps(profile).encode(), open_request=open_request)
    assert not bad.exists() and not list(tmp_path.glob('.bad_v1-*'))


def test_kervella_network_failure_does_not_publish_or_retry(kervella_bundle, tmp_path):
    _, _, profile, _ = kervella_bundle
    calls = []
    def fail(*a, **k):
        calls.append(1)
        raise OSError('Synthetic transport failure')
    with pytest.raises(OSError):
        fetcher.fetch(tmp_path / 'failed_v1', json.dumps(profile).encode(), open_request=fail)
    assert len(calls) == 1 and not (tmp_path / 'failed_v1').exists()


@pytest.mark.parametrize('fault', ['http', 'redirect', 'changed_bytes', 'expanded_cap'])
def test_kervella_bad_response_or_expansion_never_publishes(kervella_bundle, tmp_path, fault):
    _, readme, profile, compressed = kervella_bundle
    calls = []
    class Response(BytesIO):
        headers = {}
        status = 503 if fault == 'http' else 200
        def geturl(self): return 'https://unexpected.invalid/' if fault == 'redirect' else self.url
    def request(req, timeout):
        calls.append(req.full_url)
        raw = readme if req.full_url.endswith('/ReadMe') else compressed
        response = Response(b'changed' if fault == 'changed_bytes' else raw)
        response.url = req.full_url
        return response
    if fault == 'expanded_cap': profile['expanded_cap_bytes'] = 1
    output = tmp_path / 'invalid_v1'
    with pytest.raises(ValueError): fetcher.fetch(output, json.dumps(profile).encode(), open_request=request)
    assert len(calls) == (2 if fault == 'expanded_cap' else 1)
    assert not output.exists() and not list(tmp_path.glob('.invalid_v1-*'))


def test_v3_report_keeps_supplement_identity_and_completion_marker(kervella_bundle, tmp_path):
    _, _, profile, _ = kervella_bundle
    summary, hips, candidates = evaluate([hip(1)], [], [], [])
    summary, hips = audit.supplement_kervella(summary, hips,
        [dict(HIP='1', GaiaEDR3='9007199254740993', GaiaDR2=None)], profile)
    output = tmp_path / 'report_v3'
    audit.publish(output, summary, hips, candidates, {}, version=3)
    row = json.loads((output / 'published_associations_v3.jsonl').read_text())
    assert row['source_id'] == '9007199254740993' and row['release'] == 'EDR3'
    assert json.loads((output / 'audit_manifest_v3.json').read_text())['complete']
    assert not (output / 'summary_v2.json').exists()


@pytest.fixture
def hip2_bundle():
    """Constructed Hip2-format bytes; not a real provider fixture."""
    from copy import deepcopy
    profile = deepcopy(json.loads(stellar_fetch.PROFILE.read_bytes()))
    p = profile['hipparcos2']
    p['rows'] = 2
    lines = []
    for hip_id in (1, 2):
        values = dict(HIP=hip_id, Sn=5 if hip_id == 1 else 7, So=0, Nc=1,
            RArad=0.2, DErad=-0.3, Plx=-1, pmRA=0, pmDE=1,
            e_RArad=1, e_DErad=1, e_Plx=1, e_pmRA=1, e_pmDE=1)
        line = bytearray(b' '*276)
        for name, spec in p['columns'].items():
            a, b = spec['first_byte']-1, spec['last_byte']
            text = ''.join(f'{1.:7.2f}' for _ in range(15)) if name == 'UW' else str(values[name]).rjust(b-a)
            line[a:b] = text.encode()
        lines.append(bytes(line))
    raw = b'\n'.join(lines)+b'\n'
    description = 'Synthetic fixture\nByte-by-byte Description of file: hip2.dat\n'
    for name, spec in p['columns'].items():
        description += f" {spec['first_byte']}-{spec['last_byte']} A10 {spec['unit']} {name} Synthetic\n"
    readme = description.encode()
    compressed = gzip.compress(raw, mtime=0)
    p['expanded_table'] = stellar_fetch.digest(raw)
    p['resources'] = [dict(filename=name, url='https://cdsarc.cds.unistra.fr/ftp/I/311/'+name,
        **stellar_fetch.digest(payload)) for name, payload in [('ReadMe',readme),('hip2.dat.gz',compressed)]]
    return profile, raw, readme, compressed


def gaia_table(ids):
    values = dict(source_id=np.array(ids, dtype='int64'), solution_id=[100]*len(ids),
        ref_epoch=[2016.]*len(ids), ra=[10.]*len(ids), dec=[0.]*len(ids),
        parallax=[-1.]*len(ids), pmra=[0.]*len(ids), pmdec=[0.]*len(ids),
        radial_velocity=[1.]*len(ids), radial_velocity_error=[1.]*len(ids),
        astrometric_params_solved=[31]*len(ids))
    for name in ('ra_error','dec_error','parallax_error','pmra_error','pmdec_error'):
        values[name] = [1.]*len(ids)
    table = Table(values)
    for name in table.colnames:
        unit = ('yr' if name=='ref_epoch' else 'deg' if name in ('ra','dec') else
                'km/s' if name.startswith('radial_velocity') else
                'mas/yr' if name.startswith(('pmra','pmdec')) else
                'mas' if name in ('parallax','ra_error','dec_error','parallax_error') else None)
        table[name].unit = unit
    return table


def metadata_table(columns):
    return Table(dict(column_name=columns, datatype=['long' if c in ('source_id','solution_id') else 'double' for c in columns],
        unit=['']*len(columns), ucd=['']*len(columns), description=['Synthetic column']*len(columns)))


def synthetic_vot(table, status='OK'):
    stream = BytesIO()
    table.write(stream, format='votable')
    raw = stream.getvalue()
    return raw.replace(b'</RESOURCE>', f'<INFO name="QUERY_STATUS" value="{status}"/></RESOURCE>'.encode())


def test_hip2_parser_preserves_native_units_weights_and_special_solution(hip2_bundle):
    profile, raw, readme, _ = hip2_bundle
    rows = audit.parse_hipparcos2(raw, readme, profile['hipparcos2'])
    assert list(rows) == ['1','2']
    assert rows['1']['RArad'] == .2 and rows['1']['Plx'] == -1
    assert len(rows['1']['UW']) == 15
    assert rows['2']['Sn'] == 7
    assert rows['1']['original_record_ascii'].encode() == raw.splitlines()[0]


@pytest.mark.parametrize('fault', ['bytes','readme','layout','duplicate','float_hip','domain','rows'])
def test_hip2_bad_sources_refused(hip2_bundle, fault):
    profile, raw, readme, _ = hip2_bundle
    p = profile['hipparcos2']
    if fault == 'bytes': raw += b'x'
    if fault == 'readme': readme += b'x'
    if fault == 'layout': p['columns']['RArad']['unit'] = 'deg'
    if fault == 'rows': p['rows'] += 1
    if fault in ('duplicate','float_hip','domain'):
        lines = raw.splitlines()
        if fault == 'duplicate': lines[1] = lines[0]
        if fault == 'float_hip': lines[0] = b'   1.0'+lines[0][6:]
        if fault == 'domain': lines[0] = lines[0][:15]+b' 9.0000000000'+lines[0][28:]
        raw = b'\n'.join(lines)+b'\n';p['expanded_table'] = stellar_fetch.digest(raw)
    with pytest.raises(ValueError): audit.parse_hipparcos2(raw, readme, p)


@pytest.mark.parametrize('status', ['OVERFLOW','ERROR',''])
def test_tap_failure_and_overflow_refused(status):
    with pytest.raises(ValueError): stellar_fetch.votable(synthetic_vot(gaia_table([1]), status))


@pytest.mark.parametrize('fault', ['duplicate','missing','foreign','float_id','unit','epoch','schema'])
def test_gaia_parameter_admission_faults(fault):
    table = gaia_table([9007199254740993])
    columns = list(table.colnames)
    if fault == 'duplicate': table = __import__('astropy.table',fromlist=['vstack']).vstack([table,table])
    if fault == 'missing': table = table[:0]
    if fault == 'foreign': table['source_id'][0] = 2
    if fault == 'float_id': table['source_id'] = table['source_id'].astype(float)
    if fault == 'unit': table['pmra'].unit = 'deg/yr'
    if fault == 'epoch': table['ref_epoch'][0] = 2000
    if fault == 'schema': table.remove_column('pmdec')
    with pytest.raises(ValueError): stellar_fetch.validate_gaia(table,['9007199254740993'],columns, json.loads(stellar_fetch.PROFILE.read_bytes())['gaia']['reference'])


def test_coverage_preserves_links_and_uses_fallback_without_zero_fill(hip2_bundle):
    profile, raw, readme, _ = hip2_bundle
    h2 = audit.parse_hipparcos2(raw, readme, profile['hipparcos2'])
    hips = [hip(i) for i in range(1,8)]
    sources = [source(10,astrometric_params_solved=3,pmra=None,pmdec=None),
        source(20,astrometric_params_solved=95),source(30,astrometric_params_solved=31),
        source(40,astrometric_params_solved=31,pmdec=None),
        source(50,astrometric_params_solved=999)]
    best = [pair(i,sid)for i,sid in [(1,10),(3,20),(4,30),(5,40),(6,50)]]
    summary, rows, _ = evaluate(hips,best,best,sources)
    before = json.dumps([summary,rows,sources,h2])
    result, output = audit.astrometric_coverage(summary,rows,sources,h2,profile['hipparcos2'])
    coverage = [r['astrometric_coverage']for r in output]
    assert coverage[0]['preferred_available_input'] == 'hipparcos2'
    assert coverage[0]['gaia_status'] == 'position_only'
    assert coverage[0]['gaia_source']['pmra'] is None
    assert coverage[1]['hipparcos2_requires_special_model']
    assert coverage[1]['preferred_available_input'] == 'hipparcos2'
    assert coverage[2]['gaia_status'] == 'six_parameter'
    assert coverage[3]['preferred_available_input'] == 'gaia'
    assert not coverage[3]['gaia_positive_parallax']
    assert coverage[4]['gaia_status'] == 'incomplete_astrometry'
    assert coverage[5]['gaia_status'] == 'unknown_solution_type'
    assert coverage[6]['preferred_available_input'] == 'original_1997_lookup'
    assert all(r['adopted_solution'] is None for r in output)
    assert [r['original']for r in output] == [r['original']for r in rows]
    assert [r['published_association']for r in output] == [r['published_association']for r in rows]
    assert json.dumps([summary,rows,sources,h2]) == before
    assert sum(result['astrometric_coverage']['preferred_available_inputs'].values()) == 7
    with pytest.raises(ValueError, match='parameters missing'):
        audit.astrometric_coverage(summary,rows,sources[:-1],h2,profile['hipparcos2'])


def test_capture_resume_exact_query_binding_and_corruption(hip2_bundle,tmp_path,monkeypatch):
    profile, raw, readme, compressed = hip2_bundle
    t = gaia_table([9007199254740993])
    h = [dict(hip='1',original=hip(1),published_association=dict(source_id='9007199254740993'))]
    payload = json.dumps(profile).encode()
    identity = stellar_fetch.plan(h,t[:0],t.colnames,'a'*64,payload)
    requests = []
    def transport(url):
        requests.append(url)
        return (readme if url.endswith('ReadMe') else compressed), {'url':url,'status':200}
    fail = [True]
    def tap(sql,maxrec):
        requests.append(sql)
        if 'TAP_SCHEMA' in sql:
            return synthetic_vot(metadata_table(t.colnames)),dict(query=sql)
        if fail[0]: raise OSError('Synthetic DNS failure')
        return synthetic_vot(t),dict(query=sql)
    output = tmp_path/'capture'
    with pytest.raises(OSError):stellar_fetch.capture(output,identity,profile,transport=transport,tap=tap)
    assert not (output/'source_manifest_v1.json').exists()
    assert len(requests)==4
    fail[0] = False
    stellar_fetch.capture(output,identity,profile,transport=transport,tap=tap)
    assert len(requests)==5
    h2, extra, receipt = stellar_fetch.verify_capture(output,identity,profile)
    assert extra[0]['source_id']=='9007199254740993'
    assert extra[0]['parallax']==-1
    assert set(h2)=={'1','2'}
    monkeypatch.setattr(socket,'socket',lambda *a,**k:pytest.fail('Unexpected network'))
    stellar_fetch.capture(output,identity,profile,
        transport=lambda *a:pytest.fail('Reused source fetched'),tap=lambda *a:pytest.fail('Reused query fetched'))
    assert receipt['identity']['association_sha256']==stellar_fetch.association_digest(h)
    other = dict(identity,download_manifest_sha256='b'*64)
    with pytest.raises(ValueError,match='plan differs'):stellar_fetch.capture(output,other,profile)
    path = next(output.glob('gaia_*.vot'))
    path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises(ValueError,match='Changed capture'):stellar_fetch.verify_capture(output,identity,profile)


def test_plan_reuses_existing_gaia_rows_and_deduplicates_shared_sources():
    t=gaia_table([100])
    h=[dict(hip=str(i),original=hip(i),published_association=dict(source_id=str(sid)))
       for i,sid in [(1,100),(2,200),(3,200)]]
    result=stellar_fetch.plan(h,t,t.colnames,'a'*64,b'profile')
    assert result['missing_ids']==['200'] and result['reused_source_ids']==['100']
    assert result['required_ids']==['100','200']


def test_capture_overflow_stops_without_completing(hip2_bundle,tmp_path):
    profile, _, readme, compressed=hip2_bundle
    t=gaia_table([1])
    h=[dict(hip='1',original=hip(1),published_association=dict(source_id='1'))]
    identity=stellar_fetch.plan(h,t[:0],t.colnames,'a'*64,json.dumps(profile).encode())
    calls=[]
    def tap(sql,n):
        calls.append(sql)
        return synthetic_vot(metadata_table(t.colnames),status='OVERFLOW'),{}
    with pytest.raises(ValueError,match='QUERY_STATUS'):
        stellar_fetch.capture(tmp_path/'capture',identity,profile,
            transport=lambda url:((readme if url.endswith('ReadMe')else compressed),{}),tap=tap)
    assert len(calls)==1
    assert not (tmp_path/'capture/source_manifest_v1.json').exists()


def test_acquisition_main_real_cache_report_and_capture_seam(cache,hip2_bundle,tmp_path,monkeypatch):
    root,contract,policy,manifest=cache
    data=tmp_path/'checkout/docs/developer/data';data.mkdir(parents=True)
    table=gaia_table([100]); table.write(root/audit.PRODUCTS[2],format='ascii.ecsv',overwrite=True)
    manifest['identity']['columns']=table.colnames
    for name in manifest['products']:
        manifest['products'][name]=stellar_fetch.digest((root/name).read_bytes())
    newpolicy=json.dumps({'source_column_groups':{'synthetic':table.colnames}}).encode()
    manifest['identity']['policy_sha256']=sha256(newpolicy).hexdigest()
    (root/'download_manifest_v1.json').write_text(json.dumps(manifest))
    (data/'gaia_dr3_acquisition_policy_v1.json').write_bytes(newpolicy)
    (data/'stellar_enrichment_contract_v1.json').write_text(json.dumps(contract))
    rows=[dict(hip='1',original=hip(1),published_association=dict(hip='1',catalogue='Gaia',
        release='DR3',source_id='9007199254740993'))]
    report=tmp_path/'v3'
    audit.publish(report,dict(retained_published_associations=1),rows,[],
        dict(download_manifest_sha256=sha256((root/'download_manifest_v1.json').read_bytes()).hexdigest()),version=3)
    profile,_,readme,compressed=hip2_bundle
    profilepath=data/'stellar_astrometry_acquisition_v1.json'
    profilepath.write_text(json.dumps(profile))
    monkeypatch.setattr(stellar_fetch,'ROOT',data.parents[2])
    monkeypatch.setattr(stellar_fetch,'PROFILE',profilepath)
    original_capture=stellar_fetch.capture
    calls=[]
    def fake_tap(sql,n):
        calls.append(sql)
        return (synthetic_vot(metadata_table(table.colnames)) if 'TAP_SCHEMA' in sql
            else synthetic_vot(gaia_table([9007199254740993]))),dict(query=sql)
    def capture(output,identity,profile):
        return original_capture(output,identity,profile,
            transport=lambda url:((readme if url.endswith('ReadMe')else compressed),{}),tap=fake_tap)
    monkeypatch.setattr(stellar_fetch,'capture',capture)
    monkeypatch.setattr(socket,'socket',lambda *a,**k:pytest.fail('Unexpected network'))
    before={p.name:p.read_bytes()for p in root.iterdir()}
    output=tmp_path/'capture'
    stellar_fetch.main(['--cache',str(root),'--association-report',str(report),'--output',str(output)])
    assert len(calls)==2 and '100' not in calls[1]
    result=json.loads((output/'source_manifest_v1.json').read_text())
    assert result['identity']['missing_ids']==['9007199254740993']
    assert before=={p.name:p.read_bytes()for p in root.iterdir()}


@pytest.mark.parametrize('fault',['truncated','status','redirect','timeout'])
def test_request_transport_failures_do_not_retry(monkeypatch,fault):
    calls=[]
    class Response(BytesIO):
        status=503 if fault=='status' else 200
        headers={'Content-Length':'10' if fault=='truncated' else '3'}
        def geturl(self):return 'https://elsewhere.invalid' if fault=='redirect' else stellar_fetch.ENDPOINT+'/sync'
    class Opener:
        def open(self,req,timeout):
            calls.append(req)
            if fault=='timeout':raise TimeoutError('synthetic timeout')
            return Response(b'abc')
    monkeypatch.setattr(stellar_fetch,'build_opener',lambda *a:Opener())
    with pytest.raises((ValueError,TimeoutError)):
        stellar_fetch.request(stellar_fetch.ENDPOINT+'/sync',{'QUERY':'synthetic'})
    assert len(calls)==1


def test_capture_response_byte_cap():
    with pytest.raises(ValueError,match='byte cap'):stellar_fetch.read_bounded(BytesIO(b'abcd'),3)
    with pytest.raises(ValueError,match='Redirect'):
        stellar_fetch.NoRedirect().redirect_request(None,None,None,None,None,None)


@pytest.mark.parametrize('changed_name', [False, True])
def test_votable_field_names_define_schema_not_xml_ids(changed_name):
    """Synthetic Gaia-style XML IDs; names remain the exact ADQL contract."""
    import xml.etree.ElementTree as ET
    original = gaia_table([9007199254740993])
    root = ET.fromstring(synthetic_vot(original))
    for field in root.iter():
        if field.tag.split('}')[-1] == 'FIELD' and field.attrib.get('name') == 'source_id':
            field.set('ID', 'SOURCE_ID' if not changed_name else 'source_id')
            if changed_name:
                field.set('name', 'unexpected_source_column')
    raw = ET.tostring(root)
    parsed = stellar_fetch.votable(raw)
    reference = json.loads(stellar_fetch.PROFILE.read_bytes())['gaia']['reference']
    if changed_name:
        with pytest.raises(ValueError, match='schema differs'):
            stellar_fetch.validate_gaia(parsed, ['9007199254740993'], original.colnames, reference)
    else:
        stellar_fetch.validate_gaia(parsed, ['9007199254740993'], original.colnames, reference)
        assert parsed.colnames == original.colnames
        assert int(parsed['source_id'][0]) == 9007199254740993
    assert b'SOURCE_ID' in raw or changed_name


@pytest.mark.parametrize('fault',['schema','duplicate','float_identifier'])
def test_gaia_metadata_faults_refused(fault):
    table=metadata_table(['source_id','solution_id'])
    if fault=='schema':table.remove_column('description')
    if fault=='duplicate':table['column_name'][1]='source_id'
    if fault=='float_identifier':table['datatype']=['double','long']
    with pytest.raises(ValueError):
        stellar_fetch.validate_metadata(synthetic_vot(table),['source_id','solution_id'])
