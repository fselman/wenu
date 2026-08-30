"""Contracts for typed ephemeris-state sources."""

from dataclasses import FrozenInstanceError

import pytest

from wenu.coordinates import PositionStatus, observer_altaz_spec
from wenu.ephemeris import (
    EphemerisResourceIdentity,
    EphemerisState,
    EphemerisStateRequest,
    EphemerisStateSource,
)


DIGEST = "a" * 64


def _resource(**overrides):
    values = dict(
        provider="JPL",
        model="DE440",
        filename="de440s.bsp",
        sha256=DIGEST,
        coverage_start="1849-12-26T00:00:00",
        coverage_end="2150-01-22T00:00:00",
        coverage_time_scale="TDB",
        provenance=("test resource",),
    )
    values.update(overrides)
    return EphemerisResourceIdentity(**values)


def _request(**overrides):
    values = dict(
        target="venus",
        centre="solar-system-barycenter",
        frame="ICRS",
        instant="2026-08-30T00:00:00",
        time_scale="TDB",
    )
    values.update(overrides)
    return EphemerisStateRequest(**values)


def _state(**overrides):
    values = dict(
        request=_request(),
        position=(1.0, 2.0, 3.0),
        velocity=(0.1, 0.2, 0.3),
        position_unit="km",
        velocity_unit="km/day",
        resource=_resource(),
        provider_target_id="299",
        provider_centre_id="0",
        provenance=("deterministic test state",),
    )
    values.update(overrides)
    return EphemerisState(**values)


def test_resource_identity_normalizes_digest_scale_and_provenance():
    resource = _resource(
        provider=" JPL ",
        sha256="ABCDEF" * 10 + "ABCD",
        coverage_time_scale=" TDB ",
        provenance=[" source segment "],
    )

    assert resource.provider == "JPL"
    assert resource.sha256 == ("abcdef" * 10 + "abcd")
    assert resource.coverage_time_scale == "tdb"
    assert resource.provenance == ("source segment",)


@pytest.mark.parametrize(
    "digest",
    ("a" * 63, "a" * 65, "g" * 64, ""),
)
def test_resource_identity_rejects_invalid_sha256(digest):
    with pytest.raises(ValueError, match="64 hexadecimal"):
        _resource(sha256=digest)


def test_resource_identity_is_frozen():
    resource = _resource()

    with pytest.raises(FrozenInstanceError):
        resource.model = "DE441"


def test_state_request_keeps_target_centre_frame_and_dynamical_time():
    request = _request(
        target=" venus ",
        centre=" solar-system-barycenter ",
        frame=" ICRS ",
        time_scale=" TDB ",
    )

    assert request.target == "venus"
    assert request.centre == "solar-system-barycenter"
    assert request.frame == "icrs"
    assert request.time_scale == "tdb"


@pytest.mark.parametrize("name", ("target", "centre", "frame", "instant"))
def test_state_request_rejects_blank_identity(name):
    with pytest.raises(ValueError, match=name):
        _request(**{name: " "})


def test_state_is_a_complete_immutable_six_component_value():
    state = _state(position=[1, 2, 3], velocity=[4, 5, 6])

    assert state.position == (1.0, 2.0, 3.0)
    assert state.velocity == (4.0, 5.0, 6.0)
    assert state.request.target == "venus"
    assert state.resource.sha256 == DIGEST

    with pytest.raises(FrozenInstanceError):
        state.position = (0.0, 0.0, 0.0)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("position", (1.0, 2.0), "exactly three"),
        ("velocity", (1.0, 2.0, 3.0, 4.0), "exactly three"),
        ("position", (1.0, float("nan"), 3.0), "finite"),
        ("velocity", (1.0, float("inf"), 3.0), "finite"),
    ),
)
def test_state_rejects_incomplete_or_nonfinite_vectors(
    field, value, message
):
    with pytest.raises(ValueError, match=message):
        _state(**{field: value})


def test_state_rejects_position_only_input():
    values = dict(
        request=_request(),
        position=(1.0, 2.0, 3.0),
        position_unit="km",
        velocity_unit="km/day",
        resource=_resource(),
    )

    with pytest.raises(TypeError, match="velocity"):
        EphemerisState(**values)


def test_state_requires_typed_request_and_resource():
    with pytest.raises(TypeError, match="EphemerisStateRequest"):
        _state(request=object())
    with pytest.raises(TypeError, match="EphemerisResourceIdentity"):
        _state(resource=object())


def test_deterministic_source_satisfies_structural_protocol():
    class Source:
        def state(self, request):
            return _state(request=request)

    source = Source()
    request = _request()

    assert isinstance(source, EphemerisStateSource)
    assert source.state(request).request is request


def test_topocentric_status_is_removed_and_altaz_uses_apparent_status():
    assert "TOPOCENTRIC" not in PositionStatus.__members__

    class Observer:
        t_astropy = type(
            "Time",
            (),
            {"isot": "2026-08-30T00:00:00", "scale": "utc"},
        )()

    spec = observer_altaz_spec(Observer())

    assert spec.origin == "observer"
    assert spec.position_status is PositionStatus.APPARENT
