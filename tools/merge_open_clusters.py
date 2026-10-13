#!/usr/bin/env python3
"""Build a source-preserving wenu_open_clusters candidate from Dias and Hunt.

Offline software tool, separate from curation and chart adoption. Every input
row is represented exactly once. Only unambiguous one-to-one identifier matches
are combined. Ambiguous candidates stay separate and receive a review ledger.
An optional prior ID registry preserves wenu_id values across subsequent runs.
Calling without arguments prints help and creates nothing.
"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np
from astropy.table import MaskedColumn, Table

from compare_open_clusters import identifier_key, observing_crosswalk

ROOT = Path(__file__).resolve().parents[1]


def text(value):
    return '' if np.ma.is_masked(value) else str(value).strip()


def names(row):
    return [text(row['identifier']), *(
        text(row['aliases']).split(',') if 'aliases' in row.colnames else [])]


def source_nodes(dias, hunt):
    for label, table, required in [('Dias',dias,{'identifier','ra_deg','dec_deg'}),
                                  ('Hunt',hunt,{'identifier','hunt_id','ra_deg','dec_deg'})]:
        if not required.issubset(table.colnames):
            raise ValueError(label+' lacks required identity/position columns.')
        if any(not text(value) for value in table['identifier']):
            raise ValueError(label+' has an empty source identifier.')
    dias_keys = ['dias:'+identifier_key(value) for value in dias['identifier']]
    hunt_keys = []
    for value in hunt['hunt_id']:
        if np.ma.is_masked(value) or not str(value).isdigit():
            raise ValueError('Hunt IDs must be non-negative integers, not float values.')
        hunt_keys.append('hunt:'+str(int(value)))
    if any(key=='dias:' for key in dias_keys):
        raise ValueError('Dias identifier is empty after normalization.')
    if len(set(dias_keys)) != len(dias_keys) or len(set(hunt_keys)) != len(hunt_keys):
        raise ValueError('Duplicate source identities cannot receive separate stable IDs.')
    return dias_keys, hunt_keys


def identify(dias, hunt):
    """Exact primary first, then reciprocal unique aliases; no spatial guesses."""
    primary, aliases = {}, {}
    for h, row in enumerate(hunt):
        primary.setdefault(identifier_key(row['identifier']),set()).add(h)
        for name in names(row)[1:]:
            if text(name):
                aliases.setdefault(identifier_key(name),set()).add(h)
    candidates = []
    for d, row in enumerate(dias):
        key = identifier_key(row['identifier'])
        direct = primary.get(key,set())
        other = aliases.get(key,set())
        for name in names(row)[1:]:
            other = other | primary.get(identifier_key(name),set()) | aliases.get(identifier_key(name),set())
        for h in sorted(direct | other):
            candidates.append(dict(dias_index=d,hunt_index=h,
                method='primary_identifier' if h in direct else 'published_alias'))
    matched, used_d, used_h = [], set(), set()
    # A primary match reserves its pair before the alias stage. Alternative
    # source rows claiming its aliases are retained for explicit review.
    for method in ('primary_identifier','published_alias'):
        stage = [e for e in candidates if e['method']==method and
                 e['dias_index'] not in used_d and e['hunt_index'] not in used_h]
        dcounts, hcounts = {}, {}
        for edge in stage:
            dcounts[edge['dias_index']] = dcounts.get(edge['dias_index'],0)+1
            hcounts[edge['hunt_index']] = hcounts.get(edge['hunt_index'],0)+1
        for edge in stage:
            d,h = edge['dias_index'],edge['hunt_index']
            if dcounts[d]==hcounts[h]==1:
                matched.append(edge)
                used_d.add(d)
                used_h.add(h)
    accepted = {(e['dias_index'],e['hunt_index']) for e in matched}
    for edge in candidates:
        edge['status'] = 'matched' if (edge['dias_index'],edge['hunt_index']) in accepted else 'review'
        edge['dias_id'] = text(dias['identifier'][edge['dias_index']])
        edge['hunt_id'] = int(hunt['hunt_id'][edge['hunt_index']])
        edge['hunt_name'] = text(hunt['identifier'][edge['hunt_index']])
    groups = [(e['dias_index'],e['hunt_index'],e['method']) for e in matched]
    groups += [(d,None,'Dias_only') for d in range(len(dias)) if d not in used_d]
    groups += [(None,h,'Hunt_only') for h in range(len(hunt)) if h not in used_h]
    return groups, candidates


def assign_ids(groups, dias_keys, hunt_keys, registry=None):
    """Retain old IDs; changing a published merge/split requires a new decision."""
    registry = deepcopy(registry) if registry is not None else dict(
        schema_version=1,next_id=1,source_ids={})
    if (set(registry)!= {'schema_version','next_id','source_ids'} or
            registry['schema_version'] != 1 or type(registry['next_id']) is not int or
            registry['next_id']<1 or not isinstance(registry['source_ids'],dict)):
        raise ValueError('Invalid Wenu ID registry.')
    for node,value in registry['source_ids'].items():
        if not isinstance(node,str) or not node.startswith(('dias:','hunt:')) or not isinstance(value,str) or not re.fullmatch(r'WOC\d{8}',value):
            raise ValueError('Invalid source key or Wenu ID in registry.')
    existing_numbers = [int(v[3:]) for v in registry['source_ids'].values()]
    if existing_numbers and registry['next_id'] <= max(existing_numbers):
        raise ValueError('Registry next_id would reuse a published ID.')
    def nodes(group):
        d,h,_ = group
        return ([dias_keys[d]] if d is not None else [])+([hunt_keys[h]] if h is not None else [])
    ordered = sorted(groups,key=lambda group:tuple(sorted(nodes(group))))
    identifiers, used = [], set()
    for group in ordered:
        source_keys = nodes(group)
        ids = {registry['source_ids'][node] for node in source_keys if node in registry['source_ids']}
        if len(ids)>1:
            raise ValueError('Proposed match combines existing Wenu IDs; review required: '+str(source_keys))
        if ids:
            wenu_id = next(iter(ids))
        else:
            if registry['next_id']>99999999:
                raise ValueError('Wenu ID space exhausted.')
            wenu_id = f"WOC{registry['next_id']:08d}"
            registry['next_id'] += 1
        if wenu_id in used:
            raise ValueError('A published Wenu ID would split across rows; review required: '+wenu_id)
        used.add(wenu_id)
        identifiers.append(wenu_id)
        for node in source_keys:
            registry['source_ids'][node] = wenu_id
    return ordered, identifiers, registry


def copy_columns(output, source, groups, side, prefix):
    """Preserve all source values, units and masks in their own columns."""
    for name in source.colnames:
        if prefix=='dias' and name=='identifier':
            target = 'dias_id'
        elif prefix=='hunt' and name=='identifier':
            target = 'hunt_name'
        elif name.startswith(prefix+'_'):
            target = name
        else:
            target = prefix+'_'+name
        if target in output.colnames:
            raise ValueError('Source column collision: '+target)
        original = source[name]
        column = MaskedColumn(np.ma.masked_all((len(groups),)+original.shape[1:],dtype=original.dtype),name=target)
        column.unit = original.unit
        column.description = original.description
        column.meta = deepcopy(original.meta)
        for i,group in enumerate(groups):
            if group[side] is not None:
                column[i] = original[group[side]]
        output[target] = column


def merge_catalogues(dias, hunt, caldwell, messier, *, registry=None):
    """Candidate union with complete source coverage and explicit identity review."""
    dias_keys,hunt_keys = source_nodes(dias,hunt)
    groups,candidates = identify(dias,hunt)
    groups,wenu_ids,registry = assign_ids(groups,dias_keys,hunt_keys,registry)
    ra,dec,position_sources,position_epochs,display,all_names = [],[],[],[],[],[]
    for d,h,_ in groups:
        preferred = hunt[h] if h is not None else dias[d]
        ra.append(preferred['ra_deg'])
        dec.append(preferred['dec_deg'])
        position_sources.append('hunt' if h is not None else 'dias')
        position_epochs.append(text(hunt.meta.get('coordinate_epoch','unknown')) if h is not None else 'unknown')
        display.append(text(preferred['identifier']))
        combined = ([*names(dias[d])] if d is not None else [])+([*names(hunt[h])] if h is not None else [])
        all_names.append(sorted({name for name in combined if text(name)}))
    output = Table(dict(wenu_id=wenu_ids,RA=np.asarray(ra,float),Dec=np.asarray(dec,float)))
    output['RA'].unit = output['Dec'].unit = 'deg'
    copy_columns(output,dias,groups,0,'dias')
    # Put the internal Hunt ID before its named and physical parameter columns.
    hunt_order = ['hunt_id']+[c for c in hunt.colnames if c!='hunt_id']
    copy_columns(output,hunt[hunt_order],groups,1,'hunt')
    identities = Table(dict(identifier=display,aliases=[','.join(v) for v in all_names]))
    memberships,reference_edges = observing_crosswalk(identities,caldwell,messier,all_types=True)
    for source,target in [('Messier','Messier_id'),('Caldwell','Caldwell_id')]:
        output[target] = ['|'.join(sorted(set(v))) for v in memberships[source]]
    for prefix,target in [('NGC','NGC_id'),('IC','IC_id'),('Melotte','Melotte_id'),('Collinder','Collinder_id')]:
        values = []
        for aliases in all_names:
            ids = set()
            for name in aliases:
                key = identifier_key(name)
                match = re.fullmatch(prefix.casefold()+r'(\d+)',key)
                if match:
                    ids.add(prefix+' '+str(int(match[1])))
            values.append('|'.join(sorted(ids)))
        output[target] = values
    output['Other_ids'] = ['|'.join(v) for v in all_names]
    output['RA_source'] = position_sources
    output['position_epoch'] = position_epochs
    output['match_method'] = [group[2] for group in groups]
    review_d = {e['dias_index'] for e in candidates if e['status']=='review'}
    review_h = {e['hunt_index'] for e in candidates if e['status']=='review'}
    output['identity_review'] = [d in review_d or h in review_h for d,h,_ in groups]
    output['has_dias'] = [d is not None for d,_,_ in groups]
    output['has_hunt'] = [h is not None for _,h,_ in groups]
    node_ids = registry['source_ids']
    for edge in candidates:
        edge['dias_wenu_id'] = node_ids[dias_keys[edge['dias_index']]]
        edge['hunt_wenu_id'] = node_ids[hunt_keys[edge['hunt_index']]]
        del edge['dias_index'],edge['hunt_index']
    # Source aliases may themselves be shared; reference conflicts are separate.
    reference_review = set()
    for edge in reference_edges:
        edge['matched_identifier'] = edge.pop('dias_identifier')
        selected = [i for i,v in enumerate(display) if v==edge['matched_identifier']]
        edge['wenu_id'] = wenu_ids[selected[0]] if len(selected)==1 else ''
        if edge['status']=='ambiguous' or edge['other_alias_rows']:
            for i,aliases in enumerate(all_names):
                if identifier_key(edge['component']) in {identifier_key(v) for v in aliases}:
                    reference_review.add(i)
    output['reference_review'] = [i in reference_review for i in range(len(output))]
    matched = sum(d is not None and h is not None for d,h,_ in groups)
    summary = dict(database='wenu_open_clusters',schema_version=1,
        dias_rows=len(dias),hunt_rows=len(hunt),combined_rows=len(output),matched_pairs=matched,
        dias_only=len(dias)-matched,hunt_only=len(hunt)-matched,
        identity_review_rows=int(np.count_nonzero(output['identity_review'])),
        policy='Primary identifiers first; then reciprocal unique published aliases. No positional matching, filtering or same-source merging.',
        curation_status='unreviewed_candidate',
        input_scope='All rows of the provided tables; earlier source-provider exclusions are not recovered.',
        position_policy='Hunt RA/Dec when present, otherwise Dias. No averaging or epoch propagation; source positions remain preserved.')
    assert len(output)==len(dias)+len(hunt)-matched
    assert sum(output['has_dias'])==len(dias) and sum(output['has_hunt'])==len(hunt)
    output.meta.update(summary,dias_metadata=deepcopy(dias.meta),hunt_metadata=deepcopy(hunt.meta))
    edge_columns = ['dias_id','hunt_id','hunt_name','method','status','dias_wenu_id','hunt_wenu_id']
    crosswalk = Table(rows=candidates) if candidates else Table(names=edge_columns,dtype=['U1','i8','U1','U1','U1','U1','U1'])
    references = (Table(rows=reference_edges) if reference_edges else Table(
        names=['catalogue','designation','component','matched_identifier','wenu_id','status'],
        dtype=['U1']*6))
    return output,crosswalk,references,registry,summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Columns: wenu_id, RA, Dec, dias_id, dias_* parameters, hunt_id, hunt_* parameters,\n'
               'Messier_id, Caldwell_id, NGC_id, IC_id, Melotte_id, Collinder_id, Other_ids, review/source flags.\n'
               'RA and Dec are degrees. Both source positions/metadata are preserved.\n'
               'This creates a candidate only: no clean database adoption, chart change or software merge.')
    parser.add_argument('--data-directory',type=Path,default=ROOT/'src/wenu/data/catalogs')
    parser.add_argument('--dias-catalogue',type=Path,help='Explicit normalized Dias input; all its rows are retained.')
    parser.add_argument('--hunt-catalogue',type=Path,help='Explicit normalized full Hunt input; all its rows/types are retained.')
    parser.add_argument('--id-registry',type=Path,help='Previous _ids.json; preserve existing wenu_id assignments.')
    parser.add_argument('--output-directory',type=Path,default=ROOT/'output')
    parser.add_argument('--name',default='wenu_open_clusters_v1',help='New versioned output prefix; existing products are refused.')
    arguments = sys.argv[1:] if argv is None else list(argv)
    if not arguments:
        parser.print_help()
        return 0
    args = parser.parse_args(arguments)
    if not args.name or Path(args.name).name!=args.name:
        parser.error('--name must be a nonempty filename prefix.')
    if not re.search(r'_v\d+$',args.name):
        parser.error('--name must end in an explicit version, such as _v1.')
    paths = dict(dias=args.dias_catalogue or args.data_directory/'open_clusters/open_clusters_dias_heasarc.ecsv',
        hunt=args.hunt_catalogue or args.data_directory/'open_clusters/open_clusters_hunt_reffert2024_v1.ecsv',
        caldwell=args.data_directory/'caldwell/caldwell_openngc.ecsv',
        messier=args.data_directory/'messier/messier_heasarc.ecsv')
    tables = {key:Table.read(path) for key,path in paths.items()}
    if args.hunt_catalogue is None:
        from hunt_reffert_catalogue import load
        tables['hunt'],_,_ = load(paths['hunt'].parent)
    registry = json.loads(args.id_registry.read_text()) if args.id_registry else None
    output,crosswalk,references,registry,summary = merge_catalogues(
        tables['dias'],tables['hunt'],tables['caldwell'],tables['messier'],registry=registry)
    hashes = {key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in paths.items()}
    if args.id_registry:
        hashes['previous_id_registry'] = hashlib.sha256(args.id_registry.read_bytes()).hexdigest()
    summary['source_sha256'] = hashes
    output.meta['source_sha256'] = hashes
    products = {suffix:args.output_directory/(args.name+suffix) for suffix in
                ('.ecsv','.csv','_crosswalk.csv','_references.csv','_ids.json','_summary.json')}
    if any(path.exists() for path in products.values()):
        raise FileExistsError('Candidate output already exists; use a new versioned prefix.')
    args.output_directory.mkdir(parents=True,exist_ok=True)
    output.write(products['.ecsv'],format='ascii.ecsv')
    output.write(products['.csv'],format='ascii.csv')
    crosswalk.write(products['_crosswalk.csv'],format='ascii.csv')
    references.write(products['_references.csv'],format='ascii.csv')
    products['_ids.json'].write_text(json.dumps(registry,indent=2,sort_keys=True)+'\n')
    # The completion receipt is published last; interrupted candidates lack it.
    summary['products'] = {path.name:hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in products.values() if path!=products['_summary.json']}
    products['_summary.json'].write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps({key:summary[key] for key in ('dias_rows','hunt_rows','combined_rows','matched_pairs','identity_review_rows')}))
    for path in products.values():
        print(path)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
