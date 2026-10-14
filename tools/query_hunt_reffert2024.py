#!/usr/bin/env python3
"""Explicitly acquire and prepare Hunt & Reffert (2024) for offline curation.

One serial bulk request per CDS file, no automatic retries or per-star queries.
The large raw member table stays in the source cache; compact derived full and
V5<11 catalogues go in the chosen data directory. Existing outputs are refused.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

from hunt_reffert_catalogue import build

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = 'https://cdsarc.cds.unistra.fr/ftp/J/A+A/686/A42/'
FILES = ('ReadMe','clusters.dat.gz','members.dat.gz','crossma.dat.gz')


def acquire(directory):
    directory = Path(directory)
    if directory.exists():
        raise FileExistsError('Download requires a fresh source directory; use --source-directory for an existing verified cache.')
    directory.mkdir(parents=True)
    receipt = {}
    for name in FILES:
        url = BASE_URL+name
        request = urllib.request.Request(url, headers={'User-Agent':'Wenu catalogue curation (Hunt & Reffert 2024)'})
        partial = directory/(name+'.partial')
        print('Downloading '+name+' (serial bulk request)...', flush=True)
        with urllib.request.urlopen(request, timeout=600) as response:
            if response.status != 200:
                raise ValueError('CDS returned HTTP '+str(response.status))
            digest = hashlib.sha256()
            size = 0
            next_progress = 16*1024*1024
            with partial.open('xb') as target:
                while chunk := response.read(1024*1024):
                    target.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
                    if size >= next_progress:
                        print(f"  {name}: {size/(1024*1024):.0f} MiB received", flush=True)
                        next_progress += 16*1024*1024
            with partial.open('rb') as check:
                signature = check.read(2)
            if name.endswith('.gz') and signature != b'\x1f\x8b':
                raise ValueError('CDS did not return gzip data: '+name)
            receipt[name] = dict(url=url, sha256=digest.hexdigest(),bytes=size,
                retrieved_utc=datetime.now(timezone.utc).isoformat(),http_status=response.status)
        partial.rename(directory/name)
        print(f'Completed {name}: {size:,} bytes', flush=True)
    (directory/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--download-directory', type=Path,
        help='Explicit download into a NEW scientific source directory, e.g. src/wenu/data/catalogs/open_clusters/hunt_sources_v1; member file is large.')
    source.add_argument('--source-directory', type=Path,
        help='Offline reuse of complete raw CDS files and receipt.json.')
    parser.add_argument('--data-directory', type=Path, default=ROOT/'src/wenu/data/catalogs',
        help='Destination data root; writes full and curated resources under open_clusters/.')
    parser.add_argument('--min-membership-probability',type=float,default=.5)
    parser.add_argument('--member-aperture',choices=('tidal','jacobi','all'),default='tidal')
    arguments = sys.argv[1:] if argv is None else list(argv)
    if not arguments:
        parser.print_help()
        return 0
    args = parser.parse_args(arguments)
    if not 0 <= args.min_membership_probability <= 1:
        parser.error('Membership probability must be between zero and one.')
    # Reject output conflicts before any provider access.
    from hunt_reffert_catalogue import FULL_NAME, CURATED_NAME, PROVENANCE_NAME
    destination = args.data_directory/'open_clusters'
    if any((destination/name).exists() for name in (FULL_NAME,CURATED_NAME,PROVENANCE_NAME)):
        raise FileExistsError('Prepared Hunt resources already exist; use a fresh candidate data directory.')
    if args.download_directory:
        acquire(args.download_directory)
    print("Validating source hashes and preparing member statistics...", flush=True)
    table, provenance = build(args.source_directory or args.download_directory, destination,
        minimum_probability=args.min_membership_probability,aperture=args.member_aperture)
    print(f'{len(table):,} full rows; {provenance["curated_rows"]:,} open clusters with converted V5 <11.')
    print(destination)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
