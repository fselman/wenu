# resouces.py
from importlib.resources import files

_CONSTELLATION_LINE_FILES = {
    "western": (
        "wenu.data.constellations.western",
        "const_aug.fab",
    ),
    "mapuche": (
        "wenu.data.constellations.mapuche",
        "mapuche.fab",
    ),
}


def catalog_path(name):
    """
    Return the path to a built-in star catalogue.
    """
    name = name.lower()

    if name == "hipparcos":
        return files(
            "wenu.data.catalogs.hipparcos"
        ) / "hip_main.dat"

    raise ValueError(
        f"Unknown catalogue: {name}"
    )


def constellation_lines_path(system="western"):
    """
    Return the packaged .fab file for a constellation-line system.
    """

    try:
        package, filename = _CONSTELLATION_LINE_FILES[system]
    except KeyError as error:
        available = ", ".join(
            sorted(_CONSTELLATION_LINE_FILES)
        )

        raise ValueError(
            f"Unknown constellation-line system: {system!r}. "
            f"Available systems: {available}."
        ) from error

    resource = files(package) / filename

    if not resource.is_file():
        raise FileNotFoundError(
            f"Constellation-line resource not found: {resource}"
        )

    return resource


def boundary_path(name):
    """
    Return the path to a built-in boundary catalogue.
    """
    name = name.lower()

    if name == "iau":
        return files(
            "wenu.data.constellations.iau"
        ) / "bound_18.dat"

    raise ValueError(
        f"Unknown boundary set: {name}"
    )

def nonstellar_catalog_path(name, *, curated=True):
    """Prefer an accepted curated bundle; preserve explicit scientific access."""
    if curated:
        bundle = curated_catalogue_bundle(str(name).lower())
        if bundle is not None:
            return bundle['catalogue']
    return source_nonstellar_catalog_path(name)


def source_nonstellar_catalog_path(name):
    """Return the original packaged scientific snapshot, without curation."""
    catalogues = {
        "caldwell": (
            "wenu.data.catalogs.caldwell",
            ("caldwell_openngc.ecsv",),
        ),
        "messier": (
            "wenu.data.catalogs.messier",
            (
                "messier_heasarc.ecsv",
                "heasarc_messier.ecsv",
                "messier.ecsv",
            ),
        ),
        "galaxies": (
            "wenu.data.catalogs.galaxies",
            ("galaxies_openngc.ecsv",),
        ),
        "open_clusters": (
            "wenu.data.catalogs.open_clusters",
            ("open_clusters_dias_heasarc.ecsv",),
        ),
        "globular_clusters": (
            "wenu.data.catalogs.globular_clusters",
            ("globular_clusters_harris_heasarc.ecsv",),
        ),
        "supernova_remnants": (
            "wenu.data.catalogs.supernova_remnants",
            ("supernova_remnants_green_2024.ecsv",),
        ),
        "planetary_nebulae": (
            "wenu.data.catalogs.planetary_nebulae",
            ("planetary_nebulae_acker_heasarc.ecsv",),
        ),
    }
    key = str(name).lower()
    try:
        package_name, preferred = catalogues[key]
    except KeyError as error:
        available = ", ".join(sorted(catalogues))
        raise ValueError(
            f"Unknown non-stellar catalogue: {name!r}. "
            f"Available catalogues: {available}."
        ) from error

    package = files(package_name)
    for filename in preferred:
        resource = package / filename
        if resource.is_file():
            return resource

    available = tuple(
        resource
        for resource in package.iterdir()
        if resource.name.lower().endswith(".ecsv")
    )
    if len(available) == 1:
        return available[0]
    raise FileNotFoundError(
        f"Expected one ECSV catalogue in {package_name}."
    )

def milky_way_isophotes_path():
    """Return the packaged D3-Celestial Milky Way GeoJSON snapshot."""
    resource = (
        files("wenu.data.isophotes.milky_way")
        / "milky_way_d3.json"
    )
    if not resource.is_file():
        raise FileNotFoundError(
            "Milky Way isophote resource not found. Run "
            "tools/query_milky_way_isophotes_d3.py."
        )
    return resource


def milky_way_isophote_path(level):
    """Return one packaged single-level Milky Way GeoJSON snapshot."""
    normalized = str(level).strip().lower()
    if normalized not in {"ol1", "ol2", "ol3", "ol4", "ol5"}:
        raise ValueError("Milky Way isophote level must be ol1 through ol5.")
    resource = (
        files("wenu.data.isophotes.milky_way")
        / f"milky_way_{normalized}.geojson"
    )
    if not resource.is_file():
        raise FileNotFoundError(
            f"Milky Way {normalized} resource not found. Run "
            "tools/query_milky_way_isophotes_d3.py."
        )
    return resource


def magellanic_cloud_isophotes_path(cloud):
    """Return one packaged Gaia-derived Magellanic Cloud snapshot."""
    cloud = str(cloud).lower()
    if cloud not in ("lmc", "smc"):
        raise ValueError(
            f"Unknown Magellanic Cloud: {cloud!r}. "
            "Available clouds: lmc, smc."
        )
    resource = (
        files("wenu.data.isophotes.magellanic_clouds")
        / f"{cloud}_gaia_dr3.json"
    )
    if not resource.is_file():
        raise FileNotFoundError(
            f"{cloud.upper()} isophote resource not found. Run "
            "tools/query_magellanic_clouds_gaia.py."
        )
    return resource


def star_designations_manifest_path():
    """Return the offline Wikidata designation manifest (not astrometry)."""
    return (
        files("wenu.data") / "catalogs" / "star_designations" / "manifest.json"
    )


def _curated_filename(name):
    import re
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or name in {'.', '..'}:
        raise ValueError('Invalid curated product filename.')
    return name


def _curated_products(records):
    """Read both established summary encodings without rewriting receipts."""
    import re
    if not isinstance(records, dict):
        raise ValueError('Invalid curated product records.')
    products = {}
    for key, record in records.items():
        name = record['file'] if isinstance(record, dict) else key
        digest = record['sha256'] if isinstance(record, dict) else record
        _curated_filename(name)
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Invalid curated product digest.')
        if name in products and products[name] != digest:
            raise ValueError('Conflicting curated product digest.')
        products[name] = digest
    return products


def _verify_curated_products(directory, products):
    import hashlib
    from pathlib import Path
    for name, expected in _curated_products(products).items():
        resource = directory / name
        if isinstance(resource, Path) and resource.is_symlink():
            raise ValueError('Curated products must be regular files: ' + name)
        if not resource.is_file() or hashlib.sha256(resource.read_bytes()).hexdigest() != expected:
            raise ValueError('Curated product checksum mismatch: ' + name)


def build_curated_catalogue_manifest(root):
    """Verify active working bundles and describe portable installation bytes.

    This is resource/provenance admission only; it does not interpret tables,
    select objects, download resources or change scientific catalogue bytes.
    """
    import hashlib
    import json
    from pathlib import Path
    root = Path(root)
    index = root / 'manifest.json'
    if index.is_file():
        data = json.loads(index.read_text())
        _validate_curated_manifest(data)
        for domain, record in data['catalogues'].items():
            _verify_curated_products(root / domain, record['products'])
        return data
    catalogues = {}
    if root.is_dir():
        for directory in sorted(root.iterdir()):
            if not directory.is_dir():
                continue
            _curated_filename(directory.name)
            selectors = []
            for path in directory.glob('*.ecsv'):
                if path.is_symlink():
                    selectors.append((path, str(path.readlink())))
                elif path.stat().st_size <= 512:
                    # Git checkouts with core.symlinks=false store a link's
                    # relative target as a plain one-line file.
                    target = path.read_text().strip()
                    if '\n' not in target and target.endswith('.ecsv'):
                        _curated_filename(target)
                        selectors.append((path, target))
            if len(selectors) > 1:
                raise ValueError('More than one active curated selector: ' + directory.name)
            if not selectors:
                continue
            selector, target = selectors[0]
            _curated_filename(target)
            catalogue = directory / target
            if catalogue.is_symlink() or not catalogue.is_file():
                raise ValueError('Active curated catalogue must be a regular file.')
            digest = hashlib.sha256(catalogue.read_bytes()).hexdigest()
            summaries = []
            for path in directory.glob('*_summary.json'):
                data = json.loads(path.read_text())
                products = _curated_products(data.get('products', {}))
                if products.get(catalogue.name) == digest:
                    summaries.append((path, products))
            if len(summaries) != 1:
                raise ValueError('Active curated catalogue requires one matching completion summary: ' + catalogue.name)
            summary, products = summaries[0]
            products[summary.name] = hashlib.sha256(summary.read_bytes()).hexdigest()
            criteria = []
            for path in sorted(directory.glob('*.json')):
                data = json.loads(path.read_text())
                if not isinstance(data, dict) or data.get('document_kind') != 'wenu-catalogue-selection-criteria':
                    continue
                binding = data.get('catalogue')
                if not isinstance(binding, dict):
                    raise ValueError('Invalid criteria catalogue binding.')
                if binding.get('file') != catalogue.name:
                    continue
                if binding != dict(file=catalogue.name, sha256=digest):
                    raise ValueError('Criteria catalogue checksum mismatch: ' + path.name)
                if type(data.get('schema_version')) is not int or data['schema_version'] != 1:
                    raise ValueError('Unsupported criteria schema.')
                evidence = _curated_products(data['products'])
                for page in data['pages']:
                    if evidence.get(page['file']) != page['sha256']:
                        raise ValueError('Criteria PDF is not bound to its product record.')
                for name, expected in evidence.items():
                    if name in products and products[name] != expected:
                        raise ValueError('Conflicting curated evidence: ' + name)
                    products[name] = expected
                products[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
                criteria.append(path.name)
            _verify_curated_products(directory, products)
            catalogues[directory.name] = dict(catalogue=catalogue.name,
                selector=selector.name, summary=summary.name, products=products, criteria=criteria)
    return dict(schema_version=1, document_kind='wenu-curated-catalogues', catalogues=catalogues)


def _validate_curated_manifest(data):
    if (not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1 or
            data.get('document_kind') != 'wenu-curated-catalogues' or not isinstance(data.get('catalogues'), dict)):
        raise ValueError('Unsupported curated catalogue manifest.')
    for domain, record in data['catalogues'].items():
        _curated_filename(domain)
        if not isinstance(record, dict) or set(record) != {'catalogue', 'selector', 'summary', 'products', 'criteria'}:
            raise ValueError('Invalid curated catalogue record.')
        products = _curated_products(record['products'])
        for name in (record['catalogue'], record['summary'], record['selector']):
            _curated_filename(name)
        if not isinstance(record['criteria'], list):
            raise ValueError('Invalid curated criteria records.')
        for name in (record['catalogue'], record['summary'], *record['criteria']):
            _curated_filename(name)
            if name not in products:
                raise ValueError('Missing curated product binding: ' + name)


def curated_catalogue_bundle(name):
    """Return verified installed catalogue and associated evidence resources.

    Wheels use the portable manifest; a source/editable checkout may use its
    existing relative selector links. Missing domains retain scientific defaults;
    a present but invalid accepted bundle fails rather than silently falling back.
    """
    import json
    name = _curated_filename(name)
    root = files('wenu.data') / 'curated_catalogs'
    index = root / 'manifest.json'
    if index.is_file():
        data = json.loads(index.read_text())
        _validate_curated_manifest(data)
    else:
        from pathlib import Path
        data = build_curated_catalogue_manifest(Path(str(root)))
    record = data['catalogues'].get(name)
    if record is None:
        return None
    directory = root / name
    _verify_curated_products(directory, record['products'])
    return dict(catalogue=directory / record['catalogue'],
        summary=directory / record['summary'],
        criteria=tuple(directory / p for p in record['criteria']),
        products={p: directory / p for p in record['products']})



# Immutable installed presets. Layout, atlas presentation and ordinary chart
# configuration are distinct protocols; a name cannot cross those boundaries.
_CONFIGURATION_PRESETS = {
    'chart': {'atlas-v6': 'chart_atlas_v6.toml',
              'scorpius-v1': 'sco_installed_catalogues_v1.toml',
              'scorpius-v2': 'sco_installed_catalogues_v2.toml'},
    'atlas-style': {'atlas-v6': 'atlas_style_v6.toml'},
    'atlas-layout': {'b4-landscape-five-band': 'atlas_layout_b4_landscape_v1.json',
                     'b4-portrait': 'atlas_layout_b4_portrait_v3.json'},
    'atlas-index': {'b4-landscape': 'atlas_index_style_v2.toml',
                    'b4-portrait': 'atlas_index_style_v3.toml'},
}


def configuration_preset_names(kind):
    """List installed preset names for one independently owned protocol."""
    if kind not in _CONFIGURATION_PRESETS:
        raise ValueError('Unknown configuration preset kind: ' + str(kind))
    return tuple(_CONFIGURATION_PRESETS[kind])


def configuration_preset_path(name, *, kind):
    """Return an installed preset without repository-relative lookup."""
    names = configuration_preset_names(kind)
    if name not in names:
        raise ValueError(f'Unknown {kind} preset {name!r}; choose ' + ', '.join(names))
    path = files('wenu.configuration') / 'presets' / _CONFIGURATION_PRESETS[kind][name]
    if not path.is_file():
        raise FileNotFoundError('Installed configuration preset is missing: ' + str(path))
    return path


def configuration_input_path(value, *, kind):
    """Resolve a registered name or retain an explicit filesystem input."""
    from pathlib import Path
    name = str(value)
    if name in configuration_preset_names(kind):
        return configuration_preset_path(name, kind=kind)
    if any(name in values for values in _CONFIGURATION_PRESETS.values()):
        raise ValueError(f'Preset {name!r} is not a {kind} input.')
    return Path(value).expanduser()
