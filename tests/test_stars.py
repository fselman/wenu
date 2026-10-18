"""Milestone 7 tests for AstronomicalObject and Stars."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
from astropy.time import Time
import pytest
from stellar_catalogue_fixtures import native_table

from wenu.objects.astronomical_object import AstronomicalObject
from wenu.objects.stars import Stars
from wenu.sky import SkyLayer
from wenu.sky.constellation_lines import ConstellationLines
from wenu.geometry.spherical import SphericalPoints


class FakeAngle:
    def __init__(self, degrees):
        self.degrees = np.asarray(degrees, dtype=float)


class FakeApparent:
    def __init__(self, alt, az):
        self.alt = alt
        self.az = az

    def apparent(self, deflectors):
        assert deflectors == []
        return self

    def altaz(self):
        return FakeAngle(self.alt), FakeAngle(self.az), None


class FakeAt:
    def __init__(self, owner):
        self.owner = owner
        self.apparent_result = owner.apparent

    def observe(self, stars):
        self.owner.observe_calls += 1
        return self.apparent_result


class FakeSkyfieldObserver:
    def __init__(self, apparent):
        self.apparent = apparent
        self.observe_calls = 0

    def at(self, time):
        return FakeAt(self)


def make_stars():
    apparent = FakeApparent(
        alt=[20.0, -20.0, 40.0],
        az=[100.0, 200.0, 300.0],
    )
    observer = SimpleNamespace(
        skyfield=FakeSkyfieldObserver(apparent),
        t=object(),
        t_astropy=Time("2026-08-28T00:00:00", scale="utc"),
    )
    stars = Stars(observer=observer)
    stars.catalog = pd.DataFrame(
        {
            "ra_hours": [1.0, 2.0, 3.0],
            "dec_degrees": [-10.0, -20.0, -30.0],
            "magnitude": [1.0, 2.0, 3.0],
        },
        index=[100, 200, 300],
    )
    stars.catalog = native_table(stars.catalog)
    stars.hip_df = stars.catalog.copy()
    stars.skyfield_stars = object()
    return stars, observer


def test_astronomical_object_is_abstract_sky_layer():
    assert issubclass(AstronomicalObject, SkyLayer)

    with pytest.raises(TypeError):
        AstronomicalObject()


def test_stars_is_concrete_astronomical_object():
    stars, _ = make_stars()

    assert isinstance(stars, AstronomicalObject)
    assert isinstance(stars, SkyLayer)
    assert stars.layer_name == "stars"


def test_native_icrs_selection_preserves_catalogue_and_ignores_bound_observer(monkeypatch):
    from wenu.sky.realization import NATIVE_ICRS_SPEC
    from wenu.sky.realization import LayerRealizationContext
    stars, observer = make_stars()
    stars.source_catalog = stars.catalog.copy()
    stars.source_catalog["ra_degrees"] = [15., 30., 45.]
    stars.catalog["ra_degrees"] = [15., 30., 45.]
    before = stars.source_catalog.copy(deep=True)
    def forbidden(*args, **kwargs):
        raise AssertionError("Native catalogue requested observer realization")
    monkeypatch.setattr(stars, "observed_altaz", forbidden)
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    bright = stars.realize(context, None, magnitude_limit=1.5, alt_min=80)
    deep = stars.realize(context, object(), magnitude_limit=3)
    assert bright.ids.tolist() == [100]
    assert deep.ids.tolist() == [100, 200, 300]
    np.testing.assert_array_equal(deep.lon_deg, [15., 30., 45.])
    np.testing.assert_array_equal(deep.lat_deg, [-10., -20., -30.])
    assert len(bright.metadata["is_constellation_vertex"]) == 1
    assert deep.coordinate_spec.frame == "icrs"
    assert deep.coordinate_spec.position_status.value == "astrometric"
    assert deep.coordinate_spec.instant is None
    assert deep.coordinate_spec.epoch == "J1991.25"
    pd.testing.assert_frame_equal(before, stars.source_catalog)
    assert observer.skyfield.observe_calls == 0


def test_stars_returns_aligned_spherical_points():
    stars, observer = make_stars()

    geometry = stars.spherical_geometry(
        observer,
        alt_min=0.0,
    )

    assert isinstance(geometry, SphericalPoints)
    np.testing.assert_allclose(geometry.lon_deg, [100.0, 300.0])
    np.testing.assert_allclose(geometry.lat_deg, [20.0, 40.0])
    np.testing.assert_array_equal(geometry.ids, [100, 300])
    np.testing.assert_allclose(
        geometry.metadata["magnitude"],
        [1.0, 3.0],
    )
    assert geometry.metadata["catalog"] == "hipparcos"


def test_spherical_geometry_preserves_hip_lookup():
    stars, observer = make_stars()

    stars.spherical_geometry(observer, alt_min=0.0)

    assert stars.hip_index == {100: 0, 300: 1}


def test_repeated_geometry_starts_from_stable_catalogue():
    stars, observer = make_stars()

    first = stars.spherical_geometry(observer, alt_min=0.0)
    second = stars.spherical_geometry(observer, alt_min=-30.0)

    assert len(first) == 2
    assert len(second) == 3
    assert len(stars.catalog) == 3


def test_render_local_star_selections_share_one_maximal_altaz_transform():
    stars, observer = make_stars()
    stars.source_catalog = stars.catalog.copy()

    bright = stars.spherical_geometry(
        observer,
        alt_min=-90.0,
        magnitude_limit=1.5,
    )
    deep = stars.spherical_geometry(
        observer,
        alt_min=-90.0,
        magnitude_limit=3.0,
    )

    assert bright.ids.tolist() == [100]
    assert deep.ids.tolist() == [100, 200, 300]
    assert observer.skyfield.observe_calls == 1


def test_observed_altaz_cache_is_immutable_and_observer_keyed():
    stars, observer = make_stars()
    stars.source_catalog = stars.catalog.copy()
    _, first_altitude, first_azimuth = stars.observed_altaz(observer)

    assert first_altitude.flags.writeable is False
    assert first_azimuth.flags.writeable is False

    second_observer = SimpleNamespace(
        skyfield=FakeSkyfieldObserver(
            FakeApparent(
                alt=[10.0, 20.0, 30.0],
                az=[40.0, 50.0, 60.0],
            )
        ),
        t=object(),
    )
    _, second_altitude, _ = stars.observed_altaz(second_observer)

    np.testing.assert_allclose(second_altitude, [10.0, 20.0, 30.0])
    assert observer.skyfield.observe_calls == 1
    assert second_observer.skyfield.observe_calls == 1


def test_constellation_lines_reuse_the_stellar_altaz_transform(tmp_path):
    stars, observer = make_stars()
    stars.source_catalog = stars.catalog.copy()
    lines_file = tmp_path / "test.fab"
    lines_file.write_text("Cru 3 100 200 300\n", encoding="utf-8")
    lines = ConstellationLines(stars, filename=lines_file)

    stars.spherical_geometry(observer, alt_min=-90.0)
    geometry = lines.spherical_geometry(observer)

    assert len(geometry) == 2
    assert observer.skyfield.observe_calls == 1


def test_stars_contains_no_projection_or_rendering_api():
    stars, _ = make_stars()

    for name in (
        "draw",
        "project",
        "prepare",
        "compute_sizes",
        "projection",
        "artist",
        "x",
        "y",
        "sizes",
    ):
        assert not hasattr(stars, name)


def test_loaded_designations_follow_hip_through_native_and_altitude_selection(monkeypatch, tmp_path):
    from wenu.objects import stars as stars_module

    stars, observer = make_stars()
    source = stars.catalog.copy()
    source.index = [677, 80763, 85927]
    source['magnitude'] = [1.0, 9.0, 3.0]
    monkeypatch.setattr(stars_module.hipparcos, 'load_dataframe', lambda stream: source.copy())
    filename = tmp_path / 'hip.dat'
    filename.write_bytes(b'')
    metadata = source.attrs['wenu_stellar_catalogue'].copy()
    from hashlib import sha256
    metadata['source_sha256'] = sha256(b'').hexdigest()
    stars.load(filename=filename, metadata=metadata)

    assert list(stars.source_catalog.index) == [677, 80763, 85927]
    assert list(stars.catalog.index) == [677, 85927]
    assert stars.source_catalog.loc[80763, 'star_designations'].hip == 80763
    native = stars.position()
    np.testing.assert_array_equal(native.lon_deg, [15.0, 45.0])
    np.testing.assert_array_equal(native.lat_deg, [-10.0, -30.0])
    assert [r.hip for r in native.metadata['star_designations']] == list(native.ids)
    assert 'Wikidata' not in str(native.coordinate_spec)

    # Existing explicit-HIP machinery retains a faint candidate, without a
    # new selection implementation in the designation catalogue.
    retained = stars._render_catalog(magnitude_limit=2.0, include_ids=[80763, 85927])
    assert list(retained.index) == [677, 80763, 85927]
    geometry = stars.spherical_geometry(observer, magnitude_limit=10.0, alt_min=0.0)
    assert list(geometry.ids) == [677, 85927]
    assert [r.hip for r in geometry.metadata['star_designations']] == list(geometry.ids)
    np.testing.assert_array_equal(geometry.metadata['magnitude'], [1.0, 3.0])
    assert list(stars.catalog.index) == [677, 85927]


def _native_kernel_stars():
    """Constructed selected rows; no catalogue download or observed astrometry."""
    stars = Stars(None, magnitude_limit=5.0)
    stars.source_catalog = pd.DataFrame(dict(
        ra_degrees=[0.0, 90.0, 225.0, float('nan')],
        ra_hours=[0.0, 6.0, 15.0, float('nan')],
        dec_degrees=[0.0, 30.0, -30.0, 40.0],
        magnitude=[1.0, 2.0, 9.0, 3.0],
        is_constellation_vertex=[False, True, False, False],
    ), index=[11, 12, 13, 14])
    stars.source_catalog = native_table(stars.source_catalog)
    stars.catalog = stars.source_catalog[stars.source_catalog.magnitude <= 5].copy()
    return stars


def test_native_stars_query_real_kernel_and_keep_selection_metadata(monkeypatch):
    from wenu_kernel import KernelSession
    from wenu_kernel.records import TimePoint
    HIPPARCOS_SOURCE_EPOCH = TimePoint(2448349, 0.0625, 'tt')
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC

    stars = _native_kernel_stars()
    original = stars.source_catalog.copy(deep=True)
    calls = []
    evaluate = KernelSession.evaluate

    def capture(session, query):
        result = evaluate(session, query)
        calls.append((query, result))
        return result

    monkeypatch.setattr(KernelSession, "evaluate", capture)
    points = stars.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None)
    assert len(calls) == 1
    query, result = calls[0]
    assert query.times == (HIPPARCOS_SOURCE_EPOCH,)
    assert [key.value for key in query.objects] == ["hipparcos:11", "hipparcos:12"]
    assert all(row.source_epoch == HIPPARCOS_SOURCE_EPOCH for row in result.states)
    np.testing.assert_array_equal(points.ids, [11, 12, 14])
    np.testing.assert_allclose(points.lon_deg[:2], [0, 90], atol=1e-12, rtol=0)
    np.testing.assert_allclose(points.lat_deg[:2], [0, 30], atol=1e-12, rtol=0)
    assert np.isnan(points.lon_deg[-1]) and points.lat_deg[-1] == 40
    np.testing.assert_array_equal(points.metadata['magnitude'], [1, 2, 3])
    np.testing.assert_array_equal(points.metadata['is_constellation_vertex'], [False, True, False])
    assert points.coordinate_spec.epoch == "J1991.25"
    pd.testing.assert_frame_equal(stars.source_catalog, original)


def test_native_stars_coordinates_are_taken_from_kernel_results(monkeypatch):
    from dataclasses import replace
    from wenu_kernel import KernelSession

    stars = _native_kernel_stars()
    evaluate = KernelSession.evaluate

    def synthetic_quarter_turn(session, query):
        batch = evaluate(session, query)
        return replace(batch, states=tuple(replace(row,
            vector=(-row.vector[1], row.vector[0], row.vector[2])) for row in batch.states))

    monkeypatch.setattr(KernelSession, 'evaluate', synthetic_quarter_turn)
    lon, lat = stars._native_catalogue_coordinates(stars.catalog)
    np.testing.assert_allclose(lon[:2], [90, 180], atol=1e-12, rtol=0)
    np.testing.assert_allclose(lat[:2], [0, 30], atol=1e-12, rtol=0)


def test_native_stars_do_not_fall_back_when_kernel_evaluation_fails(monkeypatch):
    from wenu_kernel import KernelSession

    stars = _native_kernel_stars()
    def fail(*args):
        raise RuntimeError("synthetic kernel refusal")
    monkeypatch.setattr(KernelSession, 'evaluate', fail)
    with pytest.raises(RuntimeError, match="kernel refusal"):
        stars._native_catalogue_coordinates(stars.catalog)


def test_missing_native_positions_never_become_zero_direction_states(monkeypatch):
    from wenu_kernel import KernelSession

    stars = _native_kernel_stars()
    missing = stars.catalog.iloc[-1:]
    def forbidden(*args):
        raise AssertionError("missing positions must not produce a kernel query")
    monkeypatch.setattr(KernelSession, 'evaluate', forbidden)
    lon, lat = stars._native_catalogue_coordinates(missing)
    assert np.isnan(lon[0]) and lat[0] == 40


def test_native_kernel_round_trip_preserves_wrap_and_polar_directions():
    stars = Stars(None, magnitude_limit=5)
    lon = np.array([0., 1e-12, 90., 225., 359.999999999, 17., 340.])
    lat = np.array([0., -30., 89.999999, -89.999999, 45., 90., -90.])
    source = pd.DataFrame(dict(ra_degrees=lon, dec_degrees=lat), index=np.arange(1, len(lon)+1))
    source = native_table(source)
    actual_lon, actual_lat = stars._native_catalogue_coordinates(source)
    def vectors(ra, dec):
        ra, dec = np.deg2rad(ra), np.deg2rad(dec)
        return np.column_stack((np.cos(dec)*np.cos(ra), np.cos(dec)*np.sin(ra), np.sin(dec)))
    original, actual = vectors(lon, lat), vectors(actual_lon, actual_lat)
    separation = np.arctan2(np.linalg.norm(np.cross(original, actual), axis=1),
                            np.sum(original*actual, axis=1))
    assert np.max(separation) < 1e-12  # Numerical compatibility test, not a physical error certificate.
