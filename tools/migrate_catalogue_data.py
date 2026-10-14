#!/usr/bin/env python3
"""Move legacy observing files to per-list directories without changing bytes.

Verifies source/CSV receipts before migration and refuses conflicting targets.
The old flat directories are removed only after every file has a verified copy.
Accepted cluster catalogues are promoted separately; output experiments remain.
No arguments displays help and writes nothing.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from catalogue_data_layout import ROOT,OBSERVING,canonical_file,copy_verified,check_targets,provenance


def migrate(legacy, destination, *, accepted=None):
    legacy,destination=Path(legacy),Path(destination)
    files=[]; directories=[]; receipts={}
    for batch,sources,csvs,registry_name in [
        ('original','sources_v1','csv_v1','observing_sources_v1.json'),
        ('additions','sources_additions_v1','csv_additions_v1','observing_additions_v1.json')]:
        registry=destination/registry_name
        manifest=json.loads(registry.read_text())
        source=legacy/sources
        if not source.is_dir(): raise FileNotFoundError(str(source))
        for product in manifest['products']:
            path=source/product['file'];data=path.read_bytes()
            if len(data)!=product['bytes'] or hashlib.sha256(data).hexdigest()!=product['sha256']:
                raise ValueError('Legacy source checksum mismatch: '+str(path))
            files.append((path,canonical_file(destination,path.name,batch)))
        # Retain additional local acquisition receipts beside the registry.
        covered={p['file'] for p in manifest['products']}
        for extra in source.iterdir():
            if extra.name not in covered:
                if not extra.is_file(): raise ValueError('Unknown nested legacy directory: '+str(extra))
                files.append((extra,destination/f'{batch}_{extra.name}'))
        converted=legacy/csvs
        if batch=='original': from observing_list_membership import load_converted
        else: from observing_list_additions import load_converted
        _,receipt=load_converted(converted,registry)
        receipts[batch]=(registry,receipt)
        for path in converted.iterdir():
            if not path.is_file(): raise ValueError('Unknown nested CSV directory: '+str(path))
            files.append((path,canonical_file(destination,path.name,batch)))
        directories += [source,converted]
    check_targets(files)
    if accepted is not None:
        from prepare_open_cluster_catalogue import promotion_files
        promoted=promotion_files(accepted,destination.parent/'curated_catalogs/open_clusters')
        check_targets(promoted)
        selector=destination.parent/'curated_catalogs/open_clusters/open_star_clusters.ecsv'
        if (selector.exists() or selector.is_symlink()) and not selector.is_symlink():
            raise ValueError('Curated selector is a regular file; refusing replacement.')
    copy_verified(files)
    for batch,(registry,receipt) in receipts.items(): provenance(destination,registry,batch,receipt)
    if accepted is not None:
        from prepare_open_cluster_catalogue import promote_catalogue
        promote_catalogue(accepted,destination.parent/'curated_catalogs/open_clusters',activate=True)
        # Clean only the obsolete selector/version if they match accepted bytes.
        old=ROOT/'data/catalogs/open_clusters'
        if old.is_dir():
            target=old/Path(accepted).name;selector=old/'open_star_clusters.ecsv'
            if target.is_file() and target.read_bytes()==Path(accepted).read_bytes():
                if selector.is_symlink() and selector.resolve()==target.resolve(): selector.unlink()
                if not selector.exists() and not selector.is_symlink(): target.unlink()
            for directory in [old,old.parent,old.parent.parent]:
                if directory.is_dir() and not any(directory.iterdir()): directory.rmdir()
    for source,target in files:
        if source.resolve()!=target.resolve():
            if source.read_bytes()!=target.read_bytes(): raise ValueError('Refusing removal after failed verification.')
            source.unlink()
    for directory in directories: directory.rmdir()
    if legacy.is_dir() and not any(legacy.iterdir()): legacy.rmdir()
    report=dict(migrated_files=len(files),products={str(target):hashlib.sha256(target.read_bytes()).hexdigest() for _,target in files},
        policy='All legacy source and CSV bytes verified before copy; originals removed only after verified copies. Historical receipts/registries unchanged.')
    (destination/'migration_receipt_v1.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy-directory',type=Path,default=ROOT/'src/wenu/data/catalogs/observing_lists')
    parser.add_argument('--observing-directory',type=Path,default=OBSERVING)
    parser.add_argument('--accepted-catalogue',type=Path,help='Accepted output ECSV with its summary/ledgers; promote to curated_catalogs and select it.')
    arguments=sys.argv[1:] if argv is None else list(argv)
    if not arguments: parser.print_help();return 0
    args=parser.parse_args(arguments)
    report=migrate(args.legacy_directory,args.observing_directory,accepted=args.accepted_catalogue)
    print('Migrated verified files:',report['migrated_files'])
    print(args.observing_directory)
    return 0


if __name__=='__main__': raise SystemExit(main())
