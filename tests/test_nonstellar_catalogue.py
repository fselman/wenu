"""Current nonstellar catalogue contracts."""

# Contracts consolidated from test_milestone26_nonstellar.py.
"""Milestone 26 tests for the NonStellar catalogue layer."""

from types import SimpleNamespace

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.table import Table
from astropy.time import Time

from wenu.geometry.spherical import SphericalCurves
from wenu.objects.astronomical_object import AstronomicalObject
from wenu.objects.nonstellar import NonStellar
from wenu.sky.celestial_sphere import CelestialSphere


def test_undeclared_nonstellar_epoch_stays_unknown(catalogue):
    layer = NonStellar(None)
    layer.load(filename=catalogue)
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    for result in (layer.position(), layer.realize(context, None),
                   layer.realize(context, None, labels_only=True)):
        assert result.coordinate_spec.epoch is None
        assert result.coordinate_spec.model == "legacy-unverified-catalogue-encoding"
        assert result.metadata["catalogue_admission"]["frame"] is None
    with pytest.raises(ValueError, match="Incomplete nonstellar metadata"):
        layer.catalogue_metadata.require_complete()


def test_complete_nonstellar_metadata_controls_native_routes(catalogue):
    import hashlib
    from dataclasses import FrozenInstanceError
    table = Table.read(catalogue)
    table.meta = dict(catalog="synthetic", catalog_version="synthetic-v1",
                      documentation_url="https://example.invalid/synthetic",
                      coordinate_frame="ICRS", coordinate_origin="solar-system-barycenter",
                      coordinate_epoch="J2016.0", coordinate_epoch_scale="tt",
                      original_extra={"retained": True})
    for name, unit in (("ra", u.deg), ("dec", u.deg), ("dimension", u.arcmin), ("pa", u.deg)):
        table[name].unit = unit
    table.write(catalogue, overwrite=True)
    layer = NonStellar(None)
    layer.load(filename=catalogue, require_complete_metadata=True)
    metadata = layer.catalogue_metadata
    assert metadata.missing_fields == ()
    assert metadata.require_complete() is metadata
    record = metadata.to_record()
    assert record["source_sha256"] == hashlib.sha256(catalogue.read_bytes()).hexdigest()
    assert record["epoch_scale"] == "tt"
    record["source_metadata"]["original_extra"]["retained"] = False
    assert metadata.to_record()["source_metadata"]["original_extra"]["retained"] is True
    with pytest.raises(FrozenInstanceError):
        metadata.document_json = "{}"
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    for result in (layer.position(), layer.realize(context, None),
                   layer.realize(context, None, labels_only=True)):
        assert result.coordinate_spec.epoch == "J2016.0"
        assert result.coordinate_spec.model is None
        assert result.coordinate_spec.provider == "synthetic"
        assert result.coordinate_spec.provenance == ("https://example.invalid/synthetic",)


@pytest.mark.parametrize(("key", "value"), [
    ("coordinate_frame", "FK5"), ("coordinate_frame", 2000),
    ("coordinate_origin", "observer"), ("coordinate_equinox", "J2000"),
    ("coordinate_epoch", "invalid"), ("coordinate_epoch", "Jnan"),
    ("coordinate_epoch_scale", "not-a-scale"),
])
def test_invalid_declared_nonstellar_metadata_refuses_reload(key, value, catalogue, tmp_path):
    layer = NonStellar(None)
    layer.load(filename=catalogue)
    original = (layer.catalog, layer.source, layer.catalogue_metadata, layer._source_revision)
    table = Table.read(catalogue)
    table.meta[key] = value
    path = tmp_path / "invalid-metadata.ecsv"
    table.write(path)
    with pytest.raises(ValueError):
        layer.load(filename=path)
    assert layer.catalog is original[0] and layer.source == original[1]
    assert layer.catalogue_metadata == original[2] and layer._source_revision == original[3]


def test_strict_metadata_refusal_retains_legacy_catalogue(catalogue):
    layer = NonStellar(None)
    layer.load(filename=catalogue)
    table, metadata = layer.catalog, layer.catalogue_metadata
    with pytest.raises(ValueError, match="Incomplete nonstellar metadata"):
        layer.load(filename=catalogue, require_complete_metadata=True)
    assert layer.catalog is table and layer.catalogue_metadata == metadata


def test_static_epoch_exemption_is_explicit_and_does_not_relax_other_models(catalogue):
    layer = NonStellar(None)
    layer.load(filename=catalogue)
    record = layer.catalogue_metadata
    assert 'epoch' in record.missing_fields
    assert 'epoch_scale' in layer.admission_missing_fields
    assert 'epoch' not in record.missing_fields_for('static-direction')
    assert 'frame' in record.missing_fields_for('static-direction')
    with pytest.raises(ValueError, match='epoch'):
        layer.require_complete_metadata()
    with pytest.raises(ValueError, match='frame'):
        record.require_complete(position_model='static-direction')
    with pytest.raises(ValueError, match='Unsupported catalogue position model'):
        record.require_complete(position_model='unknown')


def test_icrs_j2000_declaration_is_not_a_measurement_epoch(catalogue):
    table = Table.read(catalogue)
    table.meta["coordinate_frame"] = "ICRS/J2000"
    table.write(catalogue, overwrite=True)
    layer = NonStellar(None)
    layer.load(filename=catalogue)
    assert layer.catalogue_metadata.to_record()["frame"] == "icrs"
    assert layer.catalogue_metadata.to_record()["epoch"] is None
    assert layer.position().coordinate_spec.equinox is None
    assert layer.position().coordinate_spec.epoch is None


def test_observed_provider_identity_comes_from_source_metadata(catalogue, observer):
    table = Table.read(catalogue)
    table.meta.update(catalog='synthetic', documentation_url='https://example.invalid/source',
                      source_files={'input': {'url': 'https://example.invalid/input'}})
    table.write(catalogue, overwrite=True)
    layer = NonStellar(observer)
    layer.load(filename=catalogue)
    record = layer.catalogue_metadata.to_record()
    assert record['provenance'] == ['https://example.invalid/input', 'https://example.invalid/source']
    for geometry in (layer.spherical_geometry(observer), layer.spherical_centers(observer)):
        assert geometry.coordinate_spec.provider == 'synthetic'
        assert geometry.coordinate_spec.model == 'legacy-unverified-catalogue-encoding'
        assert geometry.coordinate_spec.instant is not None
        assert geometry.metadata['catalogue_admission'] == record


def test_normalization_converts_declared_angles_and_preserves_source_metadata():
    """Synthetic source: declared units control encoding, not column spelling."""
    from astropy.table import MaskedColumn
    source = Table(meta={"release": "synthetic-v1", "provenance": {"license": "test"}})
    source["name"] = ["A", "B"]
    source["ra"] = [1., 2.] * u.hourangle
    source["ra"].description = "Synthetic right ascension"
    source["dec"] = [-.5, .25] * u.rad
    source["major"] = [120., 180.] * u.arcsec
    source["minor"] = MaskedColumn([60., 90.], mask=[False, True], unit=u.arcsec)
    source["pa"] = [np.pi / 2, np.pi] * u.rad
    source["extra_measurement"] = MaskedColumn([3., 4.], mask=[True, False], unit=u.kpc)
    source["extra_measurement"].description = "Preserved unconsumed source field"
    normalized = NonStellar(None)._normalize(source)
    assert normalized["ra_deg"].tolist() == pytest.approx([15., 30.])
    assert normalized["dec_deg"].tolist() == pytest.approx(np.rad2deg([-.5, .25]))
    assert normalized["major_axis_arcmin"].tolist() == pytest.approx([2., 3.])
    assert normalized["minor_axis_arcmin"][0] == pytest.approx(1.)
    assert np.isnan(normalized["minor_axis_arcmin"][1])
    assert normalized["position_angle_deg"].tolist() == pytest.approx([90., 180.])
    for name, unit in (("ra_deg", u.deg), ("dec_deg", u.deg),
                       ("major_axis_arcmin", u.arcmin), ("minor_axis_arcmin", u.arcmin),
                       ("position_angle_deg", u.deg)):
        assert normalized[name].unit == unit
    assert normalized["ra_deg"].description == source["ra"].description
    assert normalized.meta == source.meta
    assert normalized["extra_measurement"].unit == u.kpc
    assert normalized["extra_measurement"].description == source["extra_measurement"].description
    assert normalized["extra_measurement"].mask.tolist() == [True, False]
    normalized.meta["provenance"]["license"] = "changed"
    normalized["extra_measurement"][1] = 99.
    assert source.meta["provenance"]["license"] == "test"
    assert source["extra_measurement"][1] == 4.
    assert source["ra"].unit == u.hourangle
    assert source["ra"].tolist() == [1., 2.]


def test_declared_dimension_unit_is_converted_without_changing_legacy_parser():
    source = Table({"ra": [10.], "dec": [20.], "dimension": ["120 x 60"]})
    source["dimension"].unit = u.arcsec
    normalized = NonStellar(None)._normalize(source)
    assert normalized["major_axis_arcmin"][0] == 2.
    assert normalized["minor_axis_arcmin"][0] == 1.
    assert NonStellar.parse_dimension("120 x 60") == (120., 60.)


@pytest.mark.parametrize("field", ["ra", "dec", "major", "minor", "pa", "dimension"])
def test_incompatible_declared_unit_refuses_reload_without_publishing(field, catalogue, tmp_path):
    layer = NonStellar(None)
    layer.load(filename=catalogue)
    old = (layer.catalog_name, layer.source, layer.source_catalog, layer.catalog, layer._source_revision)
    layer._observed_point_cache["retained"] = object()
    cached = dict(layer._observed_point_cache)
    source = Table({"ra": [10.], "dec": [20.], "major": [2.], "minor": [1.], "pa": [0.]})
    if field == "dimension":
        source.remove_columns(["major", "minor"])
        source["dimension"] = ["2 x 1"]
    source[field].unit = u.m
    path = tmp_path / "invalid.ecsv"
    source.write(path)
    with pytest.raises(u.UnitConversionError):
        layer.load(catalog="invalid", filename=path)
    assert layer.catalog_name == old[0] and layer.source == old[1]
    assert layer.source_catalog is old[2] and layer.catalog is old[3]
    assert layer._source_revision == old[4]
    assert layer._observed_point_cache == cached


def test_geometry_preserves_independent_catalogue_metadata(catalogue, observer):
    source = Table.read(catalogue)
    source.meta = {"source": {"edition": "synthetic-v1"}}
    source.write(catalogue, overwrite=True)
    layer = NonStellar(observer)
    layer.load(filename=catalogue)
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    native = LayerRealizationContext(NATIVE_ICRS_SPEC)
    results = [layer.position(), layer.realize(native, None),
               layer.realize(native, None, labels_only=True), layer.spherical_geometry(observer)]
    for result in results:
        assert result.metadata["catalogue_metadata"] == source.meta
        result.metadata["catalogue_metadata"]["source"]["edition"] = "changed"
    assert layer.catalog.meta == source.meta


@pytest.mark.parametrize("family", ["messier", "caldwell", "galaxies", "globular_clusters",
                                  "planetary_nebulae", "supernova_remnants"])
def test_packaged_nonstellar_families_preserve_source_metadata_and_fields(family):
    from wenu.objects.galaxies import Galaxies
    from wenu.objects.globular_clusters import GlobularClusters
    from wenu.objects.planetary_nebulae import PlanetaryNebulae
    from wenu.objects.supernova_remnants import SupernovaRemnants
    from wenu.resources import nonstellar_catalog_path
    owners = {"galaxies": Galaxies, "globular_clusters": GlobularClusters,
              "planetary_nebulae": PlanetaryNebulae, "supernova_remnants": SupernovaRemnants}
    layer = owners[family](None) if family in owners else NonStellar(None, catalog=family)
    source = Table.read(nonstellar_catalog_path(family))
    layer.load()
    assert layer.source_catalog.meta == source.meta
    assert set(source.colnames) <= set(layer.source_catalog.colnames)
    # Source metadata must remain independent even in the PN specialization.
    source.meta["synthetic_probe"] = {"value": 1}
    normalized = layer._normalize(source)
    source.meta["synthetic_probe"]["value"] = 2
    assert normalized.meta["synthetic_probe"]["value"] == 1


@pytest.fixture
def catalogue(tmp_path):
    table = Table()
    table["name"] = ["M 1", "M 31", "M 42"]
    table["ra"] = [83.633, 10.685, 83.822]
    table["dec"] = [22.014, 41.269, -5.391]
    table["dimension"] = ["6 x 4", "190X60", "85"]
    table["vmag"] = [8.4, 3.4, 4.0]
    table["object_type"] = ["SNR", "Galaxy", "Nebula"]
    table["pa"] = [30.0, np.nan, np.nan]
    path = tmp_path / "messier.ecsv"
    table.write(path, format="ascii.ecsv")
    return path


@pytest.fixture
def observer():
    location = EarthLocation.from_geodetic(
        lon=-71.5 * u.deg,
        lat=-33.0 * u.deg,
        height=52.0 * u.m,
    )
    frame = AltAz(
        obstime=Time("2026-08-16T01:00:00"),
        location=location,
    )
    return SimpleNamespace(altaz_frame=frame)


def test_nonstellar_is_the_single_catalogue_layer():
    assert issubclass(NonStellar, AstronomicalObject)


def test_complete_caldwell_catalogue_uses_existing_nonstellar_loader(tmp_path):
    import hashlib
    import json
    from wenu.resources import nonstellar_catalog_path
    path = nonstellar_catalog_path('caldwell')
    source = Table.read(path)
    assert len(source) == 109
    assert list(source['caldwell_number']) == list(range(1, 110))
    assert source[13]['cluster_components'] == 'NGC0869|NGC0884'
    assert source[40]['cluster_components'] == 'Melotte 25'
    assert source[49]['primary_id'] == 'NGC2244'
    assert source[49]['parameter_source_id'] == 'NGC2239'
    assert source[36]['primary_id'] == 'NGC6885'
    assert source[36]['parameter_source_id'] == 'NGC6882'
    provenance = json.loads(path.parent.joinpath('caldwell_openngc.provenance.json').read_text())
    assert provenance['license'] == 'CC-BY-SA-4.0'
    for name, record in provenance['files'].items():
        assert hashlib.sha256(path.parent.joinpath(name).read_bytes()).hexdigest() == record['sha256']
    assert hashlib.sha256(path.parent.joinpath('caldwell_membership_v1.csv').read_bytes()).hexdigest() == provenance['membership_ledger_sha256']
    layer = NonStellar(None, catalog='caldwell')
    table = layer.load()
    assert list(table['identifier']) == [f'C {n}' for n in range(1, 110)]
    assert np.isfinite(table['ra_deg']).all() and np.isfinite(table['dec_deg']).all()
    assert set(table['object_type']) >= {'open cluster', 'globular cluster', 'galaxy', 'planetary nebula'}
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    points = layer.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None,
        selected=['C 1', 'C 14', 'C 106'], labels_only=True)
    assert set(points.ids) == {'C 1', 'C 14', 'C 106'}
    import importlib.util
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('query_caldwell_openngc', root/'tools/query_caldwell_openngc.py')
    maintenance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(maintenance)
    assert len(maintenance.membership()) == 109
    corrupted = b'corrupted cached source\n'
    assert maintenance.digest(corrupted) != maintenance.SOURCE_HASHES['NGC.csv']
    (tmp_path/'NGC.csv').write_bytes(corrupted)
    with pytest.raises(ValueError, match='Pinned OpenNGC source digest mismatch'):
        maintenance.main(['--source-directory', str(tmp_path), '--output-directory', str(tmp_path/'output')])
    assert not (tmp_path/'output').exists()


def test_dedicated_galaxy_layer_suppresses_generic_messier_outline_without_mutating_sources(catalogue):
    from wenu.objects.galaxies import Galaxies
    from wenu.charts.detail import ResolvedDetail
    from wenu.charts.detail_application import apply_resolved_detail
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    sky = CelestialSphere(None)
    layer = NonStellar(None); layer.load(filename=catalogue)
    sky.nonstellar = sky.add(layer)
    sky.galaxies = sky.add(Galaxies(None))
    original = layer.catalog.copy()
    for enabled, override, expected in (({'nonstellar_objects','galaxies'}, None, ('M 1','M 42')),
                              ({'nonstellar_objects'}, None, ('M 1','M 31','M 42')),
                              ({'nonstellar_objects','galaxies'}, False, ('M 1','M 31','M 42'))):
        application = apply_resolved_detail(sky, ResolvedDetail(enabled_layers=frozenset(enabled)),
            explicit_layer_options=None if override is None else {sky.galaxies: {'enabled': override}})
        options = application.layer_options[layer].get('geometry', {})
        rendered = layer.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None, **options)
        assert tuple(rendered.names) == expected
    assert np.array_equal(layer.catalog['identifier'], original['identifier'])


def test_dimension_parser():
    assert NonStellar.parse_dimension("26 X 14") == (26.0, 14.0)
    assert NonStellar.parse_dimension("80") == (80.0, 80.0)
    major, minor = NonStellar.parse_dimension("")
    assert np.isnan(major)
    assert np.isnan(minor)


def test_native_galaxy_subclass_keeps_its_table_contract(catalogue):
    from wenu.objects.galaxies import Galaxies
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu.geometry.spherical import SphericalPolygons
    layer = Galaxies(None)
    layer.load(filename=catalogue)
    result = layer.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None)
    assert isinstance(result, SphericalPolygons)
    assert len(result) == len(layer.catalog)


def test_native_messier_labels_keep_heterogeneous_designations_without_outlines(catalogue):
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu.geometry.spherical import SphericalPoints
    layer = NonStellar(None); layer.load(filename=catalogue)
    result = layer.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None,
        labels_only=True, excluded_categories=('galaxies','supernova_remnants'))
    assert isinstance(result, SphericalPoints)
    assert tuple(result.names) == ('M 1','M 31','M 42')
    assert result.metadata['semantic_entity_categories'] == ('supernova_remnants','galaxies','nebulae')


def test_load_normalizes_heasarc_fields(catalogue, observer):
    layer = NonStellar(observer, samples=36)
    result = layer.load(filename=catalogue)
    assert list(result["identifier"]) == ["M 1", "M 31", "M 42"]
    assert result["major_axis_arcmin"][1] == 190.0
    assert result["minor_axis_arcmin"][1] == 60.0
    assert result["position_angle_deg"][0] == 30.0


def test_geometry_is_closed_and_transformed(catalogue, observer):
    layer = NonStellar(observer, samples=36)
    layer.load(filename=catalogue)
    geometry = layer.spherical_geometry(observer)
    assert isinstance(geometry, SphericalCurves)
    assert len(geometry) == 3
    assert np.all(geometry.closed)
    assert all(len(curve) == 36 for curve in geometry.lon_deg)
    assert np.all(np.isfinite(geometry.lon_deg[0]))
    assert geometry.metadata["coordinate_system"] == "altaz"
    assert geometry.metadata["semantic_entity_keys"] == (
        "M 1", "M 31", "M 42"
    )
    assert geometry.metadata["semantic_entity_display_names"] == (
        "M 1", "M 31", "M 42"
    )
    assert geometry.metadata["semantic_entity_categories"] == (
        "supernova_remnants", "galaxies", "nebulae"
    )


@pytest.mark.parametrize(
    ("object_type", "identifier", "category"),
    (
        ("Galaxy", None, "galaxies"),
        ("S", None, "galaxies"),
        ("E", None, "galaxies"),
        ("E?", None, "galaxies"),
        ("IR", None, "galaxies"),
        ("Open Cluster", None, "open_clusters"),
        ("OC", None, "open_clusters"),
        ("GC", None, "globular_clusters"),
        ("GB", None, "globular_clusters"),
        ("Planetary Nebula", None, "planetary_nebulae"),
        ("PL", None, "planetary_nebulae"),
        ("SNR", None, "supernova_remnants"),
        ("DI", "M 1", "supernova_remnants"),
        ("DI", "M 8", "nebulae"),
        ("Emission Nebula", None, "nebulae"),
        ("H II region", None, "nebulae"),
        ("Unclassified", None, "other_objects"),
        (None, None, "other_objects"),
    ),
)
def test_catalog_object_types_use_shared_astronomical_categories(
    object_type, identifier, category
):
    assert NonStellar.semantic_category(
        object_type,
        identifier=identifier,
    ) == category


def test_unknown_position_angle_does_not_invent_orientation():
    center = SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg)
    outline = NonStellar._ellipse(center, 16.0, 4.0, np.nan, 72)
    separations = center.separation(outline).to_value(u.arcmin)
    assert np.ptp(separations) < 1.0e-10
    assert separations[0] == pytest.approx(4.0)


def test_selection(catalogue, observer):
    layer = NonStellar(observer, samples=24)
    layer.load(filename=catalogue)
    geometry = layer.spherical_geometry(
        observer,
        selected=["M 31"],
    )
    assert list(geometry.ids) == ["M 31"]
    assert geometry.metadata["semantic_entity_keys"] == ("M 31",)
    assert geometry.metadata["semantic_entity_display_names"] == ("M 31",)
    assert geometry.metadata["semantic_entity_categories"] == (
        "galaxies",
    )


def test_outline_sampling_is_render_local_and_bounded(catalogue, observer):
    layer = NonStellar(observer, samples=36)
    layer.load(filename=catalogue)

    reduced = layer.spherical_geometry(observer, samples=18)
    complete = layer.spherical_geometry(observer)

    assert all(len(curve) == 18 for curve in reduced.lon_deg)
    assert all(len(curve) == 36 for curve in complete.lon_deg)
    assert layer.samples == 36
    with pytest.raises(ValueError, match="at least 12"):
        layer.spherical_geometry(observer, samples=11)
    with pytest.raises(ValueError, match="maximum sampling quality"):
        layer.spherical_geometry(observer, samples=37)


def test_outline_selections_share_one_quality_specific_cache(
    catalogue, observer, monkeypatch
):
    layer = NonStellar(observer, samples=36)
    layer.load(filename=catalogue)
    calls = []

    def transform(
        table,
        resolved,
        *,
        samples,
        minimum_size_arcmin,
        centres=None,
    ):
        assert centres is not None
        calls.append((len(table), samples, minimum_size_arcmin))
        return (
            tuple(np.full(samples, index) for index in range(len(table))),
            tuple(np.full(samples, -index) for index in range(len(table))),
        )

    monkeypatch.setattr(layer, "_transform_outline_table", transform)
    first = layer.spherical_geometry(
        observer,
        selected=["M 31"],
        samples=18,
        minimum_size_arcmin=2.0,
    )
    second = layer.spherical_geometry(
        observer,
        selected=["M 42", "M 1"],
        samples=18,
        minimum_size_arcmin=2.0,
    )

    assert first.ids.tolist() == ["M 31"]
    assert second.ids.tolist() == ["M 1", "M 42"]
    assert calls == [(3, 18, 2.0)]
    assert len(layer._observed_outline_cache) == 1
    cached = next(iter(layer._observed_outline_cache.values()))
    assert all(
        values.flags.writeable is False
        for coordinate in cached
        for values in coordinate
    )


def test_outline_quality_and_reload_select_distinct_realizations(
    catalogue, observer, monkeypatch
):
    layer = NonStellar(observer, samples=36)
    layer.load(filename=catalogue)
    calls = []

    def transform(
        table,
        resolved,
        *,
        samples,
        minimum_size_arcmin,
        centres=None,
    ):
        assert centres is not None
        calls.append((samples, minimum_size_arcmin))
        values = tuple(np.zeros(samples) for _ in table)
        return values, values

    monkeypatch.setattr(layer, "_transform_outline_table", transform)
    for samples, minimum in ((18, None), (36, None), (36, 2.0)):
        layer.spherical_geometry(
            observer,
            samples=samples,
            minimum_size_arcmin=minimum,
        )

    assert calls == [(18, None), (36, None), (36, 2.0)]
    assert len(layer._observed_outline_cache) == 3

    layer.load(filename=catalogue)
    assert layer._observed_outline_cache == {}


def test_celestial_sphere_helper_loads_and_registers(
    catalogue,
    observer,
):
    sky = CelestialSphere(observer)
    layer = sky.add_nonstellar(filename=catalogue, samples=24)
    assert sky.nonstellar is layer
    assert layer in sky.layers


@pytest.mark.parametrize('family', ('messier', 'caldwell', 'galaxies', 'globular_clusters', 'planetary_nebulae', 'supernova_remnants'))
def test_packaged_nonstellar_gaps_remain_source_bound_and_strictly_refused(family):
    from wenu.objects.galaxies import Galaxies
    from wenu.objects.globular_clusters import GlobularClusters
    from wenu.objects.planetary_nebulae import PlanetaryNebulae
    from wenu.objects.supernova_remnants import SupernovaRemnants
    cls = {'messier': NonStellar, 'caldwell': NonStellar, 'galaxies': Galaxies, 'globular_clusters': GlobularClusters,
           'planetary_nebulae': PlanetaryNebulae, 'supernova_remnants': SupernovaRemnants}[family]
    layer = cls(None, **({'catalog': family} if family in ('messier', 'caldwell') else {})); layer.load()
    record = layer.catalogue_metadata.to_record()
    assert layer.admission_missing_fields
    for field, source_field in (('frame', 'coordinate_frame'), ('origin', 'coordinate_origin'),
                                ('epoch', 'coordinate_epoch'), ('epoch_scale', 'coordinate_epoch_scale')):
        if source_field not in layer.source_catalog.meta:
            assert record[field] is None
    with pytest.raises(ValueError, match='Incomplete nonstellar metadata'):
        layer.require_complete_metadata()
    geometry = layer.position()
    assert geometry.coordinate_spec.epoch == record['epoch']
    assert geometry.metadata['catalogue_admission'] == record
    assert record['source_sha256'] and record['source_units']['ra'] and record['source_units']['dec']


@pytest.mark.parametrize('family', ('messier', 'caldwell', 'galaxies', 'globular_clusters', 'planetary_nebulae', 'supernova_remnants'))
def test_explicit_lookup_admission_preserves_physical_gaps_and_default_geometry(family):
    from wenu.objects.galaxies import Galaxies
    from wenu.objects.globular_clusters import GlobularClusters
    from wenu.objects.planetary_nebulae import PlanetaryNebulae
    from wenu.objects.supernova_remnants import SupernovaRemnants
    cls = {'messier': NonStellar, 'caldwell': NonStellar, 'galaxies': Galaxies,
           'globular_clusters': GlobularClusters, 'planetary_nebulae': PlanetaryNebulae,
           'supernova_remnants': SupernovaRemnants}[family]
    layer = cls(None, **({'catalog': family} if family in ('messier', 'caldwell') else {}))
    layer.load()
    original = layer.catalog.copy(copy_data=True)
    record = layer.catalogue_metadata.to_record()
    before = layer.position()
    metadata = layer.require_catalogue_lookup_metadata()
    assert metadata.to_record() == record
    assert metadata.missing_fields_for('catalogue-lookup') == ()
    assert layer.admission_missing_fields
    with pytest.raises(ValueError, match='Incomplete nonstellar metadata'):
        layer.require_complete_metadata()
    spec = metadata.coordinate_spec(layer.catalog_name, position_model='catalogue-lookup')
    assert spec.epoch == record['epoch']
    assert spec.model == 'catalogue-lookup-legacy-unverified-encoding'
    assert spec.origin == 'legacy-unverified-origin'
    assert spec.instant is None and spec.time_scale is None
    assert layer.catalog.meta == original.meta
    for name in layer.catalog.colnames:
        np.testing.assert_array_equal(layer.catalog[name], original[name])
    after = layer.position()
    np.testing.assert_array_equal(before.lon_deg, after.lon_deg)
    np.testing.assert_array_equal(before.lat_deg, after.lat_deg)
    assert before.coordinate_spec == after.coordinate_spec
    assert after.metadata['catalogue_admission'] == record


@pytest.mark.parametrize('fault', ('catalogue', 'edition', 'provenance', 'digest', 'ra_unit'))
def test_lookup_admission_still_refuses_missing_source_evidence(fault):
    from wenu.objects.nonstellar import NonStellarCatalogueMetadata
    layer = NonStellar(None); layer.load()
    record = layer.catalogue_metadata.to_record()
    meta = record['source_metadata']
    units = dict(record['source_units'])
    digest = record['source_sha256']
    if fault == 'catalogue':
        for key in ('catalog', 'source'):
            meta.pop(key, None)
    elif fault == 'edition':
        for key in ('release', 'catalog_version', 'catalog_reference', 'catalogue_reference'):
            meta.pop(key, None)
    elif fault == 'provenance':
        for key in tuple(meta):
            if key == 'url' or key.endswith('_url'):
                meta.pop(key)
    elif fault == 'digest':
        digest = None
    else:
        units['ra'] = None
    table = layer.source_catalog.copy(copy_data=True); table.meta = meta
    candidate = NonStellarCatalogueMetadata.from_table(table, source_units=units, source_sha256=digest)
    with pytest.raises(ValueError, match='Incomplete nonstellar metadata'):
        candidate.require_complete(position_model='catalogue-lookup')


def test_qualified_lookup_reference_does_not_require_a_motion_epoch(catalogue):
    table = Table.read(catalogue)
    table.meta = dict(catalog='synthetic', catalog_version='synthetic-v1',
        documentation_url='https://example.invalid/synthetic',
        coordinate_frame='ICRS', coordinate_origin='solar-system-barycenter')
    for name, unit in (('ra', u.deg), ('dec', u.deg), ('dimension', u.arcmin), ('pa', u.deg)):
        table[name].unit = unit
    table.write(catalogue, overwrite=True)
    layer = NonStellar(None); layer.load(filename=catalogue)
    metadata = layer.require_catalogue_lookup_metadata()
    spec = metadata.coordinate_spec('synthetic', position_model='catalogue-lookup')
    assert spec.model == 'catalogue-lookup' and spec.epoch is None
    assert spec.origin == 'solar-system-barycenter'
    with pytest.raises(ValueError, match='epoch'):
        layer.require_complete_metadata()


@pytest.mark.parametrize('catalog', ('messier', 'caldwell'))
def test_generic_lookup_returned_states_control_all_consumers(catalog, observer, monkeypatch):
    from dataclasses import replace
    from wenu.catalogue_state import _unit_direction
    from wenu_kernel import KernelSession
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    layer = NonStellar(observer, catalog=catalog, samples=12); layer.load()
    source = layer.catalog.copy(copy_data=True)
    record = layer.catalogue_metadata.to_record()
    identifier = str(source['identifier'][0])
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    layer.spherical_centers(observer, selected=[identifier])
    layer.spherical_geometry(observer, selected=[identifier])
    evaluate, calls = KernelSession.evaluate, []
    def shift(session, query):
        batch = evaluate(session, query); calls.append(batch)
        return replace(batch, states=tuple(replace(s, vector=_unit_direction(35., -10.)) for s in batch.states))
    monkeypatch.setattr(KernelSession, 'evaluate', shift)
    native = layer.position()
    np.testing.assert_allclose(native.lon_deg, 35.)
    labels = layer.realize(context, None, selected=[identifier], labels_only=True)
    np.testing.assert_allclose(labels.lon_deg, [35.])
    outline = layer.realize(context, None, selected=[identifier])
    row = source[0]
    expected = layer._ellipse(SkyCoord(ra=35.*u.deg, dec=-10.*u.deg),
        row['major_axis_arcmin'], row['minor_axis_arcmin'], row['position_angle_deg'], 12)
    np.testing.assert_allclose(outline.lon_deg[0], expected.icrs.ra.deg)
    points = layer.spherical_centers(observer, selected=[identifier])
    horizontal = SkyCoord(ra=35.*u.deg, dec=-10.*u.deg).transform_to(observer.altaz_frame)
    np.testing.assert_allclose(points.lon_deg, [horizontal.az.deg])
    outlines = layer.spherical_geometry(observer, selected=[identifier])
    np.testing.assert_allclose(outlines.lon_deg[0], expected.transform_to(observer.altaz_frame).az.deg)
    assert len(calls) == 5  # One query per consumer, including warm observed routes.
    assert list(native.ids) == list(source['identifier'])
    assert labels.metadata['semantic_entity_keys'] == (identifier,)
    assert layer.catalogue_metadata.to_record() == record
    for name in source.colnames:
        np.testing.assert_array_equal(source[name], layer.catalog[name])
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic generic kernel refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    for action in (layer.position, lambda: layer.realize(context, None, labels_only=True),
                   lambda: layer.realize(context, None),
                   lambda: layer.spherical_centers(observer),
                   lambda: layer.spherical_geometry(observer)):
        with pytest.raises(RuntimeError, match='generic kernel refusal'):
            action()


@pytest.mark.parametrize('catalog', ('messier', 'caldwell'))
def test_generic_lookup_validates_source_even_after_cache_fill(catalog, observer, monkeypatch):
    layer = NonStellar(observer, catalog=catalog, samples=12); layer.load()
    layer.spherical_centers(observer); layer.spherical_geometry(observer)
    def refuse():
        raise ValueError('synthetic lookup admission refusal')
    monkeypatch.setattr(layer, 'require_catalogue_lookup_metadata', refuse)
    for action in (layer.position, lambda: layer.spherical_centers(observer),
                   lambda: layer.spherical_geometry(observer)):
        with pytest.raises(ValueError, match='lookup admission refusal'):
            action()


def test_generic_provider_passes_shipped_kernel_conformance(catalogue):
    from dataclasses import replace
    import io
    import unittest
    from wenu_kernel.conformance import ProviderActivity, ProviderCase, provider_suite
    from wenu_kernel.records import AccuracyRequest, StateQuery, TimePoint
    layer = NonStellar(None); layer.load(filename=catalogue)
    def factory():
        rows = [['synthetic', 10., -20.]]
        provider = layer._direction_provider(rows, 'tt')
        admission = provider.describe().admissions[0]
        query = StateQuery(admission.catalogue, admission.model, admission.objects,
            (TimePoint(-1000000, 0, 'tt'), TimePoint(3000000, 0, 'tt')),
            admission.reference, AccuracyRequest())
        probe = replace(query, times=(TimePoint(4000000, 0, 'tt'),))
        counts = {'evaluate': 0, 'close': 0}
        evaluate, close = provider.evaluate, provider.close
        def measured(query):
            counts['evaluate'] += 1
            return evaluate(query)
        def cleanup():
            counts['close'] += 1
            return close()
        provider.evaluate, provider.close = measured, cleanup
        def mutate():
            rows[0][1] = 99.
        return ProviderCase(provider, query, probe,
            lambda: ProviderActivity(counts['evaluate'], 0, counts['close']), mutate)
    result = unittest.TextTestRunner(stream=io.StringIO()).run(provider_suite(factory, name='GenericLookupContract'))
    assert result.wasSuccessful(), result.errors + result.failures
    assert result.testsRun == 8 and not result.skipped

