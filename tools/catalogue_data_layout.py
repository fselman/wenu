"""Offline working-data layout, path resolution and provenance publication.

Scientific catalogues, observing selections and accepted curation have separate
owners. Legacy flat conversions remain readable; new publication is per list.
"""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'src/wenu/data'
OBSERVING = DATA/'observing_lists'
CURATED = DATA/'curated_catalogs/open_clusters'
PREFIXES = [('herschel400_south','herschel_400_south'),('herschel400','herschel_400'),
 ('herschel2','herschel_ii'),('rasc_finest','rasc_finest_ngc'),('sac_best','sac_best_ngc'),
 ('al_planetaries_alternates','al_planetary_nebulae'),('al_planetaries_south','al_planetary_nebulae'),
 ('al_planetaries','al_planetary_nebulae'),('al_doubles','al_double_stars'),('al_multiples','al_multiple_stars'),
 ('al_dark_','al_dark_nebulae')]


def owner(directory, filename):
    directory=Path(directory)
    if filename.startswith('barnard'): return directory.parent/'catalogs/barnard'
    if filename.startswith('abell'): return directory.parent/'catalogs/abell_planetary_nebulae'
    for prefix,name in PREFIXES:
        if filename.startswith(prefix): return directory/name
    for name in ['messier','caldwell','sac_urban','sac_beyond_ngc','sac_red_stars','sac_asterisms',
                 'al_open_clusters','al_globular_clusters','al_carbon_stars','al_dark_nebulae']:
        if filename.startswith(name): return directory/name
    raise ValueError('Unknown observing-list file owner: '+filename)


def data_file(directory, filename, batch='original'):
    """Resolve immutable legacy names without rewriting receipt contents."""
    directory=Path(directory)
    if Path(filename).name!=filename: raise ValueError('Unsafe data filename.')
    if (directory/filename).is_file(): return directory/filename
    if filename=='conversion_receipt_v1.json': return directory/f'conversion_receipt_{batch}_v1.json'
    if filename=='observing_memberships_v1.csv': return directory/f'observing_memberships_{batch}_v1.csv'
    return owner(directory,filename)/filename


def canonical_file(directory, filename, batch='original'):
    if filename in ('conversion_receipt_v1.json','observing_memberships_v1.csv'):
        return Path(directory)/(filename.replace('_v1',f'_{batch}_v1'))
    return owner(directory,filename)/filename


def check_targets(files):
    """Validate every collision before copying any byte; identical files coalesce."""
    seen={}
    for source,target in files:
        data=Path(source).read_bytes();digest=hashlib.sha256(data).hexdigest()
        if target in seen and seen[target]!=digest: raise ValueError('Conflicting data products: '+str(target))
        if target.is_symlink() or (target.exists() and (not target.is_file() or target.read_bytes()!=data)):
            raise FileExistsError('Existing different product refused: '+str(target))
        seen[target]=digest


def copy_verified(files):
    check_targets(files)
    for source,target in files:
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            with target.open('xb') as stream: stream.write(Path(source).read_bytes())
        if target.read_bytes()!=Path(source).read_bytes(): raise ValueError('Copy verification failed: '+str(target))


def provenance(directory, registry_path, batch, conversion=None):
    registry=json.loads(Path(registry_path).read_text())
    grouped={}
    for product in registry['products']:
        grouped.setdefault(owner(directory,product['file']),[]).append(product)
    for folder,records in grouped.items():
        folder.mkdir(parents=True,exist_ok=True)
        record=dict(schema_version=1,source_registry=Path(registry_path).name,
            source_registry_sha256=hashlib.sha256(Path(registry_path).read_bytes()).hexdigest(),
            registry_metadata={k:v for k,v in registry.items() if k not in ('products','catalogues')},
            source_products=records,
            source_descriptions=[c for c in registry.get('catalogues',[]) if any(p['file'] in c['files'] for p in records)])
        if conversion is not None:
            record['converted_products']=[p for p in conversion['products']
                if p['file']!='observing_memberships_v1.csv' and owner(directory,p['file'])==folder]
        path=folder/f'provenance_{batch}_v1.json'
        # Source/conversion receipts remain immutable; this descriptive index
        # may acquire CSV evidence after conversion, without changing those receipts.
        path.write_text(json.dumps(record,indent=2)+'\n')
        readme=folder/'README.md'
        if not readme.exists():
            kind='Scientific source catalogue' if folder.parent.name=='catalogs' else 'Observing selection'
            readme.write_text(f'# {folder.name.replace("_"," ").title()}\n\n{kind}. Original versioned source files and converted CSVs stay together.\nSee provenance_{batch}_v1.json for publishers, acquisition evidence and hashes.\nSource inclusion does not establish a new redistribution licence.\n')


def publish_conversion(flat_directory, directory, registry_path, batch):
    directory=Path(directory)
    receipt_path=canonical_file(directory,'conversion_receipt_v1.json',batch)
    if receipt_path.exists(): raise FileExistsError('Conversion already published; choose a new version.')
    flat_directory=Path(flat_directory)
    receipt=json.loads((flat_directory/'conversion_receipt_v1.json').read_text())
    files=[(flat_directory/p['file'],canonical_file(directory,p['file'],batch)) for p in receipt['products']]
    files.append((flat_directory/'conversion_receipt_v1.json',receipt_path))
    copy_verified(files)
    provenance(directory,registry_path,batch,receipt)
    return receipt
