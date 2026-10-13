#!/usr/bin/env python3
"""Compare packaged Dias open clusters with Caldwell and Messier membership.

Joins use explicit catalogue identifiers, never nearest-position guesses.
Physical parameters always come from the same Dias rows for all three samples.
No catalogue or chart selection is changed by this offline inspection tool.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re

from astropy.table import Table
import numpy as np

from wenu.resources import nonstellar_catalog_path


def identifier_key(value):
    value = str(value).strip()
    match = re.fullmatch(r'(NGC|IC|Melotte|Collinder)\s*0*(\d+)', value, re.IGNORECASE)
    if match:
        return match[1].casefold() + str(int(match[2]))
    return ''.join(value.casefold().split())


def compare(dias, caldwell, messier):
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

    annotated = dias.copy(copy_data=True)
    for catalogue, values in memberships.items():
        annotated[catalogue.casefold()+'_designations'] = ['|'.join(sorted(set(v))) for v in values]
        annotated['in_'+catalogue.casefold()] = [bool(v) for v in values]
    summary = dict(dias_clusters=len(dias), catalogue_component_matches={}, samples={})
    for catalogue in memberships:
        selected = [edge for edge in edges if edge['catalogue'] == catalogue]
        summary['catalogue_component_matches'][catalogue] = dict(
            entries=len({e['designation'] for e in selected}), components=len(selected),
            matched=sum(e['status'] == 'matched' for e in selected),
            unmatched=[e for e in selected if e['status'] == 'unmatched'],
            ambiguous=[e for e in selected if e['status'] == 'ambiguous'],
            alias_review=[e for e in selected if e['other_alias_rows']])
    for name, keep in [('Dias', np.ones(len(dias), dtype=bool)),
            ('Caldwell', np.asarray(annotated['in_caldwell'])),
            ('Messier', np.asarray(annotated['in_messier']))]:
        statistics = {'clusters': int(np.count_nonzero(keep))}
        for column in ('apparent_diameter_arcmin', 'distance_pc', 'reddening_e_bv',
                       'log_age_years', 'member_count', 'metallicity_feh'):
            values = np.asarray(dias[column], dtype=float)[keep]
            values = values[np.isfinite(values) & ((values >= 0) if column == 'member_count' else True)]
            statistics[column] = dict(available=len(values),
                median=float(np.median(values)) if len(values) else None)
        summary['samples'][name] = statistics
    return annotated, Table(rows=edges), summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-prefix', type=Path, required=True)
    args = parser.parse_args(argv)
    paths = {name: nonstellar_catalog_path(name) for name in ('open_clusters', 'caldwell', 'messier')}
    tables = {name: Table.read(path) for name, path in paths.items()}
    annotated, crosswalk, summary = compare(tables['open_clusters'], tables['caldwell'], tables['messier'])
    summary['source_sha256'] = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                               for name, path in paths.items()}
    summary['parameter_source'] = 'Packaged Dias/HEASARC values for every comparison sample.'
    summary['matching_policy'] = 'Exact normalized identifiers first; explicit aliases only if the primary is absent. Preserve ambiguity and other alias rows. No positional matching.'
    summary['notes'] = 'C14 contributes two components. Matching catalogue entries does not establish modern physical reality or visual observability. Missing parameters are excluded separately, not imputed.'
    prefix = args.output_prefix
    products = {suffix: prefix.parent/(prefix.name+suffix) for suffix in
                ('_dias.csv', '_crosswalk.csv', '_summary.json')}
    if any(path.exists() for path in products.values()):
        raise FileExistsError('Comparison output already exists; use a new versioned prefix.')
    prefix.parent.mkdir(parents=True, exist_ok=True)
    annotated.write(products['_dias.csv'], format='ascii.csv')
    crosswalk.write(products['_crosswalk.csv'], format='ascii.csv')
    products['_summary.json'].write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    for path in products.values():
        print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
