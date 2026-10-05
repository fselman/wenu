"""Atomic same-observer multi-field crossing coordination tests."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteFieldOfView,
    SatelliteObserver,
)
from wenu.satellites import load_snapshot
from wenu.satellites.crossing_batch import (
    FieldAirmassAdmission,
    FieldAirmassCertifier,
    MultiFieldCrossingPolicy,
    MultiFieldCrossingRequest,
    MultiFieldCrossingValidationError,
    MultiFieldSatelliteCrossingCoordinator,
)
from wenu.satellites.crossing_oracle import LocalSatelliteCrossingQuery


START = datetime(2026, 9, 15, tzinfo=timezone.utc)


def iso(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def observer(identifier="la-ligua"):
    return SatelliteObserver(
        observer_id=identifier,
        longitude_deg=-71.230289,
        latitude_deg=-32.443342,
        elevation_m=52.0,
        refraction_policy="vacuum",
        earth_orientation_policy="iers-a-bundled",
    )


def field(identifier):
    return SatelliteFieldOfView(
        field_id=identifier,
        center_longitude_deg=0.0,
        center_latitude_deg=0.0,
        angular_radius_deg=1.0,
        coordinate_spec=CoordinateSpec(
            frame="gcrs-axes",
            origin="topocentric-direction",
            position_status=PositionStatus.GEOMETRIC,
            instant=iso(START),
            time_scale="utc",
            provider="multi-field test",
        ),
    )


def query(identifier, *, seconds=60.0, site=None):
    return LocalSatelliteCrossingQuery(
        snapshot=load_snapshot("synthetic_50s4b_v1"),
        observer=site or observer(),
        field_of_view=field(identifier),
        interval=InclusiveTimeInterval(
            iso(START),
            iso(START + timedelta(seconds=seconds)),
        ),
        time_tolerance_seconds=0.01,
        angular_tolerance_deg=1.0e-5,
    )


class FakeAltitudeEvaluator:
    def __init__(self, altitude):
        self.altitude = altitude

    def evaluate(self, _field, _observer, instant):
        value = (
            self.altitude(instant)
            if callable(self.altitude)
            else self.altitude
        )
        return value, SimpleNamespace(source_sha256="a" * 64)


class FakeCertifier:
    def __init__(self, failures=()):
        self.failures = set(failures)
        self.calls = []

    def certify(self, request):
        identifier = request.field_of_view.field_id
        self.calls.append(identifier)
        if identifier in self.failures:
            raise ValueError("outside admitted airmass")
        return FieldAirmassAdmission(
            field_id=identifier,
            maximum_airmass=2.0,
            minimum_altitude_deg=30.0,
            certified_lower_bound_deg=31.0,
            evaluation_count=1,
            earth_orientation_sha256=("a" * 64,),
        )


class FakeOracle:
    def __init__(self):
        self.calls = []

    def solve_with_evidence(self, request):
        identifier = request.field_of_view.field_id
        self.calls.append(identifier)
        return (f"result-{identifier}",), f"evidence-{identifier}"


def test_policy_request_and_results_are_immutable_and_validate_shape():
    policy = MultiFieldCrossingPolicy()
    request = MultiFieldCrossingRequest((query("one"),))
    with pytest.raises(FrozenInstanceError):
        policy.maximum_airmass = 3.0
    with pytest.raises(FrozenInstanceError):
        request.queries = ()
    with pytest.raises(ValueError, match="non-empty"):
        MultiFieldCrossingRequest(())
    with pytest.raises(ValueError, match="unique"):
        MultiFieldCrossingRequest((query("same"), query("same")))
    with pytest.raises(ValueError, match="at least 1"):
        MultiFieldCrossingPolicy(maximum_airmass=0.9)
    assert policy.processing_chunk_size == 10


def test_constant_accessible_centre_is_certified_for_complete_interval():
    admission = FieldAirmassCertifier(
        evaluator=FakeAltitudeEvaluator(45.0)
    ).certify(query("accessible"))

    assert admission.field_id == "accessible"
    assert admission.maximum_airmass == 2.0
    assert admission.minimum_altitude_deg == pytest.approx(30.0)
    assert admission.certified_lower_bound_deg >= 30.0
    assert admission.evaluation_count == 1
    assert admission.earth_orientation_sha256 == ("a" * 64,)
    assert any("FoV radius" in item for item in admission.provenance)


def test_inaccessible_or_uncertain_centre_fails_closed():
    with pytest.raises(ValueError, match="exceeds"):
        FieldAirmassCertifier(
            evaluator=FakeAltitudeEvaluator(29.0)
        ).certify(query("below-limit"))
    with pytest.raises(ValueError, match="cannot be certified"):
        FieldAirmassCertifier(
            evaluator=FakeAltitudeEvaluator(30.0)
        ).certify(query("on-boundary"))


def test_atomic_validation_collects_all_field_failures_before_solving():
    requests = MultiFieldCrossingRequest(
        (query("good"), query("bad-one"), query("bad-two"))
    )
    certifier = FakeCertifier(("bad-one", "bad-two"))
    oracle = FakeOracle()
    coordinator = MultiFieldSatelliteCrossingCoordinator(
        certifier=certifier,
        single_field_oracle=oracle,
    )

    with pytest.raises(MultiFieldCrossingValidationError) as captured:
        coordinator.solve(requests)

    assert tuple(
        item.field_id for item in captured.value.failures
    ) == ("bad-one", "bad-two")
    assert all(
        item.code == "airmass-not-certified"
        for item in captured.value.failures
    )
    assert certifier.calls == ["good", "bad-one", "bad-two"]
    assert oracle.calls == []


def test_observer_and_interval_domain_failures_are_ordered_and_atomic():
    requests = MultiFieldCrossingRequest(
        (
            query("reference"),
            query("other-site", site=observer("other")),
            query("too-long", seconds=61.0),
        )
    )
    oracle = FakeOracle()
    coordinator = MultiFieldSatelliteCrossingCoordinator(
        certifier=FakeCertifier(),
        single_field_oracle=oracle,
    )

    with pytest.raises(MultiFieldCrossingValidationError) as captured:
        coordinator.solve(requests)

    assert tuple(
        (item.field_id, item.code) for item in captured.value.failures
    ) == (
        ("other-site", "observer-mismatch"),
        ("too-long", "interval-outside-domain"),
    )
    assert oracle.calls == []


def test_valid_results_preserve_input_order_and_independent_intervals():
    identifiers = tuple(f"field-{index:02d}" for index in range(12))
    requests = MultiFieldCrossingRequest(
        tuple(
            query(identifier, seconds=30.0 + index)
            for index, identifier in enumerate(identifiers)
        )
    )
    certifier = FakeCertifier()
    oracle = FakeOracle()
    coordinator = MultiFieldSatelliteCrossingCoordinator(
        policy=MultiFieldCrossingPolicy(processing_chunk_size=10),
        certifier=certifier,
        single_field_oracle=oracle,
    )

    results = coordinator.solve(requests)

    assert tuple(item.field_id for item in results) == identifiers
    assert tuple(oracle.calls) == identifiers
    assert tuple(certifier.calls) == identifiers
    assert tuple(item.crossings for item in results) == tuple(
        (f"result-{identifier}",) for identifier in identifiers
    )
    assert tuple(
        item.query.interval.stop for item in results
    ) == tuple(query_.interval.stop for query_ in requests.queries)


def test_request_rejects_non_batch_input_and_exports_are_public():
    with pytest.raises(TypeError, match="MultiFieldCrossingRequest"):
        MultiFieldSatelliteCrossingCoordinator().solve(object())

    from wenu.satellites import (
        MultiFieldCrossingPolicy as ExportedPolicy,
        MultiFieldCrossingRequest as ExportedRequest,
        MultiFieldSatelliteCrossingCoordinator as ExportedCoordinator,
    )

    assert ExportedPolicy is MultiFieldCrossingPolicy
    assert ExportedRequest is MultiFieldCrossingRequest
    assert ExportedCoordinator is MultiFieldSatelliteCrossingCoordinator


def test_public_validation_composes_existing_atomic_check_without_solving():
    requests = MultiFieldCrossingRequest((query("one"), query("two")))
    certifier = FakeCertifier()
    oracle = FakeOracle()
    coordinator = MultiFieldSatelliteCrossingCoordinator(
        certifier=certifier,
        single_field_oracle=oracle,
    )

    admissions = coordinator.validate(requests)

    assert tuple(value.field_id for value in admissions) == ("one", "two")
    assert certifier.calls == ["one", "two"]
    assert oracle.calls == []
