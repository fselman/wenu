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
ENRICHMENT_SPEC = importlib.util.spec_from_file_location('wenu.stellar_enrichment',
    Path(__file__).parents[1] / 'src/wenu/stellar_enrichment.py')
# Share the canonical class when another owner already imported the codec.
# Replacing it would make real stellar-adapter isinstance/type checks fail
# solely because pytest collected this source-only owner afterwards.
if ENRICHMENT_SPEC.name in sys.modules:
    enrichment = sys.modules[ENRICHMENT_SPEC.name]
else:
    enrichment = importlib.util.module_from_spec(ENRICHMENT_SPEC)
    sys.modules[ENRICHMENT_SPEC.name] = enrichment
    ENRICHMENT_SPEC.loader.exec_module(enrichment)

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


@pytest.mark.parametrize('supplement,coverage,publish_source',
    [(False, False, False), (True, False, False), (True, True, False), (True, True, True)])
def test_main_real_ecsv_to_report_offline(cache, tmp_path, monkeypatch, kervella_bundle,
                                         hip2_bundle, supplement, coverage, publish_source):
    """Actual parser/publication path; Wenu source loading alone is synthetic."""
    import pandas as pd
    root, contract, policy, manifest = cache
    local = tmp_path / 'checkout'
    data = local / 'docs/developer/data'
    data.mkdir(parents=True)
    if publish_source:
        contract['baseline'].update(catalogue='hipparcos',edition='synthetic-original')
        contract['preserved_columns'] = ['magnitude','star_designations','ccdm_id']
    (data / 'stellar_enrichment_contract_v1.json').write_text(json.dumps(contract))
    (data / 'gaia_dr3_acquisition_policy_v1.json').write_bytes(policy)
    (data / 'gaia_dr3_audit_reference_v1.json').write_text(json.dumps(dict(PROFILE,
        release='DR3', right_ascension_motion='mu_alpha*cos(delta)')))
    table = Table({'source_id': [9007199254740993], 'solution_id': [100],
                   'ref_epoch': [2016.], 'ra': [10.], 'dec': [0.], 'pmra': [0.], 'pmdec': [0.]})
    if publish_source:
        table['parallax'] = [-1.]
        table['parallax'].unit = 'mas'
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
    if publish_source:
        h.update(star_designations={'names':['Synthetic Unicode \u03b1'], 'unknown_extra':None},
                 unconsumed_extra={'nullable':None,'vector':[1,2]})
    metadata = dict(HIP_METADATA, source_sha256=contract['baseline']['source_sha256'],
        catalogue='hipparcos', edition='synthetic-original',
        units={'ra_mas_per_year': 'mas/yr', 'dec_mas_per_year': 'mas/yr','magnitude':'mag','ra_degrees':'deg','dec_degrees':'deg'})
    class Stars:
        def __init__(self, observer): pass
        def load(self):
            self.source_catalog = pd.DataFrame([{k:v for k,v in h.items() if k != 'hip'}], index=[1])
            self.catalogue_metadata = type('Metadata', (), {'to_record': lambda self: metadata})()
            self.designation_catalogue = type('Designations', (),
                {'edition':'synthetic-names','source_sha256':'d'*64})()
    fake = ModuleType('wenu.objects.stars')
    fake.Stars = Stars
    monkeypatch.setitem(sys.modules, 'wenu', ModuleType('wenu'))
    monkeypatch.setitem(sys.modules, 'wenu.objects', ModuleType('wenu.objects'))
    monkeypatch.setitem(sys.modules, 'wenu.objects.stars', fake)
    monkeypatch.setitem(sys.modules, 'wenu.stellar_enrichment', enrichment)
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
    if publish_source:
        extra += ['--source-output', str(tmp_path/'source_v1')]
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
    if publish_source:
        snapshot = enrichment.load_stellar_enrichment(tmp_path/'source_v1')
        record = next(snapshot.records())
        assert record['original']['star_designations'] == h['star_designations']
        assert record['original']['unconsumed_extra'] == h['unconsumed_extra']
        assert record['source_references']['gaia'] == '9007199254740993'
        assert snapshot.metadata['counts']['preferred_available_inputs'] == {'hipparcos2':1}
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


@pytest.fixture
def enrichment_snapshot(hip2_bundle,monkeypatch):
    """Synthetic multi-edition input catalogue, including absent and position-only rows."""
    from types import SimpleNamespace
    from dataclasses import dataclass
    import pandas as pd
    profile,raw,readme,_=hip2_bundle
    hip2=audit.parse_hipparcos2(raw,readme,profile['hipparcos2'])
    reference=dict(PROFILE,release='DR3',right_ascension_motion='mu_alpha*cos(delta)')
    table=gaia_table([9007199254740993,200,400,500,600])
    table['astrometric_params_solved']=[31,3,95,999,31]
    table['pmra']=MaskedColumn([0.,0.,0.,0.,0.],mask=[False,True,False,False,False],unit='mas/yr')
    table['pmdec']=MaskedColumn([0.,0.,0.,0.,0.],mask=[False,True,False,False,False],unit='mas/yr')
    table['phot_g_mean_mag']=[10.,11.,12.,13.,14.];table['phot_g_mean_mag'].unit='mag'
    table['ra_dec_corr']=[.1,.2,.3,.4,.5]
    sources=list(audit.table_rows(table,('source_id','solution_id')))
    hips=[hip(i)for i in range(1,6)];hips[3]['magnitude']=None
    best=[pair(i,sid)for i,sid in [(1,9007199254740993),(2,200),(4,400),(5,500)]]
    summary,rows,candidates=audit.audit(hips,best,best+[pair(2,600)],sources,HIP_METADATA,reference)
    for row in rows:row['primary_candidate_category']=row['category']
    summary,rows=audit.astrometric_coverage(summary,rows,sources,hip2,profile['hipparcos2'])
    @dataclass(frozen=True)
    class Names:
        hip:int
        names:tuple
    originals=[]
    for h in hips:
        h=dict(h,star_designations=Names(int(h['hip']),('Synthetic \u03b1',)),
               unconsumed_column={'extra':None,'original_flag':False})
        originals.append({k:v for k,v in h.items()if k!='hip'})
    frame=pd.DataFrame(originals,index=range(1,6))
    meta=dict(HIP_METADATA,catalogue='hipparcos',edition='synthetic-original',source_sha256='a'*64,
              units={'magnitude':'mag','ra_degrees':'deg','dec_degrees':'deg','ra_mas_per_year':'mas/yr','dec_mas_per_year':'mas/yr'},provenance=['Constructed fixture; not provider data'])
    stars=SimpleNamespace(source_catalog=frame,
        catalogue_metadata=SimpleNamespace(to_record=lambda:meta),
        designation_catalogue=SimpleNamespace(edition='synthetic-names',source_sha256='d'*64))
    ids=[str(i)for i in frame.index]
    photometry=[[int(h['hip']),'missing'if h['magnitude']is None else float(h['magnitude']).hex()]for h in hips]
    contract=dict(baseline=dict(catalogue='hipparcos',edition='synthetic-original',source_sha256='a'*64,
        rows=5,ordered_hip_ids_sha256=sha256(('\n'.join(ids)+'\n').encode()).hexdigest(),
        hip_magnitude_pairs_sha256=sha256(json.dumps(photometry,separators=(',',':')).encode()).hexdigest()),
        preserved_columns=['magnitude','star_designations','unconsumed_column'])
    tables={audit.PRODUCTS[2]:table,audit.PRODUCTS[3]:metadata_table(table.colnames)}
    monkeypatch.setitem(sys.modules,'wenu.stellar_enrichment',enrichment)
    result=audit.enrichment_snapshot(stars,summary,rows,sources,hip2,candidates,tables,contract,
        {'source_kind':'constructed-synthetic','raw_sha256':'b'*64},profile)
    return result


def snapshot_mutation(snapshot,product,mutate):
    products=dict(snapshot.products)
    if product.endswith('jsonl'):
        rows=[enrichment.decode(line)for line in products[product].splitlines()]
        mutate(rows)
        products[product]=b''.join(enrichment.encode(r)+b'\n'for r in rows)
    else:
        row=enrichment.decode(products[product]);mutate(row)
        products[product]=enrichment.encode(row)+b'\n'
    manifest=enrichment.encode(dict(schema='wenu-stellar-enrichment-snapshot/1',complete=True,
        products={name:enrichment.identity(raw)for name,raw in products.items()}))
    return enrichment.StellarEnrichmentSnapshot(tuple((name,products[name])for name in enrichment.PRODUCTS),manifest)


def uncertainty_row(**changes):
    """Explicitly synthetic Gaia covariance specimen, not provider data."""
    row = source(1, astrometric_params_solved=31, parallax=10., pmra=125., pmdec=-85.)
    row.update(dict.fromkeys(audit.GAIA_ERRORS, 1.))
    row.update(dict.fromkeys(audit.GAIA_CORRELATIONS, 0.))
    row.update(changes)
    return row


@pytest.mark.parametrize('change,reason', [
    ({'ra_error': None}, 'errors'), ({'pmra_error': -1.}, 'errors'),
    ({'dec_error': float('nan')}, 'errors'), ({'ra_dec_corr': 1.01}, 'correlations'),
    ({'ra_dec_corr': True}, 'correlations'),
    ({'ra_dec_corr': .9, 'ra_parallax_corr': .9, 'dec_parallax_corr': -.9}, 'indefinite')])
def test_uncertainty_invalid_covariance_not_repaired(change, reason):
    with pytest.raises(ValueError, match=reason):
        audit.gaia_covariance(uncertainty_row(**change))


def test_uncertainty_covariance_marginal_singular_and_small_negative(monkeypatch):
    row = uncertainty_row(ra_dec_corr=.25, ra_error=2., dec_error=3., parallax_error=0.)
    c, info = audit.gaia_covariance(row)
    assert c[0, 1] == 1.5 and c[2, 2] == 0 and info['status'] == 'singular'
    _, singular = audit.gaia_covariance(uncertainty_row(ra_dec_corr=1.))
    assert singular['status'] == 'singular'
    _, weak = audit.gaia_covariance(uncertainty_row(ra_dec_corr=1.-1e-14))
    assert weak['status'] == 'ill_conditioned'
    # A tolerance is for classification only; even tiny negative values refuse.
    monkeypatch.setattr(audit.np.linalg, 'eigvalsh', lambda m: np.array([-1e-16, 1., 1., 1., 1.]))
    with pytest.raises(ValueError, match='within_roundoff'):
        audit.gaia_covariance(row)


@pytest.mark.parametrize('years', [0., -1000., 1000., -10000., 10000.])
def test_uncertainty_zero_motion_correlated_analytic_variance(years):
    row = uncertainty_row(pmra=0., pmdec=0., ra_error=2., pmra_error=3., ra_pmra_corr=.5)
    c, _ = audit.gaia_covariance(row)
    result = audit.angular_measurement_error(row, c, years)
    expected = np.diag([4 + 6*years + 9*years**2, 1 + years**2]) / 1e6
    np.testing.assert_allclose(result['covariance_arcsec2'], expected, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(np.square(result['principal_sigma_arcsec']),
                               np.linalg.eigvalsh(expected)[::-1], rtol=1e-12)


def perturbed_angular_reference(row, years, offsets):
    """B&L Eq.61/62 finite normal coordinates plus spherical departure.

    Independent of report Jacobian/normalization; supports a matrix of samples.
    """
    from astropy import units as units
    a, d = np.deg2rad([row['ra'], row['dec']])
    p = np.array([-np.sin(a), np.cos(a), 0.])
    q = np.array([-np.sin(d)*np.cos(a), -np.sin(d)*np.sin(a), np.cos(d)])
    r = np.array([np.cos(d)*np.cos(a), np.cos(d)*np.sin(a), np.sin(d)])
    k = units.mas.to(units.rad)
    z = np.asarray(offsets) * k
    x, y, ma, md = z[..., 0], z[..., 1], row['pmra']*k + z[..., 2], row['pmdec']*k + z[..., 3]
    radial = np.sqrt(1 - x*x - y*y)
    initial = x[..., None]*p + y[..., None]*q + radial[..., None]*r
    motion = ma[..., None]*p + md[..., None]*q - ((ma*x+md*y)/radial)[..., None]*r
    rate = np.linalg.norm(motion, axis=-1)
    phi = np.arctan(years*rate)
    return np.cos(phi)[..., None]*initial + (np.sin(phi)/rate)[..., None]*motion


@pytest.mark.parametrize('ra,dec', [(359.9999, 42.), (10., 90.), (140., -90.), (0., -89.99999)])
@pytest.mark.parametrize('years', [-10000., 0., 10000.])
def test_uncertainty_jacobian_against_independent_finite_perturbations(ra, dec, years):
    row = uncertainty_row(ra=ra, dec=dec, pmra=20000., pmdec=-12000.)
    direction, basis, jac = audit.angular_error_jacobian(row, years)
    np.testing.assert_allclose(direction, perturbed_angular_reference(row, years, np.zeros(4)), atol=3e-16)
    np.testing.assert_allclose(basis @ basis.T, np.eye(2), atol=5e-16)
    np.testing.assert_allclose(basis @ direction, 0, atol=3e-16)
    numerical = []
    for i in range(4):
        step = np.eye(4)[i] * (10. if i < 2 else .01)
        plus = perturbed_angular_reference(row, years, step)
        minus = perturbed_angular_reference(row, years, -step)
        numerical.append(basis @ (plus-minus) / (2*np.max(step)) / audit.MAS_RAD / 1000)
    np.testing.assert_allclose(jac, np.array(numerical).T, rtol=2e-6, atol=2e-9)


def test_uncertainty_seeded_small_error_monte_carlo():
    row = uncertainty_row(ra=145., dec=-65., pmra=500., pmdec=100.)
    # Correlated positive-definite synthetic input, constructed independently.
    factor = np.array([[.3, 0, 0, 0], [.1, .2, 0, 0], [.003, 0, .01, 0], [0, -.002, .004, .009]])
    marginal = factor @ factor.T
    covariance = np.eye(5)
    covariance[np.ix_([0, 1, 3, 4], [0, 1, 3, 4])] = marginal
    direction, basis, _ = audit.angular_error_jacobian(row, -10000.)
    draws = np.random.default_rng(1031).normal(size=(80000, 4)) @ factor.T
    points = perturbed_angular_reference(row, -10000., draws)
    residuals = (points-direction) @ basis.T / audit.MAS_RAD / 1000
    measured = np.cov(residuals.T)
    expected = audit.angular_measurement_error(row, covariance, -10000.)['covariance_arcsec2']
    np.testing.assert_allclose(measured, expected, rtol=.025, atol=1e-6)


@pytest.mark.parametrize('years', [-10000., -1000., 0., 1000., 10000.])
def test_uncertainty_rv_sensitivity_is_derivative_not_sigma(years):
    from astropy import units as units
    row = uncertainty_row(pmra=100., pmdec=0., parallax=10., radial_velocity=None)
    delta = .001
    mu = (100*units.mas).to_value(units.rad)
    rate = (delta*units.km/units.s/(100*units.pc)).to_value(1/units.yr)
    plus = np.arctan2(mu*years, 1+rate*years)
    minus = np.arctan2(mu*years, 1-rate*years)
    numerical = abs((plus-minus)/(2*delta))*units.rad.to(units.arcsec)
    assert audit.rv_sensitivity(row, years) == pytest.approx(numerical, rel=2e-8, abs=1e-14)
    if abs(years) == 10000:
        assert numerical == pytest.approx(.1022688127343643, rel=1e-7)
    with pytest.raises(ValueError, match='positive_parallax'):
        audit.rv_sensitivity(dict(row, parallax=None), years)


def complete_uncertainty_snapshot(snapshot):
    """Add labelled synthetic errors to the existing synthetic source seam."""
    products = dict(snapshot.products)
    metadata = enrichment.decode(products['metadata_v1.json'])
    rows = [enrichment.decode(line) for line in products['gaia_sources_v1.jsonl'].splitlines()]
    for row in rows:
        row.update(dict.fromkeys(audit.GAIA_ERRORS, .1))
        row.update(dict.fromkeys(audit.GAIA_CORRELATIONS, 0.))
    for name in (*audit.GAIA_ERRORS, *audit.GAIA_CORRELATIONS):
        if name not in metadata['gaia_columns']:
            metadata['gaia_columns'].append(name)
        metadata['gaia_column_units'][name] = ('mas / yr' if name.startswith('pm') else 'mas') if name in audit.GAIA_ERRORS else None
    products['metadata_v1.json'] = enrichment.encode(metadata)+b'\n'
    products['gaia_sources_v1.jsonl'] = b''.join(enrichment.encode(r)+b'\n' for r in rows)
    manifest = enrichment.encode(dict(schema='wenu-stellar-enrichment-snapshot/1', complete=True,
        products={name:enrichment.identity(raw) for name,raw in products.items()}))
    return enrichment.StellarEnrichmentSnapshot(tuple((name,products[name]) for name in enrichment.PRODUCTS), manifest)


def test_uncertainty_snapshot_cli_offline_lineage_and_no_clobber(enrichment_snapshot, tmp_path, monkeypatch):
    snapshot = complete_uncertainty_snapshot(enrichment_snapshot)
    before = snapshot.products
    source_path, output = tmp_path/'source', tmp_path/'report_v1'
    audit.publish_enrichment(source_path, snapshot)
    monkeypatch.setattr(socket, 'socket', lambda *a, **k: pytest.fail('offline report used network'))
    digest = sha256(snapshot.manifest).hexdigest()
    argv = ['--uncertainty-source', str(source_path), '--expected-source-manifest', digest,
            '--uncertainty-years', '-10000', '0', '10000', '--output', str(output)]
    audit.main(argv)
    summary = json.loads((output/'uncertainty_summary_v1.json').read_text())
    rows = [json.loads(s) for s in (output/'stellar_uncertainty_v1.jsonl').read_text().splitlines()]
    assert [r['hip'] for r in rows] == ['1', '2', '3', '4', '5']
    assert summary['retained_hip_rows'] == 5 and summary['source_manifest_sha256'] == digest
    assert summary['covariance_statuses'] == {'positive_definite': 2, 'no_five_parameter_astrometry': 2, 'no_published_gaia_association': 1}
    assert summary['angular_statuses'] == {'evaluated': 6, 'covariance_unavailable': 9}
    assert rows[3]['astrometric_params_solved'] == 95
    manifest = json.loads((output/'uncertainty_manifest_v1.json').read_text())
    assert manifest['complete'] is True
    for name, record in manifest['products'].items():
        assert enrichment.identity((output/name).read_bytes()) == record
    assert snapshot.products == before and enrichment.load_stellar_enrichment(source_path) == snapshot
    with pytest.raises(ValueError, match='already exists'):
        audit.main(argv)
    with pytest.raises(ValueError, match='manifest identity'):
        audit.main([s if s != digest else '0'*64 for s in argv])
    with pytest.raises(ValueError, match='explicit elapsed'):
        audit.main(argv[:4] + argv[-2:])
    with pytest.raises(ValueError, match='separate directories'):
        audit.main(argv[:-1] + [str(source_path/'nested_report')])
    with pytest.raises(ValueError, match='cannot acquire'):
        audit.main(argv + ['--diagnostics'])


def test_uncertainty_report_cleanup_units_and_invalid_offsets(enrichment_snapshot, tmp_path, monkeypatch):
    snapshot = complete_uncertainty_snapshot(enrichment_snapshot)
    for years in ([], [0., 0.], [float('inf')]):
        with pytest.raises(ValueError, match='finite, nonempty and unique'):
            audit.uncertainty_report(snapshot, years, tmp_path/'bad')
    wrong = snapshot_mutation(snapshot, 'metadata_v1.json', lambda m: m['gaia_column_units'].update(ra_dec_corr='mas'))
    with pytest.raises(ValueError, match='correlation unit'):
        audit.uncertainty_report(wrong, [0.], tmp_path/'bad')
    output = tmp_path/'failed'
    replace = Path.replace
    def fail(self, target):
        if self.name == 'uncertainty_manifest_v1.json':
            raise OSError('synthetic publication failure')
        return replace(self, target)
    monkeypatch.setattr(Path, 'replace', fail)
    with pytest.raises(OSError, match='synthetic publication'):
        audit.uncertainty_report(snapshot, [0.], output)
    assert not output.exists() and not list(tmp_path.glob('.failed-*'))


def test_uncertainty_invalid_matrix_is_a_per_hip_gap(enrichment_snapshot, tmp_path):
    snapshot = complete_uncertainty_snapshot(enrichment_snapshot)
    invalid = snapshot_mutation(snapshot, 'gaia_sources_v1.jsonl',
        lambda rows: rows[0].update(ra_dec_corr=.9, ra_parallax_corr=.9, dec_parallax_corr=-.9))
    summary = audit.uncertainty_report(invalid, [0., -10000.], tmp_path/'report')
    rows = [json.loads(line) for line in (tmp_path/'report/stellar_uncertainty_v1.jsonl').read_text().splitlines()]
    assert summary['retained_hip_rows'] == 5
    assert rows[0]['covariance']['status'] == 'indefinite_correlation_matrix'
    assert rows[0]['evaluations'][0]['status'] == 'covariance_unavailable'
    assert rows[3]['evaluations'][0]['status'] == 'evaluated'


def hip2_covariance_reference():
    return json.loads((Path(__file__).parents[1]/'docs/developer/data/hipparcos2_covariance_reference_v1.json').read_bytes())


def synthetic_hip2_weights(*, fit=2., transits=100, sigma=(.2, .3, .4, .5, .6), sn=5):
    """Constructed packed CDS values, with non-unit weights and both fit signs."""
    raw = list(' '*276)
    raw[104:107] = f'{transits:3d}'
    raw[108:113] = f'{fit:5.2f}'
    row = dict(Sn=sn, So=0, Nc=1, original_record_ascii=''.join(raw),
               UW=[1.2, -.7, 1.1, .2, -.4, 1.05, .3, .8, -.2, 1.3, -.6, .1, .5, -.9, 1.])
    row.update(zip(hip2_covariance_reference()['error_fields'], sigma))
    return row


@pytest.mark.parametrize('fit', [-2., 0., 3.])
def test_hip2_covariance_packing_and_published_error_scaling(fit):
    row = synthetic_hip2_weights(fit=fit)
    reference = hip2_covariance_reference()
    actual, info = audit.hip2_covariance(row, reference)
    nu = 95
    # Independent reconstruction via normal-matrix inversion, explicit packing.
    u = ((2/(9*nu))**.5*fit + 1 - 2/(9*nu))**1.5
    w = row['UW']
    upper = np.array([[w[0],w[1],w[3],w[6],w[10]], [0,w[2],w[4],w[7],w[11]],
                      [0,0,w[5],w[8],w[12]], [0,0,0,w[9],w[13]], [0,0,0,0,w[14]]], dtype=float)
    errors = np.array([row[k] for k in reference['error_fields']])
    upper[np.diag_indices(5)] *= u/errors
    expected = np.linalg.inv(upper.T @ upper) * u*u
    np.testing.assert_allclose(actual, expected, rtol=2e-13, atol=1e-14)
    assert info['unit_weight_error'] == pytest.approx(u)
    assert info['degrees_of_freedom'] == 95
    assert info['maximum_solve_identity_residual'] < 1e-12
    assert np.linalg.eigvalsh(actual)[0] > 0
    assert actual[0, 1] != 0
    # A raw inversion, whole-row/column scaling, and capped-u combination
    # convention all differ from this explicitly published-error covariance.
    if fit < 0:
        assert not np.allclose(actual, expected/u**2)


@pytest.mark.parametrize('patch,reason', [
    ({'Sn':7}, 'nonstandard'), ({'Sn':9}, 'nonstandard'), ({'Sn':1}, 'nonstandard'),
    ({'Sn':3}, 'nonstandard'), ({'Sn':0}, 'nonstandard'),
    ({'e_RArad':0.}, 'formal_errors'), ({'e_pmRA':None}, 'formal_errors'),
    ({'UW':[0.]*15}, 'singular'), ({'UW':[float('nan')]*15}, 'weights')])
def test_hip2_covariance_refuses_invalid_or_nonstandard_inputs(patch, reason):
    row = synthetic_hip2_weights(); row.update(patch)
    with pytest.raises(ValueError, match=reason):
        audit.hip2_covariance(row, hip2_covariance_reference())


def test_hip2_covariance_fit_input_refusal_and_flags():
    reference = hip2_covariance_reference()
    for row in (synthetic_hip2_weights(transits=5), synthetic_hip2_weights(transits=6, fit=-9.99)):
        with pytest.raises(ValueError, match='hip2_'):
            audit.hip2_covariance(row, reference)
    row = synthetic_hip2_weights(sn=85)
    _, info = audit.hip2_covariance(row, reference)
    assert info['Sn'] == 85  # Secondary/photocentre flags never erase a link.
    with pytest.raises(ValueError, match='Unsupported Hip2 covariance reference'):
        audit.hip2_covariance(row, dict(reference, recipe='invented'))


def test_hip2_covariance_diagonal_disagreement_is_exposed_not_rescaled():
    row = synthetic_hip2_weights(fit=99., sigma=(10., 12., 14., 16., 18.))
    matrix, info = audit.hip2_covariance(row, hip2_covariance_reference())
    assert info['F2_exactly_99'] is True
    assert info['max_absolute_relative_sigma_difference'] > .01
    assert not np.allclose(np.sqrt(np.diag(matrix)), info['quoted_sigma'])


def hip2_qualification_fixture(snapshot, tmp_path, monkeypatch):
    def add_fit(rows):
        for row in rows:
            raw = row['original_record_ascii']
            raw = raw[:104] + '100' + raw[107:108] + ' 0.00' + raw[113:]
            row['original_record_ascii'] = raw
            row['record_sha256'] = sha256(raw.encode('ascii')).hexdigest()
    snapshot = snapshot_mutation(snapshot, 'hipparcos2_sources_v1.jsonl', add_fit)
    policy = hip2_covariance_reference()
    source_profile = snapshot.metadata['hipparcos2_profile']
    policy['edition'] = 'explicitly-synthetic-not-provider-data'
    policy['source_table_sha256'] = source_profile['expanded_table']['sha256']
    policy['source_readme_sha256'] = next(r['sha256'] for r in source_profile['resources'] if r['filename']=='ReadMe')
    data = tmp_path/'docs/developer/data'; data.mkdir(parents=True)
    (data/'hipparcos2_covariance_reference_v1.json').write_text(json.dumps(policy))
    monkeypatch.setattr(audit, 'ROOT', tmp_path)
    return snapshot


def test_hip2_covariance_report_cli_source_binding_and_gaps(enrichment_snapshot, tmp_path, monkeypatch):
    snapshot = hip2_qualification_fixture(enrichment_snapshot, tmp_path, monkeypatch)
    directory, output = tmp_path/'source', tmp_path/'qualification_v1'
    audit.publish_enrichment(directory, snapshot)
    before = snapshot.products
    monkeypatch.setattr(socket, 'socket', lambda *a, **k: pytest.fail('qualification used network'))
    args = ['--hip2-covariance-source', str(directory), '--expected-source-manifest', sha256(snapshot.manifest).hexdigest(), '--output', str(output)]
    audit.main(args)
    rows = [json.loads(s) for s in (output/'hip2_covariance_qualification_v1.jsonl').read_text().splitlines()]
    summary = json.loads((output/'hip2_covariance_summary_v1.json').read_text())
    assert [r['hip'] for r in rows] == ['1','2','3','4','5']
    assert summary['statuses'] == {'decoded_standard':1, 'nonstandard_hip2_solution':1, 'no_hipparcos2_source':3}
    assert summary['fallback_statuses'] == {'nonstandard_hip2_solution':1}
    assert summary['source_manifest_sha256'] == sha256(snapshot.manifest).hexdigest()
    assert rows[0]['diagnostics']['Ntr'] == 100
    assert rows[0]['covariance'] is not None and rows[1]['covariance'] is None
    manifest = json.loads((output/'hip2_covariance_manifest_v1.json').read_text())
    assert manifest['complete'] is True
    for name, identity in manifest['products'].items():
        assert enrichment.identity((output/name).read_bytes()) == identity
    assert snapshot.products == before and enrichment.load_stellar_enrichment(directory) == snapshot
    with pytest.raises(ValueError, match='already exists'):
        audit.main(args)
    with pytest.raises(ValueError, match='does not propagate'):
        audit.main(args+['--uncertainty-years','0'])
    wrong = snapshot_mutation(snapshot, 'metadata_v1.json',
        lambda meta: meta['hipparcos2_profile']['expanded_table'].update(sha256='f'*64))
    with pytest.raises(ValueError, match='Unqualified Hip2 source edition'):
        audit.hip2_covariance_report(wrong, tmp_path/'wrong')
    wrong = snapshot_mutation(snapshot, 'metadata_v1.json',
        lambda meta: meta['hipparcos2_profile']['columns']['e_RArad'].update(unit='rad'))
    with pytest.raises(ValueError, match='Unsupported Hip2 covariance unit'):
        audit.hip2_covariance_report(wrong, tmp_path/'wrong')


def test_enrichment_round_trip_immutable_values_and_fallback(enrichment_snapshot,tmp_path):
    from dataclasses import FrozenInstanceError
    snapshot=enrichment_snapshot
    audit.publish_enrichment(tmp_path/'source_v1',snapshot)
    loaded=enrichment.load_stellar_enrichment(tmp_path/'source_v1',
        expected_manifest_sha256=sha256(snapshot.manifest).hexdigest())
    assert loaded==snapshot
    rows=list(loaded.records())
    assert [r['identity']['identifier']for r in rows]==['1','2','3','4','5']
    assert [r['input_availability']['preferred_available_input']for r in rows]==[
        'gaia','hipparcos2','original_1997_lookup','gaia','original_1997_lookup']
    assert rows[0]['original']['star_designations']=={'hip':1,'names':['Synthetic \u03b1']}
    assert rows[3]['original']['magnitude']is None
    assert rows[0]['foreign_photometry']['phot_g_mean_mag']==10.
    assert rows[0]['original']['magnitude']==5.
    gaia=list(loaded.records('gaia_sources_v1.jsonl'))
    assert gaia[0]['source_id']=='9007199254740993'and gaia[0]['parallax']==-1.
    assert gaia[1]['pmra']is None and gaia[0]['ra_dec_corr']==.1
    assert loaded.metadata['hipparcos2_profile']['reference']['epoch']['scale']is None
    rows[0]['original']['magnitude']=99
    meta=loaded.metadata;meta['counts']['retained_hip_rows']=99
    assert next(loaded.records())['original']['magnitude']==5.
    assert loaded.metadata['counts']['retained_hip_rows']==5
    with pytest.raises(FrozenInstanceError):loaded.manifest=b'changed'
    with pytest.raises(ValueError,match='manifest identity'):
        enrichment.load_stellar_enrichment(tmp_path/'source_v1',expected_manifest_sha256='0'*64)
    before={p.name:p.read_bytes()for p in (tmp_path/'source_v1').iterdir()}
    with pytest.raises(ValueError,match='already exists'):audit.publish_enrichment(tmp_path/'source_v1',snapshot)
    assert before=={p.name:p.read_bytes()for p in (tmp_path/'source_v1').iterdir()}


@pytest.mark.parametrize('fault',['membership','order','photometry','column','float_id','association',
    'unit','reference','epoch','gaia_duplicate','gaia_missing','candidate_duplicate','candidate_foreign',
    'hip2_record','hip2_field','fallback','counts','adoption','adoption_flag','foreign_photometry','bridge'])
def test_enrichment_semantic_corruption_refused_even_with_rehashed_products(enrichment_snapshot,fault):
    product='stars_v1.jsonl'
    def mutate(rows):
        if fault=='membership':rows.pop()
        if fault=='order':rows.reverse()
        if fault=='photometry':rows[0]['original']['magnitude']=10.
        if fault=='column':del rows[0]['original']['unconsumed_column']
        if fault=='float_id':rows[0]['identity']['identifier']=1.
        if fault=='association':rows[0]['published_association']['source_id']='600'
        if fault=='fallback':rows[1]['input_availability']['preferred_available_input']='gaia'
        if fault=='adoption':rows[0]['adopted_solution']={'invented':True}
        if fault=='adoption_flag':rows[0]['input_availability']['model_adopted']=True
        if fault=='foreign_photometry':rows[0]['foreign_photometry']['phot_g_mean_mag']=5.
        if fault=='bridge':rows[0]['published_association']['release']='EDR3'
    if fault in ('unit','reference','counts'):
        product='metadata_v1.json'
        def mutate(meta):
            if fault=='unit':meta['gaia_column_units']['pmra']='deg / yr'
            if fault=='reference':meta['gaia_reference']['epoch_scale']='utc'
            if fault=='counts':meta['counts']['retained_hip_rows']=4
    if fault in ('epoch','gaia_duplicate','gaia_missing'):
        product='gaia_sources_v1.jsonl'
        def mutate(rows):
            if fault=='epoch':rows[0]['ref_epoch']=2000.
            if fault=='gaia_duplicate':rows.append(rows[0])
            if fault=='gaia_missing':rows.pop()
    if fault in ('candidate_duplicate','candidate_foreign'):
        product='candidate_evidence_v1.jsonl'
        def mutate(rows):
            if fault=='candidate_duplicate':rows.append(rows[0])
            if fault=='candidate_foreign':rows[0]['hip']='999'
    if fault in ('hip2_record','hip2_field'):
        product='hipparcos2_sources_v1.jsonl'
        def mutate(rows):
            if fault=='hip2_record':rows[0]['original_record_ascii']='x'+rows[0]['original_record_ascii'][1:]
            if fault=='hip2_field':rows[0]['pmRA']=99.
    with pytest.raises((ValueError,KeyError)):
        snapshot_mutation(enrichment_snapshot,product,mutate)


@pytest.mark.parametrize('raw',[b'{"x":NaN}',b'{"x":1e999}',b'{"x":1,"x":2}'])
def test_enrichment_strict_json_refuses_unknown_nonfinite_and_duplicate_fields(raw):
    with pytest.raises(ValueError):enrichment.decode(raw)


def test_enrichment_publication_failure_removes_only_owned_output(enrichment_snapshot,tmp_path,monkeypatch):
    output=tmp_path/'source_v1';existing=tmp_path/'keep.txt';existing.write_text('unchanged')
    replace=Path.replace
    def fail(path,target):
        if path.name=='gaia_sources_v1.jsonl':raise OSError('Synthetic disk failure')
        return replace(path,target)
    monkeypatch.setattr(Path,'replace',fail)
    with pytest.raises(OSError):audit.publish_enrichment(output,enrichment_snapshot)
    assert not output.exists()and existing.read_text()=='unchanged'
    assert not list(tmp_path.glob('.source_v1-*'))


def test_enrichment_loader_standalone_without_wenu_or_astronomy(enrichment_snapshot,tmp_path):
    import subprocess
    output=tmp_path/'source_v1';audit.publish_enrichment(output,enrichment_snapshot)
    script='''import importlib.util,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('standalone_enrichment',sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s=m.load_stellar_enrichment(sys.argv[2])
assert s.metadata['counts']['retained_hip_rows']==5
assert len(list(s.records()))==5
assert not any(n.split('.')[0] in {'wenu','wenu_kernel','numpy','astropy','pandas','matplotlib','skyfield'} for n in sys.modules)
print('Standalone source reload passed')
'''
    code=tmp_path/'check.py';code.write_text(script)
    result=subprocess.run([sys.executable,'-I','-S',str(code),str(Path(__file__).parents[1]/'src/wenu/stellar_enrichment.py'),str(output)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert 'Standalone source reload passed'in result.stdout


@pytest.mark.parametrize('product',enrichment.PRODUCTS)
def test_enrichment_product_bytes_corruption_refused(enrichment_snapshot,tmp_path,product):
    root=tmp_path/'source_v1';audit.publish_enrichment(root,enrichment_snapshot)
    p=root/product;p.write_bytes(p.read_bytes()+b' ')
    with pytest.raises(ValueError,match='digest differs'):enrichment.load_stellar_enrichment(root)


def test_source_value_copies_dataclasses_mappings_masks_and_rejects_unknowns():
    from dataclasses import dataclass
    from types import MappingProxyType
    @dataclass(frozen=True)
    class Record:
        names:tuple
        evidence:object
    mutable={'extra':[1,None]}
    value=Record(('Synthetic \u03b1',),MappingProxyType(mutable))
    copied=audit.source_value(value);mutable['extra'][0]=99
    assert copied=={'names':['Synthetic \u03b1'],'evidence':{'extra':[1,None]}}
    assert audit.source_value(np.ma.masked)is None
    assert audit.source_value(float('nan'))is None
    with pytest.raises(ValueError):audit.source_value(object())


@pytest.mark.parametrize('nested',['same','source_inside_report','report_inside_source'])
def test_source_publication_output_paths_must_be_disjoint(tmp_path,nested):
    source=tmp_path/'source';report=source
    if nested=='source_inside_report':report=tmp_path;source=tmp_path/'source'
    if nested=='report_inside_source':report=source/'report'
    with pytest.raises(ValueError,match='separate directories'):
        audit.main(['--cache','unused','--kervella-source','unused','--astrometry-source','unused',
            '--source-output',str(source),'--output',str(report)])
