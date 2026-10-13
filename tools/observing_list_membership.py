"""Read hash-bound observing memberships offline; never merge physical objects."""

import csv
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np
from astropy.table import MaskedColumn, Table

from compare_open_clusters import identifier_key


LISTS = ['messier', 'caldwell', 'herschel400', 'herschel2', 'rasc_finest_ngc',
         'sac_best_ngc', 'al_open_clusters', 'al_globular_clusters',
         'herschel400_south']
SOURCE_FILES = ['messier_list_v1.csv','caldwell_list_v1.csv','sac_best_list_v1.csv',
                'herschel400_list_v1.pdf','herschel2_list_v1.pdf','rasc_finest_list_v1.pdf',
                'al_open_clusters_list_v1.xlsx','al_globular_clusters_list_v1.xlsx',
                'herschel400_south_list_v1.xls']
SOURCE_COUNTS = dict(messier=110,caldwell=109,herschel400=400,herschel2=400,
    rasc_finest_ngc=112,sac_best_ngc=111,al_open_clusters=214,
    al_globular_clusters=190,herschel400_south=150)


def key(value):
    """Expand explicit catalogue abbreviations, preserving distinct namespaces."""
    value = str(value).strip().replace('_', ' ')
    prefixes = {'berk':'Berkeley', 'ber':'Berkeley', 'ru':'Ruprecht',
                'tr':'Trumpler', 'cr':'Collinder', 'mel':'Melotte', 'n':'NGC',
                'b':'Barnard', 'caldwell':'C'}
    match = re.fullmatch(r'([A-Za-z]+)\s*0*(\d+)([a-z]?)',value,re.I)
    if match:
        prefix = prefixes.get(match[1].casefold(),match[1])
        value = prefix+' '+str(int(match[2]))+match[3].casefold()
    return identifier_key(value)


def xlsx_rows(path):
    """Read stored XLSX cells with the standard library, without executing Excel."""
    ns = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with ZipFile(path) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [''.join(x.itertext()) for x in ET.fromstring(
                archive.read('xl/sharedStrings.xml')).findall('s:si',ns)]
        sheets = sorted(n for n in archive.namelist()
                        if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n))
        result = []
        for sheet in sheets:
            rows = []
            for row in ET.fromstring(archive.read(sheet)).findall('.//s:row',ns):
                while len(rows)<int(row.attrib['r'])-1:
                    rows.append([])
                cells = {}
                for cell in row.findall('s:c',ns):
                    letters = re.match(r'[A-Z]+',cell.attrib['r'])[0]
                    column = 0
                    for letter in letters:
                        column = column*26+ord(letter)-64
                    stored = cell.find('s:v',ns)
                    value = '' if stored is None else stored.text or ''
                    if cell.attrib.get('t')=='s':
                        value = shared[int(value)]
                    elif cell.attrib.get('t')=='inlineStr':
                        value = ''.join(cell.find('s:is',ns).itertext())
                    cells[column-1] = value
                if cells:
                    rows.append([cells.get(i,'') for i in range(max(cells)+1)])
                else:
                    rows.append([])
            result.append(rows)
        return result


def excel_rows(path):
    if path.suffix=='.xlsx':
        return xlsx_rows(path)
    try:
        import xlrd
    except ImportError as exc:
        raise RuntimeError('Legacy XLS observing supplements require xlrd>=2,<3; '
                           "install with python -m pip install 'xlrd>=2,<3'.") from exc
    workbook = xlrd.open_workbook(path)
    return [[sheet.row_values(i) for i in range(sheet.nrows)] for sheet in workbook.sheets()]


def records_from_sources(directory, manifest):
    """Decode only membership identities; preserve source parameter authority."""
    directory = Path(directory)
    products = {r['file']:r for r in manifest['products'] if r['file'] in SOURCE_FILES}
    if set(products)!=set(SOURCE_FILES):raise ValueError('Registry lacks a cluster-list source.')
    for name,product in products.items():
        if Path(name).name!=name:
            raise ValueError('Invalid observing source filename.')
        data = (directory/name).read_bytes()
        if len(data)!=product['bytes'] or hashlib.sha256(data).hexdigest()!=product['sha256']:
            raise ValueError('Observing source checksum mismatch: '+name)
    records = []
    def add(catalogue, designation, identifiers, source_file):
        identifiers = sorted({str(v).strip() for v in identifiers if str(v).strip()})
        records.append(dict(catalogue=catalogue,designation=str(designation),
                            identifiers=identifiers,source_file=source_file))
    for catalogue in ('messier','caldwell','sac_best_ngc'):
        name = {'messier':'messier_list_v1.csv','caldwell':'caldwell_list_v1.csv',
                'sac_best_ngc':'sac_best_list_v1.csv'}[catalogue]
        for row in csv.DictReader((directory/name).open(encoding='utf-8')):
            if catalogue=='messier':
                # Use established observing crosswalk labels, not the historical
                # AL table's approximate M24/M45 NGC associations.
                designation = 'M '+row['Messier_number']
            elif catalogue=='caldwell':
                designation = 'C '+row['Caldwell_number']
            else:
                designation = 'NGC '+row['NGC_number']
            add(catalogue,designation,[designation],name)
    from pypdf import PdfReader
    for catalogue,name in [('herschel400','herschel400_list_v1.pdf'),
                           ('herschel2','herschel2_list_v1.pdf'),
                           ('rasc_finest_ngc','rasc_finest_list_v1.pdf')]:
        text = '\n'.join(page.extract_text() or '' for page in PdfReader(directory/name).pages)
        if catalogue=='herschel400':
            for n in re.findall(r'^\s*(\d+)\s+\d+\s+\d',text,re.M):
                add(catalogue,'NGC '+n,['NGC '+n],name)
        elif catalogue=='herschel2':
            for n in re.findall(r'^\d+h\s+\d+m.*?"\s+(\d+)\s+[A-Za-z]{3}\s*$',text,re.M):
                add(catalogue,'NGC '+n,['NGC '+n],name)
        else:
            for line in text.splitlines():
                match = re.match(r'^\s*(\d+[ab]?)\s+((?:NGC|IC)\s+\d+)\s+(.*)',line)
                if not match:
                    continue
                # Alternate IDs and explicit compound components precede RA.
                identity_text = line.split(re.search(r'\d+h\d+m',line)[0])[0]
                identities = [match[2]]+re.findall(r'Collinder\s+\d+',identity_text)
                # Explicit companions; uncertain/mislabeled references in the
                # narrative column (e.g. NGC4437) never become identity aliases.
                companions = {'17':['NGC 869'],'26':['NGC 1975','NGC 1977'],
                              '74':['NGC 4039'],'78':['NGC 4435']}
                identities.extend(companions.get(match[1],[]))
                add(catalogue,'FNGC '+match[1],identities,name)
    excel = [
        ('al_open_clusters','al_open_clusters_list_v1.xlsx'),
        ('al_globular_clusters','al_globular_clusters_list_v1.xlsx'),
        ('herschel400_south','herschel400_south_list_v1.xls')]
    for catalogue,name in excel:
        for rows in excel_rows(directory/name):
            for row in rows:
                row = [str(v).strip() if v is not None else '' for v in row]
                if catalogue=='al_open_clusters':
                    if len(row)<5 or not re.match(r'^\d',row[2]): continue
                    identifiers = [row[0]]
                    if row[1] and re.fullmatch(r'[A-Za-z][A-Za-z -]*\s*\d+[a-z]?',row[1]): identifiers.append(row[1])
                elif catalogue=='al_globular_clusters':
                    if len(row)<5 or not row[0].replace('.0','').isdigit(): continue
                    # Extragalactic Gn names are scoped to the named host.
                    identifiers = [row[1]+' '+row[2] if row[2].startswith('In ') else row[1]]
                elif catalogue=='herschel400_south':
                    if len(row)<3 or not row[0].replace('.0','').isdigit(): continue
                    identifiers = [row[1]]
                add(catalogue,identifiers[0],identifiers,name)
    observed = {name:sum(r['catalogue']==name for r in records) for name in LISTS}
    if observed!=SOURCE_COUNTS:
        raise ValueError('Observing source parse counts differ: '+str(observed))
    return records


def annotate(table, records=None, reference_edges=None):
    """Add exact-ID membership flags and a separate per-source-record ledger."""
    if records is None:
        for catalogue in LISTS+['best_ngc']:
            table['in_'+catalogue] = MaskedColumn(np.zeros(len(table),bool),mask=True)
        return Table(names=['catalogue','designation','source_file','status','wenu_ids'],
                     dtype=['U1']*5),dict(status='explicitly_skipped')
    primary,aliases = {},{}
    for i,row in enumerate(table):
        for column in ('dias_id','hunt_name'):
            if column in table.colnames and not np.ma.is_masked(row[column]):
                primary.setdefault(key(row[column]),set()).add(i)
        for name in str(row['Other_ids']).split('|'):
            if name.strip():aliases.setdefault(key(name),set()).add(i)
    review = set()
    edges = []
    for catalogue in LISTS:
        values = np.zeros(len(table),bool)
        uncertain = set()
        for record in [r for r in records if r['catalogue']==catalogue]:
            matched,ambiguous = set(),set()
            for name in record['identifiers']:
                if catalogue in ('messier','caldwell'):
                    column = 'Messier_id' if catalogue=='messier' else 'Caldwell_id'
                    direct = {i for i,row in enumerate(table) if key(name) in
                              {key(v) for v in str(row[column]).split('|') if v}}
                    claims = direct  # compound observing references may tag multiple rows
                else:
                    direct = primary.get(key(name),set())
                    claims = direct or aliases.get(key(name),set())
                if len(claims)>1 and catalogue not in ('messier','caldwell'):
                    ambiguous.update(claims)
                else:
                    matched.update(claims)
                # Preserve competing alias evidence even when a primary wins.
                if direct and catalogue not in ('messier','caldwell'):
                    ambiguous.update(aliases.get(key(name),set())-direct)
            if catalogue in ('messier','caldwell') and reference_edges is not None:
                for edge in reference_edges:
                    if (str(edge['catalogue']).casefold()!=catalogue or
                            key(edge['designation'])!=key(record['designation'])):continue
                    names = (str(edge['candidate_identifiers']) if str(edge['status'])=='ambiguous' else '')
                    names += '|'+str(edge['other_alias_rows'])
                    for name in names.split('|'):
                        ambiguous.update(primary.get(key(name),set()))
            for i in matched:values[i]=True
            uncertain.update(ambiguous)
            review.update(ambiguous)
            edges.append(dict(catalogue=catalogue,designation=record['designation'],
                source_file=record['source_file'],status='review' if ambiguous else
                'matched' if matched else 'unmatched',
                wenu_ids='|'.join(sorted(str(table['wenu_id'][i]) for i in matched)),
                review_wenu_ids='|'.join(sorted(str(table['wenu_id'][i]) for i in ambiguous))))
        table['in_'+catalogue] = MaskedColumn(values,mask=[i in uncertain and not values[i] for i in range(len(table))])
    table['in_best_ngc'] = table['in_sac_best_ngc'].copy()
    table['observing_membership_review'] = [i in review for i in range(len(table))]
    summary = dict(status='verified_sources',criterion='Explicit identifiers/aliases only; false means no resolved list identifier, masked means an unresolved claim.',
        best_ngc_alias='sac_best_ngc',counts={catalogue:dict(
            source_records=sum(r['catalogue']==catalogue for r in records),
            member_rows=int(np.count_nonzero(table['in_'+catalogue].filled(False))),
            unresolved_rows=int(np.count_nonzero(table['in_'+catalogue].mask))) for catalogue in LISTS})
    return Table(rows=edges),summary


def load_converted(directory, registry_path):
    """Use only a complete, hash-bound first-pass CSV conversion."""
    directory,registry_path = Path(directory),Path(registry_path)
    receipt_path = directory/'conversion_receipt_v1.json'
    if not receipt_path.exists():
        raise FileNotFoundError('First-pass CSV receipt missing; run tools/convert_observing_catalogues.py before compilation: '+str(receipt_path))
    receipt = json.loads(receipt_path.read_text())
    registry = json.loads(registry_path.read_text())
    if receipt['source_registry_sha256']!=hashlib.sha256(registry_path.read_bytes()).hexdigest():
        raise ValueError('CSV conversion uses a different observing source registry.')
    if receipt['source_sha256']!={r['file']:r['sha256'] for r in registry['products'] if r['file'] in SOURCE_FILES}:
        raise ValueError('CSV conversion source hashes differ from registry.')
    products = {r['file']:r for r in receipt['products']}
    for name,record in products.items():
        if Path(name).name!=name:raise ValueError('Invalid converted filename.')
        data = (directory/name).read_bytes()
        if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:
            raise ValueError('Converted CSV checksum mismatch: '+name)
    records = []
    with (directory/'observing_memberships_v1.csv').open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            records.append(dict(catalogue=row['catalogue'],designation=row['designation'],
                source_file=row['source_file'],identifiers=json.loads(row['identifiers_json'])))
    if ({name:sum(r['catalogue']==name for r in records) for name in LISTS}!=SOURCE_COUNTS
            or any(r['catalogue'] not in LISTS or r['source_file'] not in SOURCE_FILES or
                   not r['identifiers'] or not all(isinstance(v,str) and v.strip() for v in r['identifiers'])
                   for r in records)):
        raise ValueError('Converted memberships have invalid identities or list counts.')
    receipt['conversion_receipt_sha256'] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    return records,receipt
