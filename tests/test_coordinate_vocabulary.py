"""Milestone 49B.1 coordinate-vocabulary contracts."""

from dataclasses import FrozenInstanceError
from typing import get_args

import numpy as np
import pytest

from wenu.coordinates import GENERIC_SPHERICAL_SPEC

from wenu.coordinates import (
    CoordinateSpec,
    ObservationContext,
    PositionStatus,
)
from wenu.geometry import (
    SphericalCurves,
    SphericalGeometry,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)
from wenu.positions import PositionProvider


def test_coordinate_spec_is_normalized_hashable_and_immutable():
    spec = CoordinateSpec(
        frame=" ICRS ",
        origin=" BARYCENTRIC ",
        position_status="astrometric",
        epoch="J2016.0",
        instant="2026-08-28T00:00:00",
        time_scale=" TCB ",
        provider="Gaia DR3",
        provenance=["source-row-1"],
        corrections={"proper-motion"},
    )

    assert spec.frame == "icrs"
    assert spec.origin == "barycentric"
    assert spec.position_status is PositionStatus.ASTROMETRIC
    assert spec.time_scale == "tcb"
    assert spec.provenance == ("source-row-1",)
    assert spec.corrections == frozenset({"proper-motion"})
    assert isinstance(hash(spec), int)
    with pytest.raises(FrozenInstanceError):
        spec.frame = "galactic"


@pytest.mark.parametrize(
    ("values", "message"),
    (
        ({"frame": "", "origin": "barycentric"}, "frame"),
        ({"frame": "icrs", "origin": ""}, "origin"),
        (
            {"frame": "icrs", "origin": "barycentric", "instant": "now"},
            "instant and time_scale",
        ),
        (
            {"frame": "icrs", "origin": "barycentric", "time_scale": "utc"},
            "instant and time_scale",
        ),
    ),
)
def test_coordinate_spec_rejects_incomplete_identity(values, message):
    with pytest.raises(ValueError, match=message):
        CoordinateSpec(**values)


def test_observation_context_normalizes_location_and_policy():
    context = ObservationContext(
        longitude_deg=289.0,
        latitude_deg=-32.0,
        elevation_m=125.0,
        instant="2026-08-28T00:00:00",
        time_scale="UTC",
    )

    assert context.longitude_deg == -71.0
    assert context.latitude_deg == -32.0
    assert context.time_scale == "utc"
    assert context.refraction_policy == "vacuum"
    with pytest.raises(FrozenInstanceError):
        context.latitude_deg = 0.0


def test_observation_context_rejects_invalid_latitude():
    with pytest.raises(ValueError, match="between -90 and 90"):
        ObservationContext(
            longitude_deg=0.0,
            latitude_deg=91.0,
            elevation_m=0.0,
            instant="2026-08-28T00:00:00",
        )


def test_position_provider_is_one_structural_object_boundary():
    class ExampleProvider:
        def position(self, instant=None):
            return SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=np.array([1.0]),
                lat_deg=np.array([2.0]),
            )

    provider = ExampleProvider()

    assert isinstance(provider, PositionProvider)
    assert len(provider.position("2026-08-28T00:00:00")) == 1


def test_spherical_geometry_names_every_existing_geometry_kind():
    assert set(get_args(SphericalGeometry)) == {
        SphericalPoints,
        SphericalCurves,
        SphericalPolygons,
        SphericalGrid,
    }
