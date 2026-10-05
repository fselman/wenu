"""Digest-bound external satellite snapshot admission."""

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
from wenu.satellites import (
    ExternalSnapshotAdmission,
    ExternalSnapshotAdmissionPolicy,
    ExternalSnapshotIdentity,
    MultiFieldCrossingRequest,
    MultiFieldCrossingValidationError,
    MultiFieldSatelliteCrossingCoordinator,
    load_snapshot,
)
from wenu.satellites.crossing_acceleration import (
    AcceleratedCrossingPolicy,
    AcceleratedLocalSatelliteCrossingOracle,
    ConeShellDecision,
    ConeShellSelection,
    ConservativeConeShellSelector,
)
from wenu.satellites.crossing_oracle import (
    LocalSatelliteCrossingQuery,
    SatelliteCrossingConvergenceError,
)
from wenu.satellites.snapshots import SatelliteElementSnapshot


START = datetime(2026, 9, 15, tzinfo=timezone.utc)


def iso(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def external_snapshot():
    installed = load_snapshot()
    manifest = replace(
        installed.manifest,
        snapshot_id="external_test_snapshot",
        source_identity="External test source",
        source_url="https://example.test/elements.csv",
        builder_identity="wenu.test.external-builder/1",
    )
    return SatelliteElementSnapshot(manifest, installed.records)


def admission(snapshot):
    identity = ExternalSnapshotIdentity.from_snapshot(snapshot)
    policy = ExternalSnapshotAdmissionPolicy(
        policy_identity="wenu.test.external-admission/1",
        admitted_identities=(identity,),
    )
    return policy.admit(snapshot)


def query(snapshot, identifier="external-field"):
    return LocalSatelliteCrossingQuery(
        snapshot=snapshot,
        observer=SatelliteObserver(
            observer_id="la-ligua",
            longitude_deg=-71.230289,
            latitude_deg=-32.443342,
            elevation_m=52.0,
            refraction_policy="vacuum",
            earth_orientation_policy="iers-a-bundled",
        ),
        field_of_view=SatelliteFieldOfView(
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
                provider="external admission test",
            ),
        ),
        interval=InclusiveTimeInterval(
            iso(START), iso(START + timedelta(seconds=1))
        ),
        time_tolerance_seconds=0.01,
        angular_tolerance_deg=1.0e-5,
    )


class RecordingSelector:
    def __init__(self):
        self.calls = []

    def select(self, request):
        self.calls.append(request)
        return ConeShellSelection(
            snapshot_sha256=request.snapshot.manifest.content_sha256,
            field_id=request.field_of_view.field_id,
            interval_start=request.interval.start,
            interval_stop=request.interval.stop,
            decisions=tuple(
                ConeShellDecision(
                    record.norad_catalog_id,
                    "retain",
                    "test retains every record",
                )
                for record in request.snapshot.records
            ),
        )


class RecordingCertifier:
    def __init__(self):
        self.calls = []

    def certify(self, request):
        self.calls.append(request.field_of_view.field_id)
        return SimpleNamespace(field_id=request.field_of_view.field_id)


class RecordingOracle:
    def __init__(self):
        self.calls = []

    def solve_with_evidence(self, request):
        self.calls.append(request.field_of_view.field_id)
        return (), SimpleNamespace()


def test_identity_policy_and_token_are_immutable_and_exact():
    snapshot = external_snapshot()
    identity = ExternalSnapshotIdentity.from_snapshot(snapshot)
    token = admission(snapshot)

    assert token.identity == identity
    assert token.require(snapshot) is snapshot
    with pytest.raises(FrozenInstanceError):
        token.policy_identity = "changed"
    with pytest.raises(TypeError, match="must be produced"):
        ExternalSnapshotAdmission(identity, "forged")

    changed_digest = SatelliteElementSnapshot(
        replace(snapshot.manifest, content_sha256="f" * 64),
        snapshot.records,
    )
    with pytest.raises(ValueError, match="does not match"):
        token.require(changed_digest)

    changed_manifest = SatelliteElementSnapshot(
        replace(snapshot.manifest, source_identity="Another source"),
        snapshot.records,
    )
    with pytest.raises(ValueError, match="does not match"):
        token.require(changed_manifest)


def test_policy_rejects_unlisted_identity_and_duplicate_entries():
    snapshot = external_snapshot()
    identity = ExternalSnapshotIdentity.from_snapshot(snapshot)
    policy = ExternalSnapshotAdmissionPolicy(
        "wenu.test.policy/1",
        (replace(identity, builder_identity="another-builder/1"),),
    )

    with pytest.raises(ValueError, match="not admitted"):
        policy.admit(snapshot)
    with pytest.raises(ValueError, match="unique"):
        ExternalSnapshotAdmissionPolicy(
            "wenu.test.policy/1", (identity, identity)
        )


def test_selector_requires_exact_token_before_external_state_evaluation():
    snapshot = external_snapshot()
    request = query(snapshot)

    selection = ConservativeConeShellSelector().select(request)
    assert {item.outcome for item in selection.decisions} == {
        "indeterminate"
    }
    assert all(
        "outside the validated cone-shell domain" in item.reason
        for item in selection.decisions
    )

    wrong = admission(
        SatelliteElementSnapshot(
            replace(snapshot.manifest, source_identity="Another source"),
            snapshot.records,
        )
    )
    with pytest.raises(ValueError, match="does not match"):
        ConservativeConeShellSelector(
            external_snapshot_admission=wrong
        ).select(request)


def test_accelerated_coordinator_fails_before_selector_without_exact_token():
    snapshot = external_snapshot()
    request = query(snapshot)
    selector = RecordingSelector()
    oracle = AcceleratedLocalSatelliteCrossingOracle(
        selector=selector,
        policy=AcceleratedCrossingPolicy(
            selector_failure_mode="fail_closed"
        ),
    )

    with pytest.raises(
        SatelliteCrossingConvergenceError,
        match="requires explicit digest-bound admission",
    ):
        oracle.solve_with_evidence(request)
    assert selector.calls == []

    wrong = admission(
        SatelliteElementSnapshot(
            replace(snapshot.manifest, source_identity="Another source"),
            snapshot.records,
        )
    )
    mismatch = AcceleratedLocalSatelliteCrossingOracle(
        selector=selector,
        external_snapshot_admission=wrong,
    )
    with pytest.raises(
        SatelliteCrossingConvergenceError,
        match="external snapshot admission failed",
    ):
        mismatch.solve_with_evidence(request)
    assert selector.calls == []


def test_accelerated_coordinator_consumes_explicit_exact_token():
    snapshot = external_snapshot()
    request = query(snapshot)
    selector = RecordingSelector()
    oracle = AcceleratedLocalSatelliteCrossingOracle(
        selector=selector,
        external_snapshot_admission=admission(snapshot),
    )

    results, evidence = oracle.solve_with_evidence(request)

    assert selector.calls == [request]
    assert isinstance(results, tuple)
    assert evidence.snapshot_sha256 == snapshot.manifest.content_sha256
    assert evidence.rejected_norad_catalog_ids == ()


def test_batch_admission_is_atomic_before_airmass_or_crossing_work():
    snapshot = external_snapshot()
    request = MultiFieldCrossingRequest(
        (query(snapshot, "one"), query(snapshot, "two"))
    )
    certifier = RecordingCertifier()
    oracle = RecordingOracle()
    coordinator = MultiFieldSatelliteCrossingCoordinator(
        certifier=certifier,
        single_field_oracle=oracle,
    )

    with pytest.raises(MultiFieldCrossingValidationError) as caught:
        coordinator.solve(request)

    assert tuple(item.code for item in caught.value.failures) == (
        "snapshot-outside-domain",
        "snapshot-outside-domain",
    )
    assert certifier.calls == []
    assert oracle.calls == []


def test_batch_consumes_one_token_for_every_query_snapshot():
    snapshot = external_snapshot()
    request = MultiFieldCrossingRequest(
        (query(snapshot, "one"), query(snapshot, "two"))
    )
    certifier = RecordingCertifier()
    oracle = RecordingOracle()
    coordinator = MultiFieldSatelliteCrossingCoordinator(
        certifier=certifier,
        single_field_oracle=oracle,
        external_snapshot_admission=admission(snapshot),
    )

    results = coordinator.solve(request)

    assert tuple(item.field_id for item in results) == ("one", "two")
    assert certifier.calls == ["one", "two"]
    assert oracle.calls == ["one", "two"]


def test_batch_rejects_token_query_substitution_before_work():
    snapshot = external_snapshot()
    other = SatelliteElementSnapshot(
        replace(snapshot.manifest, source_identity="Another source"),
        snapshot.records,
    )
    certifier = RecordingCertifier()
    oracle = RecordingOracle()
    coordinator = MultiFieldSatelliteCrossingCoordinator(
        certifier=certifier,
        single_field_oracle=oracle,
        external_snapshot_admission=admission(other),
    )

    with pytest.raises(MultiFieldCrossingValidationError) as caught:
        coordinator.solve(MultiFieldCrossingRequest((query(snapshot),)))

    assert caught.value.failures[0].code == "snapshot-admission-failed"
    assert certifier.calls == []
    assert oracle.calls == []
