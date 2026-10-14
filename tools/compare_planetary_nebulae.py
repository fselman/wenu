#!/usr/bin/env python3
"""Offline planetary-nebula radius/H-beta comparison with observing-list overlays.

All 1,143 Strasbourg-ESO rows remain in the review catalogue. No visual
selection, catalogue promotion or sky-chart change is performed. No arguments
prints help and writes nothing. H-beta is an observed line flux, not V magnitude.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
from astropy.table import Table

from catalogue_data_layout import OBSERVING, data_file
from observing_list_membership import excel_rows, key, load_converted
from observing_list_additions import load_converted as load_additions

ROOT = Path(__file__).resolve().parents[1]
PRIORITY = ['messier', 'caldwell', 'sac_urban', 'rasc_finest_ngc',
            'sac_best_ngc', 'herschel400_south', 'herschel400', 'herschel2',
            'sac_beyond_ngc', 'al_planetary_nebulae',
            'al_planetary_nebulae_south', 'al_planetary_nebulae_alternates']
LABELS = ['Messier', 'Caldwell', 'SAC Urban', 'RASC Finest NGC', 'SAC Best NGC',
          'Herschel 400 South', 'Herschel 400', 'Herschel II', 'SAC Beyond NGC',
          'AL Planetary Nebulae', 'AL Planetary Nebulae South', 'AL Northern Alternates']
AL_FILES = [
    ('al_planetary_nebulae', 'al_planetaries_list_v1.xlsx', 110),
    ('al_planetary_nebulae_south', 'al_planetaries_south_list_v1.xls', 110),
    ('al_planetary_nebulae_alternates', 'al_planetaries_alternates_list_v1.xls', 26),
]
HBETA_DOCUMENTATION = 'https://heasarc.gsfc.nasa.gov/W3Browse/nebula-catalog/plnebulae.html'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text(value):
    return '' if np.ma.is_masked(value) else str(value).strip()


def pn_key(value):
    """Normalize explicit names; preserve coordinate signs and PN namespaces."""
    value = text(value).replace('\u2212', '-').replace('_', ' ')
    match = re.fullmatch(r'(?:PN\s*G|PNG)\s*(\d{1,3}\.\d)([+-])(\d{1,2}\.\d)', value, re.I)
    if match:
        return f'png{float(match[1]):05.1f}{match[2]}{float(match[3]):04.1f}'
    match = re.fullmatch(r'PK\s*(\d{1,3})\s*([+-])\s*(\d{1,2})[.\s]+(\d+)', value, re.I)
    if match:
        return f'pk{int(match[1])}{match[2]}{int(match[3])}.{int(match[4])}'
    # Catalogue-name expansions only; no positional or fuzzy identity inference.
    value = re.sub(r'^Abell\s*', 'A ', value, flags=re.I)
    value = re.sub(r'^Jonckheere\s*', 'J ', value, flags=re.I)
    value = re.sub(r'^Hubble\s*', 'Hb ', value, flags=re.I)
    value = re.sub(r'^Jones\s*', 'Jn ', value, flags=re.I)
    value = re.sub(r'^Pease\s*', 'Ps ', value, flags=re.I)
    return key(value)


def source_names(value):
    """Retain a published combined NGC name and its two explicit components."""
    value = text(value)
    names = [value]
    match = re.fullmatch(r'NGC\s*(\d+)\s*-\s*(\d+)', value, re.I)
    if match:
        first, suffix = match.groups()
        second = int(first[:-len(suffix)]+suffix) if len(suffix) < len(first) else int(suffix)
        if second == int(first)+1:
            names += ['NGC '+str(int(first)), 'NGC '+str(second)]
    return names


def al_identity_names(value):
    """Split explicit combined catalogue names; a parenthetical host is not an alias."""
    value = text(value)
    names = [value]
    without_host = re.sub(r'\s*\(In\s+[^)]*\)', '', value, flags=re.I).strip()
    if without_host != value:
        names.append(without_host)
    names.extend(re.findall(r'(?:NGC|IC|Hubble)\s*\d+|K\s*\d+\s*-\s*\d+', without_host, flags=re.I))
    return list(dict.fromkeys(names))


def al_records(directory):
    """Read only identity columns from the three digest-bound original workbooks."""
    directory = Path(directory)
    provenance_path = directory/'al_planetary_nebulae/provenance_original_v1.json'
    provenance = json.loads(provenance_path.read_text())
    products = {r['file']: r for r in provenance['source_products']}
    evidence = {'provenance_sha256': digest(provenance_path), 'files': {}}
    records = []
    for catalogue, filename, expected in AL_FILES:
        path = data_file(directory, filename)
        binding = products[filename]
        if path.stat().st_size != binding['bytes'] or digest(path) != binding['sha256']:
            raise ValueError('AL planetary source checksum mismatch: '+filename)
        subset = []
        for rows in excel_rows(path):
            headers = None
            for source_row, row in enumerate(rows, 1):
                row = [text(v) for v in row]
                if row and row[0].casefold() == 'primary id':
                    headers = row
                    continue
                if not headers or len(row) < 5 or not re.match(r'^\d{1,2}h', row[4]):
                    continue
                columns = {name: i for i, name in enumerate(headers)}
                identities = al_identity_names(row[0])
                for name in ('Alternate ID', 'PK Desig', 'PN G Desig', 'Henize', 'ESO', 'ARO'):
                    i = columns.get(name)
                    if i is not None and i < len(row) and row[i]:
                        identities.extend(al_identity_names(row[i]))
                subset.append(dict(catalogue=catalogue, designation=row[0],
                    identifiers=list(dict.fromkeys(identities)), source_file=filename,
                    source_row=source_row))
        if len(subset) != expected:
            raise ValueError(f'AL planetary parse count differs: {filename}: {len(subset)} != {expected}')
        records.extend(subset)
        evidence['files'][filename] = dict(sha256=digest(path), rows=len(subset))
    return records, evidence


def reference_names(directory):
    """Expand observing M/C IDs through their packaged explicit identifications."""
    directory = Path(directory)
    names, hashes = {}, {}
    for catalogue, filename in [('messier', 'messier_heasarc.ecsv'),
                                ('caldwell', 'caldwell_openngc.ecsv')]:
        path = directory/catalogue/filename
        provenance_path = path.with_suffix('.provenance.json')
        provenance = json.loads(provenance_path.read_text())
        binding = provenance['files'].get(filename, provenance['files'].get('canonical_snapshot'))
        if binding is None or digest(path) != binding['sha256']:
            raise ValueError('Reference catalogue checksum mismatch: '+filename)
        hashes[catalogue] = dict(catalogue_sha256=digest(path), provenance_sha256=digest(provenance_path))
        for row in Table.read(path):
            identities = [text(row['alt_name'])] if catalogue == 'messier' else [text(row['primary_id'])]
            names[pn_key(row['name'])] = [v for v in identities if v]
    return names, hashes


def compare(source, records, references=None, priority=None):
    """Annotate all source rows; ambiguous identities remain review claims."""
    references = references or {}
    priority = PRIORITY if priority is None else priority
    if not priority or len(set(priority)) != len(priority) or any(v not in PRIORITY for v in priority):
        raise ValueError('Priority must contain distinct supported observing lists.')
    table = source.copy(copy_data=True)
    index = {}
    for i, row in enumerate(source):
        identities = [v for c in ('identifier', 'common_name', 'pk_name') for v in source_names(row[c])]
        identities.extend(v for name in text(row['alternate_names']).split(';') for v in source_names(name))
        for identity in identities:
            if identity.strip():
                index.setdefault(pn_key(identity), set()).add(i)
    if len(set(map(str, source['identifier']))) != len(source):
        raise ValueError('Planetary source identifiers are not unique.')
    memberships = {name: np.zeros(len(source), bool) for name in PRIORITY}
    claims = [[] for _ in source]
    edges = []
    for record in records:
        catalogue = record['catalogue']
        if catalogue not in PRIORITY:
            continue
        identities = list(record['identifiers'])
        identities += [v for name in record['identifiers'] for v in references.get(pn_key(name), [])]
        candidates = set()
        matched_names = []
        for identity in identities:
            matches = index.get(pn_key(identity), set())
            if matches:
                candidates.update(matches)
                matched_names.append(identity)
        status = 'matched' if len(candidates) == 1 else 'ambiguous' if candidates else 'unmatched'
        if status == 'matched':
            memberships[catalogue][next(iter(candidates))] = True
        elif status == 'ambiguous':
            for i in candidates:
                claims[i].append(catalogue+':'+record['designation'])
        edges.append(dict(catalogue=catalogue, designation=record['designation'],
            source_file=record['source_file'], source_row=record.get('source_row', 0),
            identifiers_json=json.dumps(record['identifiers']), status=status,
            matched_names='|'.join(matched_names),
            planetary_ids='|'.join(sorted(text(source['identifier'][i]) for i in candidates))))
    for name, flags in memberships.items():
        table['in_'+name] = flags
    table['membership_review'] = ['|'.join(v) for v in claims]
    table['memberships'] = ['|'.join(name for name in PRIORITY if memberships[name][i]) for i in range(len(source))]
    table['first_list'] = [next((name for name in priority if memberships[name][i]), 'unlisted') for i in range(len(source))]
    diameter = np.asarray(np.ma.filled(table['major_axis_arcmin'], np.nan), float)
    flux = np.asarray(np.ma.filled(table['log_hbeta_flux'], np.nan), float)
    radius = diameter/2
    limited = np.array([bool(text(v)) for v in table['optical_diameter_limit']])
    valid = np.isfinite(radius) & (radius > 0) & ~limited
    surface = np.full(len(table), np.nan)
    measured = valid & np.isfinite(flux)
    surface[measured] = flux[measured]-np.log10(np.pi*(radius[measured]*60)**2)
    table['radius_arcmin'] = radius
    table['radius_arcmin'].unit = 'arcmin'
    table['radius_status'] = ['diameter_limit' if limited[i] else 'measured' if valid[i] else 'missing_or_nonpositive' for i in range(len(table))]
    table['log_hbeta_surface_brightness_proxy'] = surface
    table['hbeta_flux_status'] = ['available' if np.isfinite(v) else 'missing' for v in flux]
    table.meta['comparison_semantics'] = 'Observed H-beta flux in erg s-1 cm-2; surface proxy per arcsec2. Not V or OIII; no extinction correction, visual-selection threshold or imputation.'
    crosswalk = Table(rows=edges) if edges else Table(names=['catalogue', 'designation', 'source_file', 'source_row', 'identifiers_json', 'status', 'matched_names', 'planetary_ids'], dtype=['U1', 'U1', 'U1', int, 'U1', 'U1', 'U1', 'U1'])
    counts = {name: dict(source_records=sum(r['catalogue'] == name for r in records),
        member_rows=int(memberships[name].sum()),
        ambiguous_records=sum(r['catalogue'] == name and r['status'] == 'ambiguous' for r in edges),
        unmatched_records=sum(r['catalogue'] == name and r['status'] == 'unmatched' for r in edges)) for name in PRIORITY}
    return table, crosswalk, dict(rows=len(table), priority=list(priority), lists=counts,
        listed_rows=int(sum(bool(v) for v in table['memberships'])),
        membership_review_rows=int(sum(bool(v) for v in table['membership_review'])))


def plot(table, prefix, view, priority):
    """One symbol per nebula; unavailable axes occupy explicit margins."""
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    column = 'log_hbeta_flux' if view == 'flux' else 'log_hbeta_surface_brightness_proxy'
    x = np.asarray(table['radius_arcmin'], float)
    y = np.asarray(table[column], float)
    valid_x = np.array(table['radius_status']) == 'measured'
    valid_y = np.isfinite(y)
    masks = [valid_x & valid_y, valid_x & ~valid_y, ~valid_x & valid_y, ~valid_x & ~valid_y]
    fig = plt.figure(figsize=(15, 10), layout='constrained')
    grid = fig.add_gridspec(2, 3, width_ratios=(1.1, 8, 3.2), height_ratios=(8, 1.1))
    ax = fig.add_subplot(grid[0, 1])
    missing_y = fig.add_subplot(grid[1, 1], sharex=ax)
    missing_x = fig.add_subplot(grid[0, 0], sharey=ax)
    missing_both = fig.add_subplot(grid[1, 0])
    legend_ax = fig.add_subplot(grid[:, 2]); legend_ax.axis('off')
    markers = ['*', 's', 'D', '^', 'v', 'P', 'X', 'p', 'h', 'd', '<', '>']
    styles = {name: (markers[PRIORITY.index(name)], plt.get_cmap('tab20')(2*PRIORITY.index(name) % 20)) for name in PRIORITY}
    styles['unlisted'] = ('.', '#888888')
    handles = []
    labels = np.asarray(table['first_list'])
    uncertain = np.array([bool(text(v)) for v in table['optical_diameter_uncertain']])
    for name in ['unlisted']+list(reversed(priority)):
        selection = labels == name
        marker, color = styles[name]
        for panel, mask, xx, yy in [(ax, masks[0], x, y),
                (missing_y, masks[1], x, np.full(len(x), .5)),
                (missing_x, masks[2], np.full(len(x), .5), y)]:
            for hollow in (False, True):
                keep = selection & mask & (uncertain == hollow)
                if not keep.any():
                    continue
                panel.scatter(xx[keep], yy[keep], marker=marker,
                    s=18 if name == 'unlisted' else 95,
                    facecolors='none' if hollow else color, edgecolors=color,
                    linewidths=1.4, alpha=.35 if name == 'unlisted' else .9,
                    zorder=1 if name == 'unlisted' else 3)
        count = int((selection & masks[0]).sum())
        if selection.any():
            label = 'Other catalogue objects' if name == 'unlisted' else LABELS[PRIORITY.index(name)]
            handles.append(Line2D([], [], marker=marker, color=color, linestyle='',
                markersize=10, label=f'{label} ({count})'))
    ax.set_xscale('log')
    ax.set_ylabel('log₁₀ observed Hβ flux [erg s⁻¹ cm⁻²]' if view == 'flux' else
        'log₁₀ mean Hβ surface-brightness proxy [erg s⁻¹ cm⁻² arcsec⁻²]', fontsize=14)
    ax.set_title(f'Planetary nebulae: observing-list comparison\n{len(table):,} catalogue objects; {int(masks[0].sum()):,} in main panel', fontsize=17)
    ax.grid(alpha=.18)
    ax.tick_params(labelsize=12)
    plt.setp(ax.get_xticklabels(), visible=False)
    missing_y.set(ylim=(0, 1), yticks=[])
    missing_y.set_xlabel('Optical angular radius (arcmin; half the Acker diameter)', fontsize=14)
    missing_y.text(.02, .82, f'{int(masks[1].sum())} without this Hβ quantity', transform=missing_y.transAxes, fontsize=11)
    missing_x.set(xlim=(0, 1), xticks=[])
    plt.setp(missing_x.get_yticklabels(), visible=False)
    missing_x.set_ylabel(f'{int(masks[2].sum())} unknown/limited radius', fontsize=11)
    missing_both.axis('off')
    missing_both.text(.5, .5, f'{int(masks[3].sum())}\nunavailable\nboth axes', ha='center', va='center', fontsize=11)
    legend_ax.legend(handles=handles[::-1], loc='upper left', fontsize=11, frameon=False,
        title='First list by priority\n(main-panel counts)', title_fontsize=12)
    legend_ax.text(0, .12, 'All memberships remain in the table.\nHollow symbols: uncertain diameter.\nDiameter limits stay outside main panel.\nMissing data are not faint detections.\n\nHβ is not visual magnitude or [O III].\nNo visibility cutoff has been applied.',
        transform=legend_ax.transAxes, fontsize=11, va='bottom')
    fig.supxlabel('Observed flux; no extinction correction. Surface brightness assumes a circular optical area and is a diagnostic proxy.', fontsize=11)
    for suffix in ('png', 'svg', 'pdf'):
        fig.savefig(prefix.parent/(prefix.name+'_radius_hbeta_'+view+'.'+suffix), dpi=180)
    plt.close(fig)
    return dict(main_panel=int(masks[0].sum()), missing_y=int(masks[1].sum()),
        missing_or_limited_radius=int(masks[2].sum()), unavailable_both=int(masks[3].sum()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Default priority: '+','.join(PRIORITY)+'\nExample: PYTHONPATH=src MPLBACKEND=Agg python tools/compare_planetary_nebulae.py --name planetary_nebulae_comparison_v1\nLegacy AL .xls sources require xlrd>=2,<3. Both views are generated by default.')
    parser.add_argument('--data-directory', type=Path, default=ROOT/'src/wenu/data/catalogs')
    parser.add_argument('--observing-directory', type=Path, default=OBSERVING)
    parser.add_argument('--output-directory', type=Path, default=ROOT/'output/planetary_nebulae_comparison_v1')
    parser.add_argument('--name', default='planetary_nebulae_comparison_v1')
    parser.add_argument('--view', choices=('flux', 'surface-brightness', 'both'), default='both')
    parser.add_argument('--priority', default=','.join(PRIORITY))
    arguments = sys.argv[1:] if argv is None else list(argv)
    if not arguments:
        parser.print_help(); return 0
    args = parser.parse_args(arguments)
    if not args.name or Path(args.name).name != args.name or not re.search(r'_v\d+(?:\.\d+)*$', args.name):
        raise ValueError('Output name must be a filename prefix ending in an explicit _vN version.')
    path = args.data_directory/'planetary_nebulae/planetary_nebulae_acker_heasarc.ecsv'
    provenance_path = path.with_suffix('.provenance.json')
    provenance = json.loads(provenance_path.read_text())
    if digest(path) != provenance['files']['canonical_snapshot']['sha256']:
        raise ValueError('Planetary source checksum mismatch.')
    source = Table.read(path)
    if len(source) != provenance['expected_row_count']:
        raise ValueError('Planetary source row count mismatch.')
    records, original = load_converted(args.observing_directory, args.observing_directory/'observing_sources_v1.json')
    extra, additions = load_additions(args.observing_directory, args.observing_directory/'observing_additions_v1.json')
    al, al_evidence = al_records(args.observing_directory)
    references, reference_hashes = reference_names(args.data_directory)
    priority = args.priority.split(',')
    table, crosswalk, summary = compare(source, records+extra+al, references, priority)
    views = ['flux', 'surface-brightness'] if args.view == 'both' else [args.view]
    prefix = args.output_directory/args.name
    products = [prefix.with_name(prefix.name+s) for s in ('_catalogue.csv', '_catalogue.ecsv', '_crosswalk.csv', '_summary.json')]
    products += [prefix.with_name(prefix.name+'_radius_hbeta_'+view+'.'+suffix) for view in views for suffix in ('png', 'svg', 'pdf')]
    if any(p.exists() or p.is_symlink() for p in products):
        raise FileExistsError('Comparison output exists; use a new versioned name or directory.')
    summary.update(source_sha256=digest(path), provenance_sha256=digest(provenance_path),
        original_conversion=original, additions_conversion=additions, al_sources=al_evidence,
        reference_catalogues=reference_hashes, command=arguments,
        scientific_policy=table.meta['comparison_semantics'],
        surface_brightness_formula='log10(S_Hbeta) = log_hbeta_flux - log10(pi*(60*radius_arcmin)^2)',
        diameter_policy='Upper/lower limits retained as limits; excluded from measured-radius main panels. Uncertain diameters are hollow. No radius or flux imputation.',
        matching_policy='Explicit normalized PN G, PK, common names and published aliases; no positions. Conflicting identities are ambiguous, with no resolved membership.',
        unmatched_notice='Broad observing lists contain other object types; an unmatched reference is not proof of a missing planetary nebula.',
        quantity_documentation=dict(url=HBETA_DOCUMENTATION, checked='2026-10-14', flux_unit='erg s-1 cm-2 (equivalent to mW m-2)'),
        final_visual_selection='not_adopted')
    commit = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True, capture_output=True)
    summary['wenu_commit'] = commit.stdout.strip() if commit.returncode == 0 else 'unavailable'
    args.output_directory.mkdir(parents=True, exist_ok=True)
    table.write(products[0], format='ascii.csv'); table.write(products[1], format='ascii.ecsv')
    crosswalk.write(products[2], format='ascii.csv')
    summary['plots'] = {view: plot(table, prefix, view, priority) for view in views}
    summary['products'] = {p.name: digest(p) for p in products if p != products[3]}
    products[3].write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: summary[k] for k in ('rows', 'listed_rows', 'membership_review_rows', 'lists', 'plots')}, indent=2))
    for p in products:
        print(p)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
