#!/usr/bin/env python3
"""Depurate a selected union and optionally install an atlas catalogue.

Keep Hunt type o and Dias-only open clusters. Exclude single-source objects
without another catalogue designation or resolved observing-list membership;
masked claims remain for review. HSC alone is not corroboration; OC and other
modern catalogues count. No physical identity is decided by sky proximity.
All source columns/IDs are retained. The original selection is never changed. Trial products belong in output/.
Use --promote-catalogue only after reviewing an accepted version; its entire
verified bundle is copied to curated_catalogs without filtering again.
No arguments prints help and creates nothing.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np
from astropy.coordinates import angular_separation
from astropy.table import Table
from wenu.objects.open_clusters import OpenClusters
from merge_open_clusters import text


from catalogue_data_layout import CURATED, check_targets, copy_verified
DEFAULT_INSTALL_DIRECTORY = CURATED


def depurate(table):
    """Annotate every row; retain unresolved corroboration, not false absences."""
    marked = table.copy(copy_data=True)
    reasons, evidence, uncertain = [], [], []
    list_columns = [c for c in table.colnames if c.startswith('in_')]
    for row in table:
        identifiers = {v.strip() for c in ('dias_id','hunt_name','Messier_id','Caldwell_id',
            'NGC_id','IC_id','Melotte_id','Collinder_id','Other_ids')
            if c in table.colnames for v in text(row[c]).split('|') if v.strip()}
        external = sorted(v for v in identifiers if not re.fullmatch(r'HSC[ _-]*\d+',v,re.I))
        memberships = [c for c in list_columns if not np.ma.is_masked(row[c]) and bool(row[c])]
        claims = [c for c in list_columns if np.ma.is_masked(row[c])]
        exclusive = bool(row['has_dias']) != bool(row['has_hunt'])
        uncorroborated = exclusive and not external and not memberships and not claims
        reason = ('hunt_type_'+text(row['hunt_type']) if bool(row['has_hunt']) and text(row['hunt_type']) != 'o'
                  else 'single_source_no_other_compilation' if uncorroborated else '')
        reasons.append(reason)
        evidence.append('|'.join(external + memberships))
        uncertain.append(bool(claims) and not external and not memberships)
    marked['depuration_reason'] = reasons
    marked['other_compilation_evidence'] = evidence
    marked['other_compilation_unresolved'] = uncertain
    marked['depuration_retained'] = [not r for r in reasons]
    selected = marked[np.asarray(marked['depuration_retained'],bool)]
    return OpenClusters.normalize_catalogue(selected), marked


def positional_review(table):
    """Audit all source-centre pairs inside both half-diameters; never merge."""
    records = []
    for i, a in enumerate(table):
        for b in table[i+1:]:
            for sa in ('dias','hunt'):
                if not a['has_'+sa]: continue
                for sb in ('dias','hunt'):
                    if not b['has_'+sb]: continue
                    fields = [(r,s+'_'+c) for r,s in ((a,sa),(b,sb))
                              for c in ('ra_deg','dec_deg','apparent_diameter_arcmin')]
                    if any(np.ma.is_masked(r[c]) for r,c in fields): continue
                    ra,da,diam_a,rb,db,diam_b = [float(r[c]) for r,c in fields]
                    if not np.all(np.isfinite([ra,da,diam_a,rb,db,diam_b])) or abs(da)>90 or abs(db)>90 or min(diam_a,diam_b)<=0: continue
                    separation = float(np.rad2deg(angular_separation(*np.deg2rad([ra,da,rb,db])))*60)
                    if separation < diam_a/2 and separation < diam_b/2:
                        records.append((text(a['wenu_id']),text(b['wenu_id']),text(a['identifier']),text(b['identifier']),sa,sb,separation,diam_a,diam_b))
    return Table(rows=records, names=['wenu_id_a','wenu_id_b','cluster_a','cluster_b','source_a','source_b',
        'separation_arcmin','diameter_a_arcmin','diameter_b_arcmin'],
        dtype=['U32','U32','U128','U128','U8','U8',float,float,float])


def install(catalogue, directory, *, activate=False):
    """Install immutable bytes, then atomically replace only the selector link."""
    directory = Path(directory)
    data = Path(catalogue).read_bytes()
    if not re.fullmatch(r'wenu_open_clusters_v\d+(?:\.\d+)?\.ecsv',Path(catalogue).name):
        raise ValueError('Only a versioned wenu_open_clusters ECSV can be installed.')
    normalized = OpenClusters.normalize_catalogue(Table.read(catalogue,format='ascii.ecsv'))
    OpenClusters._validate(normalized)
    target = directory/Path(catalogue).name
    selector = directory/'open_star_clusters.ecsv'
    if target.exists() or target.is_symlink():
        raise FileExistsError('Installed version exists; choose a new version.')
    if activate and (selector.exists() or selector.is_symlink()) and not selector.is_symlink():
        raise ValueError('Active selector is a regular file; refusing replacement.')
    directory.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream: stream.write(data)
    if activate:
        import os
        import tempfile
        name = Path(tempfile.mkdtemp(prefix='.wenu-selector-',dir=directory))
        try:
            link = name/'selector'
            link.symlink_to(target.name)
            os.replace(link,selector)
        finally:
            name.rmdir()
    return selector if activate else target


def promotion_files(catalogue, directory):
    """Admit the complete accepted output bundle using its recorded hashes."""
    catalogue,directory=Path(catalogue),Path(directory)
    OpenClusters._validate(OpenClusters.normalize_catalogue(Table.read(catalogue,format='ascii.ecsv')))
    summary_path=catalogue.with_name(catalogue.stem+'_summary.json')
    summary=json.loads(summary_path.read_text())
    records=summary['products']
    files=[]
    for name,record in records.items():
        filename=record['file'] if isinstance(record,dict) else name
        digest=record['sha256'] if isinstance(record,dict) else record
        if Path(filename).name!=filename or not filename.startswith(catalogue.stem):
            raise ValueError('Invalid accepted product filename.')
        source=catalogue.parent/filename
        if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:
            raise ValueError('Accepted product checksum mismatch: '+filename)
        files.append((source,directory/filename))
    if catalogue.name not in [p.name for p,_ in files]: raise ValueError('Accepted ECSV is absent from summary.')
    files.append((summary_path,directory/summary_path.name))
    return files


def promote_catalogue(catalogue, directory=CURATED, *, activate=False):
    """Copy accepted data and review evidence; preserve all output experiments."""
    files=promotion_files(catalogue,directory)
    selector=Path(directory)/'open_star_clusters.ecsv'
    if activate and (selector.exists() or selector.is_symlink()) and not selector.is_symlink():
        raise ValueError('Selector is a regular file; refusing replacement.')
    copy_verified(files)
    if activate:
        import os,tempfile
        stage=Path(tempfile.mkdtemp(prefix='.wenu-selector-',dir=directory))
        try:
            link=stage/'selector';link.symlink_to(Path(catalogue).name);os.replace(link,selector)
        finally: stage.rmdir()
    return selector if activate else Path(directory)/Path(catalogue).name


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example (from tools): PYTHONPATH=../src python prepare_open_cluster_catalogue.py --catalogue ../output/curation_v0.1/wenu_open_clusters_v0.1.ecsv --output-directory ../output/curation_v0.2 \n'
        'Plot the resulting ECSV with plot_merged_open_clusters.py. Atlas: --open-cluster-catalogue <installed directory>/open_star_clusters.ecsv.\n'
        'Promote after review: --promote-catalogue ../output/curation_v0.2/wenu_open_clusters_v0.2.ecsv --activate\n'
        'Existing different versions are refused. Overlap candidates stay separate; _positions.csv is a review ledger, not a duplicate count.')
    parser.add_argument('--catalogue',type=Path,help='Selected union ECSV, with original masks and source parameters.')
    parser.add_argument('--output-directory',type=Path)
    parser.add_argument('--promote-catalogue',type=Path,help='Accepted output ECSV: verify and copy its complete bundle, without filtering again.')
    parser.add_argument('--curated-directory',type=Path,default=CURATED,help='Accepted working catalogues; default src/wenu/data/curated_catalogs/open_clusters.')
    parser.add_argument('--name',default='wenu_open_clusters_v0.2',help='New versioned prefix.')
    parser.add_argument('--install-directory',type=Path,help='Explicit accepted-directory override for the legacy combined filtering/promotion mode; prefer separate --promote-catalogue.')
    parser.add_argument('--activate',action='store_true',help='Install and select by relative symlink; default src/wenu/data/curated_catalogs/open_clusters.')
    arguments = sys.argv[1:] if argv is None else list(argv)
    if not arguments: parser.print_help(); return 0
    args = parser.parse_args(arguments)
    if not re.fullmatch(r'wenu_open_clusters_v\d+(?:\.\d+)?',args.name): raise ValueError('Use a versioned wenu_open_clusters name.')
    products = {s:args.output_directory/(args.name+s) for s in ('.ecsv','.csv','_depuration.csv','_positions.csv','_summary.json')}
    if any(p.exists() or p.is_symlink() for p in products.values()): raise FileExistsError('Products exist; choose a new version.')
    table = Table.read(args.catalogue,format='ascii.ecsv')
    if not len(table) or len(set(map(str,table['wenu_id']))) != len(table):
        raise ValueError('Empty input or duplicate Wenu IDs.')
    selected,marked = depurate(table)
    if not len(selected): raise ValueError('Depuration retained no open clusters.')
    digest = hashlib.sha256(args.catalogue.read_bytes()).hexdigest()
    selected.meta = deepcopy(table.meta)
    selected.meta.update(database='wenu_open_clusters',version=args.name.rsplit('_v',1)[1],selected_rows=len(selected),
        depuration=dict(input_sha256=digest,policy=__doc__,excluded_counts=dict(Counter(str(v) for v in marked['depuration_reason'] if v))))
    positions = positional_review(selected)
    d,h = np.asarray(selected['has_dias'],bool),np.asarray(selected['has_hunt'],bool)
    summary = dict(input_file=str(args.catalogue),input_sha256=digest,input_rows=len(table),selected_rows=len(selected),
        excluded_counts=selected.meta['depuration']['excluded_counts'],
        source_presence=dict(both=int(sum(d&h)),dias_only=int(sum(d&~h)),hunt_only=int(sum(h&~d))),
        spatial_candidate_pairs=len(set(zip(positions['wenu_id_a'],positions['wenu_id_b']))),
        spatial_source_comparisons=len(positions),physical_duplicate_count=None,
        identity_review_rows=int(sum(selected['identity_review'])),
        note='Spatial overlaps are review candidates. No additional identity merges; all source IDs/positions and provisional-pair flags are preserved.')
    args.output_directory.mkdir(parents=True,exist_ok=True)
    selected.write(products['.ecsv'],format='ascii.ecsv')
    selected.write(products['.csv'],format='ascii.csv')
    marked[['wenu_id','dias_id','hunt_name','hunt_type','has_dias','has_hunt','depuration_retained','depuration_reason',
            'other_compilation_evidence','other_compilation_unresolved']].write(products['_depuration.csv'],format='ascii.csv')
    positions.write(products['_positions.csv'],format='ascii.csv')
    summary['products'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for s,p in products.items() if s!='_summary.json'}
    products['_summary.json'].write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='products'},indent=2))
    if args.install_directory is not None or args.activate:
        print(promote_catalogue(products['.ecsv'],args.install_directory or DEFAULT_INSTALL_DIRECTORY,activate=args.activate))
    return 0


if __name__ == '__main__': raise SystemExit(main())
