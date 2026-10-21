"""Milestone 9 tests for geometry-only CelestialPoints."""

from types import SimpleNamespace

import numpy as np
import pytest
from astropy.coordinates import BarycentricTrueEcliptic
from astropy.time import Time

from wenu.sky import GeometricalObject, SkyLayer
from wenu.sky.points import CelestialPoints
from wenu.geometry.spherical import SphericalPoints


def make_observer(latitude=-33.0):
    return SimpleNamespace(
        icrs_frame="icrs",
        galactic_frame="galactic",
        ecliptic_frame="geocentrictrueecliptic",
        t=object(),
        t_astropy=SimpleNamespace(
            isot="2026-08-28T00:00:00.000", scale="utc"
        ),
        lat_deg=latitude,
        lon_deg=-71.5,
        elevation_m=100.0,
    )


def test_points_are_geometrical_sky_layer():
    assert issubclass(CelestialPoints, GeometricalObject)
    assert issubclass(CelestialPoints, SkyLayer)


def test_empty_collection_returns_empty_spherical_points():
    observer = make_observer()
    geometry = CelestialPoints(observer).spherical_geometry(observer)

    assert isinstance(geometry, SphericalPoints)
    assert len(geometry) == 0
    assert geometry.labels.size == 0


def test_single_point_returns_collection_and_style_metadata(monkeypatch):
    observer = make_observer()
    points = CelestialPoints(observer)
    points.add_equatorial_point(
        10.0,
        -20.0,
        label="test",
        marker="+",
        size=42.0,
        color="cyan",
        zorder=8,
        fontsize=11,
    )

    def fake_transform(self, geometry, target_spec, observation=None):
        if target_spec.frame == "icrs":
            np.testing.assert_allclose(geometry.lon_deg, [10.0])
            np.testing.assert_allclose(geometry.lat_deg, [-20.0])
            return SphericalPoints(
                lon_deg=geometry.lon_deg,
                lat_deg=geometry.lat_deg,
                coordinate_spec=target_spec,
            )
        assert target_spec.frame == "altaz"
        assert observation.longitude_deg == observer.lon_deg
        return SphericalPoints(
            lon_deg=np.asarray([140.0]),
            lat_deg=np.asarray([35.0]),
            coordinate_spec=target_spec,
            labels=geometry.labels,
            metadata=geometry.metadata,
        )

    monkeypatch.setattr(
        "wenu.sky.points.CoordinateService.transform",
        fake_transform,
    )
    geometry = points.spherical_geometry(observer)

    assert len(geometry) == 1
    np.testing.assert_allclose(geometry.lon_deg, [140.0])
    np.testing.assert_allclose(geometry.lat_deg, [35.0])
    np.testing.assert_array_equal(geometry.labels, ["test"])
    assert geometry.metadata["marker"][0] == "+"
    assert geometry.metadata["size"][0] == 42.0
    assert geometry.metadata["color"][0] == "cyan"
    assert geometry.metadata["zorder"][0] == 8
    assert geometry.metadata["style"][0]["fontsize"] == 11


def test_visible_pole_uses_observer_hemisphere():
    southern = CelestialPoints(make_observer(-33.0))
    northern = CelestialPoints(make_observer(20.0))

    southern.add_equatorial_pole()
    northern.add_equatorial_pole()

    assert southern._points[0].label == "SCP"
    assert southern._points[0].coord.dec.deg == -90.0
    assert northern._points[0].label == "NCP"
    assert northern._points[0].coord.dec.deg == 90.0


def test_ecliptic_cardinal_labels_are_preserved():
    points = CelestialPoints(make_observer())
    points.add_ecliptic_keypoints()

    assert [point.label for point in points._points] == [
        "♈",
        "♋",
        "♎",
        "♑",
    ]


def test_ecliptic_keypoints_accept_the_reference_grid_frame():
    points = CelestialPoints(make_observer())
    frame = BarycentricTrueEcliptic(equinox=Time("2026-08-16"))

    points.add_ecliptic_keypoints(frame=frame, marker="x")

    assert len(points) == 4
    assert all(
        point.coord.frame.is_equivalent_frame(frame)
        for point in points._points
    )
    assert all(point.marker == "x" for point in points._points)


def test_clear_preserves_collection_api():
    points = CelestialPoints(make_observer())
    points.add_equatorial_point(0.0, 0.0)
    assert len(points) == 1

    assert points.clear() is points
    assert len(points) == 0


def test_domain_layer_has_no_projection_or_rendering_api():
    points = CelestialPoints(make_observer())
    for name in ("draw", "project", "artist", "artists"):
        assert not hasattr(points, name)


def test_constructed_points_consume_native_and_observed_service_results(monkeypatch):
    from wenu.coordinate_service import CoordinateService
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    observer = make_observer()
    points = CelestialPoints(observer)
    points.add_equatorial_pole(pole='north')
    points.add_galactic_center()
    points.add_ecliptic_keypoints(frame=BarycentricTrueEcliptic(equinox=Time('J2000')))
    original = CoordinateService.transform
    results = []
    def changed(service, source, target, observation=None):
        result = original(service, source, target, observation)
        if target.frame == 'icrs':
            result.lon_deg = (result.lon_deg + 0.125) % 360
        results.append((source.coordinate_spec, result))
        return result
    monkeypatch.setattr(CoordinateService, 'transform', changed)
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    native = points.realize(context, None)
    assert {source.frame for source, _ in results} == {'icrs', 'galactic', 'barycentric-true-ecliptic'}
    np.testing.assert_array_equal(native.lon_deg, [r.lon_deg[0] for _, r in results])
    assert native.labels.tolist() == ['NCP', 'GC', '♈', '♋', '♎', '♑']
    results.clear()
    observed = points.spherical_geometry(observer)
    assert observed is results[-1][1] and observed.coordinate_spec.frame == 'altaz'
    np.testing.assert_array_equal(results[-1][1].labels, native.labels)
    def refused(*args, **kwargs):
        raise RuntimeError('reference point service refused')
    monkeypatch.setattr(CoordinateService, 'transform', refused)
    for call in (lambda: points.realize(context, None), lambda: points.spherical_geometry(observer)):
        with pytest.raises(RuntimeError, match='service refused'):
            call()


def test_antisolar_point_retains_construction_observation_and_legacy_values(monkeypatch):
    from dataclasses import FrozenInstanceError
    from astropy.coordinates import get_sun
    from wenu.coordinates import observation_context
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu_kernel.kernel import KernelSession
    observer=make_observer();observer.t_astropy=Time('2026-08-28T00:00:00',scale='utc')
    points=CelestialPoints(observer)
    original=points._to_icrs(get_sun(observer.t_astropy))
    def forbidden(*args,**kwargs):
        pytest.fail('a constructed antipode must not become a physical state query')
    monkeypatch.setattr(KernelSession,'evaluate',forbidden)
    points.add_equatorial_point(12.,34.,label='fixed')
    assert points.add_antisolar_point(label='anti',fontsize=13) is points
    native=points.realize(LayerRealizationContext(NATIVE_ICRS_SPEC),None)
    np.testing.assert_array_equal(native.lon_deg,[12.,(original.lon_deg[0]+180.)%360.])
    np.testing.assert_array_equal(native.lat_deg,[34.,-original.lat_deg[0]])
    records=native.metadata['constructed_reference_provenance']
    assert records[0] is None
    receipt=records[1]
    assert receipt.kind=='antisolar-point'
    assert receipt.observation==observation_context(observer)
    assert receipt.source_coordinate_spec.frame=='gcrs'
    assert receipt.source_coordinate_spec.origin=='earth-center'
    assert receipt.source_resource is None
    assert receipt.available
    with pytest.raises(FrozenInstanceError):
        receipt.method='new numerical model'
    # Rebinding the display observer preserves the construction-time anchor.
    later=make_observer();later.t_astropy=Time('2026-08-29T00:00:00',scale='utc')
    observed=points.spherical_geometry(later)
    assert observed.metadata['constructed_reference_provenance'][1]==receipt
    assert observed.coordinate_spec.instant!=receipt.observation.instant
    assert native.labels.tolist()==['fixed','anti']
    assert native.metadata['style'][1]['fontsize']==13
    assert points.clear() is points
    assert points.realize(LayerRealizationContext(NATIVE_ICRS_SPEC),None).metadata['constructed_reference_provenance']==()


def test_antisolar_point_consumes_coordinate_result_and_refuses_before_append(monkeypatch):
    from wenu.coordinate_service import CoordinateService
    observer=make_observer();observer.t_astropy=Time('2026-08-28T00:00:00',scale='utc')
    points=CelestialPoints(observer)
    original=CoordinateService.transform
    def changed(service,source,target,observation=None):
        value=original(service,source,target,observation)
        if source.coordinate_spec.frame=='gcrs':
            value.lon_deg[:]=42.;value.lat_deg[:]=17.
        return value
    monkeypatch.setattr(CoordinateService,'transform',changed)
    points.add_antisolar_point()
    assert points._points[0].coord.ra.deg==222.
    assert points._points[0].coord.dec.deg==-17.
    def refused(*args,**kwargs):
        raise ValueError('antisolar source conversion refused')
    monkeypatch.setattr(CoordinateService,'transform',refused)
    with pytest.raises(ValueError,match='source conversion refused'):
        points.add_antisolar_point()
    assert len(points)==1
