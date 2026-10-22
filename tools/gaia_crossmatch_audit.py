#!/usr/bin/env python3
"""Retain published Hipparcos-2 Gaia associations from a verified offline cache.

Published associations are separate from astrometric-solution usability. This
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
import re
from copy import deepcopy

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


def parse_kervella_table(payload, readme, profile):
    """Read published A.1 identifiers exactly; never recompute the crossmatch."""
    require(sha256(payload).hexdigest() == profile['expanded_table']['sha256']
            and len(payload) == profile['expanded_table']['bytes'], 'Kervella table identity differs')
    metadata = next(r for r in profile['resources'] if r['filename'] == 'ReadMe')
    require(sha256(readme).hexdigest() == metadata['sha256'] and len(readme) == metadata['bytes'],
            'Kervella ReadMe identity differs')
    description = readme.decode('ascii')
    require('Byte-by-byte Description of file: tablea1.dat' in description,
            'Kervella table description missing')
    section = description.split('Byte-by-byte Description of file: tablea1.dat', 1)[1].split('Note (1):', 1)[0]
    declared = {}
    for line in section.splitlines():
        m = re.match(r'^\s*(\d+)(?:-\s*(\d+))?\s+\S+\s+(\S+)\s+(\S+)\s+', line)
        if m:
            declared[m[4]] = (int(m[1]), int(m[2] or m[1]), m[3])
    for name, spec in profile['columns'].items():
        require(declared.get(name) == (spec['first_byte'], spec['last_byte'], spec['unit']),
                'Published Kervella column layout differs: ' + name)
    lines = payload.splitlines()
    require(len(lines) == profile['rows'], 'Published Kervella row count differs')
    result, seen = [], set()
    for number, line in enumerate(lines, 1):
        require(len(line) == profile['record_length'], 'Kervella record length differs')
        record = {'source_row_number': number, 'record_sha256': sha256(line).hexdigest()}
        for name, spec in profile['columns'].items():
            text = line[spec['first_byte']-1:spec['last_byte']].decode('ascii').strip()
            if spec['kind'] == 'identifier':
                require(not text or (text.isdigit() and int(text) > 0), 'Invalid Kervella integer ID: ' + name)
                record[name] = str(int(text)) if text else None
            elif spec['kind'] == 'number':
                value = float(text) if text else None
                require(value is None or math.isfinite(value), 'Non-finite Kervella field: ' + name)
                record[name] = value
            else:
                record[name] = text or None
        require(record['HIP'] is not None and record['HIP'] not in seen, 'Missing/duplicate Kervella HIP')
        seen.add(record['HIP'])
        result.append(record)
    return result


def supplement_kervella(summary, hips, records, profile):
    """Supplement exact HIP keys while preserving every accepted primary link."""
    require(profile['gaia_identity_bridge']['from_release'] == 'EDR3'
            and profile['gaia_identity_bridge']['to_release'] == 'DR3'
            and profile['gaia_identity_bridge']['policy'] == 'ESA-explicit-identical-source-list',
            'Missing explicit EDR3/DR3 source-list bridge')
    by_hip = {r['HIP']: r for r in records}
    require(len(by_hip) == len(records), 'Duplicate Kervella HIP')
    old_hip_ids = [r['hip'] for r in hips]
    require(len(set(old_hip_ids)) == len(old_hip_ids), 'Duplicate retained HIP')
    retained = set(old_hip_ids)
    counts = Counter()
    output = []
    primary = {r['hip']: deepcopy(r['published_association']) for r in hips if r['published_association']}
    for original in hips:
        row = dict(original)
        row['primary_candidate_category'] = original['category']
        evidence = by_hip.get(row['hip'])
        association = row['published_association']
        row['kervella_evidence'] = evidence
        if evidence is None:
            state = 'not_in_published_table'
        elif evidence['GaiaEDR3'] is None:
            state = 'no_published_edr3_id'
            if evidence['GaiaDR2'] is not None:
                counts['dr2_only_evidence'] += 1
        elif association:
            state = 'agreement' if association['source_id'] == evidence['GaiaEDR3'] else 'conflict_primary_preserved'
        else:
            state = 'supplement_added'
            row['published_association'] = {
                'hip': row['hip'], 'catalogue': 'Gaia', 'release': 'EDR3',
                'source_id': evidence['GaiaEDR3'],
                'equivalent_dr3_identity': {'release': 'DR3', 'source_id': evidence['GaiaEDR3'],
                    'bridge': profile['gaia_identity_bridge']},
                'method': 'Kervella et al. 2022 published Table A.1; exact HIP key',
                'decision': 'retained_kervella_published_association',
                'citation': profile['citation'], 'source_catalogue': profile['catalogue'],
                'source_table_sha256': profile['expanded_table']['sha256'],
                'evidence': evidence}
        row['kervella_status'] = state
        row['association_status'] = ('primary_retained' if row['hip'] in primary
                                     else 'supplemented' if state == 'supplement_added'
                                     else 'unassociated')
        counts[state] += 1
        output.append(row)
    require([r['hip'] for r in output] == old_hip_ids, 'Supplement changed HIP membership/order')
    require(all(r['published_association'] == primary[r['hip']] for r in output if r['hip'] in primary),
            'Supplement changed an accepted primary association')
    associated = [r for r in output if r['published_association'] is not None]
    source_claims = defaultdict(list)
    for row in associated:
        source_claims[row['published_association']['source_id']].append(row['hip'])
    for row in output:
        association = row['published_association']
        row['association_shared_hip_ids'] = source_claims[association['source_id']] if association else []
    report = deepcopy(summary)
    report['primary_published_associations'] = len(primary)
    report['retained_published_associations'] = len(associated)
    report['hip_without_published_association'] = len(output) - len(associated)
    report['association_policy'] = 'primary-best-neighbour-plus-kervella-table-a1/1'
    report['primary_candidate_categories'] = deepcopy(report['categories'])
    report['categories_scope'] = 'Original primary candidate tables only; combined coverage uses retained_published_associations and hip_without_published_association'
    report['kervella_supplement'] = {
        'catalogue': profile['catalogue'], 'citation': profile['citation'], 'rows': len(records),
        'rows_with_edr3_id': sum(r['GaiaEDR3'] is not None for r in records),
        'rows_outside_retained_hip_population': sum(r['HIP'] not in retained for r in records),
        'statuses': dict(counts), 'new_associations': counts['supplement_added'],
        'dr2_only_evidence': counts['dr2_only_evidence'],
        'shared_gaia_sources_after_supplement': sum(len(v) > 1 for v in source_claims.values()),
        'primary_associations_preserved': True,
        'new_gaia_source_parameters': 'not acquired; this supplement retains published identities only'}
    # Fixed half-magnitude bins preserve original V; missing values remain separate.
    def histogram(rows):
        values = [r['original']['magnitude'] for r in rows if r['original']['magnitude'] is not None]
        bins = Counter(math.floor(v * 2) for v in values)
        return {'missing_magnitude': len(rows)-len(values), 'bins': [
            {'v_min': k/2, 'v_max': (k+1)/2, 'count': bins[k]}
            for k in range(min(bins, default=0), max(bins, default=-1)+1)]}
    report['association_magnitude_histograms'] = {
        'unassociated_before': histogram([r for r in hips if r['published_association'] is None]),
        'newly_associated': histogram([r for r in output if r['kervella_status'] == 'supplement_added']),
        'unassociated_after': histogram([r for r in output if r['published_association'] is None])}
    return report, output


def audit(hips, best, neighbours, sources, hip_metadata, gaia_profile, *, diagnostics=False):
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
    require(all(len(rows) == 1 for rows in by_hip['best'].values()),
            'Contradictory published best-neighbour rows for one HIP')
    epoch = hip_metadata['epoch']
    hip_time = Time(epoch['value'], format=epoch['format'], scale=epoch['scale']) if diagnostics else None
    hip_target = float(getattr(hip_time, gaia_profile['epoch_scale']).jyear) if diagnostics else None
    # Conversion is only between catalogue epochs: no UTC, IERS or observer data.
    epochs = sorted({row['ref_epoch'] for row in sources if row['ref_epoch'] is not None}) if diagnostics else []
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
            reasons = []
            if set(b) - set(n) or len(b) != 1:
                reasons.append('best_neighbourhood_inconsistent')
            if any(len(claims[sid]) > 1 for sid in ids):
                reasons.append('shared_gaia_source')
            if hip.get('is_multiple'):
                reasons.append('original_multiple_system')
                reasons.append('component_identity_needs_review')
        for reason in reasons:
            warnings[reason] += 1
        association = None
        if b:
            sid = next(iter(b))
            association = {'catalogue': 'Gaia', 'release': 'DR3', 'source_id': sid,
                'hip': key, 'intermediate_catalogue': 'Hipparcos-2',
                'method': 'gaiadr3.hipparcos2_best_neighbour',
                'decision': 'retained_published_association', 'evidence': b[sid]}
            counts['retained_published_associations'] += 1
        hip_records.append({'hip': key, 'category': category, 'candidate_count': len(ids),
                            'candidate_source_ids': ids, 'review_reasons': reasons,
                            'pivot': 'exact HIP key: ESA-1997-I/239 -> Hipparcos-2 -> Gaia DR3',
                            'pivot_evidence_present': bool(ids),
                            'published_association': association,
                            'original': hip, 'adopted_solution': None})
        for sid in ids:
            source = source_map[sid]
            t = source['ref_epoch']
            at_hip, at_gaia = None, None
            diagnostic_status = 'not_requested'
            if diagnostics:
                try:
                    require(t is None or t == gaia_profile['expected_ref_epoch'], 'Unexpected Gaia reference epoch')
                    original = unit_direction(hip['ra_degrees'], hip['dec_degrees'])
                    gaia_native = unit_direction(source['ra'], source['dec'])
                    back = None if t is None else unit_direction(source['ra'], source['dec'],
                        source['pmra'], source['pmdec'], hip_target - t)
                    forward = None if t is None else unit_direction(hip['ra_degrees'], hip['dec_degrees'],
                        hip['ra_mas_per_year'], hip['dec_mas_per_year'], epoch_deltas[t])
                    at_hip, at_gaia = separation(original, back), separation(forward, gaia_native)
                    diagnostic_status = 'evaluated' if at_hip is not None and at_gaia is not None else 'missing_input'
                except ValueError as error:
                    diagnostic_status = 'unavailable: ' + str(error)
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
                'diagnostic_status': diagnostic_status,
                'diagnostic_missing_input': at_hip is None or at_gaia is None,
                'decision': 'retained_published_association' if sid in b else 'neighbourhood_alternative',
                'adopted_solution': None})
    summary = {'retained_hip_rows': len(hips), 'gaia_source_rows': len(sources),
               'candidate_pairs': len(candidates), 'adopted_astrometric_solutions': 0,
               'retained_published_associations': counts['retained_published_associations'],
               'hip_without_published_association': len(hips) - counts['retained_published_associations'],
               'association_policy': 'retain-published-hipparcos2-best-neighbour/1',
               'hip_with_crossmatch_candidates': len(hips) - counts['unmatched'],
               'hip_without_crossmatch_candidates': counts['unmatched'],
               'categories': {k: counts[k] for k in ('unmatched', 'unique_candidate', 'multiple_candidates')},
               'diagnostics': {k: counts[k] for k in ('candidates_with_gaia_back_diagnostic',
                                                     'candidates_with_hip_forward_diagnostic')},
               'shared_gaia_sources': sum(len(v) > 1 for v in claims.values()),
               'pivot': 'exact HIP identifier; no 1997-to-Hipparcos-2 positional rematching',
               'hip_review_reasons': dict(warnings),
               'hip_epoch': epoch, 'gaia_reference': gaia_profile,
               'diagnostics_requested': diagnostics,
               'diagnostic_model': 'normalized linear tangent direction; PM-only; source-scale Julian years',
               'limits': ['Published best-neighbour association retained; no independent rematching',
                          'Alternative neighbourhood candidates preserved without selecting them',
                          'Association retention is separate from astrometric-solution/model admission',
                          'No distance/RV/perspective/binary or covariance model',
                          'Separations are diagnostics, not match thresholds or accuracy claims',
                          'Missing candidate is not physical absence from Gaia',
                          'Published associations retained without downloading 2007 astrometry']}
    summary['quality_inventory'] = {
        'solution_types': dict(Counter(str(s.get('astrometric_params_solved')) for s in sources)),
        'sources_missing_pm': sum(s['pmra'] is None or s['pmdec'] is None for s in sources),
        'sources_missing_rv': sum(s.get('radial_velocity') is None for s in sources),
        'sources_with_nonpositive_parallax': sum(s.get('parallax') is not None and s['parallax'] <= 0 for s in sources),
        'best_xm_flags': dict(Counter(str(r.get('xm_flag')) for r in best)),
        'neighbourhood_xm_flags': dict(Counter(str(r.get('xm_flag')) for r in neighbours)),
    }
    return summary, hip_records, candidates


def parse_hipparcos2(payload, readme, profile):
    """Source-bound Hip2 values; native radians and upper-triangular weights retained."""
    def identity(raw):
        return {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}
    require(identity(payload) == profile['expanded_table'], 'Hipparcos-2 table identity differs')
    spec = next(r for r in profile['resources'] if r['filename'] == 'ReadMe')
    require(identity(readme) == {k: spec[k] for k in ('bytes', 'sha256')},
            'Hipparcos-2 ReadMe identity differs')
    section = readme.decode('ascii').split('Byte-by-byte Description of file: hip2.dat', 1)[1]
    section = section.split('Note (1):', 1)[0]
    declared = {}
    for line in section.splitlines():
        m = re.match(r'^\s*(\d+)(?:-\s*(\d+))?\s+\S+\s+(\S+)\s+(\S+)\s+', line)
        if m:
            declared[m[4]] = (int(m[1]), int(m[2] or m[1]), m[3])
    for name, spec in profile['columns'].items():
        require(declared.get(name) == (spec['first_byte'], spec['last_byte'], spec['unit']),
                'Hipparcos-2 column layout differs: ' + name)
    lines = payload.splitlines()
    require(len(lines) == profile['rows'], 'Hipparcos-2 row count differs')
    output = {}
    for number, line in enumerate(lines, 1):
        require(len(line) == profile['record_length'], 'Hipparcos-2 record length differs')
        row = {'source_row_number': number, 'record_sha256': sha256(line).hexdigest(),
               'original_record_ascii': line.decode('ascii')}
        for name, spec in profile['columns'].items():
            text = line[spec['first_byte']-1:spec['last_byte']].decode('ascii').strip()
            if name == 'HIP':
                require(text.isascii() and text.isdigit() and int(text) > 0, 'Invalid Hipparcos-2 HIP')
                value = str(int(text))
            elif spec['kind'] == 'integer':
                require(text.isdigit(), 'Invalid Hipparcos-2 integer')
                value = int(text)
            elif name == 'UW':
                value = [float(line[i:i+7]) for i in range(spec['first_byte']-1, spec['last_byte'], 7)]
                require(len(value) == 15 and all(math.isfinite(v) for v in value), 'Invalid Hip2 weights')
            else:
                value = float(text) if text else None
                require(value is None or math.isfinite(value), 'Non-finite Hipparcos-2 value')
            row[name] = value
        key = row['HIP']
        require(key not in output, 'Duplicate Hipparcos-2 HIP')
        require(row['RArad'] is not None and 0 <= row['RArad'] < 2*math.pi
            and row['DErad'] is not None and abs(row['DErad']) <= math.pi/2,
            'Hipparcos-2 coordinates outside domain')
        output[key] = row
    return output


def astrometric_coverage(summary, hips, sources, hip2, profile):
    """Inventory available measurements, never admit a propagation model."""
    by_source = {s['source_id']: s for s in sources}
    require(len(by_source) == len(sources), 'Duplicate coverage Gaia source')
    counts, gaia_counts, fallback_reasons = Counter(), Counter(), Counter()
    output = []
    for original in hips:
        row = deepcopy(original)
        association = row['published_association']
        s = by_source.get(association['source_id']) if association else None
        require(association is None or s is not None, 'Associated Gaia source parameters missing')
        def available(source, fields):
            return source is not None and all(source.get(k) is not None
                and isinstance(source[k], (int, float)) and math.isfinite(source[k]) for k in fields)
        position = available(s, ('ra', 'dec', 'ref_epoch'))
        if position:
            require(0 <= s['ra'] < 360 and abs(s['dec']) <= 90
                    and s['ref_epoch'] == summary['gaia_reference']['expected_ref_epoch'],
                    'Invalid Gaia reference coordinates')
        full = position and available(s, ('pmra', 'pmdec', 'parallax'))
        code = s.get('astrometric_params_solved') if s else None
        status = ('unassociated' if s is None else
            'five_parameter' if code == 31 and full else
            'six_parameter' if code == 95 and full else
            'position_only' if code == 3 and position else
            'unknown_solution_type' if code not in (3, 31, 95) else 'incomplete_astrometry')
        gaia_counts[status] += 1
        use_gaia = status in ('five_parameter', 'six_parameter')
        fallback = hip2.get(row['hip'])
        hip2_motion = available(fallback, ('RArad', 'DErad', 'Plx', 'pmRA', 'pmDE'))
        choice = 'gaia' if use_gaia else 'hipparcos2' if hip2_motion else 'original_1997_lookup'
        counts[choice] += 1
        if not use_gaia:
            fallback_reasons[status] += 1
        row['astrometric_coverage'] = {
            'gaia_status': status, 'gaia_solution_type': code,
            'preferred_available_input': choice, 'model_adopted': False,
            'gaia_source': s, 'gaia_reference': summary['gaia_reference'],
            'gaia_positive_parallax': bool(s and s.get('parallax') is not None and s['parallax'] > 0),
            'gaia_radial_velocity_available': available(s, ('radial_velocity',)),
            'hipparcos2_present': fallback is not None,
            'hipparcos2_motion_inputs_available': hip2_motion,
            'hipparcos2_solution_type': fallback['Sn'] if fallback else None,
            'hipparcos2_requires_special_model': bool(fallback and fallback['Sn'] % 10 != 5),
            'hipparcos2_fallback_source': fallback if not use_gaia else None,
            'hipparcos2_reference': profile['reference'],
            'fallback_reason': None if use_gaia else status,
            'radial_velocity_policy': 'No Hip2 RV; no component or companion RV is borrowed',
            'limits': 'Measurement availability only; quality, covariance, distance inference and model admission separate'}
        output.append(row)
    report = deepcopy(summary)
    report['astrometric_coverage'] = {
        'gaia_statuses': dict(gaia_counts), 'preferred_available_inputs': dict(counts),
        'fallback_reasons': dict(fallback_reasons),
        'hipparcos2_rows': len(hip2),
        'retained_entries_absent_from_hipparcos2': sum(r['hip'] not in hip2 for r in hips),
        'adopted_astrometric_solutions': 0,
        'policy': 'Gaia 31/95 with position/parallax/PM inputs; otherwise Hip2 inputs; original lookup retained if absent/incomplete',
        'quality_policy': 'Flags retained; no RUWE threshold or independent identity veto',
        'limits': 'Input inventory is not scientific model or production-provider admission'}
    require(len(output) == len(hips), 'Coverage changed membership')
    return report, output


def publish(output, summary, hips, candidates, provenance, *, version=2):
    """Refuse overwrite; publish the completion manifest last; clean up on failure."""
    output = Path(output)
    require(version in (2, 3, 4), 'Unsupported audit report version')
    require(not output.exists(), 'Report output already exists; choose a new version')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.' + output.name + '-', dir=output.parent))
    try:
        for name, rows in ((f'hip_review_v{version}.jsonl', hips), (f'candidate_evidence_v{version}.jsonl', candidates)):
            with (temporary / name).open('w') as stream:
                for row in rows:
                    stream.write(json.dumps(row, allow_nan=False) + '\n')
        fields = ['hip', 'source_id', 'separation_at_hip_epoch_arcsec', 'separation_at_gaia_epoch_arcsec']
        with (temporary / f'candidate_separations_v{version}.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for row in candidates:
                writer.writerow({k: row[k] for k in fields})
        summary = dict(summary, provenance=provenance)
        (temporary / f'summary_v{version}.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
        with (temporary / f'published_associations_v{version}.jsonl').open('w') as stream:
            for row in hips:
                if row.get('published_association') is not None:
                    stream.write(json.dumps(row['published_association'], allow_nan=False) + '\n')
        products = {p.name: {'sha256': sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
                    for p in temporary.iterdir()}
        (temporary / f'audit_manifest_v{version}.json').write_text(json.dumps(
            {'schema': f'wenu-gaia-candidate-audit/{version}', 'complete': True, 'products': products}, indent=2) + '\n')
        # mkdir reserves the destination without clobbering another invocation.
        output.mkdir()
        try:
            for p in sorted(temporary.iterdir(), key=lambda p: p.name == f'audit_manifest_v{version}.json'):
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
    parser.add_argument('--diagnostics', action='store_true',
                        help='Optional 1997/Gaia motion diagnostics; never veto published associations')
    parser.add_argument('--kervella-source', type=Path,
                        help='Verified external Kervella Table A.1 capture; supplement unassociated HIP entries')
    parser.add_argument('--astrometry-source', type=Path,
                        help='Verified explicit Gaia/Hipparcos-2 capture; report measurement coverage only')
    args = parser.parse_args(argv)
    require(args.astrometry_source is None or args.kervella_source is not None,
            'Astrometry coverage requires the published Kervella associations')
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
    summary, hip_rows, candidate_rows = audit(hips, best, neighbours, sources, metadata, profile,
                                             diagnostics=args.diagnostics)
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
    version = 2
    if args.kervella_source is not None:
        from fetch_kervella_catalogue import verify_capture
        supplement_payload = (data / 'kervella_association_source_v1.json').read_bytes()
        supplement_profile = json.loads(supplement_payload)
        source_dir = args.kervella_source.expanduser()
        capture = verify_capture(source_dir, supplement_payload)
        kervella_rows = parse_kervella_table((source_dir / 'tablea1.dat').read_bytes(),
            (source_dir / 'ReadMe').read_bytes(), supplement_profile)
        summary, hip_rows = supplement_kervella(summary, hip_rows, kervella_rows, supplement_profile)
        provenance['kervella_capture'] = capture
        provenance['kervella_profile_sha256'] = sha256(supplement_payload).hexdigest()
        version = 3
    if args.astrometry_source is not None:
        from fetch_stellar_astrometry import plan, verify_capture
        astrometry_payload = (data / 'stellar_astrometry_acquisition_v1.json').read_bytes()
        astrometry_profile = json.loads(astrometry_payload)
        identity = plan(hip_rows, tables[PRODUCTS[2]], manifest['identity']['columns'],
                        receipt['download_manifest_sha256'], astrometry_payload)
        hip2, extra, capture_receipt = verify_capture(args.astrometry_source.expanduser(), identity,
                                                     astrometry_profile)
        summary, hip_rows = astrometric_coverage(summary, hip_rows, sources + extra, hip2,
                                                astrometry_profile['hipparcos2'])
        summary['astrometric_coverage']['additional_gaia_source_rows'] = len(extra)
        summary['astrometric_coverage']['total_cached_gaia_source_rows'] = len(sources) + len(extra)
        summary['kervella_supplement']['new_gaia_source_parameters'] = (
            'Acquired separately in the verified astrometry capture; see astrometric_coverage')
        summary['limits'] = [v for v in summary['limits']
                             if v != 'Published associations retained without downloading 2007 astrometry']
        summary['limits'].append('Hipparcos-2 captured for fallback only; published associations unchanged')
        provenance['astrometry_capture'] = capture_receipt
        version = 4
    publish(args.output, summary, hip_rows, candidate_rows, provenance, version=version)
    display = {k: summary[k] for k in ('retained_hip_rows', 'gaia_source_rows',
        'candidate_pairs', 'categories', 'shared_gaia_sources', 'retained_published_associations',
        'hip_without_published_association', 'adopted_astrometric_solutions')}
    if version >= 3:
        display['primary_candidate_categories'] = display.pop('categories')
    print(json.dumps(display, indent=2))
    if version >= 3:
        print(json.dumps(summary['kervella_supplement'], indent=2))
    if version == 4:
        print(json.dumps(summary['astrometric_coverage'], indent=2))
    print('AUDIT COMPLETE:', args.output.resolve())


if __name__ == '__main__':
    main()
