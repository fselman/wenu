"""Astrometric Solar-System direction realization contracts."""

from dataclasses import FrozenInstanceError, replace
from math import sqrt

import pytest
from astropy.time import Time, TimeDelta

from wenu.coordinates import PositionStatus
from wenu.ephemeris import (
    EphemerisResourceIdentity,
    EphemerisState,
)
from wenu.solar_system_directions import (
    LIGHT_SPEED_AU_PER_DAY,
    AstrometricDirectionConvergenceError,
    AstrometricDirectionIdentityError,
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
    ObserverBarycentricState,
)

RESOURCE = EphemerisResourceIdentity(
    provider="test/JPL",
    model="DE440-test",
    filename="deterministic.bsp",
    sha256="a" * 64,
    coverage_start="JD 2400000.5",
    coverage_end="JD 2500000.5",
    coverage_time_scale="tdb",
    provenance=("deterministic resource",),
)
RECEPTION = "2026-08-30T00:00:00.000"


def request(**overrides):
    values = dict(
        target="venus",
        centre="solar system barycenter",
        reception_instant=RECEPTION,
        reception_time_scale="tdb",
    )
    values.update(overrides)
    return AstrometricDirectionRequest(**values)


def observer_state(**overrides):
    values = dict(
        observer_id="La Ligua",
        centre="solar system barycenter",
        frame="icrf",
        instant=RECEPTION,
        time_scale="tdb",
        position=(0.0, 0.0, 0.0),
        velocity=(0.0, 0.0, 0.0),
        position_unit="au",
        velocity_unit="au/day",
        resource=RESOURCE,
        provider_observer_id="test site",
        provider_centre_id="0",
        provenance=("deterministic observer",),
    )
    values.update(overrides)
    return ObserverBarycentricState(**values)


class FixedSource:
    def __init__(self, *, resource=RESOURCE, position=(1.0, 1.0, 0.0)):
        self.resource = resource
        self.position = position
        self.requests = []

    def state(self, state_request):
        self.requests.append(state_request)
        return EphemerisState(
            request=state_request,
            position=self.position,
            velocity=(0.0, 0.0, 0.0),
            position_unit="au",
            velocity_unit="au/day",
            resource=self.resource,
            provider_target_id="299",
            provider_centre_id="0",
            provenance=("fixed test state",),
        )


def test_request_and_observer_state_are_frozen_and_explicit():
    direction_request = request()
    state = observer_state()

    assert direction_request.reception_time_scale == "tdb"
    assert direction_request.light_time_tolerance_days == 1.0e-12
    assert direction_request.maximum_iterations == 10
    assert state.frame == "icrf"
    assert state.position_unit == "au"

    with pytest.raises(FrozenInstanceError):
        direction_request.target = "mars"
    with pytest.raises(FrozenInstanceError):
        state.observer_id = "elsewhere"


def test_realizer_iterates_light_time_and_retains_scientific_identity():
    source = FixedSource()
    result = AstrometricDirectionRealizer().direction(
        source,
        request(),
        observer_state(),
    )

    expected_distance = sqrt(2.0)
    expected_light_time = expected_distance / LIGHT_SPEED_AU_PER_DAY
    assert result.geometry.lon_deg == pytest.approx((45.0,))
    assert result.geometry.lat_deg == pytest.approx((0.0,))
    assert result.distance_au == pytest.approx(expected_distance)
    assert result.light_time_days == pytest.approx(expected_light_time)
    assert result.iterations == 2
    assert len(source.requests) == 2
    assert Time(source.requests[0].instant, scale="tdb") == Time(
        RECEPTION,
        scale="tdb",
    )
    expected_emission = Time(RECEPTION, scale="tdb") - TimeDelta(
        result.light_time_days,
        format="jd",
    )
    actual_emission = Time(result.emission_instant, scale="tdb")
    assert abs((actual_emission - expected_emission).to_value("day")) < 1.0e-12

    spec = result.geometry.coordinate_spec
    assert spec.frame == "icrs"
    assert spec.origin == "observer"
    assert spec.position_status is PositionStatus.ASTROMETRIC
    assert Time(spec.instant, scale="tdb") == Time(RECEPTION, scale="tdb")
    assert spec.time_scale == "tdb"
    assert spec.epoch is None
    assert spec.equinox is None
    assert spec.corrections == frozenset(("one-way-light-time",))
    assert result.target_provider_id == "299"
    assert result.geometry.ids.tolist() == ["venus"]


def test_realizer_uses_observer_position_at_reception():
    result = AstrometricDirectionRealizer().direction(
        FixedSource(position=(2.0, 1.0, 0.0)),
        request(),
        observer_state(position=(1.0, 0.0, 0.0)),
    )

    assert result.geometry.lon_deg == pytest.approx((45.0,))
    assert result.distance_au == pytest.approx(sqrt(2.0))


def test_realizer_rejects_nonconvergence_deterministically():
    with pytest.raises(
        AstrometricDirectionConvergenceError,
        match="within 1 iterations",
    ):
        AstrometricDirectionRealizer().direction(
            FixedSource(),
            request(maximum_iterations=1),
            observer_state(),
        )


@pytest.mark.parametrize(
    ("state", "message"),
    (
        (observer_state(centre="earth"), "centre"),
        (observer_state(frame="gcrs"), "frame='icrf'"),
        (observer_state(position_unit="km"), "must use AU"),
        (
            observer_state(instant="2026-08-30T00:01:00.000"),
            "reception instant",
        ),
    ),
)
def test_realizer_rejects_mismatched_observer_state(state, message):
    with pytest.raises(AstrometricDirectionIdentityError, match=message):
        AstrometricDirectionRealizer().direction(
            FixedSource(),
            request(),
            state,
        )


def test_realizer_rejects_target_state_from_another_resource():
    other_resource = replace(RESOURCE, sha256="b" * 64)

    with pytest.raises(
        AstrometricDirectionIdentityError,
        match="same resource",
    ):
        AstrometricDirectionRealizer().direction(
            FixedSource(resource=other_resource),
            request(),
            observer_state(),
        )


@pytest.mark.parametrize(
    ("overrides", "error", "message"),
    (
        ({"light_time_tolerance_days": 0.0}, ValueError, "positive"),
        ({"light_time_tolerance_days": float("nan")}, ValueError, "finite"),
        ({"maximum_iterations": 0}, ValueError, "positive"),
        ({"maximum_iterations": 1.5}, TypeError, "integer"),
    ),
)
def test_request_rejects_invalid_convergence_policy(overrides, error, message):
    with pytest.raises(error, match=message):
        request(**overrides)
