"""Validated, data-only stellar catalogue ingestion and metadata preservation.

Source-specific facts belong in catalogue metadata resources, never in geometry
or kernel consumers. The current native consumer admits ICRS degree directions
with one explicitly declared reference epoch; other semantics are refused.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
from math import isfinite
from pathlib import Path

import numpy as np
from astropy.time import Time

from wenu.coordinates import icrs_catalogue_spec
from wenu_kernel.records import ReferenceSpec, TimePoint

METADATA_KEY = 'wenu_stellar_catalogue'


@dataclass(frozen=True)
class StellarCatalogueMetadata:
    """Immutable mirror of a preserved Wenu catalogue metadata document."""

    document_json: str

    def __post_init__(self):
        data = self.to_record()
        required = {'schema', 'catalogue', 'edition', 'frame', 'origin', 'epoch',
                    'units', 'provenance', 'source_sha256', 'source_metadata'}
        if not isinstance(data, dict) or not required <= data.keys():
            raise ValueError('Missing required stellar catalogue metadata.')
        if data['schema'] != 'wenu-stellar-catalogue/1':
            raise ValueError('Unsupported stellar catalogue metadata schema.')
        for key in ('catalogue', 'edition', 'frame', 'origin'):
            if not isinstance(data[key], str) or not data[key].strip():
                raise ValueError(f'Invalid catalogue metadata: {key}.')
        epoch = data['epoch']
        if (not isinstance(epoch, dict) or set(epoch) != {'value', 'format', 'scale'}
                or type(epoch['value']) not in (int, float) or not isfinite(epoch['value'])
                or epoch['format'] not in ('jyear', 'jd')
                or epoch['scale'] not in Time.SCALES):
            raise ValueError('Invalid or incomplete catalogue reference epoch.')
        if (data['frame'], data['origin']) != ('icrs', 'solar-system-barycenter'):
            raise ValueError('Unsupported native catalogue frame/origin; a transform is required.')
        units = data['units']
        if not isinstance(units, dict) or any(units.get(k) != 'deg' for k in ('ra_degrees', 'dec_degrees')):
            raise ValueError('Native catalogue requires declared angular units in degrees.')
        if (not isinstance(data['provenance'], list) or not data['provenance']
                or any(not isinstance(p, str) or not p.strip() for p in data['provenance'])):
            raise ValueError('Catalogue provenance is required.')
        digest = data['source_sha256']
        if (not isinstance(digest, str) or len(digest) != 64
                or any(c not in '0123456789abcdef' for c in digest)
                or not isinstance(data['source_metadata'], dict)):
            raise ValueError('Catalogue requires source identity and preserved metadata.')
        # Force epoch parsing at admission, before any layer is published.
        time = self.astropy_epoch
        original_jd = data['source_metadata'].get('reference_epoch_jd')
        if original_jd is not None and (type(original_jd) not in (int, float)
                or not isfinite(original_jd) or abs(float(time.jd) - original_jd) > 1e-9):
            raise ValueError('Declared epoch disagrees with preserved source epoch metadata.')

    @classmethod
    def from_record(cls, record):
        return cls(json.dumps(record, sort_keys=True, allow_nan=False, separators=(',', ':')))

    def to_record(self):
        return json.loads(self.document_json)

    @property
    def astropy_epoch(self):
        epoch = self.to_record()['epoch']
        return Time(epoch['value'], format=epoch['format'], scale=epoch['scale'])

    @property
    def source_epoch(self):
        time = self.astropy_epoch
        return TimePoint(float(time.jd1), float(time.jd2), time.scale)

    @property
    def epoch_label(self):
        return f'J{float(self.astropy_epoch.jyear):.12g}'

    @property
    def reference(self):
        data = self.to_record()
        return ReferenceSpec(data['frame'], data['origin'], 'native-catalogue', 'direction', 'rad',
                             'unpropagated source directions; no requested-epoch astrometry')

    def coordinate_spec(self):
        data = self.to_record()
        return icrs_catalogue_spec(f"{data['catalogue']} stellar catalogue", epoch=self.epoch_label,
                                   provenance=tuple(data['provenance']))


@dataclass(frozen=True)
class StellarCatalogue:
    """Standard table plus immutable metadata; legacy layers retain table access."""

    table: object
    metadata: StellarCatalogueMetadata


def packaged_stellar_metadata(name):
    """Read a declared catalogue profile; unknown catalogues have no defaults."""
    if not isinstance(name, str) or not name.isidentifier():
        raise ValueError('Invalid stellar catalogue name.')
    try:
        raw = files('wenu.data.catalogs').joinpath(name).joinpath('metadata.json').read_text()
    except (FileNotFoundError, ModuleNotFoundError) as error:
        raise ValueError(f'No metadata profile for stellar catalogue {name!r}.') from error
    return StellarCatalogueMetadata.from_record(json.loads(raw))


def source_stellar_metadata(name, payload, filename=None, metadata=None):
    """Admit a supplied/adjacent document, or a byte-identical packaged source."""
    if metadata is None and filename is not None:
        sidecar = Path(str(filename) + '.metadata.json')
        if sidecar.is_file():
            metadata = json.loads(sidecar.read_text())
    result = (packaged_stellar_metadata(name) if metadata is None else metadata
              if isinstance(metadata, StellarCatalogueMetadata) else StellarCatalogueMetadata.from_record(metadata))
    if result.to_record()['catalogue'] != name:
        raise ValueError('Catalogue identity disagrees with metadata.')
    if result.to_record()['source_sha256'] != sha256(payload).hexdigest():
        raise ValueError('Source bytes differ from metadata; supply a matching catalogue metadata document.')
    return result


def ingest_stellar_catalogue(table, metadata):
    """Validate and copy into Wenu's standard table, preserving all input columns."""
    if not isinstance(metadata, StellarCatalogueMetadata):
        raise ValueError('Explicit validated catalogue metadata is required.')
    required = {'ra_degrees', 'dec_degrees', 'epoch_year'}
    if not required <= set(table.columns):
        raise ValueError('Stellar table lacks coordinates or reference-epoch metadata.')
    if not table.index.is_unique:
        raise ValueError('Duplicate stellar catalogue identities.')
    epochs = table['epoch_year'].to_numpy(dtype=float)
    units = metadata.to_record()['units']
    canonical_units = dict(epoch_year='Julian year', ra_hours='hourangle', parallax_mas='mas',
                           ra_mas_per_year='mas/yr', dec_mas_per_year='mas/yr', magnitude='mag')
    for column, unit in canonical_units.items():
        if column in table and units.get(column) != unit:
            raise ValueError(f'Missing or unsupported stellar column unit: {column}.')
    if np.any(~np.isfinite(epochs)) or np.any(epochs != float(metadata.astropy_epoch.jyear)):
        raise ValueError('Stellar row epochs disagree with catalogue metadata.')
    lon = table['ra_degrees'].to_numpy(dtype=float)
    lat = table['dec_degrees'].to_numpy(dtype=float)
    if (np.any(np.isinf(lon)) or np.any(np.isinf(lat))
            or np.any((lon[np.isfinite(lon)] < 0) | (lon[np.isfinite(lon)] >= 360))
            or np.any(np.abs(lat[np.isfinite(lat)]) > 90)):
        raise ValueError('Invalid native stellar coordinates.')
    if 'ra_hours' in table and not np.allclose(table['ra_hours'] * 15, lon, equal_nan=True):
        raise ValueError('Inconsistent stellar coordinate encodings.')
    result = table.copy(deep=True)
    result.attrs[METADATA_KEY] = metadata.to_record()
    return StellarCatalogue(result, metadata)


def stellar_table_metadata(table):
    """Require metadata preserved by ingestion; never infer it from object names."""
    if METADATA_KEY not in table.attrs:
        raise ValueError('Stellar catalogue has no validated metadata; ingest it before use.')
    return StellarCatalogueMetadata.from_record(table.attrs[METADATA_KEY])
