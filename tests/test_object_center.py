"""Typed point-object chart-center resolution."""

from types import SimpleNamespace

import pytest

from wenu.charts.object_center import ObjectCenter, get_object_center
from wenu.charts.target_resolver import ResolvedTarget
from wenu.geometry.spherical import SphericalPoints
from wenu.coordinates import icrs_catalogue_spec


def test_object_center_requires_exactly_one_point():
    geometry = SphericalPoints(
        lon_deg=[1.0, 2.0],
        lat_deg=[3.0, 4.0],
        coordinate_spec=icrs_catalogue_spec("test"),
    )

    with pytest.raises(ValueError, match="exactly one"):
        ObjectCenter(geometry, "target", "Target", ("test",))


def test_fixed_target_uses_the_shared_coordinate_service(monkeypatch):
    target = ResolvedTarget(
        key="sirius",
        display_name="Sirius",
        ra_deg=101.28715533,
        dec_deg=-16.71611586,
        components=(),
        provenance="test catalogue",
    )
    horizontal = SphericalPoints(
        lon_deg=[123.0],
        lat_deg=[45.0],
        coordinate_spec=icrs_catalogue_spec("test result"),
    )
    calls = []
    monkeypatch.setattr(
        "wenu.charts.object_center.CoordinateService.transform_skycoord",
        lambda self, coordinate, spec, context: (
            calls.append((coordinate, spec, context)) or horizontal
        ),
    )
    monkeypatch.setattr(
        "wenu.charts.object_center._product_spec", lambda observer: object()
    )
    monkeypatch.setattr(
        "wenu.charts.object_center.observation_context",
        lambda observer: object(),
    )

    center = get_object_center(target, SimpleNamespace())

    assert center.key == "sirius"
    assert center.altitude_deg == pytest.approx(45.0)
    assert center.azimuth_deg == pytest.approx(123.0)
    assert center.provenance == ("test catalogue",)
    assert len(calls) == 1


def test_named_target_center_uses_returned_kernel_state_and_refuses(monkeypatch):
    from dataclasses import replace
    import numpy as np
    from astropy.coordinates import AltAz, EarthLocation, SkyCoord
    from astropy.time import Time
    import astropy.units as u
    from wenu import ChartSubjectRequest, resolve_target
    from wenu.catalogue_state import _unit_direction
    from wenu_kernel import KernelSession
    target = resolve_target(ChartSubjectRequest(target='M17'))
    observer = SimpleNamespace(altaz_frame=AltAz(obstime=Time('2026-08-16T01:00:00'),
        location=EarthLocation.from_geodetic(-71.5, -33., 52.)))
    baseline = get_object_center(target, observer)
    evaluate = KernelSession.evaluate
    def shift(session, query):
        batch = evaluate(session, query)
        return replace(batch, states=tuple(replace(s, vector=_unit_direction(35., -10.)) for s in batch.states))
    monkeypatch.setattr(KernelSession, 'evaluate', shift)
    result = get_object_center(target, observer)
    expected = SkyCoord(ra=35.*u.deg, dec=-10.*u.deg).transform_to(observer.altaz_frame)
    np.testing.assert_allclose(result.azimuth_deg, expected.az.deg)
    assert result.azimuth_deg != baseline.azimuth_deg
    assert result.key == baseline.key and result.provenance == baseline.provenance
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic target refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    with pytest.raises(RuntimeError, match='target refusal'):
        get_object_center(target, observer)
    explicit = resolve_target(ChartSubjectRequest(ra_deg=10., dec_deg=-20.))
    assert explicit.coordinate.ra.deg == 10.  # Constructed coordinates remain distinct.
