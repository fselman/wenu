#!/usr/bin/env python3
"""Compare packaged Dias open clusters with Caldwell and Messier membership.

Joins use explicit catalogue identifiers, never nearest-position guesses.
Spatial and physical parameters come from the same Dias rows for every sample;
V photometry comes from a separately source-traced OpenNGC supplement.
Original catalogue files and chart defaults remain intact. Selection is exported
as annotations and, optionally, a separate filtered catalogue.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re

from astropy.table import Table
import numpy as np

from wenu.objects.open_clusters import OpenClusters


def identifier_key(value):
    value = str(value).strip()
    match = re.fullmatch(r'(NGC|IC|Melotte|Mel|Collinder)\s*0*(\d+)', value, re.IGNORECASE)
    if match:
        prefix = 'melotte' if match[1].casefold() == 'mel' else match[1].casefold()
        return prefix + str(int(match[2]))
    return ''.join(value.casefold().split())


def compare(dias, caldwell, messier, *, exclude_ir_embedded=False,
            max_ebv=None, min_ebv=None, missing_ebv='exclude'):
    lookup = {}
    for index, name in enumerate(dias['identifier']):
        lookup.setdefault(identifier_key(name), []).append(index)
    edges = []
    memberships = {'Caldwell': [[] for _ in dias], 'Messier': [[] for _ in dias]}

    def add(catalogue, designation, component, aliases=()):
        direct = lookup.get(identifier_key(component), []) if component else []
        alternatives = sorted({i for alias in aliases for i in lookup.get(identifier_key(alias), [])})
        candidates = direct if direct else alternatives
        chosen = candidates[0] if len(candidates) == 1 else None
        status = 'unmatched' if not candidates else 'ambiguous' if len(candidates) > 1 else 'matched'
        method = 'exact_identifier' if direct else 'explicit_alias' if alternatives else ''
        other_aliases = [i for i in alternatives if i not in direct]
        if chosen is not None:
            memberships[catalogue][chosen].append(designation)
        edges.append(dict(catalogue=catalogue, designation=designation, component=component,
            dias_identifier='' if chosen is None else str(dias['identifier'][chosen]),
            status=status, match_method=method,
            candidate_identifiers='|'.join(str(dias['identifier'][i]) for i in candidates),
            other_alias_rows='|'.join(str(dias['identifier'][i]) for i in other_aliases)))

    for row in caldwell:
        if str(row['membership_type']) not in ('open_cluster', 'open_cluster_group', 'cluster_with_nebulosity'):
            continue
        components = str(row['cluster_components']).split('|')
        aliases = ([] if np.ma.is_masked(row['related_aliases'])
                   else str(row['related_aliases']).split('|'))
        for component in components:
            add('Caldwell', str(row['name']), component, aliases if len(components) == 1 else ())
    for row in messier:
        if str(row['object_type']).strip() != 'OC':
            continue
        designation = str(row['name']).strip()
        # M45 has no alt_name in the packaged HEASARC table. Its explicit
        # Melotte 22 identity is supplied by OpenNGC's Mel022/M=045 record.
        component = 'Melotte 22' if identifier_key(designation) == 'm45' else str(row['alt_name']).strip()
        add('Messier', designation, component)

    annotated = OpenClusters.mark_amateur_exclusions(dias)
    for catalogue, values in memberships.items():
        annotated[catalogue.casefold()+'_designations'] = ['|'.join(sorted(set(v))) for v in values]
        annotated['in_'+catalogue.casefold()] = [bool(v) for v in values]
    eligible = (~np.asarray(annotated['excluded_ir_embedded']) if exclude_ir_embedded
                else np.ones(len(dias), dtype=bool))
    eligible, reasons = selection_mask(annotated, eligible, max_ebv, min_ebv, missing_ebv)
    annotated['in_amateur_sample'] = eligible
    annotated['selection_exclusion_reason'] = reasons
    summary = dict(dias_clusters=len(dias), catalogue_component_matches={}, samples={},
        selection=dict(exclude_ir_embedded=exclude_ir_embedded, max_ebv=max_ebv,
            min_ebv=min_ebv, missing_ebv=missing_ebv,
            marked_ir_embedded=int(np.count_nonzero(annotated['excluded_ir_embedded'])),
            eligible=int(np.count_nonzero(eligible)), retained_catalogue_rows=len(dias)))
    for catalogue in memberships:
        selected = [edge for edge in edges if edge['catalogue'] == catalogue]
        summary['catalogue_component_matches'][catalogue] = dict(
            entries=len({e['designation'] for e in selected}), components=len(selected),
            matched=sum(e['status'] == 'matched' for e in selected),
            unmatched=[e for e in selected if e['status'] == 'unmatched'],
            ambiguous=[e for e in selected if e['status'] == 'ambiguous'],
            alias_review=[e for e in selected if e['other_alias_rows']])
    for name, keep in [('Dias', eligible),
            ('Caldwell', np.asarray(annotated['in_caldwell']) & eligible),
            ('Messier', np.asarray(annotated['in_messier']) & eligible)]:
        statistics = {'clusters': int(np.count_nonzero(keep))}
        for column in ('apparent_diameter_arcmin', 'distance_pc', 'reddening_e_bv',
                       'log_age_years', 'member_count', 'metallicity_feh'):
            values = np.asarray(dias[column], dtype=float)[keep]
            values = values[np.isfinite(values) & ((values >= 0) if column == 'member_count' else True)]
            statistics[column] = dict(available=len(values),
                median=float(np.median(values)) if len(values) else None)
        summary['samples'][name] = statistics
    return annotated, Table(rows=edges), summary


def openngc_photometry(dias, sources):
    """Attach V measurements by explicit identities; preserve missing/review cases."""
    index = {}
    for name, (_, row) in sources.items():
        keys = [name, *row['Identifiers'].split(',')]
        for key in keys:
            if key.strip():
                index.setdefault(identifier_key(key), set()).add(name)
    def resolve(name):
        visited = set()
        while sources[name][1]['Type'] == 'Dup':
            if name in visited:
                raise ValueError('OpenNGC duplicate cycle.')
            visited.add(name)
            row = sources[name][1]
            links = [(prefix, row[prefix]) for prefix in ('NGC','IC') if row[prefix].strip()]
            if len(links) != 1 or not links[0][1].isdigit():
                return None
            name = links[0][0]+links[0][1].zfill(4)
            if name not in sources:
                return None
        return name
    primary = {identifier_key(name): name for name in sources}
    records = []
    for identifier in dias['identifier']:
        key = identifier_key(identifier)
        names = {primary[key]} if key in primary else index.get(key, set())
        targets = {resolve(name) for name in names}
        targets.discard(None)
        record = dict(identifier=str(identifier), v_magnitude=np.nan,
            photometry_source_id='', photometry_status='unmatched', photometry_match_method='',
            photometry_candidates='|'.join(sorted(targets)), v_source_code='', photometry_notes='')
        if len(targets) > 1:
            record['photometry_status'] = 'ambiguous'
        elif len(targets) == 1:
            target = next(iter(targets))
            row = sources[target][1]
            record['v_source_code'] = '|'.join(code for code in row['Sources'].split('|') if code.startswith('V-Mag:'))
            record['photometry_notes'] = '|'.join(filter(None, (row['OpenNGC notes'], row['NED notes'])))
            record['photometry_source_id'] = target
            record['photometry_match_method'] = 'primary_identifier' if key in primary else 'explicit_alias'
            if row['Type'] not in ('OCl', 'Cl+N'):
                record['photometry_status'] = 'type_conflict'
            elif row['V-Mag'].strip():
                record['v_magnitude'] = float(row['V-Mag'])
                record['photometry_status'] = 'measured_V'
            else:
                record['photometry_status'] = 'missing_V'
        records.append(record)
    counts = {}
    for record in records:
        target = record['photometry_source_id']
        if target:
            counts[target] = counts.get(target, 0)+1
    for record in records:
        record['photometry_identity_review'] = counts.get(record['photometry_source_id'], 0) > 1
    table = Table(rows=records)
    table['v_magnitude'].unit = 'mag'
    return table


PARAMETERS = {
    'diameter': ('apparent_diameter_arcmin', 'Angular diameter (arcmin)', True),
    'members': ('member_count', 'Estimated member count (richness proxy)', True),
    'brightness': ('v_magnitude', 'Integrated apparent V magnitude', False),
    'distance': ('distance_pc', 'Heliocentric distance (pc)', True),
    'ebv': ('reddening_e_bv', 'E(B−V) (mag)', False),
    'log_age': ('log_age_years', 'log₁₀ age (yr)', False),
    'metallicity': ('metallicity_feh', '[Fe/H] (dex)', False),
    'physical_diameter': ('physical_diameter_pc', 'Projected diameter (pc; derived)', True),
}


def selection_mask(table, eligible, max_ebv, min_ebv, missing_ebv):
    for limit in (max_ebv, min_ebv):
        if limit is not None and (isinstance(limit, bool) or not np.isfinite(limit) or limit < 0):
            raise ValueError('E(B-V) bounds must be finite and non-negative.')
    if max_ebv is not None and min_ebv is not None and min_ebv > max_ebv:
        raise ValueError('Minimum E(B-V) exceeds maximum.')
    if missing_ebv not in ('exclude', 'include'):
        raise ValueError('Invalid missing E(B-V) policy.')
    keep = eligible.copy()
    reasons = [str(table['amateur_exclusion_reason'][i]) if not keep[i] else ''
               for i in range(len(table))]
    ebv = np.asarray(table['reddening_e_bv'], dtype=float)
    if max_ebv is not None or min_ebv is not None:
        for i, value in enumerate(ebv):
            reason = ('missing_E_BV' if not np.isfinite(value) and missing_ebv == 'exclude' else
                      'above_max_E_BV' if np.isfinite(value) and max_ebv is not None and value > max_ebv else
                      'below_min_E_BV' if np.isfinite(value) and min_ebv is not None and value < min_ebv else '')
            if reason:
                keep[i] = False
                reasons[i] = '|'.join(filter(None, (reasons[i], reason)))
    return keep, reasons


def plot_comparison(table, prefix, x_parameter='diameter', y_parameter='members'):
    """Plot chosen measured/derived parameters with categorical missing margins."""
    import matplotlib.pyplot as plt
    if x_parameter == y_parameter:
        raise ValueError('Choose two different plot parameters.')
    eligible = np.asarray(table['in_amateur_sample'], dtype=bool)
    def values(parameter):
        column, label, logarithmic = PARAMETERS[parameter]
        if parameter == 'physical_diameter':
            diameter = np.asarray(table['apparent_diameter_arcmin'], dtype=float)
            distance = np.asarray(table['distance_pc'], dtype=float)
            value = 2*distance*np.tan(np.radians(diameter/60)/2)
            value[(diameter <= 0) | (distance <= 0)] = np.nan
        else:
            value = np.asarray(table[column], dtype=float)
        valid = np.isfinite(value) & ((value > 0) if logarithmic else True)
        return value, valid, label, logarithmic
    x, valid_x, xlabel, log_x = values(x_parameter)
    y, valid_y, ylabel, log_y = values(y_parameter)
    masks = [eligible & valid_x & valid_y, eligible & valid_x & ~valid_y,
             eligible & ~valid_x & valid_y, eligible & ~valid_x & ~valid_y]
    figure = plt.figure(figsize=(10.5, 8.5), layout='constrained')
    grid = figure.add_gridspec(2, 2, width_ratios=(1, 10), height_ratios=(10, 1))
    ax = figure.add_subplot(grid[0,1])
    missing_y = figure.add_subplot(grid[1,1], sharex=ax)
    missing_x = figure.add_subplot(grid[0,0], sharey=ax)
    missing_both = figure.add_subplot(grid[1,0])
    groups = {}
    for group, selection, marker, color, size in (
            ('Dias', eligible, '.', '#777777', 12),
            ('Caldwell', eligible & np.asarray(table['in_caldwell']), 'o', '#0072B2', 70),
            ('Messier', eligible & np.asarray(table['in_messier']), '^', '#D55E00', 70)):
        options = dict(marker=marker, s=size, zorder=2 if group=='Dias' else 4)
        if group == 'Dias':
            options.update(color=color, alpha=.35)
        else:
            options.update(facecolors='none', edgecolors=color, linewidths=1.4)
        ax.scatter(x[masks[0] & selection], y[masks[0] & selection],
            label=f'{group} ({np.count_nonzero(masks[0] & selection):,})', **options)
        missing_y.scatter(x[masks[1] & selection], np.full(np.count_nonzero(masks[1] & selection), .5), **options)
        missing_x.scatter(np.full(np.count_nonzero(masks[2] & selection), .5), y[masks[2] & selection], **options)
        groups[group] = dict(selected=int(np.count_nonzero(selection)),
            plotted_with_both=int(np.count_nonzero(masks[0] & selection)))
    if log_x:
        ax.set_xscale('log')
    if log_y:
        ax.set_yscale('log')
    if x_parameter == 'brightness':
        ax.invert_xaxis()
    if y_parameter == 'brightness':
        ax.invert_yaxis()
    ax.set_ylabel(ylabel, fontsize=13)
    if not masks[0].any():
        ax.text(.5, .5, 'No selected cluster has both parameters.',
            transform=ax.transAxes, ha='center', va='center')
    ax.grid(True, which='major', alpha=.15)
    ax.set_title(f'Open clusters for amateur-target review\n{np.count_nonzero(eligible):,} selected; '
                 f'{np.count_nonzero(masks[0]):,} with both parameters', fontsize=16)
    ax.legend(loc='best', fontsize=11)
    plt.setp(ax.get_xticklabels(), visible=False)
    missing_y.set(ylim=(0,1), yticks=[])
    missing_y.set_xlabel(xlabel, fontsize=13)
    missing_y.text(.02,.82, f'{np.count_nonzero(masks[1]):,} without {y_parameter}',
        transform=missing_y.transAxes, fontsize=10)
    missing_x.set(xlim=(0,1), xticks=[])
    plt.setp(missing_x.get_yticklabels(), visible=False)
    missing_x.set_ylabel(f'{np.count_nonzero(masks[2])} without {x_parameter}', fontsize=10)
    missing_both.axis('off')
    missing_both.text(.5,.5,f'{np.count_nonzero(masks[3])}\nmissing\nboth', ha='center', va='center', fontsize=10)
    figure.supxlabel('Legend counts refer to the main panel. Missing values occupy labelled margins; no imputation.\n'
        'Member count is a richness proxy. V photometry is heterogeneous; brighter values lie up/right.', fontsize=10)
    for suffix in ('png', 'svg', 'pdf'):
        figure.savefig(prefix.parent/(prefix.name+'_figure.'+suffix), dpi=180)
    plt.close(figure)
    return dict(x=x_parameter, y=y_parameter, both=int(np.count_nonzero(masks[0])),
        missing_y=int(np.count_nonzero(masks[1])), missing_x=int(np.count_nonzero(masks[2])),
        missing_both=int(np.count_nonzero(masks[3])), groups=groups)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-prefix', type=Path)
    parser.add_argument('--output-directory', type=Path, default=Path(__file__).resolve().parents[1]/'output')
    parser.add_argument('--data-directory', type=Path, default=Path(__file__).resolve().parents[1]/'src/wenu/data/catalogs')
    parser.add_argument('--name', default='open_clusters_comparison_v2')
    parser.add_argument('--x', choices=tuple(PARAMETERS), default='diameter')
    parser.add_argument('--y', choices=tuple(PARAMETERS), default='members')
    parser.add_argument('--max-ebv', type=float)
    parser.add_argument('--min-ebv', type=float)
    parser.add_argument('--missing-ebv', choices=('exclude','include'), default='exclude')
    parser.add_argument('--write-filtered-catalogue', action='store_true')
    parser.add_argument('--include-infrared-embedded', action='store_true')
    args = parser.parse_args(argv)
    if args.x == args.y:
        raise ValueError('Choose two different plot parameters.')
    paths = {name: args.data_directory/name/filename for name,filename in (
        ('open_clusters','open_clusters_dias_heasarc.ecsv'), ('caldwell','caldwell_openngc.ecsv'),
        ('messier','messier_heasarc.ecsv'))}
    tables = {name: Table.read(path) for name, path in paths.items()}
    annotated, crosswalk, summary = compare(tables['open_clusters'], tables['caldwell'], tables['messier'],
        exclude_ir_embedded=not args.include_infrared_embedded, max_ebv=args.max_ebv,
        min_ebv=args.min_ebv, missing_ebv=args.missing_ebv)
    photometry_path = paths['open_clusters'].parent/'open_clusters_openngc_photometry_v1.ecsv'
    photometry_provenance = json.loads(photometry_path.with_suffix('.provenance.json').read_text())
    if (hashlib.sha256(photometry_path.read_bytes()).hexdigest() !=
            photometry_provenance['files'][photometry_path.name]['sha256'] or
            hashlib.sha256(paths['open_clusters'].read_bytes()).hexdigest() != photometry_provenance['dias_sha256']):
        raise ValueError('Photometry supplement or Dias source digest mismatch.')
    photometry = Table.read(photometry_path)
    if list(photometry['identifier']) != list(annotated['identifier']):
        raise ValueError('Photometry identifiers do not match the Dias snapshot.')
    for column in photometry.colnames:
        if column != 'identifier':
            annotated[column] = photometry[column]
    summary['source_sha256'] = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                               for name, path in paths.items()}
    summary['parameter_source'] = 'Packaged Dias/HEASARC values for every comparison sample.'
    summary['photometry_source_sha256'] = hashlib.sha256(photometry_path.read_bytes()).hexdigest()
    summary['photometry_provenance'] = photometry_provenance
    summary['matching_policy'] = 'Exact normalized identifiers first; explicit aliases only if the primary is absent. Preserve ambiguity and other alias rows. No positional matching.'
    summary['notes'] = 'C14 contributes two components. Matching catalogue entries does not establish modern physical reality or visual observability. Missing parameters are excluded separately, not imputed.'
    if not args.name or Path(args.name).name != args.name:
        raise ValueError('Output name must be a nonempty filename prefix.')
    prefix = args.output_prefix or args.output_directory/args.name
    products = {suffix: prefix.parent/(prefix.name+suffix) for suffix in
                ('_dias.csv', '_crosswalk.csv', '_summary.json')}
    products.update({suffix: prefix.parent/(prefix.name+suffix) for suffix in
        ('_figure.png', '_figure.svg', '_figure.pdf')})
    if args.write_filtered_catalogue:
        products['_filtered.ecsv'] = prefix.parent/(prefix.name+'_filtered.ecsv')
    if any(path.exists() for path in products.values()):
        raise FileExistsError('Comparison output already exists; use a new versioned prefix.')
    prefix.parent.mkdir(parents=True, exist_ok=True)
    annotated.write(products['_dias.csv'], format='ascii.csv')
    crosswalk.write(products['_crosswalk.csv'], format='ascii.csv')
    summary['plot_parameter_availability'] = plot_comparison(annotated, prefix, args.x, args.y)
    if args.write_filtered_catalogue:
        selected = annotated[np.asarray(annotated['in_amateur_sample'], dtype=bool)]
        selected.meta.update(selection=summary['selection'], source_sha256=summary['source_sha256'],
            photometry_source_sha256=summary['photometry_source_sha256'])
        selected.write(products['_filtered.ecsv'], format='ascii.ecsv')
    products['_summary.json'].write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    for path in products.values():
        print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
