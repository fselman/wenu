"""Versioned acquisition conversion for the six supplementary observing lists."""

import csv
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
from zipfile import ZipFile

from observing_list_membership import xlsx_rows

COUNTS = dict(sac_urban=100, sac_beyond_ngc=110, sac_red_stars=333,
              sac_asterisms=114, al_carbon_stars=128, al_dark_nebulae=140)


class SourceTables(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.row = None; self.cell = None
    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.row = []
        if tag in ('td', 'th') and self.row is not None: self.cell = ''
    def handle_data(self, value):
        if self.cell is not None: self.cell += value
    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(self.cell.strip()); self.cell = None
        if tag == 'tr' and self.row is not None:
            if self.row: self.rows.append(self.row)
            self.row = None


def source_rows(directory):
    """Preserve source tables, never infer an identity from narrative or position."""
    directory = Path(directory)
    result = []
    for catalogue, filename in [('sac_urban', 'sac_urban_source_v1.html'),
                                ('sac_beyond_ngc', 'sac_beyond_ngc_source_v1.html')]:
        parser = SourceTables(); parser.feed((directory/filename).read_text())
        rows = [r for r in parser.rows if (r[0].isdigit() if catalogue == 'sac_urban'
                                          else len(r) >= 7 and r[1].upper() in {v.upper() for v in CONSTELLATIONS})]
        for row in rows:
            identifier = row[1] if catalogue == 'sac_urban' else row[0]
            result.append((catalogue, identifier, filename, row))
    for catalogue, filename in [('sac_red_stars', 'sac_red_stars_source_v1.zip'),
                                ('sac_asterisms', 'sac_asterisms_source_v1.zip')]:
        with ZipFile(directory/filename) as archive:
            member = next(n for n in archive.namelist() if 'qcq' in n.lower())
            rows = list(csv.reader(io.StringIO(archive.read(member).decode('cp1252'))))
        for row in rows[1:]:
            if row and row[0].strip():
                result.append((catalogue, row[0].strip(), filename, [v.strip() for v in row]))
    filename = 'al_carbon_stars_source_v1.xlsx'
    for sheet, rows in enumerate(xlsx_rows(directory/filename), 1):
        for row in rows:
            if len(row) > 5 and re.fullmatch(r'\d{2}\s+\d{2}\s+\d{2}', row[4].strip()):
                result.append(('al_carbon_stars', row[2].strip(), filename, [str(sheet)]+row))
    from pypdf import PdfReader
    for filename, subset in [('al_dark_required_source_v1.pdf', 'required'),
                             ('al_dark_optional_source_v1.pdf', 'optional')]:
        for number, page in enumerate(PdfReader(directory/filename).pages, 1):
            text = page.extract_text() or ''
            for match in re.finditer(r'^(.+?)\s+([A-Za-z]{3})\s+(\d+h.*?)$', text, re.M):
                if match[2] not in CONSTELLATIONS: continue
                identifier = re.sub(r'\s+', ' ', match[1].strip())
                if identifier == 'Coalsack': identifier = 'Northern Coalsack'
                # Store factual coordinate fields, leaving ambiguous sizes unparsed.
                coord = re.match(r'(.*?)\s+([+\-]\s*\d+°\s*\d+)', match[3])
                if coord is None: raise ValueError('Unparsed dark-nebula coordinate: '+identifier)
                result.append(('al_dark_nebulae', identifier, filename,
                               [subset, str(number), identifier, match[2], coord[1], coord[2]]))
        if subset == 'required':
            # One programme target is a whole-sky feature, with no single centre.
            result.append(('al_dark_nebulae', 'The Great Rift', filename,
                           [subset, '1', 'The Great Rift', '', '', '']))
    observed = {name: sum(r[0] == name for r in result) for name in COUNTS}
    if observed != COUNTS: raise ValueError('Addition parse counts differ: '+str(observed))
    return result


CONSTELLATIONS = set('And Ant Aps Aqr Aql Ara Ari Aur Boo Cae Cam Cnc CVn CMa CMi Cap Car Cas Cen Cep Cet Cha Cir Col Com CrA CrB Crv Crt Cru Cyg Del Dor Dra Equ Eri For Gem Gru Her Hor Hya Hyi Ind Lac Leo LMi Lep Lib Lup Lyn Lyr Men Mic Mon Mus Nor Oct Oph Ori Pav Peg Per Phe Pic Psc PsA Pup Pyx Ret Sge Sgr Sco Scl Sct Ser Sex Tau Tel Tri TrA Tuc UMa UMi Vel Vir Vol Vul'.split())


def convert(directory, destination, registry_path):
    directory, destination, registry_path = map(Path, (directory, destination, registry_path))
    if destination.exists(): raise FileExistsError('CSV destination already exists; use a new version.')
    registry = json.loads(registry_path.read_text())
    for product in registry['products']:
        name = product['file']
        if Path(name).name != name: raise ValueError('Invalid source filename.')
        data = (directory/name).read_bytes()
        if len(data) != product['bytes'] or hashlib.sha256(data).hexdigest() != product['sha256']:
            raise ValueError('Addition source checksum mismatch: '+name)
    records = source_rows(directory)
    products = {}; details = []
    def emit(name, columns, rows):
        stream = io.StringIO(newline=''); writer = csv.writer(stream)
        writer.writerow(columns); writer.writerows(rows)
        data = stream.getvalue().encode('utf-8'); products[name] = data
        details.append(dict(file=name, rows=len(rows), bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    memberships = []
    for catalogue in COUNTS:
        subset = [r for r in records if r[0] == catalogue]
        width = max(len(r[3]) for r in subset)
        emit(catalogue+'_list_v1.csv', ['identifier', 'source_file']+
             ['source_column_'+str(i+1) for i in range(width)],
             [[r[1], r[2]]+r[3]+['']*(width-len(r[3])) for r in subset])
        for _, identifier, filename, _ in subset:
            # A star near/in a cluster and an asterism's narrative NGC reference
            # are not identities of that physical cluster.
            memberships.append([catalogue, identifier, json.dumps([identifier]), filename])
    emit('observing_memberships_v1.csv', ['catalogue', 'designation', 'identifiers_json', 'source_file'], memberships)
    receipt = dict(schema_version=1, source_registry_sha256=hashlib.sha256(registry_path.read_bytes()).hexdigest(),
                   source_sha256={r['file']: r['sha256'] for r in registry['products']}, products=details,
                   policy='Six supplementary lists; exact primary identities only. Dark-nebula coordinate extraction excludes narrative aliases; Great Rift has no centre.')
    destination.mkdir(parents=True)
    for name, data in products.items(): (destination/name).write_bytes(data)
    (destination/'conversion_receipt_v1.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


def load_converted(directory, registry_path):
    directory, registry_path = map(Path, (directory, registry_path))
    receipt_path = directory/'conversion_receipt_v1.json'
    receipt = json.loads(receipt_path.read_text()); registry = json.loads(registry_path.read_text())
    if receipt['source_registry_sha256'] != hashlib.sha256(registry_path.read_bytes()).hexdigest():
        raise ValueError('Supplementary CSV registry mismatch.')
    if receipt['source_sha256'] != {r['file']: r['sha256'] for r in registry['products']}:
        raise ValueError('Supplementary source hashes differ.')
    products = {r['file']: r for r in receipt['products']}
    expected = {name+'_list_v1.csv' for name in COUNTS} | {'observing_memberships_v1.csv'}
    if set(products) != expected: raise ValueError('Incomplete supplementary CSV set.')
    for name, product in products.items():
        data = (directory/name).read_bytes()
        if len(data) != product['bytes'] or hashlib.sha256(data).hexdigest() != product['sha256']:
            raise ValueError('Supplementary CSV checksum mismatch: '+name)
    with (directory/'observing_memberships_v1.csv').open(newline='', encoding='utf-8') as stream:
        records = [dict(catalogue=r['catalogue'], designation=r['designation'],
                        identifiers=json.loads(r['identifiers_json']), source_file=r['source_file'])
                   for r in csv.DictReader(stream)]
    if ({name: sum(r['catalogue'] == name for r in records) for name in COUNTS} != COUNTS or
            any(r['catalogue'] not in COUNTS or r['source_file'] not in receipt['source_sha256'] or
                r['identifiers'] != [r['designation']] or not r['designation'].strip() for r in records)):
        raise ValueError('Invalid supplementary identities or counts.')
    receipt['conversion_receipt_sha256'] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    return records, receipt
