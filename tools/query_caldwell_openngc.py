#!/usr/bin/env python3
"""Build the complete Caldwell observing catalogue from pinned OpenNGC data.

Membership is a versioned factual cross-identification ledger. Parameters are
from OpenNGC, not from the observing list. This maintenance tool is never run
by chart generation.
"""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'src/wenu/data/catalogs/caldwell'
RELEASE = 'v20260501'
RAW_ROOT = f'https://raw.githubusercontent.com/mattiaverga/OpenNGC/{RELEASE}'
SOURCE_HASHES = {
    'NGC.csv': '840fe0c9ee1332e551b2e722a0e92726cd7b157914a3d2177602832aadd3aa9e',
    'addendum.csv': '1d8f0914e643ada325a5a94d88d8fefad6a4937a2f77cc34f21483af22b11983',
}
MEMBERSHIP_URL = 'https://old.astroleague.org/al/obsclubs/caldwell/cldwlist.html'
TYPE_NAMES = {'OCl': 'open cluster', 'GCl': 'globular cluster',
    'Cl+N': 'open cluster with nebulosity', '*Ass': 'stellar association',
    'G': 'galaxy', 'PN': 'planetary nebula', 'SNR': 'supernova remnant',
    'HII': 'HII region', 'DrkN': 'dark nebula', 'RfN': 'reflection nebula',
    'EmN': 'emission nebula', 'Neb': 'nebula'}


def digest(content):
    return hashlib.sha256(content).hexdigest()


def membership(path=OUTPUT/'caldwell_membership_v1.csv'):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if [int(row['caldwell_number']) for row in rows] != list(range(1, 110)):
        raise ValueError('Caldwell membership must contain numbers 1 through 109 exactly once.')
    return rows


def read_sources(payloads):
    rows = {}
    for filename, content in payloads.items():
        reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig')), delimiter=';')
        for row in reader:
            if row['Name'] in rows:
                raise ValueError(f"Duplicate OpenNGC name: {row['Name']}")
            rows[row['Name']] = (filename, row)
    return rows


def normalize(members, sources):
    records = []
    def number(value):
        return float(value) if value.strip() else np.nan
    for member in members:
        primary = member['primary_id']
        source_name = primary
        visited = set()
        while True:
            if source_name in visited:
                raise ValueError(f'Duplicate-reference cycle at {primary}.')
            visited.add(source_name)
            if source_name not in sources:
                raise ValueError(f'Missing OpenNGC record: {source_name}.')
            filename, row = sources[source_name]
            if row['Type'] != 'Dup':
                break
            links = [('NGC', row['NGC']), ('IC', row['IC'])]
            links = [(prefix, value) for prefix, value in links if value.strip()]
            if len(links) != 1 or not links[0][1].isdigit():
                raise ValueError(f'Ambiguous duplicate-reference target for {source_name}.')
            source_name = links[0][0] + links[0][1].zfill(4)
        coordinate = SkyCoord(row['RA'], row['Dec'], unit=(u.hourangle, u.deg), frame='icrs')
        kind = TYPE_NAMES.get(row['Type'], row['Type'])
        if member['membership_type'] == 'open_cluster_group':
            kind = 'open cluster group'
        records.append(dict(name=f"C {int(member['caldwell_number'])}",
            caldwell_number=int(member['caldwell_number']), primary_id=primary,
            parameter_source_id=source_name, object_type=kind,
            source_object_type=row['Type'], membership_type=member['membership_type'],
            cluster_components=member['cluster_components'], related_aliases=member['related_aliases'],
            ra_deg=float(coordinate.ra.deg), dec_deg=float(coordinate.dec.deg),
            constellation=row['Const'], major_axis_arcmin=number(row['MajAx']),
            minor_axis_arcmin=number(row['MinAx']), position_angle_deg=number(row['PosAng']),
            vmag=number(row['V-Mag']), b_magnitude=number(row['B-Mag']),
            identifiers=row['Identifiers'], common_name=row['Common names'],
            parameter_sources=row['Sources'], source_file=filename))
    table = Table(rows=records)
    for column in ('ra_deg', 'dec_deg', 'position_angle_deg'):
        table[column].unit = u.deg
    for column in ('major_axis_arcmin', 'minor_axis_arcmin'):
        table[column].unit = u.arcmin
    return table


def download(url):
    request = Request(url, headers={'User-Agent': 'Wenu-catalogue-maintenance/1.0'})
    with urlopen(request, timeout=120) as response:
        return response.read()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-directory', type=Path,
        help='Use cached complete pinned source files instead of downloading.')
    parser.add_argument('--output-directory', type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    payloads = {}
    for name, expected in SOURCE_HASHES.items():
        content = ((args.source_directory/name).read_bytes() if args.source_directory
                   else download(f'{RAW_ROOT}/database_files/{name}'))
        if digest(content) != expected:
            raise ValueError(f'Pinned OpenNGC source digest mismatch: {name}.')
        payloads[name] = content
    licence = (args.source_directory/'CC-BY-SA-4.0.txt').read_bytes() if args.source_directory else download(
        f'{RAW_ROOT}/LICENSES/CC-BY-SA-4.0.txt')
    if digest(licence) != 'cde7883b9050a1104f4ac19a1572aafd6e5d7323b68351aaf51fbf4beba54966':
        raise ValueError('Pinned OpenNGC licence digest mismatch.')
    members = membership()
    table = normalize(members, read_sources(payloads))
    provenance = dict(source='Caldwell membership with OpenNGC parameters',
        catalogue_reference='Patrick Moore, Beyond Messier: The Caldwell Catalog, Sky & Telescope, December 1995',
        membership_source_url=MEMBERSHIP_URL, membership_ledger_sha256=digest(
            (OUTPUT/'caldwell_membership_v1.csv').read_bytes()),
        parameter_source='OpenNGC', release=RELEASE, coordinate_frame='ICRS/J2000',
        retrieved_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        row_count=len(table), license='CC-BY-SA-4.0',
        source_files={name:dict(url=f'{RAW_ROOT}/database_files/{name}',sha256=value)
                      for name,value in SOURCE_HASHES.items()},
        notes='Membership is heterogeneous. C14 is a two-cluster group. OpenNGC duplicate targets supply parameters without changing the original observing designation. Missing photometry is not inferred.')
    table.meta.update(provenance)
    output = args.output_directory
    output.mkdir(parents=True, exist_ok=True)
    products = []
    for suffix in ('ecsv', 'csv'):
        path = output/f'caldwell_openngc.{suffix}'
        table.write(path, format=f'ascii.{suffix}', overwrite=True)
        products.append(path)
    license_path = output/'CC-BY-SA-4.0.txt'
    license_path.write_bytes(licence)
    products.append(license_path)
    provenance['files'] = {p.name:dict(sha256=digest(p.read_bytes())) for p in products}
    (output/'caldwell_openngc.provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(output/'caldwell_openngc.ecsv')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
