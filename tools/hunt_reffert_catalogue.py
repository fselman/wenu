"""Offline Hunt & Reffert (2024) member photometry and catalogue preparation.

Developer-tool owner only: never changes Wenu's installed sky layer.
CDS byte ranges are from J/A+A/686/A42/ReadMe, 08-Mar-2024.
"""

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from astropy.table import Table

CATALOGUE = 'J/A+A/686/A42'
PAPER = 'https://doi.org/10.1051/0004-6361/202348662'
TRANSFORM_URL = ('https://gea.esac.esa.int/archive/documentation/GDR3/'
    'Data_processing/chap_cu5pho/cu5pho_sec_photSystem/cu5pho_ssec_photRelations.html')
# Polynomial gives G - band, ascending powers of observed BP-RP.
# ESA DR3 documentation 1.3, Tables 5.9 and 5.10. B/R > 2 require
# confirmed M giants; absent a spectral classification we fail closed there.
TRANSFORMS = {
    'V': ([-.02704, .01424, -.2156, .01426], -.5, 5., .03017),
    'B': ([.01448, -.6874, -.3604, .06718, -.006061], -.5, 2., .0633),
    'R': ([-.02275, .3961, -.1243, -.01396, .003775], 0., 2., .03167),
}
FULL_NAME = 'open_clusters_hunt_reffert2024_v1.ecsv'
CURATED_NAME = 'open_clusters_hunt_reffert2024_v5lt11_v1.ecsv'
PROVENANCE_NAME = 'open_clusters_hunt_reffert2024_v1.provenance.json'


def gaia_to_bvr(g, bp, rp):
    """Observed Johnson B/V and Cousins R; no extrapolation or dereddening."""
    g, bp, rp = np.broadcast_arrays(np.asarray(g, float), np.asarray(bp, float), np.asarray(rp, float))
    colour = bp-rp
    result = {}
    for band, (coefficients, lower, upper, _) in TRANSFORMS.items():
        valid = np.isfinite(g) & np.isfinite(colour) & (colour > lower) & (colour < upper)
        result[band] = np.where(valid, g-np.polynomial.polynomial.polyval(colour, coefficients), np.nan)
    return result


def numeric(value):
    return float(value.strip()) if value.strip() else np.nan


def _verified_bytes(path, files):
    path = Path(path)
    data = path.read_bytes()
    expected = files.get(path.name, {})
    if (expected.get('sha256') != hashlib.sha256(data).hexdigest()
            or expected.get('bytes') != len(data)):
        raise ValueError(f'Unverified astrometry source: {path.name}')
    return data


def read_cluster_astrometry(path, readme, specification):
    """Read CDS columns using the captured ReadMe, not duplicated byte offsets.

    The versioned data specification records reviewed meanings and their source
    evidence. Units, descriptions, missing values and parsing ranges come from
    CDS. This offline ingestion service does not evaluate physical positions.
    """
    from copy import deepcopy
    from astropy import units as u

    if specification.get('schema') != 'wenu-open-cluster-astrometry-source/1':
        raise ValueError('Unsupported astrometry source specification.')
    _verified_bytes(path, specification['files'])
    _verified_bytes(readme, specification['files'])
    table = Table.read(path, format='ascii.cds', readme=str(readme))
    _verified_bytes(path, specification['files'])
    _verified_bytes(readme, specification['files'])
    fields = specification['columns']
    if not fields or not set(fields).issubset(table.colnames):
        raise ValueError('Required astrometry fields are missing.')
    for name, record in fields.items():
        column = table[name]
        if column.description != record['source_description']:
            raise ValueError(f'Changed source meaning: {name}')
        declared = record['source_unit']
        if (None if column.unit is None else str(column.unit)) != declared:
            raise ValueError(f'Changed source unit: {name}')
        if declared is not None:
            u.Unit(declared)  # Refuse unsupported declarations before publishing.
        if column.dtype.kind in 'iuf':
            values = np.asarray(column)[~np.ma.getmaskarray(column)]
            if not np.all(np.isfinite(values)):
                raise ValueError(f'Non-finite unmasked source field: {name}')
            if record.get('nonnegative') and np.any(values < 0):
                raise ValueError(f'Negative source uncertainty/count/distance: {name}')
    identity = table['ID']
    if np.any(np.ma.getmaskarray(identity)) or len(set(identity)) != len(table):
        raise ValueError('Missing or duplicate source cluster ID.')
    for fact in specification['facts'].values():
        if isinstance(fact, dict) and 'evidence_column' in fact:
            if fact['evidence'] not in table[fact['evidence_column']].description:
                raise ValueError('Astrometric declaration lacks source evidence.')
    low, middle, high = (table[name] for name in ('dist16', 'dist50', 'dist84'))
    available = ~(np.ma.getmaskarray(low) | np.ma.getmaskarray(middle) | np.ma.getmaskarray(high))
    if np.any(low[available] > middle[available]) or np.any(middle[available] > high[available]):
        raise ValueError('Unordered distance percentiles.')
    output = table[list(fields)].copy(copy_data=True)
    output.meta['astrometry_source'] = deepcopy(specification)
    return output


def _check_astrometry_join(catalogue, astrometry):
    """Refuse ID, coordinate or source mixing, including a reordered companion."""
    required = {'wenu_id', 'RA_source', 'hunt_id', 'hunt_name', 'hunt_ra_deg', 'hunt_dec_deg'}
    if not required.issubset(catalogue.colnames):
        raise ValueError('Selected catalogue lacks source identity/coordinate fields.')
    ids = list(map(str, catalogue['wenu_id']))
    if len(set(ids)) != len(ids) or ids != list(map(str, astrometry['wenu_id'])):
        raise ValueError('Astrometry must match unique selected IDs in source order.')
    if list(catalogue['RA_source']) != list(astrometry['centre_source']):
        raise ValueError('Changed centre-source assignment.')
    for index, row in enumerate(catalogue):
        missing = np.ma.is_masked(row['hunt_id'])
        if missing != np.ma.is_masked(astrometry['ID'][index]):
            raise ValueError('Conflicting Hunt availability.')
        if missing:
            if row['RA_source'] != 'dias' or any(
                    not np.ma.is_masked(astrometry[name][index])
                    for name in astrometry.meta['astrometry_source']['columns']):
                raise ValueError('Dias-only astrometry must remain unadopted and masked.')
        else:
            if (row['RA_source'] != 'hunt' or int(row['hunt_id']) != int(astrometry['ID'][index])
                    or str(row['hunt_name']) != str(astrometry['Name'][index])
                    or row['hunt_ra_deg'] != astrometry['RAdeg'][index]
                    or row['hunt_dec_deg'] != astrometry['DEdeg'][index]):
                raise ValueError('Source ID/name/centre mismatch; no cross-source substitution.')


def build_astrometry_companion(catalogue_path, source_path, readme, specification):
    """Recover only the selected clusters; all unqualified source facts stay null."""
    from copy import deepcopy
    from astropy.table import MaskedColumn

    catalogue_path = Path(catalogue_path)
    original_bytes = catalogue_path.read_bytes()
    catalogue = Table.read(catalogue_path, format='ascii.ecsv')
    source = read_cluster_astrometry(source_path, readme, specification)
    lookup = {int(identity): index for index, identity in enumerate(source['ID'])}
    indices, absent = [], []
    for value in catalogue['hunt_id']:
        missing = np.ma.is_masked(value)
        if not missing and int(value) not in lookup:
            raise ValueError('Selected Hunt cluster absent from source.')
        indices.append(0 if missing else lookup[int(value)])
        absent.append(missing)
    result = Table(dict(wenu_id=catalogue['wenu_id'].copy(),
                        centre_source=catalogue['RA_source'].copy()))
    for name in source.colnames:
        column = MaskedColumn(source[name][indices], name=name, copy=True)
        column.mask = np.ma.getmaskarray(column) | absent
        result.add_column(column)
    result.meta.update(schema='wenu-open-cluster-astrometry/1',
        selected_catalogue_sha256=hashlib.sha256(original_bytes).hexdigest(),
        selected_catalogue_name=catalogue_path.name,
        astrometry_source=deepcopy(specification),
        adoption_policy='Hunt solution for Hunt centres only; not yet propagated.',
        dias_only_policy='Retain original Dias columns in selected catalogue; epoch and RA-motion convention unresolved; no adopted solution.',
        propagation_enabled=False)
    _check_astrometry_join(catalogue, result)
    if catalogue_path.read_bytes() != original_bytes:
        raise ValueError('Selected catalogue changed during ingestion.')
    return result


def attach_cluster_astrometry(catalogue_path, companion_path, receipt_path):
    """Return an enriched independent table for explicit later admission.

    No default selector or source file is changed. The existing cluster metadata
    record mirrors the returned columns and complete source envelope unchanged.
    """
    from copy import deepcopy

    receipt = json.loads(Path(receipt_path).read_text())
    if receipt.get('schema') != 'wenu-open-cluster-astrometry-receipt/1':
        raise ValueError('Unsupported astrometry receipt.')
    data = _verified_bytes(companion_path, receipt['products'])
    companion = Table.read(data.decode('utf-8').splitlines(), format='ascii.ecsv')
    if companion.meta.get('schema') != 'wenu-open-cluster-astrometry/1':
        raise ValueError('Unsupported astrometry companion.')
    if (receipt['selected_catalogue_sha256'] != companion.meta['selected_catalogue_sha256']
            or receipt['selected_rows'] != len(companion)
            or receipt['hunt_rows'] != int(np.count_nonzero(~np.ma.getmaskarray(companion['ID'])))):
        raise ValueError('Conflicting astrometry receipt identity/counts.')
    catalogue_path = Path(catalogue_path)
    original = catalogue_path.read_bytes()
    if hashlib.sha256(original).hexdigest() != companion.meta['selected_catalogue_sha256']:
        raise ValueError('Astrometry belongs to different selected catalogue bytes.')
    catalogue = Table.read(original.decode('utf-8').splitlines(), format='ascii.ecsv')
    _check_astrometry_join(catalogue, companion)
    output = catalogue.copy(copy_data=True)
    for name in companion.meta['astrometry_source']['columns']:
        target = 'hunt_astrometry_' + name
        if target in output.colnames:
            raise ValueError('Astrometry target column already exists.')
        column = companion[name].copy()
        column.name = target
        output.add_column(column)
    output.meta['astrometry_companion'] = deepcopy(companion.meta)
    output.meta['astrometry_companion']['receipt'] = deepcopy(receipt)
    return output


def publish_astrometry_companion(table, output_directory):
    """Publish a new versioned directory atomically; refuse existing outputs."""
    import os
    import tempfile

    destination = Path(output_directory)
    if destination.exists():
        raise FileExistsError('Use a fresh versioned astrometry output directory.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        staging = Path(temporary) / 'products'
        staging.mkdir()
        path = staging / 'open_clusters_hunt_astrometry_v1.ecsv'
        table.write(path, format='ascii.ecsv')
        receipt = dict(schema='wenu-open-cluster-astrometry-receipt/1',
            products={path.name: dict(bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())},
            selected_rows=len(table), hunt_rows=int(np.count_nonzero(~np.ma.getmaskarray(table['ID']))),
            selected_catalogue_sha256=table.meta['selected_catalogue_sha256'])
        (staging / 'open_clusters_hunt_astrometry_v1.provenance.json').write_text(
            json.dumps(receipt, indent=2, allow_nan=False) + '\n')
        os.rename(staging, destination)


def astrometry_main(argv=None):
    """Offline-only CLI; acquire the small CDS source explicitly beforehand."""
    import argparse
    parser = argparse.ArgumentParser(description='Recover selected cluster astrometry from verified local CDS bytes.')
    for option in ('selected-catalogue', 'clusters', 'readme', 'specification', 'output-directory'):
        parser.add_argument('--' + option, type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output_directory.exists():
        raise FileExistsError('Use a fresh versioned astrometry output directory.')
    specification = json.loads(args.specification.read_text())
    table = build_astrometry_companion(args.selected_catalogue, args.clusters, args.readme, specification)
    publish_astrometry_companion(table, args.output_directory)
    return 0


def read_clusters(path):
    """Retain all source rows, types and aliases, plus normalized review columns."""
    rows = []
    with gzip.open(path, 'rt', encoding='ascii') as stream:
        for line in stream:
            if len(line.rstrip('\n')) != 1131:
                raise ValueError('Unexpected CDS clusters record length.')
            av = numeric(line[842:853])
            rows.append(dict(identifier=line[:20].strip(), hunt_id=int(line[21:25]),
                aliases=line[26:279].strip(), hunt_type=line[280],
                source_type_flag='', ra_deg=numeric(line[319:331]), dec_deg=numeric(line[332:344]),
                apparent_diameter_arcmin=120*numeric(line[370:381]),
                tidal_diameter_arcmin=120*numeric(line[394:405]),
                total_diameter_arcmin=120*numeric(line[406:417]),
                distance_pc=numeric(line[599:614]), av_magnitude=av,
                reddening_e_bv=av/3.1, log_age_years=numeric(line[807:818]),
                member_count=int(line[294:300]), metallicity_feh=np.nan,
                cluster_significance=numeric(line[282:293]),
                cmd_quality=numeric(line[758:768]), hunt_note=line[1098:1131].strip()))
    return Table(rows=rows)


def read_members(path):
    """Stream required fields; preserve 64-bit IDs as decimal text, never float."""
    with gzip.open(path, 'rt', encoding='ascii') as stream:
        for line in stream:
            if len(line.rstrip('\n')) != 1197:
                raise ValueError('Unexpected CDS members record length.')
            yield dict(hunt_id=int(line[29:33]), source_id=line[34:53].strip(),
                probability=numeric(line[58:78]), inrt=int(line[56]), inrj=int(line[54]),
                g=numeric(line[788:807]), bp=numeric(line[808:827]), rp=numeric(line[828:847]))


def member_statistics(clusters, members, *, minimum_probability=.5, aperture='tidal'):
    """Rank accepted members separately in each band; retain missing diagnostics."""
    if not np.isfinite(minimum_probability) or not 0 <= minimum_probability <= 1:
        raise ValueError('Membership probability must be between zero and one.')
    if aperture not in ('tidal', 'jacobi', 'all'):
        raise ValueError('Unknown member aperture.')
    groups = {int(i): [] for i in clusters['hunt_id']}
    seen = set()
    total = 0
    for star in members:
        total += 1
        identity = (star['hunt_id'], star['source_id'])
        if identity in seen:
            raise ValueError('Duplicate Gaia member within a cluster.')
        seen.add(identity)
        if star['hunt_id'] not in groups:
            raise ValueError('Member refers to an unknown cluster.')
        p = star['probability']
        if not np.isfinite(p) or not 0 <= p <= 1:
            raise ValueError('Invalid member probability.')
        if p < minimum_probability or (aperture != 'all' and not star['inrt' if aperture == 'tidal' else 'inrj']):
            continue
        groups[star['hunt_id']].append(star)
    output = clusters.copy(copy_data=True)
    records = []
    for row in clusters:
        stars = groups[int(row['hunt_id'])]
        g = np.array([s['g'] for s in stars])
        bp = np.array([s['bp'] for s in stars])
        rp = np.array([s['rp'] for s in stars])
        values = {'G': g, **gaia_to_bvr(g, bp, rp)}
        record = dict(accepted_member_count=len(stars), missing_v_members=0)
        for band, magnitudes in values.items():
            valid = np.flatnonzero(np.isfinite(magnitudes))
            order = sorted(valid, key=lambda i: (magnitudes[i], stars[i]['source_id']))
            key = band.lower()
            record[key+'_valid_members'] = len(valid)
            record[key+'_integrated'] = (float(-2.5*np.log10(np.sum(10**(-.4*magnitudes[valid]))))
                                       if len(valid) else np.nan)
            for rank in (5, 10):
                record[key+str(rank)] = float(magnitudes[order[rank-1]]) if len(order) >= rank else np.nan
            record[key+'5_source_id'] = stars[order[4]]['source_id'] if len(order) >= 5 else ''
        record['missing_v_members'] = len(stars)-record['v_valid_members']
        record['v_bright_members'] = int(np.count_nonzero(values['V'] < 11))
        record['v5_status'] = ('fewer_than_five_valid_V' if not np.isfinite(record['v5']) else
                               'partial_photometry' if record['missing_v_members'] else 'available')
        records.append(record)
    statistics = Table(rows=records)
    for column in statistics.colnames:
        output[column] = statistics[column]
    output['v_magnitude'] = output['v_integrated']
    output.meta.update(catalogue='Hunt & Reffert (2024)', paper=PAPER,
        coordinate_frame='ICRS', coordinate_epoch='J2016.0',
        diameter_definition='2*r50 (50% of members within tidal radius), arcmin',
        reddening_definition='AV50/3.1; assumed R_V=3.1, not measured E(B-V)',
        photometry='Observed member sums; no completeness correction or dereddening',
        member_policy=dict(minimum_probability=minimum_probability, aperture=aperture),
        transformations=dict(url=TRANSFORM_URL, equations='band = G - polynomial(BP-RP)',
            coefficients={k: v[0] for k,v in TRANSFORMS.items()},
            colour_limits={k: list(v[1:3]) for k,v in TRANSFORMS.items()},
            fit_scatter_mag={k: v[3] for k,v in TRANSFORMS.items()},
            note='B/R colour >2 needs confirmed M giants; conservatively omitted. R is Cousins R.'),
        source_member_rows=total)
    return output


def build(source_directory, output_directory, *, minimum_probability=.5, aperture='tidal'):
    source, destination = Path(source_directory), Path(output_directory)
    receipt = json.loads((source/'receipt.json').read_text())
    for name in ('ReadMe', 'clusters.dat.gz', 'members.dat.gz', 'crossma.dat.gz'):
        digest = hashlib.sha256()
        with (source/name).open('rb') as stream:
            while chunk := stream.read(1024*1024):
                digest.update(chunk)
        if digest.hexdigest() != receipt[name]['sha256']:
            raise ValueError('Source digest mismatch: '+name)
    paths = [destination/name for name in (FULL_NAME, CURATED_NAME, PROVENANCE_NAME)]
    if any(path.exists() for path in paths):
        raise FileExistsError('Hunt resource already exists; use a new candidate directory.')
    table = member_statistics(read_clusters(source/'clusters.dat.gz'),
        read_members(source/'members.dat.gz'), minimum_probability=minimum_probability, aperture=aperture)
    if len(table) != 7167 or table.meta['source_member_rows'] != 1291929:
        raise ValueError('Source row count differs from the published 2024 catalogue.')
    table['curated_v5lt11'] = (np.asarray(table['hunt_type']) == 'o') & (np.asarray(table['v5']) < 11)
    table['curation_reason'] = ['' if keep else 'not_open_cluster' if kind != 'o' else
        'fewer_than_five_valid_V' if not np.isfinite(value) else 'V5_not_brighter_than_11'
        for keep, kind, value in zip(table['curated_v5lt11'],table['hunt_type'],table['v5'])]
    destination.mkdir(parents=True, exist_ok=True)
    table.write(paths[0], format='ascii.ecsv')
    curated = table[np.asarray(table['curated_v5lt11'])]
    curated.meta['curation'] = 'Type o and fifth-brightest valid converted V strictly <11 mag'
    curated.write(paths[1], format='ascii.ecsv')
    provenance = dict(catalogue=CATALOGUE, paper=PAPER, source_receipts=receipt,
        source_rows=len(table), source_member_rows=table.meta['source_member_rows'], curated_rows=len(curated),
        member_policy=table.meta['member_policy'], transformations=table.meta['transformations'],
        policy_checked='2026-10-13',
        provider_policy='https://cds.unistra.fr/vizier-org/licences_vizier.html',
        redistribution='Public CDS source; retain authors/CDS/Gaia acknowledgement. No blanket CC0 claim.',
        files={p.name:dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths[:2]})
    paths[2].write_text(json.dumps(provenance, indent=2)+'\n')
    return table, provenance


def load(directory, curated=False):
    directory = Path(directory)
    name = CURATED_NAME if curated else FULL_NAME
    if not (directory/PROVENANCE_NAME).is_file():
        raise FileNotFoundError('Prepare Hunt data first with tools/query_hunt_reffert2024.py; see docs/user_guide/curation.md.')
    provenance = json.loads((directory/PROVENANCE_NAME).read_text())
    path = directory/name
    if hashlib.sha256(path.read_bytes()).hexdigest() != provenance['files'][name]['sha256']:
        raise ValueError('Hunt catalogue digest mismatch.')
    return Table.read(path), provenance, path


def compare_main(args, *, compare_function, plot_function, parameters, key_function):
    """Adapt Hunt tables to the existing comparison/plot/export owners offline."""
    if args.x == args.y:
        raise ValueError('Choose two different plot parameters.')
    for rank in (5, 10):
        limit = getattr(args, 'max_v'+str(rank))
        if limit is not None and not np.isfinite(limit):
            raise ValueError(f'--max-v{rank} must be finite.')
    directory = args.data_directory
    table, provenance, source_path = load(directory/'open_clusters', args.catalogue == 'hunt-curated')
    dias_path = directory/'open_clusters/open_clusters_dias_heasarc.ecsv'
    dias = Table.read(dias_path)
    flags = {key_function(row['identifier']): str(row['source_type_flag']) for row in dias}
    attached, evidence = [], []
    for row in table:
        matched = {flags[key] for name in [row['identifier'], *str(row['aliases']).split(',')]
                   if (key := key_function(name)) in flags}
        marked = matched & {'IR', 'E'}
        attached.append('E' if 'E' in marked else 'IR' if marked else '')
        evidence.append('marked' if marked else 'Dias_crossmatch_unflagged' if matched else 'unknown')
    table['source_type_flag'] = attached
    table['ir_embedded_evidence'] = evidence
    paths = dict(open_clusters=source_path, dias_classification=dias_path,
        caldwell=directory/'caldwell/caldwell_openngc.ecsv', messier=directory/'messier/messier_heasarc.ecsv')
    name = 'Hunt & Reffert 2024'
    annotated, crosswalk, summary = compare_function(table, Table.read(paths['caldwell']),
        Table.read(paths['messier']), exclude_ir_embedded=not args.include_infrared_embedded,
        max_ebv=args.max_ebv, min_ebv=args.min_ebv, missing_ebv=args.missing_ebv, catalogue_name=name)
    keep = np.asarray(annotated['in_amateur_sample'], dtype=bool).copy()
    reasons = [str(value) for value in annotated['selection_exclusion_reason']]
    for i, row in enumerate(annotated):
        row_reasons = ['not_open_cluster'] if row['hunt_type'] != 'o' else []
        for rank in (5, 10):
            limit = getattr(args, 'max_v'+str(rank))
            if limit is None:
                continue
            magnitude = row['v'+str(rank)]
            if not np.isfinite(magnitude):
                row_reasons.append(f'missing_V{rank}')
            elif magnitude >= limit:
                row_reasons.append(f'V{rank}_not_brighter_than_limit')
        if row_reasons:
            keep[i] = False
            reasons[i] = '|'.join(filter(None, (reasons[i], *row_reasons)))
    annotated['in_amateur_sample'] = keep
    annotated['selection_exclusion_reason'] = reasons
    summary['hunt_clusters'] = summary.pop('dias_clusters')
    summary['catalogue'] = args.catalogue
    summary['selection'].update(max_v5=args.max_v5, max_v10=args.max_v10, hunt_open_clusters_only=True,
        eligible=int(np.count_nonzero(keep)), member_policy=table.meta['member_policy'])
    # Recompute statistics after the extra Hunt type/member-magnitude criteria.
    for group, statistics in summary['samples'].items():
        selected = keep if group == name else keep & np.asarray(annotated['in_'+group.casefold()])
        statistics['clusters'] = int(np.count_nonzero(selected))
        for column in ('apparent_diameter_arcmin', 'distance_pc', 'reddening_e_bv',
                       'log_age_years', 'member_count', 'metallicity_feh'):
            values = np.asarray(table[column], float)[selected]
            values = values[np.isfinite(values) & ((values >= 0) if column == 'member_count' else True)]
            statistics[column] = dict(available=len(values), median=float(np.median(values)) if len(values) else None)
    crosswalk.rename_column('dias_identifier', 'source_identifier')
    for group in summary['catalogue_component_matches'].values():
        for field in ('unmatched', 'ambiguous', 'alias_review'):
            for edge in group[field]:
                if 'dias_identifier' in edge:
                    edge['source_identifier'] = edge.pop('dias_identifier')
    summary.update(parameter_source=dict(table.meta), photometry_provenance=provenance,
        source_sha256={key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in paths.items()},
        matching_policy='Exact normalized primary and published AllNames aliases; ambiguous identities remain unresolved.',
        notes='B/V/R are calibrated estimates. Missing photometry can make V5/V10 too faint and member sums too faint. IR/E flags are positive Dias crossmatch evidence only.')
    if not args.name or Path(args.name).name != args.name:
        raise ValueError('Output name must be a nonempty filename prefix.')
    prefix = args.output_prefix or args.output_directory/args.name
    suffixes = ['_hunt.csv','_crosswalk.csv','_summary.json','_figure.png','_figure.svg','_figure.pdf']
    if args.write_filtered_catalogue:
        suffixes.append('_filtered.ecsv')
    products = {suffix:prefix.parent/(prefix.name+suffix) for suffix in suffixes}
    if any(path.exists() for path in products.values()):
        raise FileExistsError('Output already exists; use a new versioned prefix.')
    prefix.parent.mkdir(parents=True, exist_ok=True)
    # Restore shared parameter labels even across sequential library calls.
    replacements = dict(diameter=('apparent_diameter_arcmin','Hunt diameter 2r50 (arcmin)',True),
        ebv=('reddening_e_bv','E(B−V) proxy = AV50/3.1 (mag)',False),
        brightness=('v_magnitude','Summed converted member V magnitude',False))
    original = {key:parameters[key] for key in replacements}
    try:
        parameters.update(replacements)
        summary['plot_parameter_availability'] = plot_function(annotated,prefix,args.x,args.y,name)
    finally:
        parameters.update(original)
    annotated.write(products['_hunt.csv'], format='ascii.csv')
    crosswalk.write(products['_crosswalk.csv'], format='ascii.csv')
    if args.write_filtered_catalogue:
        selected = annotated[keep]
        selected.meta.update(selection=summary['selection'],source_sha256=summary['source_sha256'])
        selected.write(products['_filtered.ecsv'],format='ascii.ecsv')
    products['_summary.json'].write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    for path in products.values():
        print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(astrometry_main())
