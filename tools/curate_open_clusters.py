#!/usr/bin/env python3
"""Create an explicit v0.1 cluster selection from the source-preserving union.

Retain all cluster rows identified in Messier, Caldwell, SAC Urban, RASC Finest
NGC or SAC Best NGC, including flagged unresolved list claims for review.
Additional objects require Hunt V10 < 12.5 AND V10 < 17.5-(12.5/3)*log10(radius
in arcmin), with E(B-V)<=3 and valid positive member counts. Every available
source point must pass by default. No inherited V10<11 cut is applied.
Existing primary/alias identities remain intact. Position pairing accepts only
reciprocal unique, otherwise unmatched Dias/Hunt rows inside BOTH published
radii. Published alias ambiguities remain review flags on positional pairs;
other coincidences are audited.
No arguments displays help. No installed data or chart defaults are changed.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np
from astropy.table import MaskedColumn,Table
from merge_open_clusters import positional_audit,text
from plot_merged_open_clusters import number

MANDATORY = ['messier','caldwell','sac_urban','rasc_finest_ngc','sac_best_ngc']
ID_COLUMNS = ['Messier_id','Caldwell_id','NGC_id','IC_id','Melotte_id','Collinder_id','Other_ids']


def position_pairs(table, mode='unique-mutual-radii'):
    """Pair before photometric selection; keep the original ID lineage."""
    if mode not in ('unique-mutual-radii','audit-only'): raise ValueError('Invalid position-match mode.')
    table=table.copy(copy_data=True)
    for name in table.colnames:
        if table[name].dtype.kind=='U':
            original=table[name]
            table.replace_column(name,MaskedColumn(original,dtype='U'+str(max(128,2*original.dtype.itemsize//4+1)),
                                 mask=np.ma.getmaskarray(original),unit=original.unit))
    original_wenu_ids=[text(v) for v in table['wenu_id']]
    drows=[i for i,row in enumerate(table) if bool(row['has_dias'])]
    hrows=[i for i,row in enumerate(table) if bool(row['has_hunt'])]
    def source(indices,prefix):
        output=Table()
        for column in ['ra_deg','dec_deg','apparent_diameter_arcmin']:
            output[column]=table[prefix+'_'+column][indices]
        output['identifier']=table['dias_id' if prefix=='dias' else 'hunt_name'][indices]
        if prefix=='hunt': output['hunt_id']=table['hunt_id'][indices]
        return output
    dindex={row:i for i,row in enumerate(drows)}; hindex={row:i for i,row in enumerate(hrows)}
    groups=[(dindex.get(i),hindex.get(i),'existing') for i in range(len(table))]
    ledger,counts=positional_audit(source(drows,'dias'),source(hrows,'hunt'),groups)
    lookup_d={text(table['dias_id'][i]):i for i in drows}
    lookup_h={int(table['hunt_id'][i]):i for i in hrows}
    candidates=[row for row in ledger if row['category']=='both_unmatched']
    dc=Counter(text(row['dias_id']) for row in candidates)
    hc=Counter(int(row['hunt_id']) for row in candidates)
    removed=set(); redirects=[]; decisions=[]
    table['previous_wenu_ids']=MaskedColumn([text(v) for v in table['wenu_id']],dtype='U64')
    table['positional_pair_separation_arcmin']=MaskedColumn(np.zeros(len(table)),mask=True)
    table['positional_pair_provisional']=np.zeros(len(table),bool)
    for row in ledger:
        di=lookup_d[text(row['dias_id'])]; hi=lookup_h[int(row['hunt_id'])]
        source_ids=[text(table['wenu_id'][di]),text(table['wenu_id'][hi])]
        decision='existing_identifier_pair' if row['identifier_matched'] else 'matched_elsewhere_review'
        if row['category']=='both_unmatched':
            if dc[text(row['dias_id'])]!=1 or hc[int(row['hunt_id'])]!=1:
                decision='competing_position_candidates'
            elif mode=='audit-only': decision='unique_position_candidate'
            else:
                decision='paired_position_provisionally'
                original_d={c:table[c][di] for c in table.colnames}
                original_h={c:table[c][hi] for c in table.colnames}
                for column in table.colnames:
                    if column.startswith('hunt_'): table[column][di]=original_h[column]
                    elif column.startswith('in_'):
                        a,b=original_d[column],original_h[column]
                        table[column][di]=(True if (not np.ma.is_masked(a) and bool(a)) or
                          (not np.ma.is_masked(b) and bool(b)) else np.ma.masked if np.ma.is_masked(a) or np.ma.is_masked(b) else False)
                    elif column in ID_COLUMNS:
                        values={v.strip() for value in (original_d[column],original_h[column]) for v in text(value).split('|') if v.strip()}
                        table[column][di]='|'.join(sorted(values))
                for column in ('RA','Dec','RA_source','position_epoch'): table[column][di]=original_h[column]
                for column in ('identity_review','reference_review','observing_membership_review'):
                    if column in table.colnames: table[column][di]=bool(original_d[column]) or bool(original_h[column])
                table['has_hunt'][di]=True
                table['match_method'][di]='position_mutual_radii_unique'
                retained=min(source_ids);table['wenu_id'][di]=retained
                table['previous_wenu_ids'][di]='|'.join(sorted(set(source_ids)))
                table['positional_pair_separation_arcmin'][di]=row['separation_arcmin']
                table['positional_pair_provisional'][di]=True
                removed.add(hi);redirects.append(dict(previous_ids=source_ids,retained_id=retained))
        decisions.append(decision)
    ledger['curation_pair_decision']=decisions
    ledger['dias_input_wenu_id']=[original_wenu_ids[lookup_d[text(row['dias_id'])]] for row in ledger]
    ledger['hunt_input_wenu_id']=[original_wenu_ids[lookup_h[int(row['hunt_id'])]] for row in ledger]
    # The source identifiers and both published centres remain authoritative;
    # redirects provide exact pre-curation ID lineage for accepted pairs.
    output=table[[i for i in range(len(table)) if i not in removed]]
    return output,ledger,dict(input_rows=len(table),post_pair_rows=len(output),
        added_positional_pairs=len(removed),decisions=dict(Counter(decisions)),redirects=redirects,positional_audit=counts)


def selection(table,max_v10=12.5,max_ebv=3.0,source_policy='all'):
    """Mandatory lists OR intersection of numeric tests, with explicit reasons."""
    if not np.isfinite(max_v10) or (max_ebv is not None and not np.isfinite(max_ebv)):
        raise ValueError('Cuts must be finite.')
    if source_policy not in ('all','any'): raise ValueError('Invalid source policy.')
    table=table.copy(copy_data=True); evidence=[]
    for row in table:
        certain=[name for name in MANDATORY if not np.ma.is_masked(row['in_'+name]) and bool(row['in_'+name])]
        uncertain=[name for name in MANDATORY if np.ma.is_masked(row['in_'+name])]
        record=dict(mandatory_lists='|'.join(certain),mandatory_list_claims='|'.join(uncertain),
                    retained_by_mandatory_list=bool(certain),retained_by_mandatory_review=bool(uncertain))
        passes=[]; sources=[]; v10=number(row,'hunt_v10')
        for source in ('dias','hunt'):
            radius=number(row,source+'_apparent_diameter_arcmin')/2
            members=number(row,source+'_member_count'); ebv=number(row,source+'_reddening_e_bv')
            boundary=17.5-(12.5/3)*np.log10(radius) if np.isfinite(radius) and radius>0 else np.nan
            exists=bool(row['has_'+source])
            reason=('not_in_source' if not exists else 'missing_v10' if not np.isfinite(v10) else
              'invalid_radius' if not np.isfinite(boundary) else
              'invalid_member_count' if not np.isfinite(members) or members<=0 else
              'missing_ebv' if max_ebv is not None and not np.isfinite(ebv) else
              'ebv_cut' if max_ebv is not None and ebv>max_ebv else
              'v10_cut' if v10>=max_v10 else 'radius_v10_boundary' if v10>=boundary else 'pass')
            record[source+'_radius_arcmin']=radius; record[source+'_v10_boundary']=boundary
            record[source+'_numeric_reason']=reason; record[source+'_numeric_pass']=reason=='pass'
            if exists: passes.append(reason=='pass')
            if reason=='pass': sources.append(source)
        numeric=bool(passes) and (all(passes) if source_policy=='all' else any(passes))
        record['retained_by_numeric_intersection']=numeric
        record['numeric_passing_sources']='|'.join(sources)
        record['selected']=bool(certain or uncertain or numeric)
        record['selection_reason']='|'.join((['mandatory_list'] if certain else [])+
          (['mandatory_list_claim_review'] if uncertain else [])+(['numeric_intersection'] if numeric else [])) or 'excluded'
        record['source_catalogues']='|'.join(source for source in ('dias','hunt') if row['has_'+source])
        evidence.append(record)
    for column in evidence[0]: table['selection_'+column]=[r[column] for r in evidence]
    return table


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog='Usage: PYTHONPATH=../src python curate_open_clusters.py --catalogue ../output/open_cluster_comparison_v3/wenu_open_clusters_v3.ecsv --output-directory ../output/curation_v0.1\n'
      'The first CSV row contains column names; provenance/criteria are explicit row columns and a JSON summary.\n'
      'Outputs: <name>.csv/.ecsv, _selection.csv, _pairing.csv, _summary.json; existing products are refused.\n'
      'Position pairs remain provisional; old union IDs are retained in previous_wenu_ids/redirects. No chart adoption.')
    parser.add_argument('--catalogue',type=Path,required=True,help='Full union ECSV, including verified observing memberships and source masks.')
    parser.add_argument('--output-directory',type=Path,required=True)
    parser.add_argument('--name',default='wenu_open_clusters_v0.1')
    parser.add_argument('--max-v10',type=float,default=12.5,help='Strict Hunt V10 limit for numeric additions; default 12.5.')
    parser.add_argument('--max-ebv',type=float,default=3.,help='Source-specific E(B-V) <= limit for numeric additions only.')
    parser.add_argument('--without-ebv-cut',action='store_true')
    parser.add_argument('--source-policy',choices=['all','any'],default='all',help='Numeric additions must pass every available source point (default), or at least one.')
    parser.add_argument('--position-match',choices=['unique-mutual-radii','audit-only'],default='unique-mutual-radii')
    arguments=sys.argv[1:] if argv is None else list(argv)
    if not arguments: parser.print_help();return 0
    args=parser.parse_args(arguments)
    if not re.fullmatch(r'[A-Za-z0-9_-]+_v\d+(?:\.\d+)?',args.name): raise ValueError('Use an explicit versioned filename prefix.')
    paths={suffix:args.output_directory/(args.name+suffix) for suffix in ('.csv','.ecsv','_selection.csv','_pairing.csv','_summary.json')}
    if any(path.exists() for path in paths.values()): raise FileExistsError('Curation products exist; use a new version.')
    table=Table.read(args.catalogue,format='ascii.ecsv')
    if not len(table) or len(set(table['wenu_id']))!=len(table): raise ValueError('Empty or duplicate-ID union.')
    counts=table.meta.get('observing_membership',{}).get('counts',{})
    for name in MANDATORY:
        if 'in_'+name not in table.colnames or counts.get(name,{}).get('source_records',0)<=0:
            raise ValueError('Mandatory list unavailable or unverified: '+name)
    original_ids=table['wenu_id'].copy()
    paired,pair_ledger,pair_summary=position_pairs(table,args.position_match)
    ebv=None if args.without_ebv_cut else args.max_ebv
    annotated=selection(paired,args.max_v10,ebv,args.source_policy)
    selected=annotated[np.asarray(annotated['selection_selected'],bool)]
    policy=dict(mandatory_lists=MANDATORY,mandatory_policy='All resolved cluster rows and unresolved claims retained; mandatory rows bypass all numeric cuts.',
      numeric_policy='Intersection: positive source radius/member_count, finite Hunt V10, strict V10 below sloping boundary and max_v10; source-specific reddening cut.',
      boundary='V10 < 17.5 - (12.5/3) * log10(radius_arcmin); extrapolated outside 1..1000 arcmin.',
      max_v10=args.max_v10,max_ebv=ebv,source_policy=args.source_policy,
      position_policy='Strict separation < both published radii; reciprocal unique unmatched pairs are provisional and retain unresolved alias review flags.',
      position_mode=args.position_match,previous_v10lt11_cut_inherited=False,
      scope='Cluster union only; non-cluster list targets are not inserted. Source definitions are preserved; no member-count threshold beyond valid positive plot coordinates.')
    input_hash=hashlib.sha256(args.catalogue.read_bytes()).hexdigest()
    selected['selection_criteria']='mandatory five lists OR [V10 < '+str(args.max_v10)+' AND V10 < 17.5-(12.5/3)*log10(radius_arcmin) AND '+('no reddening cut' if ebv is None else 'E(B-V) <= '+str(ebv))+']; positive source member_count/radius; '+args.source_policy+' available source points'
    selected['input_catalogue_sha256']=input_hash
    selected.meta=dict(database='wenu_open_clusters',version=args.name.rsplit('_v',1)[1],
                      selected_rows=len(selected),selection_policy=policy,input_catalogue_metadata=deepcopy(table.meta))
    summary=dict(version=selected.meta['version'],input_file=str(args.catalogue),input_sha256=input_hash,
      input_rows=len(table),selected_rows=len(selected),policy=policy,pairing=pair_summary,
      retained_by_mandatory_list=int(np.count_nonzero(selected['selection_retained_by_mandatory_list'])),
      retained_by_mandatory_review=int(np.count_nonzero(selected['selection_retained_by_mandatory_review'])),
      retained_by_numeric_intersection=int(np.count_nonzero(selected['selection_retained_by_numeric_intersection'])),
      new_numeric_only=int(np.count_nonzero(selected['selection_retained_by_numeric_intersection'] &
          ~selected['selection_retained_by_mandatory_list'] & ~selected['selection_retained_by_mandatory_review'])),
      input_id_conservation=len(original_ids)==sum(len(text(v).split('|')) for v in paired['previous_wenu_ids']))
    assert summary['input_id_conservation']
    args.output_directory.mkdir(parents=True,exist_ok=True)
    selected.write(paths['.csv'],format='ascii.csv');selected.write(paths['.ecsv'],format='ascii.ecsv')
    columns=['wenu_id','previous_wenu_ids','dias_id','hunt_id','hunt_name']+[c for c in annotated.colnames if c.startswith('selection_')]
    annotated[columns].write(paths['_selection.csv'],format='ascii.csv')
    pair_ledger.write(paths['_pairing.csv'],format='ascii.csv')
    summary['products']={suffix:dict(file=path.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for suffix,path in paths.items() if suffix!='_summary.json'}
    paths['_summary.json'].write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({key:summary[key] for key in ('input_rows','selected_rows','retained_by_mandatory_list','retained_by_mandatory_review','new_numeric_only')}))
    print('Additional positional pairs:',pair_summary['added_positional_pairs'])
    for path in paths.values():print(path)
    return 0


if __name__=='__main__':raise SystemExit(main())
