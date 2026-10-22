#!/usr/bin/env python3
"""Audit a completed Wenu Gaia cache offline; never adopt a counterpart.

Candidate evidence is separate from identity and astrometric usability. This
maintenance tool is not a production provider or a stellar propagation API.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
import tempfile

import numpy as np
import astropy
from astropy.table import Table
from astropy.time import Time
import astropy.units as u

ROOT = Path(__file__).resolve().parents[1]
MAS_RAD = math.pi / (180 * 3600 * 1000)
PRODUCTS = (
    'hipparcos2_best_neighbour_v1.ecsv', 'hipparcos2_neighbourhood_v1.ecsv',
    'gaia_dr3_source_subset_v1.ecsv', 'source_column_metadata_v1.ecsv',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def scalar(value):
    """Preserve masks as null and reject infinity; JSON never emits NaN."""
    if np.ma.is_masked(value) or value is None:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        if math.isnan(value):
            return None
        require(math.isfinite(value), 'Infinite source value')
    return value


def identifier(value):
    value = scalar(value)
    require(type(value) is int and value > 0,
            'Identifiers must be positive integers, never floats or masks')
    return str(value)


def unit_direction(ra, dec, pmra=0., pmdec=0., years=0.):
    """Normalized r + dt*(mu_alpha_star*east + mu_delta*north).

    Nominal angular diagnostic only: no distance, perspective, binaries,
    covariance or accuracy/adoption threshold. PM inputs are mas/Julian year
    in the source time scale; never divide by cos(dec), including at the poles.
    """
    values = (ra, dec, pmra, pmdec, years)
    if any(v is None for v in values):
        return None
    require(all(math.isfinite(v) for v in values), 'Non-finite diagnostic input')
    require(0 <= ra < 360 and abs(dec) <= 90, 'Coordinate outside angular domain')
    a, d = math.radians(ra), math.radians(dec)
    r = np.array([math.cos(d)*math.cos(a), math.cos(d)*math.sin(a), math.sin(d)])
    east = np.array([-math.sin(a), math.cos(a), 0.])
    north = np.array([-math.sin(d)*math.cos(a), -math.sin(d)*math.sin(a), math.cos(d)])
    result = r + years * MAS_RAD * (pmra * east + pmdec * north)
    require(np.all(np.isfinite(result)), 'Diagnostic overflow')
    return result / np.linalg.norm(result)


def separation(a, b):
    if a is None or b is None:
        return None
    return math.atan2(float(np.linalg.norm(np.cross(a, b))), float(np.dot(a, b))) / MAS_RAD / 1000


def verify_cache(root, contract, policy_payload):
    """Check identities and bytes before interpreting any candidate table."""
    payload = (root / 'download_manifest_v1.json').read_bytes()
    manifest = json.loads(payload)
    require(manifest.get('schema') == 'wenu-gaia-raw-download/1'
            and manifest.get('complete') is True, 'Incomplete/unknown download')
    identity = manifest['identity']
    baseline = contract['baseline']
    require(identity['release'] == 'Gaia DR3', 'Wrong catalogue release')
    require(identity['endpoint'] == 'https://gea.esac.esa.int/tap-server/tap',
            'Unexpected acquisition endpoint')
    require(identity['membership_sha256'] == baseline['ordered_hip_ids_sha256']
            and identity['source_sha256'] == baseline['source_sha256']
            and identity['rows'] == baseline['rows'], 'Source membership mismatch')
    require(identity['policy_sha256'] == sha256(policy_payload).hexdigest(),
            'Acquisition policy digest mismatch')
    require(manifest.get('adopted_matches') == 0, 'Unexpected existing adoptions')
    require(set(PRODUCTS) <= manifest['products'].keys(), 'Missing required product receipt')
    for name, record in manifest['products'].items():
        require(Path(name).name == name and name not in ('.', '..'), 'Unsafe product path')
        raw = (root / name).read_bytes()
        require(len(raw) == record['bytes'] and sha256(raw).hexdigest() == record['sha256'],
                'Product digest/size mismatch: ' + name)
    completed = 0
    for key, record in manifest['jobs'].items():
        require(sha256((identity['endpoint'] + '\n' + record['query']).encode()).hexdigest() == key,
                'Query identity mismatch')
        if not record.get('sha256'):
            continue  # Failed/superseded jobs remain evidence, not empty results.
        name = record['filename']
        require(name == key + '.vot', 'Raw result filename mismatch')
        raw = (root / name).read_bytes()
        require(len(raw) == record['bytes'] and sha256(raw).hexdigest() == record['sha256'],
                'Raw result digest/size mismatch')
        completed += 1
    return manifest, {'download_manifest_sha256': sha256(payload).hexdigest(),
                      'completed_raw_results_verified': completed}


def check_units(table, expected):
    for name, unit in expected.items():
        require(name in table.colnames, 'Missing column: ' + name)
        actual = table[name].unit
        require(actual is not None and u.Unit(actual) == u.Unit(unit),
                'Wrong/missing unit: ' + name)


def table_rows(table, id_columns):
    for row in table:
        result = {name: scalar(row[name]) for name in table.colnames}
        for name in id_columns:
            result[name] = identifier(row[name])
        yield result


def audit(hips, best, neighbours, sources, hip_metadata, gaia_profile):
    """Yield summary plus per-HIP/per-candidate evidence without input mutation."""
    require(gaia_profile['frame'] == hip_metadata['frame'] == 'icrs', 'Unsupported frame')
    require(gaia_profile['origin'] == hip_metadata['origin'] == 'solar-system-barycenter',
            'Unsupported origin')
    hip_ids = [row['hip'] for row in hips]
    require(len(set(hip_ids)) == len(hip_ids), 'Duplicate HIP membership')
    population = set(hip_ids)
    source_map = {row['source_id']: row for row in sources}
    require(len(source_map) == len(sources), 'Duplicate Gaia source')
    by_hip = {'best': defaultdict(dict), 'neighbourhood': defaultdict(dict)}
    claims = defaultdict(set)
    for label, rows in (('best', best), ('neighbourhood', neighbours)):
        for row in rows:
            hip, sid = row['original_ext_source_id'], row['source_id']
            require(hip in population and sid in source_map, 'Unrequested HIP or missing Gaia source')
            require(sid not in by_hip[label][hip], 'Duplicate candidate pair')
            by_hip[label][hip][sid] = row
            claims[sid].add(hip)
    require(set(claims) == set(source_map), 'Unreferenced or missing Gaia source')
    epoch = hip_metadata['epoch']
    hip_time = Time(epoch['value'], format=epoch['format'], scale=epoch['scale'])
    hip_target = float(getattr(hip_time, gaia_profile['epoch_scale']).jyear)
    # Conversion is only between catalogue epochs: no UTC, IERS or observer data.
    epochs = sorted({row['ref_epoch'] for row in sources if row['ref_epoch'] is not None})
    epoch_deltas = {t: float(getattr(Time(t, format='jyear', scale=gaia_profile['epoch_scale']),
                                   epoch['scale']).jyear) - float(hip_time.jyear) for t in epochs}
    counts = Counter()
    warnings = Counter()
    hip_records, candidates = [], []
    for hip in hips:
        key = hip['hip']
        b, n = by_hip['best'][key], by_hip['neighbourhood'][key]
        ids = sorted(set(b) | set(n), key=int)
        category = 'unmatched' if not ids else 'unique_candidate' if len(ids) == 1 else 'multiple_candidates'
        counts[category] += 1
        reasons = []
        if ids:
            reasons = ['crossmatch_flags_unqualified']
            if set(b) - set(n) or len(b) != 1:
                reasons.append('best_neighbourhood_inconsistent')
            if any(len(claims[sid]) > 1 for sid in ids):
                reasons.append('shared_gaia_source')
            if hip.get('is_multiple'):
                reasons.append('original_multiple_system')
                reasons.append('component_identity_needs_review')
        for reason in reasons:
            warnings[reason] += 1
        original = unit_direction(hip['ra_degrees'], hip['dec_degrees'])
        hip_records.append({'hip': key, 'category': category, 'candidate_count': len(ids),
                            'candidate_source_ids': ids, 'review_reasons': reasons,
                            'pivot': 'exact HIP key: ESA-1997-I/239 -> Hipparcos-2 -> Gaia DR3',
                            'pivot_evidence_present': bool(ids),
                            'original': hip, 'adopted_solution': None})
        for sid in ids:
            source = source_map[sid]
            gaia_native = unit_direction(source['ra'], source['dec'])
            t = source['ref_epoch']
            require(t is None or t == gaia_profile['expected_ref_epoch'], 'Unexpected Gaia reference epoch')
            back = None if t is None else unit_direction(source['ra'], source['dec'],
                    source['pmra'], source['pmdec'], hip_target - t)
            forward = None if t is None else unit_direction(hip['ra_degrees'], hip['dec_degrees'],
                    hip['ra_mas_per_year'], hip['dec_mas_per_year'], epoch_deltas[t])
            at_hip, at_gaia = separation(original, back), separation(forward, gaia_native)
            if at_hip is not None:
                counts['candidates_with_gaia_back_diagnostic'] += 1
            if at_gaia is not None:
                counts['candidates_with_hip_forward_diagnostic'] += 1
            candidates.append({'hip': key, 'source_id': sid, 'best': b.get(sid),
                'neighbourhood': n.get(sid), 'gaia_source': source,
                'link_method': 'exact HIP key plus published Hipparcos-2 Gaia candidate tables',
                'shared_hip_ids': sorted(claims[sid], key=int),
                'separation_at_hip_epoch_arcsec': at_hip,
                'separation_at_gaia_epoch_arcsec': at_gaia,
                'diagnostic_missing_input': at_hip is None or at_gaia is None,
                'decision': 'unresolved', 'adopted_solution': None})
    summary = {'retained_hip_rows': len(hips), 'gaia_source_rows': len(sources),
               'candidate_pairs': len(candidates), 'adopted_matches': 0,
               'hip_with_crossmatch_candidates': len(hips) - counts['unmatched'],
               'hip_without_crossmatch_candidates': counts['unmatched'],
               'categories': {k: counts[k] for k in ('unmatched', 'unique_candidate', 'multiple_candidates')},
               'diagnostics': {k: counts[k] for k in ('candidates_with_gaia_back_diagnostic',
                                                     'candidates_with_hip_forward_diagnostic')},
               'shared_gaia_sources': sum(len(v) > 1 for v in claims.values()),
               'pivot': 'exact HIP identifier; no 1997-to-Hipparcos-2 positional rematching',
               'hip_review_reasons': dict(warnings),
               'hip_epoch': epoch, 'gaia_reference': gaia_profile,
               'diagnostic_model': 'normalized linear tangent direction; PM-only; source-scale Julian years',
               'limits': ['No identity decisions or automatic adoption',
                          'No distance/RV/perspective/binary or covariance model',
                          'Separations are diagnostics, not match thresholds or accuracy claims',
                          'Missing candidate is not physical absence from Gaia',
                          'Hipparcos-2 source solutions/components not acquired or verified']}
    summary['quality_inventory'] = {
        'solution_types': dict(Counter(str(s.get('astrometric_params_solved')) for s in sources)),
        'sources_missing_pm': sum(s['pmra'] is None or s['pmdec'] is None for s in sources),
        'sources_missing_rv': sum(s.get('radial_velocity') is None for s in sources),
        'sources_with_nonpositive_parallax': sum(s.get('parallax') is not None and s['parallax'] <= 0 for s in sources),
        'best_xm_flags': dict(Counter(str(r.get('xm_flag')) for r in best)),
        'neighbourhood_xm_flags': dict(Counter(str(r.get('xm_flag')) for r in neighbours)),
    }
    return summary, hip_records, candidates


def publish(output, summary, hips, candidates, provenance):
    """Refuse overwrite; publish the completion manifest last; clean up on failure."""
    output = Path(output)
    require(not output.exists(), 'Report output already exists; choose a new version')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.' + output.name + '-', dir=output.parent))
    try:
        for name, rows in (('hip_review_v1.jsonl', hips), ('candidate_evidence_v1.jsonl', candidates)):
            with (temporary / name).open('w') as stream:
                for row in rows:
                    stream.write(json.dumps(row, allow_nan=False) + '\n')
        fields = ['hip', 'source_id', 'separation_at_hip_epoch_arcsec', 'separation_at_gaia_epoch_arcsec']
        with (temporary / 'candidate_separations_v1.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for row in candidates:
                writer.writerow({k: row[k] for k in fields})
        summary = dict(summary, provenance=provenance)
        (temporary / 'summary_v1.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
        products = {p.name: {'sha256': sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
                    for p in temporary.iterdir()}
        (temporary / 'audit_manifest_v1.json').write_text(json.dumps(
            {'schema': 'wenu-gaia-candidate-audit/1', 'complete': True, 'products': products}, indent=2) + '\n')
        # mkdir reserves the destination without clobbering another invocation.
        output.mkdir()
        try:
            for p in sorted(temporary.iterdir(), key=lambda p: p.name == 'audit_manifest_v1.json'):
                p.replace(output / p.name)
        except BaseException:
            shutil.rmtree(output)
            raise
    finally:
        shutil.rmtree(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    require(not args.output.exists(), 'Report output already exists; choose a new version')
    data = ROOT / 'docs/developer/data'
    contract_payload = (data / 'stellar_enrichment_contract_v1.json').read_bytes()
    contract = json.loads(contract_payload)
    policy_payload = (data / 'gaia_dr3_acquisition_policy_v1.json').read_bytes()
    profile_payload = (data / 'gaia_dr3_audit_reference_v1.json').read_bytes()
    profile = json.loads(profile_payload)
    manifest, receipt = verify_cache(args.cache, contract, policy_payload)
    tables = {name: Table.read(args.cache / name, format='ascii.ecsv') for name in PRODUCTS}
    check_units(tables[PRODUCTS[2]], {'ra': 'deg', 'dec': 'deg', 'pmra': 'mas/yr',
                                     'pmdec': 'mas/yr', 'ref_epoch': 'yr'})
    require(tables[PRODUCTS[2]].colnames == manifest['identity']['columns'], 'Source column schema mismatch')
    from wenu.objects.stars import Stars
    stars = Stars(None)
    stars.load()
    source = stars.source_catalog
    metadata = stars.catalogue_metadata.to_record()
    baseline = contract['baseline']
    ids = [identifier(x) for x in source.index]
    digest = sha256(('\n'.join(ids) + '\n').encode()).hexdigest()
    require(len(ids) == baseline['rows'] and digest == baseline['ordered_hip_ids_sha256']
            and metadata['source_sha256'] == baseline['source_sha256'], 'Current Hipparcos source differs')
    photometry = [[int(hip), 'missing' if math.isnan(float(value)) else float(value).hex()]
                  for hip, value in source.magnitude.items()]
    require(sha256(json.dumps(photometry, separators=(',', ':')).encode()).hexdigest()
            == baseline['hip_magnitude_pairs_sha256'], 'Original visual photometry differs')
    units = metadata['units']
    require(all(units.get(c) == 'mas/yr' for c in ('ra_mas_per_year', 'dec_mas_per_year')),
            'Hipparcos proper-motion units unavailable')
    fields = ['ra_degrees', 'dec_degrees', 'ra_mas_per_year', 'dec_mas_per_year', 'magnitude',
              'is_multiple', 'component_count', 'multiple_annex', 'ccdm_id', 'is_variable']
    hips = [dict(hip=identifier(i), **{c: scalar(row[c]) for c in fields}) for i, row in source.iterrows()]
    # iterrows may coerce identifiers, so IDs always come from the index above.
    best = list(table_rows(tables[PRODUCTS[0]], ('original_ext_source_id', 'source_id')))
    neighbours = list(table_rows(tables[PRODUCTS[1]], ('original_ext_source_id', 'source_id')))
    sources = list(table_rows(tables[PRODUCTS[2]], ('source_id', 'solution_id')))
    summary, hip_rows, candidate_rows = audit(hips, best, neighbours, sources, metadata, profile)
    for name in ('retained_hip_rows', 'gaia_source_rows', 'hip_with_crossmatch_candidates',
                 'hip_without_crossmatch_candidates'):
        require(summary[name] == manifest['counts'][name], 'Download count mismatch: ' + name)
    unmatched = [r['hip'] for r in hip_rows if r['category'] == 'unmatched']
    require(unmatched == json.loads((args.cache / 'crossmatch_unmatched_hip_ids_v1.json').read_text()),
            'Unmatched HIP list mismatch')
    provenance = dict(receipt, membership_sha256=digest, hip_metadata=metadata,
        software={'numpy': np.__version__, 'astropy': astropy.__version__},
        input_products=manifest['products'],
        tool_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        contract_sha256=sha256(contract_payload).hexdigest(),
        reference_profile_sha256=sha256(profile_payload).hexdigest(),
        policy_sha256=sha256(policy_payload).hexdigest())
    publish(args.output, summary, hip_rows, candidate_rows, provenance)
    print(json.dumps({k: summary[k] for k in ('retained_hip_rows', 'gaia_source_rows',
        'candidate_pairs', 'categories', 'shared_gaia_sources', 'diagnostics', 'adopted_matches')}, indent=2))
    print('AUDIT COMPLETE:', args.output.resolve())


if __name__ == '__main__':
    main()
