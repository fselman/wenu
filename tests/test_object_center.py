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
