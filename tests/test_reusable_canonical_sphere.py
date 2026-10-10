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
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(snapshots, "generate_native_icrs_sphere", factory)
        patch.setattr(Stars, "load", counted_load)
        patch.setattr(socket, "socket", forbidden)
        digest = snapshots.prepare_native_sky_snapshot(raw, destination)
    assert counts == dict(spheres=1, catalogues=1)
    return raw, destination, digest, cold[0]


def _assert_native_geometry_equal(first, second):
    import numpy as np
    assert type(first) is type(second)
    assert first.coordinate_spec == second.coordinate_spec
    assert len(first) == len(second)
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
from wenu import star_designations
from wenu import stellar_research
from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
import resource
soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (min(64, soft), hard))
def forbidden(*args, **kwargs):
    raise AssertionError("No original source loading or whole-sphere preparation on resume")
for owner in (Stars, ConstellationLines, MilkyWayIsophotes, MagellanicCloudIsophotes):
    owner.load = forbidden
maximal_sphere.generate_native_icrs_sphere = forbidden
maximal_sphere.generate_celestial_sphere = forbidden
maximal_sphere.build_maximal_sphere = forbidden
star_designations.load_star_designations = forbidden
star_designations.load_stellar_curation = forbidden
stellar_research.load_stellar_research = forbidden
snapshot = read_native_sky_snapshot(sys.argv[1], expected_manifest_sha256=sys.argv[2])
sky = snapshot.make_sky()
points = sky.stars.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None, magnitude_limit=6)
assert len(points) > 4000
assert sky.stars.designation_catalogue.curation_sha256
assert sky.constellation_lines.star_ids_for(("Sco",))
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


def test_native_snapshot_requires_coverage_and_preserves_completed_bundle(native_snapshot_case):
    import hashlib
    from wenu.sky.native_snapshot import read_native_sky_snapshot, prepare_native_sky_snapshot
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    raw, destination, digest, _ = native_snapshot_case
    snapshot = read_native_sky_snapshot(destination)
    snapshot.require(layers=("stars", "constellation_lines"), star_magnitude_limit=6,
                     design_sha256=hashlib.sha256(raw).hexdigest())
    for kwargs in (dict(layers=("galaxies",)), dict(layers=("constellation_boundaries",)),
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
    "span", "overlap", "logical-shape"))
def test_native_snapshot_rejects_corruption_before_use(native_snapshot_case, tmp_path, fault):
    import hashlib
    import json
    import shutil
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    _, original, _, _ = native_snapshot_case
    destination = tmp_path / "broken"
    shutil.copytree(original, destination)
    manifest = json.loads((destination / "manifest.json").read_bytes())
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
        manifest["layers"].append("galaxies")
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
