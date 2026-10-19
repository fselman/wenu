"""Family-spanning contracts for one reusable canonical celestial sphere."""

from dataclasses import fields
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from wenu import Observer, generate_celestial_sphere, get_chart_view
from wenu.charts.detail import SkyContentSelection
from wenu.sky.observed_cache import observer_geometry_key


VIEW_REQUESTS = (
    (
        "planisphere",
        {
            "family": "planisphere",
            "constellations": ("Cru", "Cen"),
            "mask": True,
        },
    ),
    (
        "regional-single",
        {
            "family": "regional",
            "constellations": ("Cru",),
            "mask": True,
        },
    ),
    (
        "regional-group",
        {
            "family": "regional",
            "group": "galactic-center",
        },
    ),
    (
        "circumpolar",
        {
            "family": "circumpolar",
            "pole": "south",
            "limiting_declination_deg": -69.75,
        },
    ),
    (
        "binocular",
        {
            "family": "binocular",
            "target": "omega-centauri",
            "field_diameter_deg": 6.5,
        },
    ),
    ("all-sky", {"family": "all_sky"}),
)


@pytest.fixture(scope="module")
def canonical_sphere():
    return generate_celestial_sphere()


@pytest.fixture(scope="module")
def observers():
    values = (
        Observer(location="La Ligua", time="2026-08-15 21:00"),
        Observer(location="La Ligua", time="2026-08-16 00:00"),
        Observer(location="Papudo", time="2026-08-15 21:00"),
    )
    yield values
    for observer in values:
        observer.close()


def _content_summary(view):
    content = view._prepared.resolved.request.content
    return tuple(
        (field.name, getattr(content, field.name))
        for field in fields(SkyContentSelection)
    )


def _view_summary(view):
    return (
        view.family,
        view.mask,
        None if view.target is None else view.target.key,
        (
            None
            if view.constellations is None
            else view.constellations.key
        ),
        view.frame,
        _content_summary(view),
    )


@pytest.mark.integration
def test_every_chart_family_prepares_from_one_observer_independent_sphere(
    canonical_sphere,
    observers,
):
    observer = observers[0]
    canonical_layers = canonical_sphere.layers

    views = {
        name: get_chart_view(canonical_sphere, observer, **arguments)
        for name, arguments in VIEW_REQUESTS
    }

    assert canonical_sphere.observer is None
    assert all(view.sky is canonical_sphere for view in views.values())
    assert all(view.observer is observer for view in views.values())
    assert canonical_sphere.layers == canonical_layers
    assert views["planisphere"].constellations.key == "cru+cen"
    assert views["planisphere"].mask is True
    assert views["regional-single"].constellations.key == "cru"
    assert views["regional-single"].mask is True
    assert views["regional-group"].constellations.key == "galactic-center"
    assert views["circumpolar"].frame.pole == "south"
    assert views["binocular"].target.key == "omega-centauri"
    assert views["all-sky"].coordinate_frame == "galactic"


@pytest.mark.integration
def test_family_order_does_not_change_selection_subjects_or_masks(
    canonical_sphere,
    observers,
):
    observer = observers[0]
    canonical_layers = canonical_sphere.layers

    forward = {
        name: _view_summary(
            get_chart_view(canonical_sphere, observer, **arguments)
        )
        for name, arguments in VIEW_REQUESTS
    }
    reverse = {
        name: _view_summary(
            get_chart_view(canonical_sphere, observer, **arguments)
        )
        for name, arguments in reversed(VIEW_REQUESTS)
    }

    assert reverse == forward
    assert canonical_sphere.layers == canonical_layers


@pytest.mark.integration
def test_observers_and_instants_use_separate_reusable_observed_caches(
    canonical_sphere,
    observers,
):
    stars = canonical_sphere.stars

    first = stars.observed_altaz(observers[0])
    later = stars.observed_altaz(observers[1])
    papudo = stars.observed_altaz(observers[2])
    repeated = stars.observed_altaz(observers[0])

    assert repeated[1] is first[1]
    assert repeated[2] is first[2]
    assert later[1] is not first[1]
    assert papudo[1] is not first[1]
    keys = {
        key[0]
        for key in stars._observed_altaz_cache
    }
    assert {
        observer_geometry_key(observer)
        for observer in observers
    } <= keys
    assert canonical_sphere.observer is None


def test_observed_cache_identity_includes_ephemeris():
    common = {
        "lat_deg": -32.443342,
        "lon_deg": -71.230289,
        "elevation_m": 52.0,
        "utc_datetime": datetime(
            2026, 8, 16, 1, 0, tzinfo=timezone.utc
        ),
        "data_directory": "/tmp/wenu-cache",
    }
    first = SimpleNamespace(ephemeris_name="de440s.bsp", **common)
    second = SimpleNamespace(ephemeris_name="de421.bsp", **common)

    assert observer_geometry_key(first) != observer_geometry_key(second)

# Native snapshots are scientific input, independent of index appearance.
@pytest.fixture(scope="module")
def native_snapshot_case(tmp_path_factory):
    from pathlib import Path
    import tomllib
    from wenu.atlas_design import AtlasDesignRequest
    from wenu.sky import native_snapshot as snapshots
    from wenu.objects.stars import Stars
    import socket

    raw = AtlasDesignRequest.from_dict(tomllib.loads(
        (Path(__file__).resolve().parents[1] /
         "examples/atlas_design_request_v1.toml").read_text())).resolve().to_json().encode()
    destination = tmp_path_factory.mktemp("native-snapshot") / "sky-v1"
    counts = dict(spheres=0, catalogues=0)
    cold = []
    fixed_counts = {name: 0 for name in (*snapshots._CATALOGUES, "constellation_boundaries")}
    generate, load = snapshots.generate_native_icrs_sphere, Stars.load

    def factory(**options):
        counts["spheres"] += 1
        sky = generate(**options)
        cold.append(sky)
        return sky

    def counted_load(self, **options):
        counts["catalogues"] += 1
        return load(self, **options)

    def forbidden(*args, **kwargs):
        raise AssertionError("Native preparation must not use network/observation")
    def count_fixed_load(original):
        def counted(self, *args, **kwargs):
            fixed_counts[self.layer_name] += 1
            return original(self, *args, **kwargs)
        return counted
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(snapshots, "generate_native_icrs_sphere", factory)
        patch.setattr(Stars, "load", counted_load)
        patch.setattr(socket, "socket", forbidden)
        for owner in (snapshots.NonStellar, snapshots.OpenClusters, snapshots.ConstellationBoundaries):
            patch.setattr(owner, "load", count_fixed_load(owner.load))
        digest = snapshots.prepare_native_sky_snapshot(raw, destination)
    assert counts == dict(spheres=1, catalogues=1)
    assert fixed_counts == {name: 1 for name in fixed_counts}
    return raw, destination, digest, cold[0]


def _assert_native_geometry_equal(first, second):
    import numpy as np
    assert type(first) is type(second)
    assert first.coordinate_spec == second.coordinate_spec
    assert len(first) == len(second)
    if hasattr(first, "components"):
        assert first.components.keys() == second.components.keys()
        for key in first.components:
            _assert_native_geometry_equal(first.components[key], second.components[key])
        assert first.metadata == second.metadata
        return
    for name in ("lon_deg", "lat_deg"):
        a, b = getattr(first, name), getattr(second, name)
        if isinstance(a, tuple):
            for left, right in zip(a, b, strict=True):
                np.testing.assert_array_equal(left, right)
        else:
            np.testing.assert_array_equal(a, b)
    for name in ("ids", "names", "labels", "closed"):
        a, b = getattr(first, name, None), getattr(second, name, None)
        if a is None:
            assert b is None
        else:
            np.testing.assert_array_equal(a, b)
    assert first.metadata.keys() == second.metadata.keys()
    for key, a in first.metadata.items():
        b = second.metadata[key]
        if isinstance(a, np.ndarray):
            if a.dtype.kind == "f":
                # Existing ring area reductions vary at machine precision
                # with mapped-buffer alignment; vertices/topology stay exact.
                np.testing.assert_allclose(a, b, rtol=1e-13, atol=1e-15, equal_nan=True)
            elif a.dtype.kind == "O":
                assert a.shape == b.shape
                for left, right in zip(a.flat, b.flat, strict=True):
                    if isinstance(left, (float, np.floating)) and np.isnan(left):
                        assert isinstance(right, (float, np.floating)) and np.isnan(right)
                    else:
                        assert left == right
            else:
                np.testing.assert_array_equal(a, b)
        else:
            assert a == b


def test_native_snapshot_matches_cold_full_sphere_and_layer_options(native_snapshot_case, monkeypatch):
    import numpy as np
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu.objects.stars import Stars
    from wenu.sky.constellation_lines import ConstellationLines
    from wenu.sky.milky_way import MilkyWayIsophotes
    from wenu.sky.magellanic_clouds import MagellanicCloudIsophotes

    raw, destination, digest, cold = native_snapshot_case
    def forbidden(*args, **kwargs):
        raise AssertionError("Resume must not reload an original catalogue")
    for owner in (Stars, ConstellationLines, MilkyWayIsophotes, MagellanicCloudIsophotes):
        monkeypatch.setattr(owner, "load", forbidden)
    snapshot = read_native_sky_snapshot(destination, expected_manifest_sha256=digest)
    assert snapshot.design_bytes == raw
    assert len(snapshot.make_sky().stars.source_catalog) == 118218
    assert len(snapshot.make_sky().stars.catalog) > 100000
    assert all(isinstance(a, np.memmap) and not a.flags.writeable for a in snapshot.arrays.values())
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    warm = snapshot.make_sky()
    for a, b in zip(cold.layers, warm.layers, strict=True):
        _assert_native_geometry_equal(a.realize(context, None), b.realize(context, None))
    assert warm.stars.designation_catalogue == cold.stars.designation_catalogue
    assert warm.stars.designation_catalogue.get(78820).assignments("bayer")
    for limit in (4.5, 6, 11):
        _assert_native_geometry_equal(
            cold.stars.realize(context, None, magnitude_limit=limit),
            warm.stars.realize(context, None, magnitude_limit=limit))
    _assert_native_geometry_equal(
        cold.stars.realize(context, None, magnitude_limit=4, include_ids={78820}, constellations=("Sco",)),
        warm.stars.realize(context, None, magnitude_limit=4, include_ids={78820}, constellations=("Sco",)))
    _assert_native_geometry_equal(
        cold.constellation_lines.realize(context, None, selected=("Sco", "Lib")),
        warm.constellation_lines.realize(context, None, selected=("Sco", "Lib")))
    for left, right in ((cold.milky_way_isophotes, warm.milky_way_isophotes),
                        (cold.magellanic_cloud_isophotes["lmc"], warm.magellanic_cloud_isophotes["lmc"])):
        level = left.available_levels[-1]
        _assert_native_geometry_equal(left.realize(context, None, levels=(level,)),
                                      right.realize(context, None, levels=(level,)))
    other = snapshot.make_sky()
    warm.stars.include_ids = frozenset({78820})
    assert not other.stars.include_ids
    with pytest.raises(ValueError):
        next(iter(snapshot.arrays.values()))[0] = 0


def test_native_snapshot_resumes_in_fresh_process_without_sources(native_snapshot_case):
    import os
    from pathlib import Path
    import subprocess
    import sys
    _, destination, digest, _ = native_snapshot_case
    program = r'''
import sys
from wenu.sky.native_snapshot import read_native_sky_snapshot
from wenu.objects.stars import Stars
from wenu.sky.constellation_lines import ConstellationLines
from wenu.sky.milky_way import MilkyWayIsophotes
from wenu.sky.magellanic_clouds import MagellanicCloudIsophotes
from wenu.sky import maximal_sphere
from wenu.sky.native_snapshot import _CATALOGUES, ConstellationBoundaries
from wenu import star_designations
from wenu import stellar_research
from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
import resource
soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (min(64, soft), hard))
def forbidden(*args, **kwargs):
    raise AssertionError("No original source loading or whole-sphere preparation on resume")
for owner in (Stars, ConstellationLines, MilkyWayIsophotes, MagellanicCloudIsophotes, ConstellationBoundaries, *_CATALOGUES.values()):
    owner.load = forbidden
maximal_sphere.generate_native_icrs_sphere = forbidden
maximal_sphere.generate_celestial_sphere = forbidden
maximal_sphere.build_maximal_sphere = forbidden
star_designations.load_star_designations = forbidden
star_designations.load_stellar_curation = forbidden
stellar_research.load_stellar_research = forbidden
import wenu.sky.native_snapshot as snapshot_module
snapshot_module.packaged_stellar_metadata = forbidden
snapshot = read_native_sky_snapshot(sys.argv[1], expected_manifest_sha256=sys.argv[2])
sky = snapshot.make_sky()
points = sky.stars.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None, magnitude_limit=6)
assert len(points) > 4000
assert sky.stars.position().coordinate_spec.epoch == 'J1991.25'
vertices = sky.stars.native_positions(sky.constellation_lines.star_ids)
edges = sky.constellation_lines.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None)
assert vertices.coordinate_spec.epoch == edges.coordinate_spec.epoch == 'J1991.25'
assert len(edges) and set(vertices.ids) <= set(sky.stars.source_catalog.index)
anchors = sky.constellation_labels.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None)
assert len(anchors) >= 88 and anchors.coordinate_spec.epoch == 'J1991.25'
assert sky.stars.designation_catalogue.curation_sha256
assert sky.constellation_lines.star_ids_for(("Sco",))
context = LayerRealizationContext(NATIVE_ICRS_SPEC)
for name in _CATALOGUES:
    layer = getattr(sky, name)
    identifier = str(layer.realize(context, None).ids[0])
    assert len(layer.realize(context, None, selected=(identifier,))) == 1, name
assert len(sky.constellation_boundaries.realize(context, None, selected=("Sco",))) == 1
assert not sky.solar_system_bodies and sky.moon is None
labels = star_designations.resolve_star_labels(
    star_designations.StarLabelSelection(bayer=("Peg:delta",), show_full_bayer_designation=True),
    catalogue=sky.stars.designation_catalogue, research=sky.stellar_research)
assert labels.labels == ((677, "δ Peg"),)
print("verified frozen native sphere")
'''
    env = dict(os.environ)
    root = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run([sys.executable, "-c", program, str(destination), digest],
                            env=env, text=True, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "verified frozen native sphere"


def test_native_position_api_and_vertex_edges_match_cold_and_saved_sky(native_snapshot_case):
    import numpy as np
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    _, destination, _, cold = native_snapshot_case
    saved = read_native_sky_snapshot(destination).make_sky()
    assert saved.stars.catalogue_metadata == cold.stars.catalogue_metadata
    assert saved.stars.catalogue_metadata.to_record()['source_metadata']['reference_epoch_jd'] == 2448349.0625
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    _assert_native_geometry_equal(cold.stars.position(), saved.stars.position())
    identifiers = cold.constellation_lines.star_ids
    left, right = cold.stars.native_positions(identifiers), saved.stars.native_positions(identifiers)
    _assert_native_geometry_equal(left, right)
    a, b = cold.constellation_lines.realize(context, None), saved.constellation_lines.realize(context, None)
    _assert_native_geometry_equal(a, b)
    index = {int(identifier): i for i, identifier in enumerate(left.ids)}
    for hip_edge, lon, lat in zip(a.metadata['hip_edges'], a.lon_deg, a.lat_deg, strict=True):
        positions = [index[int(identifier)] for identifier in hip_edge]
        np.testing.assert_array_equal(lon, left.lon_deg[positions])
        np.testing.assert_array_equal(lat, left.lat_deg[positions])
    assert left.coordinate_spec.epoch == a.coordinate_spec.epoch == 'J1991.25'


def test_native_snapshot_preserves_cluster_epoch_lineage_and_selected_specs(native_snapshot_case):
    import numpy as np
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    _, destination, _, cold = native_snapshot_case
    snapshot = read_native_sky_snapshot(destination)
    warm = snapshot.make_sky()
    first, second = cold.open_clusters, warm.open_clusters
    assert first.catalog.meta == second.catalog.meta
    assert snapshot._records['fixed']['catalogues']['open_clusters']['epoch'] is None
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    for field in ('position_epoch', 'RA_source'):
        np.testing.assert_array_equal(first.catalog[field], second.catalog[field])
        np.testing.assert_array_equal(np.ma.getmaskarray(first.catalog[field]), np.ma.getmaskarray(second.catalog[field]))
    for row in (first.catalog[0], next(row for row in first.catalog if str(row['position_epoch']) == 'unknown')):
        selected = (str(row['wenu_id']),)
        left, right = (layer.realize(context, None, selected=selected) for layer in (first, second))
        _assert_native_geometry_equal(left, right)
        expected = None if str(row['position_epoch']) == 'unknown' else str(row['position_epoch'])
        assert left.coordinate_spec.epoch == right.coordinate_spec.epoch == expected
    np.testing.assert_array_equal(first.position().lon_deg, second.position().lon_deg)


def test_native_snapshot_preserves_nonstellar_admission_and_unknown_epochs(native_snapshot_case):
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    _, destination, _, cold = native_snapshot_case
    snapshot = read_native_sky_snapshot(destination)
    saved = snapshot.make_sky()
    assert snapshot._manifest['schema_version'] == 5
    for name in ('nonstellar', 'galaxies', 'globular_clusters', 'planetary_nebulae', 'supernova_remnants'):
        first, second = getattr(cold, name), getattr(saved, name)
        assert first.catalogue_metadata == second.catalogue_metadata
        record = second.catalogue_metadata.to_record()
        assert record['source_sha256'] == snapshot.source_digests[name]
        assert record['source_metadata'] == second.source_catalog.meta
        assert record['epoch'] is None
        assert 'epoch' in second.catalogue_metadata.missing_fields
        assert second.position().coordinate_spec.epoch is None
        assert snapshot._records['fixed']['catalogues'][name]['epoch'] is None
        with pytest.raises(ValueError, match='Incomplete nonstellar metadata'):
            second.catalogue_metadata.require_complete()
        geometry = second.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None,
                                  selected=(str(second.catalog['identifier'][0]),))
        assert geometry.coordinate_spec == second.native_coordinate_spec()
        assert geometry.metadata['catalogue_admission'] == record


def test_native_snapshot_preserves_declared_nonstellar_epoch(native_snapshot_case, tmp_path):
    from dataclasses import replace
    from astropy.table import Table
    from wenu.sky import native_snapshot as snapshots
    raw, _, _, _ = native_snapshot_case
    source = Table(dict(name=['synthetic'], ra_deg=[10.], dec_deg=[-20.],
                        major_axis_arcmin=[2.], minor_axis_arcmin=[1.], position_angle_deg=[30.]))
    source.meta = dict(catalog='synthetic', catalog_version='v1', coordinate_frame='ICRS',
                       coordinate_origin='solar-system-barycenter', coordinate_epoch='J2016.0',
                       coordinate_epoch_scale='tt', documentation_url='https://example.invalid/synthetic')
    for name, unit in (('ra_deg', 'deg'), ('dec_deg', 'deg'), ('major_axis_arcmin', 'arcmin'),
                       ('minor_axis_arcmin', 'arcmin'), ('position_angle_deg', 'deg')):
        source[name].unit = unit
    path = tmp_path/'synthetic.ecsv'
    source.write(path)
    profile = replace(snapshots.CANONICAL_MAXIMAL_SPHERE_PROFILE, galaxy_filename=path)
    destination = tmp_path/'known-epoch'
    snapshots.prepare_native_sky_snapshot(raw, destination, profile=profile)
    snapshot = snapshots.read_native_sky_snapshot(destination)
    galaxy = snapshot.make_sky().galaxies
    assert galaxy.catalogue_metadata.require_complete() is galaxy.catalogue_metadata
    assert galaxy.position().coordinate_spec.epoch == 'J2016.0'
    assert snapshot._records['fixed']['catalogues']['galaxies']['epoch'] == 'J2016.0'


def test_native_snapshot_retains_static_galaxy_model_without_epoch(native_snapshot_case, tmp_path):
    from dataclasses import replace
    from astropy.table import Table
    from wenu.sky import native_snapshot as snapshots
    raw, _, _, _ = native_snapshot_case
    source = Table(dict(name=['synthetic'], ra_deg=[10.], dec_deg=[-20.],
                        major_axis_arcmin=[2.], minor_axis_arcmin=[1.], position_angle_deg=[30.]))
    source.meta = dict(catalog='synthetic', catalog_version='v1', coordinate_frame='ICRS',
                       coordinate_origin='solar-system-barycenter',
                       documentation_url='https://example.invalid/synthetic')
    for name, unit in (('ra_deg', 'deg'), ('dec_deg', 'deg'), ('major_axis_arcmin', 'arcmin'),
                       ('minor_axis_arcmin', 'arcmin'), ('position_angle_deg', 'deg')):
        source[name].unit = unit
    path = tmp_path/'static-galaxy.ecsv'
    source.write(path)
    profile = replace(snapshots.CANONICAL_MAXIMAL_SPHERE_PROFILE, galaxy_filename=path)
    destination = tmp_path/'static-galaxy'
    _, cold = snapshots.prepare_native_sky_snapshot(raw, destination, profile=profile, return_sky=True)
    snapshot = snapshots.read_native_sky_snapshot(destination)
    warm = snapshot.make_sky()
    for sky in (cold, warm):
        assert sky.galaxies.admission_missing_fields == ()
        sky.galaxies.require_complete_metadata()
        points = sky.galaxies.position()
        assert points.coordinate_spec.model == 'static-direction'
        assert points.coordinate_spec.epoch is None
        assert sky.galaxies.catalogue_metadata.to_record()['epoch_scale'] is None
    _assert_native_geometry_equal(cold.galaxies.position(), warm.galaxies.position())
    assert snapshot._records['fixed']['catalogues']['galaxies']['epoch'] is None


@pytest.mark.parametrize('fault', ('missing-record', 'header-epoch', 'source-digest',
                                  'frame-conflict', 'table-metadata', 'column-unit', 'record-epoch'))
def test_native_snapshot_rejects_nonstellar_metadata_conflicts(native_snapshot_case, tmp_path, fault):
    import json
    import shutil
    from wenu.sky import native_snapshot as snapshots
    _, original, _, _ = native_snapshot_case
    destination = tmp_path/'broken-nonstellar'
    shutil.copytree(original, destination)
    manifest = json.loads((destination/'manifest.json').read_text())
    def mapping(value):
        return dict(value['mapping'])
    def change(value, key, replacement):
        for pair in value['mapping']:
            if pair[0] == key:
                pair[1] = replacement
                return
        raise AssertionError(key)
    galaxies = mapping(mapping(mapping(manifest['records'])['fixed'])['catalogues'])['galaxies']
    metadata = mapping(galaxies)['metadata']
    if fault == 'missing-record':
        galaxies['mapping'] = [pair for pair in galaxies['mapping'] if pair[0] != 'metadata']
    elif fault == 'header-epoch':
        change(galaxies, 'epoch', 'J2000.0')
    elif fault == 'source-digest':
        change(metadata, 'source_sha256', '0'*64)
    elif fault == 'frame-conflict':
        change(metadata, 'frame', 'fk5')
    elif fault == 'record-epoch':
        change(metadata, 'epoch', 'J2016.0')
    elif fault == 'table-metadata':
        table = mapping(galaxies)['table']
        raw_meta = json.loads(mapping(table)['meta_json'])
        raw_meta['coordinate_epoch'] = 'J2016.0'
        change(table, 'meta_json', json.dumps(raw_meta))
    else:
        column = mapping(mapping(mapping(galaxies)['table'])['columns'])['ra_deg']
        change(column, 'unit', 'rad')
    (destination/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        snapshots.read_native_sky_snapshot(destination)


def test_native_snapshot_requires_coverage_and_preserves_completed_bundle(native_snapshot_case):
    import hashlib
    from wenu.sky.native_snapshot import read_native_sky_snapshot, prepare_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    raw, destination, digest, _ = native_snapshot_case
    snapshot = read_native_sky_snapshot(destination)
    snapshot.require(layers=("stars", "constellation_lines"), star_magnitude_limit=6,
                     design_sha256=hashlib.sha256(raw).hexdigest())
    for kwargs in (dict(layers=("planets",)), dict(layers=("satellites",)),
                   dict(layers="stars"), dict(star_magnitude_limit=11.1),
                   dict(star_magnitude_limit=float("nan")), dict(star_magnitude_limit=True),
                   dict(design_sha256="0" * 64)):
        with pytest.raises(ValueError):
            snapshot.require(**kwargs)
    sky = snapshot.make_sky()
    with pytest.raises(ValueError):
        sky.stars.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None, magnitude_limit=12)
    with pytest.raises(ValueError):
        sky.stars.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None, include_ids={9999999})
    with pytest.raises(ValueError):
        sky.stars.spherical_geometry(None)
    before = (destination / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        prepare_native_sky_snapshot(raw, destination)
    assert (destination / "manifest.json").read_bytes() == before
    with pytest.raises(ValueError):
        read_native_sky_snapshot(destination, expected_manifest_sha256="0" * 64)
    assert snapshot.manifest_sha256 == digest


@pytest.mark.parametrize("fault", (
    "schema", "unknown", "frame", "epoch", "layer", "dtype", "shape", "checksum",
    "unsafe", "design", "record", "missing", "symlink", "evidence",
    "span", "overlap", "logical-shape", "fixed-frame", "boundary-equinox",
    "fixed-shape", "reference-equinox", "moving-content", "stellar-metadata-missing",
    "stellar-metadata-epoch", "stellar-metadata-digest", "stellar-metadata-frame", "cluster-epoch"))
def test_native_snapshot_rejects_corruption_before_use(native_snapshot_case, tmp_path, fault):
    import hashlib
    import json
    import shutil
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    _, original, _, _ = native_snapshot_case
    destination = tmp_path / "broken"
    shutil.copytree(original, destination)
    manifest = json.loads((destination / "manifest.json").read_bytes())
    if fault.startswith('stellar-metadata'):
        from wenu.sky import native_snapshot as snapshots
        decoded = snapshots.read_native_sky_snapshot(destination).stellar_metadata.to_record()
        if fault == 'stellar-metadata-missing':
            manifest['records']['mapping'] = [p for p in manifest['records']['mapping'] if p[0] != 'stellar_metadata']
        else:
            if fault == 'stellar-metadata-epoch': decoded['epoch']['value'] = 2000.
            if fault == 'stellar-metadata-digest': decoded['source_sha256'] = '0' * 64
            if fault == 'stellar-metadata-frame': decoded['frame'] = 'fk5'
            replacement = snapshots._Encoder(destination).encode(decoded)
            for pair in manifest['records']['mapping']:
                if pair[0] == 'stellar_metadata': pair[1] = replacement
    array_name = next(name for name in manifest["payloads"] if name.endswith(".npy"))
    if fault == "schema":
        manifest["schema_version"] = True
    elif fault == "unknown":
        manifest["unused"] = "ignored"
    elif fault == "frame":
        manifest["frame"] = "fk5"
    elif fault == "epoch":
        manifest["stellar_epoch"] = "J2000"
    elif fault == "layer":
        manifest["layers"].append("planets")
    elif fault == "dtype":
        manifest["payloads"][array_name]["dtype"] = "|O"
    elif fault == "shape":
        manifest["payloads"][array_name]["shape"] = [999]
    elif fault == "checksum":
        p = destination / array_name
        p.write_bytes(p.read_bytes()[:-1] + b"!")
    elif fault == "unsafe":
        manifest["payloads"]["../outside.npy"] = manifest["payloads"].pop(array_name)
    elif fault == "design":
        p = destination / "design.json"
        d = json.loads(p.read_bytes())
        d["geometry"]["coordinate_frame"] = "fk5"
        raw = json.dumps(d).encode()
        p.write_bytes(raw)
        manifest["payloads"]["design.json"] = dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    elif fault == "record":
        manifest["records"] = {"record": "os.system", "fields": {}}
    elif fault == "missing":
        (destination / array_name).unlink()
    elif fault == "symlink":
        (destination / array_name).unlink()
        (destination / array_name).symlink_to(original / array_name)
    elif fault == "evidence":
        manifest["source_digests"]["designation_curation.json"] = "0" * 64
    elif fault == "span":
        next(iter(manifest["array_index"].values()))["offset"] = 10 ** 20
    elif fault == "overlap":
        item = next(iter(manifest["array_index"].values()))
        manifest["array_index"]["data-9999"] = dict(item)
    elif fault == "logical-shape":
        next(iter(manifest["array_index"].values()))["shape"] = [True]
    elif fault in {"fixed-frame", "boundary-equinox", "fixed-shape", "reference-equinox", "moving-content", "cluster-epoch"}:
        def mapping(value):
            return {key: item for key, item in value["mapping"]}
        def change(value, key, item):
            for pair in value["mapping"]:
                if pair[0] == key:
                    pair[1] = item
                    return
            raise AssertionError(key)
        fixed = mapping(manifest["records"])["fixed"]
        catalogues = mapping(fixed)["catalogues"]
        if fault == "fixed-frame":
            change(mapping(catalogues)["galaxies"], "frame", "fk5")
        elif fault == 'cluster-epoch':
            change(mapping(catalogues)['open_clusters'], 'epoch', 'J1900.0')
        elif fault == "boundary-equinox":
            change(mapping(fixed)["boundaries"], "equinox", "B1950.0")
        elif fault == "fixed-shape":
            change(mapping(mapping(catalogues)["galaxies"])["table"], "count", -1)
        elif fault == "reference-equinox":
            change(mapping(mapping(fixed)["references"])["ecliptic_grid"], "equinox", "of_date")
        else:
            catalogues["mapping"].append(["planets", {"mapping": []}])
    (destination / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises((ValueError, TypeError)):
        read_native_sky_snapshot(destination)


def test_native_snapshot_failure_cleans_only_owned_uncommitted_output(native_snapshot_case, tmp_path, monkeypatch):
    from wenu.sky import native_snapshot as snapshots
    import os
    raw, _, _, _ = native_snapshot_case
    destination = tmp_path / "new"
    original = os.link
    calls = []
    def interrupt(source, target):
        calls.append(target)
        if len(calls) == 2:
            raise KeyboardInterrupt("simulated interruption")
        return original(source, target)
    monkeypatch.setattr(os, "link", interrupt)
    with pytest.raises(KeyboardInterrupt):
        snapshots.prepare_native_sky_snapshot(raw, destination)
    assert len(calls) == 2
    assert not destination.exists()
    assert not list(tmp_path.glob(".wenu-native-snapshot-*"))
def test_native_snapshot_publication_race_preserves_other_writer(native_snapshot_case, tmp_path, monkeypatch):
    from wenu.sky import native_snapshot as snapshots
    raw, _, _, _ = native_snapshot_case
    destination = tmp_path / "contended"
    original = snapshots.read_native_sky_snapshot
    def other_writer(*args, **kwargs):
        result = original(*args, **kwargs)
        destination.mkdir()
        (destination / "other-writer").write_bytes(b"preserve")
        return result
    monkeypatch.setattr(snapshots, "read_native_sky_snapshot", other_writer)
    with pytest.raises(FileExistsError):
        snapshots.prepare_native_sky_snapshot(raw, destination)
    assert (destination / "other-writer").read_bytes() == b"preserve"
    assert not (destination / "manifest.json").exists()
    assert not list(tmp_path.glob(".wenu-native-snapshot-*"))


def test_native_snapshot_labels_and_gaps_use_frozen_curation(native_snapshot_case, monkeypatch):
    from dataclasses import replace
    import matplotlib.pyplot as plt
    from wenu.charts import detail_application
    from wenu.charts.composition import compose_chart
    from wenu.charts.detail import DetailOverrides
    from wenu.charts.polar_planisphere import PolarPlanisphereChart
    from wenu.rendering.matplotlib import MatplotlibRenderer
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu.star_designations import StarLabelSelection
    _, destination, _, _ = native_snapshot_case
    sky = read_native_sky_snapshot(destination).make_sky()
    def forbidden(*args, **kwargs):
        raise AssertionError("A saved effective catalogue must not reload current curation")
    monkeypatch.setattr(detail_application, "load_effective_star_designations", forbidden)
    from wenu import stellar_research
    monkeypatch.setattr(stellar_research, "load_stellar_research", forbidden)
    face = PolarPlanisphereChart(pole="south", projection_name="stereographic")
    composition = compose_chart(face, style="cartoon", mode="print",
        detail_overrides=DetailOverrides(star_magnitude_limit=5,
            enabled_layers=frozenset({"stars", "constellation_lines"}),
            star_labels=StarLabelSelection(names=("Sco:Antares",), bayer=("Sco:beta1",))))
    composition = replace(composition, style=replace(composition.style,
        grids=replace(composition.style.grids, constellation_line_gap_points=1)))
    options = composition.layer_options(sky).layer_options
    from wenu.sky.native_snapshot import _CATALOGUES
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    for name in _CATALOGUES:
        layer = getattr(sky, name)
        identifier = str(layer.realize(context, None).ids[0])
        options[layer] = {"geometry": {"selected": (identifier,)}}
    options[sky.constellation_boundaries] = {"geometry": {"selected": ("Sco", "Lib")}}
    for layer in sky.layers:
        if layer.layer_name in {"coordinates_grid", "celestial_points"}:
            options[layer] = {}
    figure, ax = plt.subplots(figsize=(3, 3))
    try:
        result = face.render(sky, MatplotlibRenderer(ax), style=composition.style,
            layer_options=options,
            realization_context=LayerRealizationContext(NATIVE_ICRS_SPEC))
        labels = {text.get_text() for text in ax.texts}
        assert "Antares" in labels and any("β" in text for text in labels)
        assert result is not None
    finally:
        plt.close(figure)


@pytest.mark.parametrize("name", ("nonstellar", "galaxies", "open_clusters", "globular_clusters", "supernova_remnants", "planetary_nebulae"))
def test_native_snapshot_fixed_catalogue_rows_masks_units_and_subsets(native_snapshot_case, name):
    import numpy as np
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    _, destination, _, cold = native_snapshot_case
    warm = read_native_sky_snapshot(destination).make_sky()
    first, second = getattr(cold, name), getattr(warm, name)
    left = first.catalog if name == "open_clusters" else first.source_catalog
    right = second.catalog if name == "open_clusters" else second.source_catalog
    assert len(left) == len(right) and left.colnames == right.colnames
    assert left.meta == right.meta
    for column in left.colnames:
        assert left[column].unit == right[column].unit
        assert left[column].description == right[column].description
        np.testing.assert_array_equal(np.ma.getmaskarray(left[column]), np.ma.getmaskarray(right[column]))
        a, b = np.asarray(left[column]), np.asarray(right[column])
        if a.dtype.kind == "O":
            for x, y in zip(a, b, strict=True):
                assert (isinstance(x, float) and np.isnan(x) and isinstance(y, float) and np.isnan(y)) or x == y
        else:
            np.testing.assert_array_equal(a, b)
    identifier = str(first.catalog["identifier"][0])
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    options = dict(selected=(identifier,))
    if name not in {"open_clusters", "planetary_nebulae"}:
        options["samples"] = 12
    _assert_native_geometry_equal(first.realize(context, None, **options), second.realize(context, None, **options))
    assert not warm.solar_system_bodies and warm.moon is None


@pytest.mark.parametrize('version', (1, 2, 3, 4))
def test_native_snapshot_legacy_coverage_stays_truthful(native_snapshot_case, tmp_path, version):
    import json
    import shutil
    from wenu.sky import native_snapshot as snapshots
    _, original, _, _ = native_snapshot_case
    directory = tmp_path / "legacy-v1"
    shutil.copytree(original, directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    manifest["schema_version"] = version
    manifest["compatibility"] = {1: snapshots.LEGACY_COMPATIBILITY,
        2: snapshots.PRE_METADATA_COMPATIBILITY, 3: snapshots.PRE_CLUSTER_METADATA_COMPATIBILITY,
        4: snapshots.PRE_NONSTELLAR_METADATA_COMPATIBILITY}[version]
    manifest["layers"] = list(snapshots.LEGACY_LAYERS if version == 1 else snapshots.LAYERS)
    removed = {'stellar_metadata', 'fixed'} if version == 1 else {'stellar_metadata'} if version == 2 else set()
    manifest["records"]["mapping"] = [pair for pair in manifest["records"]["mapping"] if pair[0] not in removed]
    if version == 1:
        for key in (*snapshots._CATALOGUES, "iau_boundaries"):
            del manifest["source_digests"][key]
    else:
        fixed = dict(manifest['records']['mapping'])['fixed']
        catalogues = dict(dict(fixed['mapping'])['catalogues']['mapping'])
        for name, content in catalogues.items():
            content['mapping'] = [pair for pair in content['mapping'] if pair[0] != 'metadata']
            if name != 'open_clusters' or version < 4:
                for pair in content['mapping']:
                    if pair[0] == 'epoch': pair[1] = 'J2000.0'
    (directory / "manifest.json").write_text(json.dumps(manifest))
    legacy = snapshots.read_native_sky_snapshot(directory)
    legacy.require()
    if version == 1:
        with pytest.raises(ValueError):
            legacy.require(layers=("galaxies",))
    else:
        legacy.require(layers=('galaxies',))
    sky = legacy.make_sky()
    if version == 1:
        assert sky.galaxies is None and sky.constellation_boundaries is None
    else:
        assert sky.galaxies is not None and sky.constellation_boundaries is not None
        assert sky.open_clusters.position().coordinate_spec.epoch is None
        assert sky.galaxies.position().coordinate_spec.epoch is None
        assert sky.galaxies.catalogue_metadata.to_record()['source_sha256'] is None
        assert 'source_sha256' in sky.galaxies.catalogue_metadata.missing_fields
    assert sky.stars.catalogue_metadata.epoch_label == manifest['stellar_epoch']


def test_atlas_chart_batch_cold_saved_and_spawned_pages_match(native_snapshot_case, tmp_path, monkeypatch):
    import hashlib
    import json
    from pathlib import Path
    import numpy as np
    from matplotlib.image import imread
    from pypdf import PdfReader
    from pypdf import PdfWriter
    original_stream = PdfWriter._create_stream
    def complete_stream(writer, source):
        # Raw paths can produce short reads on virtual/network filesystems.
        if isinstance(source, (str, Path)):
            raise OSError('simulated short raw PDF read')
        return original_stream(writer, source)
    monkeypatch.setattr(PdfWriter, '_create_stream', complete_stream)

    from wenu.charts.atlas_publication import AtlasChartPresentation, create_atlas
    from wenu.sky import native_snapshot
    from wenu.atlas_design import AtlasBandTiling
    raw, bundle, digest, cold = native_snapshot_case
    design = tmp_path/'design.json'
    design.write_bytes(raw)
    presentation = AtlasChartPresentation(dpi=36, formats=('png', 'pdf', 'svg'))
    calls = []
    original = native_snapshot.generate_native_icrs_sphere
    def counted(**kwargs):
        calls.append(1)
        return original(**kwargs)
    monkeypatch.setattr(native_snapshot, 'generate_native_icrs_sphere', counted)
    first = create_atlas(design, tmp_path/'cold', presentation=presentation,
                         charts='10,14', jobs=1, save_sky=tmp_path/'saved')
    assert calls == [1]
    def forbidden(*args, **kwargs):
        raise AssertionError('Saved reuse must not prepare a sphere')
    monkeypatch.setattr(native_snapshot, 'prepare_native_sky_snapshot', forbidden)
    import matplotlib.pyplot as plt
    index = tmp_path/'index.pdf'
    figure = plt.figure(figsize=(14,8))
    figure.text(0.5,0.5,'Synthetic atlas index',ha='center')
    for suffix in ('pdf', 'png', 'svg'):
        figure.savefig(index.with_suffix('.' + suffix))
    plt.close(figure)
    index_before = index.read_bytes()
    for mode, jobs in (('serial', 1), ('spawn', 2)):
        if mode == 'serial':
            from wenu.cli.atlas import create_main
            config = tmp_path/'presentation.toml'
            config.write_text('schema_version = 1\ndocument_kind = "wenu-atlas-chart-presentation"\ndpi = 36\nstar_magnitude_limit = 4.0\n')
            assert create_main(['--design',str(design),'--config',str(config),
                '--charts','14,10','--jobs','1','--from-sky',str(tmp_path/'saved'),
                '--magnitude-limit','6',
                '--output-dir',str(tmp_path/mode),'--index',str(index)]) == 0
            manifest = tmp_path/mode/'manifest.json'
        else:
            manifest = create_atlas(design, tmp_path/mode, presentation=presentation,
                                   charts='14,10', jobs=jobs, from_sky=tmp_path/'saved', index=index)
        data = json.loads(manifest.read_text())
        assert data['charts'] == [10, 14] and data['workers'] == jobs
        book = PdfReader(manifest.parent/'atlas.pdf')
        assert book.page_layout == '/TwoPageLeft'
        assert len(book.pages) == 9
        assert 'Synthetic atlas index' in book.pages[0].extract_text()
        assert data['report_content'] == 'reserved'
        assert data['index_sha256'] == hashlib.sha256(index_before).hexdigest()
        assert data['page_order'] == [dict(page=1,kind='index'),
            dict(page=2,kind='blank'),
            dict(page=3,kind='report',chart=10),dict(page=4,kind='chart',chart=10),
            dict(page=5,kind='report',chart=14),dict(page=6,kind='chart',chart=14),
            dict(page=7,kind='stellar_sizing_report'), dict(page=8,kind='stellar_area_budget'),
            dict(page=9,kind='catalogue_star_counts')]
        assert not book.pages[1].extract_text().strip()
        for suffix in ('pdf', 'png', 'svg'):
            assert (manifest.parent/f'atlas-index.{suffix}').read_bytes() == index.with_suffix('.'+suffix).read_bytes()
        assert 'Atlas catalogue star counts' in book.pages[-1].extract_text()
        assert book.outline[-1].title == 'Catalogue star counts'
        assert book.get_destination_page_number(book.outline[-1]) == 8
        counts = json.loads((manifest.parent/'atlas-star-counts.json').read_text())
        assert counts['magnitude_limit'] == 6
        assert counts['provenance'] == dict(design_sha256=data['design_sha256'],
                                            snapshot_sha256=data['snapshot_sha256'])
        for suffix in ('png', 'pdf', 'svg', 'json'):
            assert f'atlas-star-counts.{suffix}' in data['products']
        for filename in ('atlas-star-counts.json', 'atlas-star-counts_catalogue.csv'):
            assert (manifest.parent/filename).read_bytes() == (tmp_path/'cold'/filename).read_bytes()
        np.testing.assert_array_equal(imread(tmp_path/'cold'/'atlas-star-counts.png'),
                                      imread(manifest.parent/'atlas-star-counts.png'))
        for position, number in ((2,10),(4,14)):
            text = book.pages[position].extract_text()
            assert f'Chart {number}' in text and 'Object report' in text
            assert 'Reserved for the object report' in text
            report = json.loads((manifest.parent/f'chart-{number:02d}_report_data.json').read_text())
            visible_count = report['stars']['statistics']['visible_count']
            assert f'Star magnitude ({visible_count:,})' in text
            assert 'Centre: ICRS' in text and 'RA' in text and 'Dec' in text
            chart_text = book.pages[position+1].extract_text()
            assert str(number) in chart_text.splitlines()
            assert f'Chart {number}' not in chart_text
        atlas = AtlasBandTiling.from_json(raw.decode())
        page = atlas.geometry.page
        for number in (10,14):
            report = json.loads((manifest.parent/f'chart-{number:02d}_report_data.json').read_text())
            assert report['design_sha256'] == data['design_sha256']
            assert report['snapshot_sha256'] == data['snapshot_sha256']
            assert report['presentation'] == data['presentation']
            statistics = report['stars']['statistics']
            assert report['stars']['reference_range'][0] <= statistics['brightest_magnitude']
            for suffix in presentation.formats:
                assert (manifest.parent/f'chart-{number:02d}_report.{suffix}').is_file()
            np.testing.assert_array_equal(imread(tmp_path/'cold'/f'chart-{number:02d}.png'),
                                          imread(manifest.parent/f'chart-{number:02d}.png'))
            media = PdfReader(manifest.parent/f'chart-{number:02d}.pdf').pages[0].mediabox
            np.testing.assert_allclose([float(media.width),float(media.height)],
                                      [page.width_mm*72/25.4,page.height_mm*72/25.4])
        for pdf_page in book.pages:
            np.testing.assert_allclose([float(pdf_page.mediabox.width),float(pdf_page.mediabox.height)],
                                      [page.width_mm*72/25.4,page.height_mm*72/25.4])
            assert pdf_page.rotation == 0
    assert calls == [1]
    assert index.read_bytes() == index_before
    with pytest.raises(ValueError):
        create_atlas(design, tmp_path/'cold', presentation=presentation, from_sky=tmp_path/'saved')
    assert design.read_bytes() == raw


def test_atlas_chart_batch_failure_preserves_saved_data(native_snapshot_case, tmp_path, monkeypatch):
    from wenu.charts import atlas_publication as owner
    raw, bundle, digest, _ = native_snapshot_case
    design = tmp_path/'design.json'; design.write_bytes(raw)
    before = (bundle/'manifest.json').read_bytes()
    def broken(*args, **kwargs):
        raise RuntimeError('Chart 14 injected render failure')
    monkeypatch.setattr(owner, '_render_atlas_sheet', broken)
    with pytest.raises(RuntimeError, match='Chart 14'):
        owner.create_atlas(design, tmp_path/'failed', presentation=owner.AtlasChartPresentation(),
                           charts='14', jobs=1, from_sky=bundle)
    assert not (tmp_path/'failed').exists()
    assert not list(tmp_path.glob('.wenu-atlas-pages-*'))
    assert (bundle/'manifest.json').read_bytes() == before


def test_atlas_chart_batch_publication_race_preserves_other_writer(native_snapshot_case, tmp_path, monkeypatch):
    from pathlib import Path
    from pypdf import PdfWriter
    from wenu.charts import atlas_publication as owner
    raw, bundle, _, _ = native_snapshot_case
    design = tmp_path/'design.json'; design.write_bytes(raw)
    output = tmp_path/'contended'
    def page(task, sky=None):
        import json
        sheet, _, _, directory = task
        with PdfWriter() as writer:
            writer.add_blank_page(width=72,height=72)
            writer.write(Path(directory)/f'chart-{sheet.number:02d}.pdf')
        (Path(directory)/f'chart-{sheet.number:02d}_report_data.json').write_text(json.dumps({'stellar_sizing': record}))
        return sheet.number
    # This test owns atomic publication, not diagnostic SVG measurement.
    def diagnostic(*args, **kwargs):
        directory = Path(args[1]).parent
        with PdfWriter() as writer:
            writer.add_blank_page(width=72, height=72)
            writer.write(directory/'stellar-sizing-report.pdf')
    from wenu.charts import stellar_sizing_report
    monkeypatch.setattr(stellar_sizing_report, 'analyze', diagnostic)
    from wenu.charts.presets import AtlasChartStyle
    record = stellar_sizing_report.resolved_sizing_record(AtlasChartStyle().stars, 6)
    original = PdfWriter.write
    def race(self, destination):
        result = original(self, destination)
        if Path(destination).name == 'atlas.pdf':
            output.mkdir()
            (output/'other-writer').write_text('preserve')
            assert output.is_dir()
        return result
    monkeypatch.setattr(owner, '_render_atlas_sheet', page)
    monkeypatch.setattr(PdfWriter, 'write', race)
    with pytest.raises(FileExistsError):
        owner.create_atlas(design, output, presentation=owner.AtlasChartPresentation(formats=('pdf',)),
                           charts='14', jobs=1, from_sky=bundle)
    assert (output/'other-writer').read_text() == 'preserve'
    assert not (output/'manifest.json').exists()
    assert not list(tmp_path.glob('.wenu-atlas-pages-*'))



def test_kernel_native_stars_preserve_legacy_page_pixels(native_snapshot_case, tmp_path, monkeypatch):
    """Same canonical renderer; compare accepted raw native rows with kernel access."""
    import numpy as np
    from matplotlib.image import imread
    from wenu.atlas_design import AtlasBandTiling
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu.charts.request_generation import AtlasSheetChartRequest, generate_chart_request
    from wenu.objects.stars import Stars

    raw, _, _, sky = native_snapshot_case
    atlas = AtlasBandTiling.from_json(raw.decode())
    sheet = atlas.geometry.sheets[13]
    presentation = AtlasChartPresentation(layers=('stars', 'constellation_lines'),
        star_magnitude_limit=6, formats=('png', 'pdf'), dpi=72)

    def legacy_native_rows(self, catalog):
        # Exact source-table route replaced by the first kernel adapter.
        return (catalog['ra_degrees'].to_numpy(dtype=float),
                catalog['dec_degrees'].to_numpy(dtype=float))

    with monkeypatch.context() as baseline:
        baseline.setattr(Stars, '_native_catalogue_coordinates', legacy_native_rows)
        generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
            presentation, tmp_path/'legacy'), sky=sky)
    generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
        presentation, tmp_path/'kernel'), sky=sky)
    name = f'chart-{sheet.number:02d}.png'
    np.testing.assert_array_equal(imread(tmp_path/'legacy'/name), imread(tmp_path/'kernel'/name))


@pytest.mark.parametrize('layout', ('polar', 'regional', 'hemisphere'))
def test_native_atlas_page_layout_is_independent_of_display_dpi(native_snapshot_case, tmp_path, layout):
    """HiDPI display scaling cannot change exported native grid-label placement."""
    import matplotlib
    from matplotlib.image import imread
    import numpy as np
    import xml.etree.ElementTree as ET
    from pathlib import Path
    from wenu.atlas_design import AtlasBandTiling, AtlasDesignRequest
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu.charts.request_generation import AtlasSheetChartRequest, generate_chart_request

    raw, _, _, sky = native_snapshot_case
    atlas = AtlasBandTiling.from_json(raw.decode())
    sheet = atlas.geometry.sheets[0 if layout == 'polar' else 9]
    if layout == 'hemisphere':
        import tomllib
        source = Path(__file__).resolve().parents[1] / 'examples/atlas_design_hemispheres_v1.toml'
        atlas = AtlasDesignRequest.from_dict(tomllib.loads(source.read_text())).resolve()
        sheet = atlas.geometry.sheets[0]
    presentation = AtlasChartPresentation(layers=('equatorial_grid',),
        chart_legend_visible=False, dpi=36, formats=('png', 'pdf', 'svg'))
    outputs = []
    for ambient_dpi in (100, 200):
        directory = tmp_path / str(ambient_dpi)
        with matplotlib.rc_context({'figure.dpi': ambient_dpi}):
            generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
                presentation, directory), sky=sky)
        outputs.append(directory / f'chart-{sheet.number:02d}')

    def grid_labels(path):
        return tuple((text.text, text.get('x'), text.get('y'), text.get('transform'))
            for text in ET.parse(path).getroot().iter()
            if text.tag.endswith('}text') and text.get('data-wenu-layer') == 'equatorial_grid_labels')
    assert grid_labels(outputs[0].with_suffix('.svg'))
    assert grid_labels(outputs[0].with_suffix('.svg')) == grid_labels(outputs[1].with_suffix('.svg'))
    np.testing.assert_array_equal(imread(outputs[0].with_suffix('.png')),
                                  imread(outputs[1].with_suffix('.png')))


def test_kernel_galaxy_routes_preserve_accepted_atlas_pixels(native_snapshot_case, tmp_path, monkeypatch):
    from matplotlib.image import imread
    from wenu.atlas_design import AtlasBandTiling
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu.charts.request_generation import AtlasSheetChartRequest, generate_chart_request
    from wenu.objects.galaxies import Galaxies
    from wenu.objects.nonstellar import NonStellar
    import numpy as np
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    raw, destination, _, sky = native_snapshot_case
    saved = read_native_sky_snapshot(destination).make_sky()
    for layer in (sky.galaxies, saved.galaxies):
        layer.require_catalogue_lookup_metadata()
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    for options in (dict(selected=["NGC5128"]), dict(selected=["NGC5128"], labels_only=True)):
        _assert_native_geometry_equal(sky.galaxies.realize(context, None, **options),
                                      saved.galaxies.realize(context, None, **options))
    atlas = AtlasBandTiling.from_json(raw.decode())
    identifier = atlas.primary_sheet_id(201.365, -43.019)
    sheet = next(sheet for sheet in atlas.geometry.sheets if sheet.sheet_id == identifier)
    presentation = AtlasChartPresentation(layers=('galaxies',), formats=('png', 'pdf', 'svg'), dpi=36)
    with monkeypatch.context() as baseline:
        baseline.setattr(Galaxies, '_native_centres', NonStellar._native_centres)
        generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
            presentation, tmp_path/'legacy-galaxies'), sky=sky)
    generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
        presentation, tmp_path/'kernel-galaxies'), sky=sky)
    generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
        presentation, tmp_path/'saved-galaxies'), sky=saved)
    name = f'chart-{sheet.number:02d}.png'
    np.testing.assert_array_equal(imread(tmp_path/'legacy-galaxies'/name),
                                  imread(tmp_path/'kernel-galaxies'/name))

    np.testing.assert_array_equal(imread(tmp_path/'kernel-galaxies'/name),
                                  imread(tmp_path/'saved-galaxies'/name))


def test_kernel_cluster_routes_preserve_native_pixels_and_saved_state(native_snapshot_case, tmp_path, monkeypatch):
    from matplotlib.image import imread
    from wenu.atlas_design import AtlasBandTiling
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu.charts.request_generation import AtlasSheetChartRequest, generate_chart_request
    from wenu.objects.open_clusters import OpenClusters
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu_kernel import KernelSession
    import numpy as np
    raw, destination, _, cold = native_snapshot_case
    warm = read_native_sky_snapshot(destination).make_sky()
    first, second = cold.open_clusters, warm.open_clusters
    assert first.catalogue_metadata_for(first.catalog) == second.catalogue_metadata_for(second.catalog)
    # Check actual saved source-bound provider use, not only restored source columns.
    seen = []
    evaluate = KernelSession.evaluate
    def capture(session, query):
        result = evaluate(session, query)
        if query.reference.status == 'catalogue-lookup':
            seen.append(result)
        return result
    monkeypatch.setattr(KernelSession, 'evaluate', capture)
    np.testing.assert_array_equal(first.position().lon_deg, second.position().lon_deg)
    assert len(seen) == 2 and seen[0].query == seen[1].query
    assert all(row.source_epoch is None for result in seen for row in result.states)
    atlas = AtlasBandTiling.from_json(raw.decode())
    row = first.catalog[0]
    identifier = atlas.primary_sheet_id(float(row['ra_deg']), float(row['dec_deg']))
    sheet = next(sheet for sheet in atlas.geometry.sheets if sheet.sheet_id == identifier)
    presentation = AtlasChartPresentation(layers=('open_clusters',), formats=('png', 'pdf', 'svg'), dpi=36)
    def legacy(self, table, instant=None, **options):
        return np.asarray(table['ra_deg'], dtype=float), np.asarray(table['dec_deg'], dtype=float)
    with monkeypatch.context() as baseline:
        baseline.setattr(OpenClusters, '_native_centres', legacy)
        generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
            presentation, tmp_path/'legacy-clusters'), sky=cold)
    for name, sky in (('cold-clusters', cold), ('saved-clusters', warm)):
        generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
            presentation, tmp_path/name), sky=sky)
        output = f'chart-{sheet.number:02d}.png'
        np.testing.assert_array_equal(imread(tmp_path/'legacy-clusters'/output), imread(tmp_path/name/output))


def test_native_snapshot_explicit_cluster_motion_matches_cold_geometry_and_pixels(native_snapshot_case, monkeypatch):
    # Closest native fixed-catalogue subset and pixel tests remain unchanged.
    # Protect a saved-source bypass, mutable model installation and product guard.
    from pathlib import Path
    import numpy as np
    import matplotlib.pyplot as plt
    from wenu.cluster_state import load_cluster_motion
    from wenu_kernel.records import TimePoint, TimeSpan
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu.projections import StereographicProjection
    from wenu.rendering import MatplotlibRenderer
    from wenu.objects.open_clusters import OpenClusters
    _, destination, _, cold = native_snapshot_case
    snapshot = read_native_sky_snapshot(destination)
    saved = snapshot.make_sky()
    root = Path(__file__).resolve().parents[1]/'src/wenu/data/catalogs/open_clusters'
    motion = load_cluster_motion(root/'open_clusters_hunt_astrometry_v1.ecsv',
        root/'open_clusters_hunt_motion_admission_v1.json',
        coverage=TimeSpan(TimePoint(2400000,0,'tcb'), TimePoint(2500000,0,'tcb')))
    selected = [row.identifier for row in motion.rows if row.unavailable_reason is None][:3]
    context = LayerRealizationContext(NATIVE_ICRS_SPEC,
        evaluation_instant='J2050.0', evaluation_time_scale='tcb')
    def forbidden(*args, **kwargs):
        raise AssertionError('Restored consumer must not reload the selected catalogue')
    monkeypatch.setattr(OpenClusters, 'load', forbidden)
    options = dict(selected=selected, motion=motion)
    a = cold.open_clusters.realize(context, None, **options)
    b = saved.open_clusters.realize(context, None, **options)
    _assert_native_geometry_equal(a, b)
    plain = LayerRealizationContext(NATIVE_ICRS_SPEC)
    # Static neighbouring layers retain source semantics, despite the requested epoch.
    for name in ('stars','galaxies','globular_clusters','constellation_lines'):
        layer = getattr(saved, name)
        _assert_native_geometry_equal(layer.realize(plain,None), layer.realize(context,None))
    images=[]
    for sky in (cold, saved):
        configured = {layer: {'enabled': False} for layer in sky.layers}
        configured[sky.open_clusters] = {'geometry': options}
        figure, ax = plt.subplots(figsize=(3,3), dpi=100)
        try:
            result = sky.draw_chart(projection=StereographicProjection(), renderer=MatplotlibRenderer(ax),
                realization_context=context, layer_options=configured)
            assert result is not None
            figure.canvas.draw()
            images.append(np.asarray(figure.canvas.buffer_rgba()).copy())
        finally:
            plt.close(figure)
    np.testing.assert_array_equal(*images)
    restored = snapshot.make_sky()
    assert restored.open_clusters.selected is None
    assert restored.open_clusters.position().metadata['catalogue_position_model'] == 'catalogue_lookup'
    # Requested model data never replace the saved source rows or v5 header.
    assert snapshot._manifest['schema_version'] == 5
    assert saved.open_clusters.catalogue_metadata_for(saved.open_clusters.catalog) == cold.open_clusters.catalogue_metadata_for(cold.open_clusters.catalog)


def test_native_snapshot_explicit_cluster_motion_in_fresh_process(native_snapshot_case, tmp_path):
    import os, subprocess, sys
    from pathlib import Path
    _, destination, _, _ = native_snapshot_case
    root = Path(__file__).resolve().parents[1]
    code = r"""
from pathlib import Path
import socket, sys
from wenu.cluster_state import load_cluster_motion
from wenu_kernel.records import TimePoint, TimeSpan
from wenu.sky.native_snapshot import read_native_sky_snapshot
from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
from wenu.objects.open_clusters import OpenClusters
def forbidden(*args, **kwargs):
    raise AssertionError('No source catalogue loading or network during saved consumption')
OpenClusters.load = forbidden
socket.socket = forbidden
root = Path(sys.argv[2])/'src/wenu/data/catalogs/open_clusters'
motion = load_cluster_motion(root/'open_clusters_hunt_astrometry_v1.ecsv',
    root/'open_clusters_hunt_motion_admission_v1.json',
    coverage=TimeSpan(TimePoint(2400000,0,'tcb'),TimePoint(2500000,0,'tcb')))
sky = read_native_sky_snapshot(sys.argv[1]).make_sky()
selected = [row.identifier for row in motion.rows if row.unavailable_reason is None][:3]
context = LayerRealizationContext(NATIVE_ICRS_SPEC,evaluation_instant='J2050.0',evaluation_time_scale='tcb')
result = sky.open_clusters.realize(context,None,motion=motion,selected=selected)
assert result.ids.tolist() == selected
assert result.coordinate_spec.instant == 'J2050.0'
assert len(result.metadata['cluster_motion_states']) == 3
assert sky.open_clusters.position().metadata['catalogue_position_model'] == 'catalogue_lookup'
"""
    env = dict(os.environ, PYTHONPATH=str(root/'src'))
    completed = subprocess.run([sys.executable,'-c',code,str(destination),str(root)],
        cwd=tmp_path, env=env, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr


def _saved_cluster_observation(root):
    """Prepare explicit offline per-process resources; nothing saved as state."""
    from pathlib import Path
    from hashlib import sha256
    from astropy.utils import iers
    from wenu.astrometric_observation import ErfaReceptionBackend, reception_backend_identity
    from wenu.cluster_state import load_cluster_motion
    from wenu.sky.realization import LayerRealizationContext
    from wenu_kernel.records import TimePoint, TimeSpan
    backend = ErfaReceptionBackend(leap_seconds_path=iers.IERS_LEAP_SECOND_FILE,
        leap_seconds_sha256=sha256(Path(iers.IERS_LEAP_SECOND_FILE).read_bytes()).hexdigest(),
        eop_path=iers.IERS_B_FILE, eop_sha256=sha256(Path(iers.IERS_B_FILE).read_bytes()).hexdigest(),
        coverage=TimeSpan(TimePoint(2456300,0,'tt'),TimePoint(2458000,0,'tt')),
        backend_identity=reception_backend_identity())
    context = LayerRealizationContext.from_reception(backend.prepare('2016-12-31T23:59:60Z',
        longitude_deg=-71.23,latitude_deg=-32.44,height_m=52.))
    data = Path(root)/'src/wenu/data/catalogs/open_clusters'
    motion = load_cluster_motion(data/'open_clusters_hunt_astrometry_v1.ecsv',
        data/'open_clusters_hunt_motion_admission_v1.json',
        coverage=TimeSpan(TimePoint(2400000,0,'tcb'),TimePoint(2500000,0,'tcb')))
    return context, motion


def test_saved_cluster_observation_cold_saved_pixels_and_public_output(native_snapshot_case, tmp_path, monkeypatch):
    # Closest native snapshot motion test; protect a restored-source bypass,
    # changed projection units, missing actual output and persisted context.
    from pathlib import Path
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.objects.open_clusters import OpenClusters
    from wenu.projections import StereographicProjection
    from wenu.rendering import MatplotlibRenderer
    import matplotlib.pyplot as plt
    import numpy as np
    _, destination, _, cold = native_snapshot_case
    snapshot = read_native_sky_snapshot(destination)
    saved = snapshot.make_sky()
    context, motion = _saved_cluster_observation(Path(__file__).resolve().parents[1])
    selected = [row.identifier for row in motion.rows if row.unavailable_reason is None][:3]
    options = dict(motion=motion, selected=selected)
    original_record = saved.open_clusters.catalogue_metadata_for(saved.open_clusters.catalog)
    def forbidden(*args, **kwargs):
        raise AssertionError('No reload or legacy observation in restored motion route')
    monkeypatch.setattr(OpenClusters, 'load', forbidden)
    monkeypatch.setattr(OpenClusters, 'spherical_geometry', forbidden)
    geometries = [sky.open_clusters.realize(context, None, **options) for sky in (cold,saved)]
    _assert_native_geometry_equal(*geometries)
    images = []
    for index, sky in enumerate((cold,saved)):
        configured = {layer: {'enabled': False} for layer in sky.layers}
        configured[sky.open_clusters] = {'geometry': options}
        figure, ax = plt.subplots(figsize=(3,3), dpi=100)
        try:
            sky.draw_chart(projection=StereographicProjection(), renderer=MatplotlibRenderer(ax),
                realization_context=context, layer_options=configured)
            figure.canvas.draw()
            images.append(np.asarray(figure.canvas.buffer_rgba()).copy())
            output = tmp_path/f'observed-{index}.svg'
            figure.savefig(output)
            assert '<path' in output.read_text() and output.stat().st_size > 1000
        finally:
            plt.close(figure)
    np.testing.assert_array_equal(*images)
    assert np.any(images[0][:,:,:3] < 200)
    assert snapshot._manifest['schema_version'] == 5
    assert saved.open_clusters.catalogue_metadata_for(saved.open_clusters.catalog) == original_record
    assert snapshot.make_sky().open_clusters.position().metadata['catalogue_position_model'] == 'catalogue_lookup'


def test_saved_cluster_observation_fresh_process(native_snapshot_case, tmp_path):
    import inspect, json, os, subprocess, sys
    from pathlib import Path
    _, destination, _, _ = native_snapshot_case
    root = Path(__file__).resolve().parents[1]
    context, motion = _saved_cluster_observation(root)
    selected = [row.identifier for row in motion.rows if row.unavailable_reason is None][:3]
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    expected = read_native_sky_snapshot(destination).make_sky().open_clusters.realize(
        context,None,motion=motion,selected=selected)
    code = inspect.getsource(_saved_cluster_observation) + r'''
import json,socket,sys
from wenu.sky.native_snapshot import read_native_sky_snapshot
from wenu.objects.open_clusters import OpenClusters
from wenu.projections import StereographicProjection
from wenu.rendering import MatplotlibRenderer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def forbidden(*args,**kwargs):
    raise AssertionError('No network/catalogue reload/legacy observer')
socket.socket=forbidden
OpenClusters.load=forbidden
OpenClusters.spherical_geometry=forbidden
context,motion=_saved_cluster_observation(sys.argv[2])
sky=read_native_sky_snapshot(sys.argv[1]).make_sky()
selected=[r.identifier for r in motion.rows if r.unavailable_reason is None][:3]
options=dict(motion=motion,selected=selected)
geometry=sky.open_clusters.realize(context,None,**options)
configured={layer:{'enabled':False} for layer in sky.layers}
configured[sky.open_clusters]={'geometry':options}
figure,ax=plt.subplots()
sky.draw_chart(projection=StereographicProjection(),renderer=MatplotlibRenderer(ax),
    realization_context=context,layer_options=configured)
figure.savefig(sys.argv[3])
plt.close(figure)
print(json.dumps(dict(lon=geometry.lon_deg.tolist(),lat=geometry.lat_deg.tolist(),ids=geometry.ids.tolist())))
'''
    output = tmp_path/'fresh-observed.svg'
    completed = subprocess.run([sys.executable,'-c',code,str(destination),str(root),str(output)],
        cwd=tmp_path, env=dict(os.environ,PYTHONPATH=str(root/'src')),text=True,capture_output=True)
    assert completed.returncode == 0, completed.stdout+completed.stderr
    result = json.loads(completed.stdout)
    assert result == dict(lon=expected.lon_deg.tolist(),lat=expected.lat_deg.tolist(),ids=selected)
    assert output.stat().st_size > 1000


def test_native_label_kernel_route_preserves_cold_saved_anchors_and_page_pixels(native_snapshot_case, tmp_path, monkeypatch):
    """Compare the previous raw anchor inputs with public kernel positions."""
    import numpy as np
    from matplotlib.image import imread
    from wenu.atlas_design import AtlasBandTiling
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu.charts.request_generation import AtlasSheetChartRequest, generate_chart_request
    from wenu.geometry.spherical import SphericalPoints
    from wenu.objects.stars import Stars
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    raw, destination, _, cold = native_snapshot_case
    saved = read_native_sky_snapshot(destination).make_sky()
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    query = Stars.native_positions
    def previous_anchor_inputs(self, identifiers=None):
        if identifiers is not None:
            return query(self, identifiers)
        source = self.source_catalog
        return SphericalPoints(lon_deg=source['ra_degrees'].to_numpy(dtype=float),
            lat_deg=source['dec_degrees'].to_numpy(dtype=float),
            coordinate_spec=query(self, ()).coordinate_spec)
    with monkeypatch.context() as baseline:
        baseline.setattr(Stars, 'native_positions', previous_anchor_inputs)
        previous = cold.constellation_labels.realize(context, None)
    current = cold.constellation_labels.realize(context, None)
    _assert_native_geometry_equal(previous, current)
    _assert_native_geometry_equal(current, saved.constellation_labels.realize(context, None))
    atlas = AtlasBandTiling.from_json(raw.decode())
    sheet = atlas.geometry.sheets[13]
    presentation = AtlasChartPresentation(layers=('stars', 'constellation_lines', 'constellation_labels'),
        star_magnitude_limit=6, formats=('png', 'pdf'), dpi=72)
    with monkeypatch.context() as baseline:
        baseline.setattr(Stars, 'native_positions', previous_anchor_inputs)
        generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
            presentation, tmp_path/'legacy-labels'), sky=cold)
    for name, sky in (('kernel-labels', cold), ('saved-labels', saved)):
        generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
            presentation, tmp_path/name), sky=sky)
        filename = f'chart-{sheet.number:02d}.png'
        np.testing.assert_array_equal(imread(tmp_path/'legacy-labels'/filename), imread(tmp_path/name/filename))


def test_restored_galaxy_warm_routes_do_not_hide_kernel_refusal(native_snapshot_case, monkeypatch):
    from astropy.coordinates import AltAz, EarthLocation
    from astropy.time import Time
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu_kernel import KernelSession
    _, destination, _, _ = native_snapshot_case
    layer = read_native_sky_snapshot(destination).make_sky().galaxies
    original = layer.catalogue_metadata.to_record()
    assert layer.require_catalogue_lookup_metadata().to_record() == original
    observer = SimpleNamespace(altaz_frame=AltAz(obstime=Time('2026-08-16T01:00:00'),
        location=EarthLocation.from_geodetic(-71.5, -33., 52.)))
    selected = ['NGC5128']
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    layer.spherical_centers(observer, selected=selected)
    layer.spherical_geometry(observer, selected=selected, samples=12)
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic restored galaxy refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    for action in (lambda: layer.position(),
                   lambda: layer.realize(context, None, selected=selected),
                   lambda: layer.realize(context, None, selected=selected, labels_only=True),
                   lambda: layer.spherical_centers(observer, selected=selected),
                   lambda: layer.spherical_geometry(observer, selected=selected, samples=12)):
        with pytest.raises(RuntimeError, match='restored galaxy refusal'):
            action()
    assert layer.catalogue_metadata.to_record() == original


@pytest.mark.parametrize('catalog', ('messier', 'caldwell'))
def test_kernel_nonstellar_cold_saved_pixels_and_warm_refusal(native_snapshot_case, tmp_path, monkeypatch, catalog):
    from dataclasses import replace
    import numpy as np
    from matplotlib.image import imread
    from astropy.coordinates import AltAz, EarthLocation
    from astropy.time import Time
    from wenu.atlas_design import AtlasBandTiling
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu.charts.request_generation import AtlasSheetChartRequest, generate_chart_request
    from wenu.objects.nonstellar import NonStellar
    from wenu.resources import nonstellar_catalog_path
    from wenu.sky import native_snapshot as snapshots
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu_kernel import KernelSession
    raw, destination, _, cold = native_snapshot_case
    if catalog == 'caldwell':
        profile = replace(snapshots.CANONICAL_MAXIMAL_SPHERE_PROFILE,
            nonstellar_filename=nonstellar_catalog_path('caldwell'))
        destination = tmp_path/'caldwell-sky'
        _, cold = snapshots.prepare_native_sky_snapshot(raw, destination, profile=profile, return_sky=True)
    saved = snapshots.read_native_sky_snapshot(destination).make_sky()
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    for options in ({}, {'labels_only': True}):
        _assert_native_geometry_equal(cold.nonstellar.realize(context, None, **options),
                                      saved.nonstellar.realize(context, None, **options))
    atlas = AtlasBandTiling.from_json(raw.decode())
    row = cold.nonstellar.catalog[0]
    identifier = atlas.primary_sheet_id(float(row['ra_deg']), float(row['dec_deg']))
    sheet = next(s for s in atlas.geometry.sheets if s.sheet_id == identifier)
    presentation = AtlasChartPresentation(layers=('nonstellar',), formats=('png', 'pdf', 'svg'), dpi=36)
    with monkeypatch.context() as baseline:
        baseline.setattr(NonStellar, '_native_centres', lambda self, table, instant=None:
            (np.asarray(table['ra_deg'], dtype=float), np.asarray(table['dec_deg'], dtype=float)))
        generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
            presentation, tmp_path/'legacy'), sky=cold)
    for name, sky in (('cold', cold), ('saved', saved)):
        generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
            presentation, tmp_path/name), sky=sky)
    filename = f'chart-{sheet.number:02d}.png'
    for name in ('cold', 'saved'):
        np.testing.assert_array_equal(imread(tmp_path/'legacy'/filename), imread(tmp_path/name/filename))
    observer = SimpleNamespace(altaz_frame=AltAz(obstime=Time('2026-08-16T01:00:00'),
        location=EarthLocation.from_geodetic(-71.5, -33., 52.)))
    layer = saved.nonstellar
    selected = [str(row['identifier'])]
    layer.spherical_centers(observer, selected=selected)
    layer.spherical_geometry(observer, selected=selected, samples=12)
    record = layer.catalogue_metadata.to_record()
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic saved generic refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    for action in (layer.position, lambda: layer.realize(context, None, labels_only=True),
                   lambda: layer.realize(context, None),
                   lambda: layer.spherical_centers(observer, selected=selected),
                   lambda: layer.spherical_geometry(observer, selected=selected, samples=12)):
        with pytest.raises(RuntimeError, match='saved generic refusal'):
            action()
    assert layer.catalogue_metadata.to_record() == record


def test_restored_globular_warm_routes_do_not_hide_kernel_refusal(native_snapshot_case, monkeypatch):
    from astropy.coordinates import AltAz, EarthLocation
    from astropy.time import Time
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu_kernel import KernelSession
    _, destination, _, _ = native_snapshot_case
    layer = read_native_sky_snapshot(destination).make_sky().globular_clusters
    original = layer.catalogue_metadata.to_record()
    assert layer.require_catalogue_lookup_metadata().to_record() == original
    observer = SimpleNamespace(altaz_frame=AltAz(obstime=Time('2026-08-16T01:00:00'),
        location=EarthLocation.from_geodetic(-71.5, -33., 52.)))
    selected = ['NGC 5139']
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    layer.spherical_centers(observer, selected=selected)
    layer.spherical_geometry(observer, selected=selected, samples=12)
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic restored globular refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    for action in (lambda: layer.position(),
                   lambda: layer.realize(context, None, selected=selected),
                   lambda: layer.realize(context, None, selected=selected, labels_only=True),
                   lambda: layer.spherical_centers(observer, selected=selected),
                   lambda: layer.spherical_geometry(observer, selected=selected, samples=12)):
        with pytest.raises(RuntimeError, match='restored globular refusal'):
            action()
    assert layer.catalogue_metadata.to_record() == original



def test_kernel_globular_routes_preserve_accepted_atlas_pixels(native_snapshot_case, tmp_path, monkeypatch):
    from matplotlib.image import imread
    from wenu.atlas_design import AtlasBandTiling
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu.charts.request_generation import AtlasSheetChartRequest, generate_chart_request
    from wenu.objects.globular_clusters import GlobularClusters
    from wenu.objects.nonstellar import NonStellar
    import numpy as np
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    raw, destination, _, sky = native_snapshot_case
    saved = read_native_sky_snapshot(destination).make_sky()
    for layer in (sky.globular_clusters, saved.globular_clusters):
        layer.require_catalogue_lookup_metadata()
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    for options in (dict(selected=["NGC 5139"]), dict(selected=["NGC 5139"], labels_only=True)):
        _assert_native_geometry_equal(sky.globular_clusters.realize(context, None, **options),
                                      saved.globular_clusters.realize(context, None, **options))
    atlas = AtlasBandTiling.from_json(raw.decode())
    identifier = atlas.primary_sheet_id(201.697, -47.480)
    sheet = next(sheet for sheet in atlas.geometry.sheets if sheet.sheet_id == identifier)
    presentation = AtlasChartPresentation(layers=('globular_clusters',), formats=('png', 'pdf', 'svg'), dpi=36)
    with monkeypatch.context() as baseline:
        baseline.setattr(GlobularClusters, '_native_centres', lambda self, table, instant=None:
            (np.asarray(table['ra_deg'], dtype=float), np.asarray(table['dec_deg'], dtype=float)))
        generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
            presentation, tmp_path/'legacy-globulars'), sky=sky)
    generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
        presentation, tmp_path/'kernel-globulars'), sky=sky)
    generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
        presentation, tmp_path/'saved-globulars'), sky=saved)
    name = f'chart-{sheet.number:02d}.png'
    np.testing.assert_array_equal(imread(tmp_path/'legacy-globulars'/name),
                                  imread(tmp_path/'kernel-globulars'/name))

    np.testing.assert_array_equal(imread(tmp_path/'kernel-globulars'/name),
                                  imread(tmp_path/'saved-globulars'/name))



def test_restored_pn_warm_routes_do_not_hide_kernel_refusal(native_snapshot_case, monkeypatch):
    from astropy.coordinates import AltAz, EarthLocation
    from astropy.time import Time
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu_kernel import KernelSession
    _, destination, _, _ = native_snapshot_case
    layer = read_native_sky_snapshot(destination).make_sky().planetary_nebulae
    original = layer.catalogue_metadata.to_record()
    assert layer.require_catalogue_lookup_metadata().to_record() == original
    observer = SimpleNamespace(altaz_frame=AltAz(obstime=Time('2026-08-16T01:00:00'),
        location=EarthLocation.from_geodetic(-71.5, -33., 52.)))
    selected = ['PN G063.1+13.9']
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    layer.spherical_centers(observer, selected=selected)
    layer.spherical_geometry(observer, selected=selected)
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic restored PN refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    for action in (lambda: layer.position(),
                   lambda: layer.realize(context, None, selected=selected),
                   lambda: layer.spherical_centers(observer, selected=selected),
                   lambda: layer.spherical_geometry(observer, selected=selected)):
        with pytest.raises(RuntimeError, match='restored PN refusal'):
            action()
    assert layer.catalogue_metadata.to_record() == original


def test_kernel_pn_routes_preserve_accepted_atlas_pixels(native_snapshot_case, tmp_path, monkeypatch):
    from matplotlib.image import imread
    from wenu.atlas_design import AtlasBandTiling
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu.charts.request_generation import AtlasSheetChartRequest, generate_chart_request
    from wenu.objects.planetary_nebulae import PlanetaryNebulae
    from wenu.objects.nonstellar import NonStellar
    import numpy as np
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    raw, destination, _, sky = native_snapshot_case
    saved = read_native_sky_snapshot(destination).make_sky()
    for layer in (sky.planetary_nebulae, saved.planetary_nebulae):
        layer.require_catalogue_lookup_metadata()
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    for options in (dict(selected=["PN G063.1+13.9"]), dict(selected=["PN G063.1+13.9"], minimum_size_arcmin=0.)):
        _assert_native_geometry_equal(sky.planetary_nebulae.realize(context, None, **options),
                                      saved.planetary_nebulae.realize(context, None, **options))
    atlas = AtlasBandTiling.from_json(raw.decode())
    row = sky.planetary_nebulae.catalog[sky.planetary_nebulae.catalog["identifier"] == "PN G063.1+13.9"][0]
    identifier = atlas.primary_sheet_id(float(row["ra_deg"]), float(row["dec_deg"]))
    sheet = next(sheet for sheet in atlas.geometry.sheets if sheet.sheet_id == identifier)
    presentation = AtlasChartPresentation(layers=('planetary_nebulae',), formats=('png', 'pdf', 'svg'), dpi=36)
    with monkeypatch.context() as baseline:
        baseline.setattr(PlanetaryNebulae, '_native_centres', lambda self, table, instant=None:
            (np.asarray(table['ra_deg'], dtype=float), np.asarray(table['dec_deg'], dtype=float)))
        generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
            presentation, tmp_path/'legacy-PN'), sky=sky)
    generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
        presentation, tmp_path/'kernel-PN'), sky=sky)
    generate_chart_request(AtlasSheetChartRequest(sheet, atlas.geometry.page,
        presentation, tmp_path/'saved-PN'), sky=saved)
    name = f'chart-{sheet.number:02d}.png'
    np.testing.assert_array_equal(imread(tmp_path/'legacy-PN'/name),
                                  imread(tmp_path/'kernel-PN'/name))

    np.testing.assert_array_equal(imread(tmp_path/'kernel-PN'/name),
                                  imread(tmp_path/'saved-PN'/name))
