"""Explicit synthetic catalogue metadata for constructed stellar owner fixtures."""
from hashlib import sha256

from wenu.stellar_catalogue import StellarCatalogueMetadata, ingest_stellar_catalogue


def native_table(table, *, epoch=1991.25):
    table = table.copy(deep=True)
    if 'ra_degrees' not in table:
        table['ra_degrees'] = table['ra_hours'] * 15
    if 'epoch_year' not in table:
        table['epoch_year'] = epoch
    metadata = StellarCatalogueMetadata.from_record({
        'schema': 'wenu-stellar-catalogue/1', 'catalogue': 'hipparcos',
        'edition': 'synthetic-test/1', 'frame': 'icrs', 'origin': 'solar-system-barycenter',
        'epoch': {'value': epoch, 'format': 'jyear', 'scale': 'tt'},
        'units': {'ra_degrees': 'deg', 'dec_degrees': 'deg', 'epoch_year': 'Julian year',
                  'ra_hours': 'hourangle', 'magnitude': 'mag', 'parallax_mas': 'mas',
                  'ra_mas_per_year': 'mas/yr', 'dec_mas_per_year': 'mas/yr'},
        'provenance': ['Constructed synthetic stellar table'],
        'source_sha256': sha256(b'constructed test input').hexdigest(),
        'source_metadata': {'kind': 'constructed; not real catalogue evidence'},
    })
    return ingest_stellar_catalogue(table, metadata).table
