#!/usr/bin/env python3
"""Build a separate pinned OpenNGC V-photometry supplement for Dias clusters.

Keep original Dias rows and physical values intact. Acquisition is explicit
maintenance; plotting reads the packaged supplement without network access.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from astropy.table import Table

from query_caldwell_openngc import SOURCE_HASHES, RAW_ROOT, RELEASE, digest, download, read_sources
from compare_open_clusters import openngc_photometry


ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-directory', type=Path)
    parser.add_argument('--data-directory', type=Path, default=ROOT/'src/wenu/data/catalogs')
    args = parser.parse_args(argv)
    payloads = {}
    for name, expected in SOURCE_HASHES.items():
        content = ((args.source_directory/name).read_bytes() if args.source_directory
                   else download(f'{RAW_ROOT}/database_files/{name}'))
        if digest(content) != expected:
            raise ValueError(f'Pinned OpenNGC source digest mismatch: {name}.')
        payloads[name] = content
    dias_path = args.data_directory/'open_clusters/open_clusters_dias_heasarc.ecsv'
    table = openngc_photometry(Table.read(dias_path), read_sources(payloads))
    provenance = dict(source='OpenNGC', release=RELEASE, license='CC-BY-SA-4.0',
        licence_path='../caldwell/CC-BY-SA-4.0.txt',
        retrieved_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        dias_sha256=digest(dias_path.read_bytes()),
        source_files={name:dict(url=f'{RAW_ROOT}/database_files/{name}',sha256=value)
                      for name,value in SOURCE_HASHES.items()},
        matching_policy='Explicit primary identifier first, then source aliases; collapse source duplicate references, reject multiple targets and non-cluster types. No positional matching or imputed photometry.',
        brightness_notice='Source V magnitudes are heterogeneous integrated values. Retain source codes, notes and shared-identity review flags; availability is not an observability ranking.')
    table.meta.update(provenance)
    destination = dias_path.parent/'open_clusters_openngc_photometry_v1.ecsv'
    table.write(destination, format='ascii.ecsv', overwrite=True)
    provenance['files'] = {destination.name:dict(sha256=digest(destination.read_bytes()))}
    (dias_path.parent/'open_clusters_openngc_photometry_v1.provenance.json').write_text(
        json.dumps(provenance, indent=2)+'\n')
    print(destination)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
