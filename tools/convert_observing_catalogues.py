#!/usr/bin/env python3
"""First-pass CSV conversion of verified observing lists containing star clusters.

Preserve source fields/sheets; no cluster union, filtering or chart adoption.
PN, dark-nebula and double/multiple-star programme work is deferred.
No arguments prints help and writes nothing. Excel XLS needs optional xlrd.
"""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys

from observing_list_membership import SOURCE_FILES, excel_rows, records_from_sources

ROOT = Path(__file__).resolve().parents[1]


def convert(directory, destination, registry_path):
    directory,destination,registry_path = map(Path,(directory,destination,registry_path))
    if destination.exists():
        raise FileExistsError('CSV destination already exists; use a new version.')
    manifest = json.loads(registry_path.read_text())
    # Verify the nine source hashes and source-specific membership counts.
    records = records_from_sources(directory,manifest)
    products = {}
    details = []
    def emit(name,columns,rows,source_file,status='source_fields_preserved'):
        stream = io.StringIO(newline='')
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)
        data = stream.getvalue().encode('utf-8')
        products[name] = data
        details.append(dict(file=name,source_file=source_file,rows=len(rows),
            columns=columns,status=status,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    for product in manifest['products']:
        name = product['file']
        if name not in SOURCE_FILES:continue
        path = directory/name
        stem = path.stem
        if path.suffix=='.csv':
            rows = list(csv.reader(path.open(encoding='utf-8',newline='')))
            emit(name,rows[0],rows[1:],name)
        elif path.suffix in ('.xlsx','.xls'):
            for number,rows in enumerate(excel_rows(path),1):
                if not any(any(str(v).strip() for v in row if v is not None) for row in rows):continue
                width = max(map(len,rows))
                # Preserve every cell, including titles, repeated headings and
                # challenge rules. Source row numbers remain explicit.
                emit(stem+f'__sheet{number}.csv',
                    ['source_row']+['source_column_'+str(i+1) for i in range(width)],
                    [[i+1]+[(v if v is not None else '') for v in row]+['']*(width-len(row))
                     for i,row in enumerate(rows)],name,
                    'Original cell grid; title/header rows and separate sheets retained.')
        elif path.suffix=='.pdf':
            from pypdf import PdfReader
            rows = []
            for number,page in enumerate(PdfReader(path).pages,1):
                for line in (page.extract_text() or '').splitlines():
                    if name.startswith('herschel400'):
                        match = re.match(r'^\s*(\d+)\s+(\d+)\s+([\d.]+)\s+([+\-‐−]?\d+)\s+(\d+)\s+([\d.]+)\s+(\S+)\s+(\S+)\s+(.*)',line)
                        if match:rows.append([number,'NGC '+match[1],*match.groups()[1:],line])
                    elif name.startswith('herschel2'):
                        match = re.match(r'^(\d+h\s+\d+m\s+[\d.]+s)\s+(.*?)\s+(\d+)\s+([A-Za-z]{3})\s*$',line)
                        if match:rows.append([number,'NGC '+match[3],match[1],match[2],match[4],line])
                    else:
                        match = re.match(r'^\s*(\d+[ab]?)\s+((?:NGC|IC)\s+\d+)\s+(.*?)\s+(\d+h\d+m[\d.]+s)\s+([+\-].*?\")\s+(.*)',line)
                        if match:rows.append([number,match[1],match[2],match[3],match[4],match[5],match[6],line])
            columns = (['source_page','identifier','RA_h','RA_m','Dec_deg','Dec_arcmin','magnitude','source_type','constellation','source_tail','source_row_text'] if name.startswith('herschel400') else
                       ['source_page','identifier','RA_source','Dec_source','constellation','source_row_text'] if name.startswith('herschel2') else
                       ['source_page','observing_number','identifier','source_alias_and_type','RA_source','Dec_source','source_tail','source_row_text'])
            expected = 112 if name.startswith('rasc') else 400
            if len(rows)!=expected:raise ValueError('PDF CSV row count differs: '+name+' '+str(len(rows)))
            emit(stem+'.csv',columns,rows,name,'Structured identity/coordinate fields plus original row/tail retained; no physical reclassification.')
    emit('observing_memberships_v1.csv',
         ['catalogue','designation','identifiers_json','source_file'],
         [[r['catalogue'],r['designation'],json.dumps(r['identifiers'],ensure_ascii=False),r['source_file']] for r in records],
         'all_source_tables','Membership index only; no source parameters are replaced.')
    receipt = dict(schema_version=1,conversion_version='v1',
        source_registry_sha256=hashlib.sha256(registry_path.read_bytes()).hexdigest(),
        source_sha256={r['file']:r['sha256'] for r in manifest['products'] if r['file'] in SOURCE_FILES},products=details,
        policy='Cluster-containing lists only; all mixed-list rows and source fields/sheets retained. Other programmes deferred. No union, selection or chart adoption.')
    # Build and validate everything before creating the new directory.
    destination.mkdir(parents=True)
    for name,data in products.items():(destination/name).write_bytes(data)
    (destination/'conversion_receipt_v1.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Usage: python tools/convert_observing_catalogues.py --source-directory src/wenu/data/catalogs/observing_lists/sources_v1\n'
               'Output: CSV files per source/sheet, observing_memberships_v1.csv and conversion_receipt_v1.json.\n'
               'Existing outputs are refused. XLSX/CSV/TSV/PDF remain offline; legacy XLS requires xlrd>=2,<3.')
    parser.add_argument('--source-directory',type=Path,required=True)
    parser.add_argument('--output-directory',type=Path,default=ROOT/'src/wenu/data/catalogs/observing_lists/csv_v1')
    parser.add_argument('--registry',type=Path,default=ROOT/'src/wenu/data/catalogs/observing_lists/observing_sources_v1.json')
    arguments = sys.argv[1:] if argv is None else list(argv)
    if not arguments:parser.print_help();return 0
    args = parser.parse_args(arguments)
    receipt = convert(args.source_directory,args.output_directory,args.registry)
    print(f"Converted {len(receipt['source_sha256'])} verified source files into {len(receipt['products'])} CSV files.")
    print(args.output_directory)
    return 0


if __name__=='__main__':raise SystemExit(main())
