"""Fake-data-only tests for strict crossing equivalence matrices."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess

import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteFieldOfView,
    SatelliteObserver,
)
from wenu.satellites.crossing_acceleration import (
    AcceleratedCrossingEvidence,
    ConeShellDecision,
    ConeShellSelection,
)
from wenu.satellites.crossing_matrix_execution import (
    ACCEPTED_MEDIUM_IDENTITY,
    MATRIX_REQUEST_FIXTURE,
    MATRIX_REQUEST_FIXTURE_SHA256,
    MATRIX_WORKER_PROTOCOL,
    REAL_EXECUTION_ACKNOWLEDGEMENT,
    FreshSubprocessMatrixExecutor,
    build_matrix_queries,
    run_production_equivalence_matrix,
    validate_accepted_medium_receipt,
)
from wenu.satellites.crossing_matrix import (
    CROSSING_MATRIX_IMPLEMENTATION,
    MATRIX_DOCUMENT_KIND,
    CrossingMatrixPolicy,
    MatrixEquivalenceError,
    MatrixResourceObservation,
    MatrixRouteRun,
    MatrixSpecimenIdentity,
    run_equivalence_matrix,
)
from wenu.satellites.crossing_oracle import LocalSatelliteCrossingQuery
from wenu.satellites.elements import canonical_json_bytes, sha256_hex
from wenu.satellites.snapshot_admission import (
    ExternalSnapshotAdmissionPolicy,
    ExternalSnapshotIdentity,
)
from wenu.satellites.snapshots import load_snapshot, load_snapshot_directory


START = datetime(2026, 9, 17, 1, tzinfo=timezone.utc)


def iso(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def mapping(record):
    return {
        "OBJECT_NAME": record.object_name,
        "OBJECT_ID": record.international_designator,
        "NORAD_CAT_ID": record.norad_catalog_id,
        "CLASSIFICATION_TYPE": record.classification,
        "EPOCH": record.epoch_utc,
        "MEAN_MOTION": record.mean_motion_rev_per_day,
        "ECCENTRICITY": record.eccentricity,
        "INCLINATION": record.inclination_deg,
        "RA_OF_ASC_NODE": record.ra_of_ascending_node_deg,
        "ARG_OF_PERICENTER": record.argument_of_pericenter_deg,
        "MEAN_ANOMALY": record.mean_anomaly_deg,
        "EPHEMERIS_TYPE": record.ephemeris_type,
        "ELEMENT_SET_NO": record.element_set_number,
        "REV_AT_EPOCH": record.revolution_number_at_epoch,
        "BSTAR": record.bstar,
        "MEAN_MOTION_DOT": record.mean_motion_dot,
        "MEAN_MOTION_DDOT": record.mean_motion_ddot,
        "CENTER_NAME": record.center_name,
        "REF_FRAME": record.reference_frame,
        "TIME_SYSTEM": record.time_system,
        "MEAN_ELEMENT_THEORY": record.mean_element_theory,
        "source_identity": record.source_identity,
        "source_record_sha256": record.source_record_sha256,
        "provenance": list(record.provenance),
    }


def fake_specimen(tmp_path):
    installed = load_snapshot()
    records_bytes = canonical_json_bytes(
        [mapping(record) for record in installed.records]
    )
    digest = sha256_hex(records_bytes)
    root = tmp_path / "fake-medium"
    root.mkdir(parents=True)
    manifest = {
        "schema_version": 1,
        "snapshot_id": "fake_medium_matrix",
        "created_utc": iso(START),
        "source_identity": installed.manifest.source_identity,
        "source_url": installed.manifest.source_url,
        "source_format": "fake canonical OMM JSON",
        "records_file": "records.json",
        "content_sha256": digest,
        "record_count": len(installed.records),
        "builder_identity": "wenu.test.fake-medium/1",
        "provider_policy_url": installed.manifest.provider_policy_url,
        "provider_policy_checked_utc": iso(START),
        "provenance": ["fake-data-only"],
        "warnings": ["not real provider data"],
    }
    (root / "manifest.json").write_bytes(canonical_json_bytes(manifest))
    (root / "records.json").write_bytes(records_bytes)
    parent_digest = "a" * 64
    receipt = {
        "schema_version": 1,
        "document_kind": "fake-medium-selection-receipt",
        "implementation_identity": "wenu.test.fake-medium/1",
        "parent_identity": {"content_sha256": parent_digest},
        "actual_record_count": len(installed.records),
        "subset_canonical_records_sha256": digest,
        "warnings": ["fake data only"],
    }
    receipt_bytes = canonical_json_bytes(receipt)
    (root / "selection-receipt.json").write_bytes(receipt_bytes)
    snapshot = load_snapshot_directory(root)
    identity = MatrixSpecimenIdentity(
        content_sha256=digest,
        selection_receipt_sha256=sha256_hex(receipt_bytes),
        parent_content_sha256=parent_digest,
        record_count=len(snapshot.records),
    )
    admission = ExternalSnapshotAdmissionPolicy(
        "wenu.test.matrix-admission/1",
        (ExternalSnapshotIdentity.from_snapshot(snapshot),),
    ).admit(snapshot)
    return root, snapshot, identity, admission


def observer(identifier="la-ligua"):
    return SatelliteObserver(
        observer_id=identifier,
        longitude_deg=-71.230289,
        latitude_deg=-32.443342,
        elevation_m=52.0,
        refraction_policy="vacuum",
        earth_orientation_policy="iers-a-bundled",
    )


def field(identifier, longitude):
    return SatelliteFieldOfView(
        field_id=identifier,
        center_longitude_deg=longitude,
        center_latitude_deg=-30.0,
        angular_radius_deg=1.0,
        coordinate_spec=CoordinateSpec(
            frame="gcrs-axes",
            origin="topocentric-direction",
            position_status=PositionStatus.GEOMETRIC,
            instant=iso(START),
            time_scale="utc",
            provider="fake matrix request",
        ),
    )


def queries(snapshot):
    durations = (15, 15, 30, 45, 60, 30, 45, 60, 15, 30)
    starts = (0, 0, 120, 240, 360, 480, 600, 720, 840, 960)
    return tuple(
        LocalSatelliteCrossingQuery(
            snapshot=snapshot,
            observer=observer(),
            field_of_view=field(f"field-{index:02d}", index * 20.0),
            interval=InclusiveTimeInterval(
                iso(START + timedelta(seconds=offset)),
                iso(START + timedelta(seconds=offset + duration)),
            ),
            time_tolerance_seconds=0.01,
            angular_tolerance_deg=1.0e-5,
        )
        for index, (offset, duration) in enumerate(
            zip(starts, durations, strict=True)
        )
    )


class FakeCertifier:
    def __init__(self, fail=None):
        self.fail = fail
        self.calls = []

    def certify(self, query):
        self.calls.append(query.field_of_view.field_id)
        if query.field_of_view.field_id == self.fail:
            raise ValueError("fake airmass failure")
        return {
            "field_id": query.field_of_view.field_id,
            "maximum_airmass": 2.0,
            "fake": True,
        }


class FakeExecutor:
    def __init__(self, *, mismatch=False, fallback=False):
        self.mismatch = mismatch
        self.fallback = fallback
        self.calls = []

    def __call__(self, route, query, repetition, measured):
        self.calls.append(
            (route, query.field_of_view.field_id, repetition, measured)
        )
        records = query.snapshot.records
        identifiers = tuple(record.norad_catalog_id for record in records)
        selection = ConeShellSelection(
            snapshot_sha256=query.snapshot.manifest.content_sha256,
            field_id=query.field_of_view.field_id,
            interval_start=query.interval.start,
            interval_stop=query.interval.stop,
            decisions=(
                ConeShellDecision(identifiers[0], "reject", "fake reject"),
                ConeShellDecision(identifiers[1], "retain", "fake retain"),
                ConeShellDecision(
                    identifiers[2], "indeterminate", "fake indeterminate"
                ),
            ),
        )
        if self.fallback:
            evidence = AcceleratedCrossingEvidence(
                snapshot_sha256=query.snapshot.manifest.content_sha256,
                field_id=query.field_of_view.field_id,
                interval_start=query.interval.start,
                interval_stop=query.interval.stop,
                rejected_norad_catalog_ids=(),
                exact_solver_norad_catalog_ids=identifiers,
                selection=None,
                fallback_to_exhaustive=True,
                fallback_reason="fake fallback",
            )
        else:
            evidence = AcceleratedCrossingEvidence(
                snapshot_sha256=query.snapshot.manifest.content_sha256,
                field_id=query.field_of_view.field_id,
                interval_start=query.interval.start,
                interval_stop=query.interval.stop,
                rejected_norad_catalog_ids=(identifiers[0],),
                exact_solver_norad_catalog_ids=identifiers[1:],
                selection=selection,
                fallback_to_exhaustive=False,
            )
        results = (
            ("fake mismatch",)
            if self.mismatch and route == "accelerated"
            else ()
        )
        resource = MatrixResourceObservation(
            route=route,
            field_id=query.field_of_view.field_id,
            repetition=max(repetition, 0),
            wall_seconds=0.01,
            cpu_seconds=0.005,
            peak_python_bytes=1024,
            environment={"python": "fake", "wenu": "fake"},
        )
        return MatrixRouteRun(
            results=results,
            resource=resource,
            acceleration_evidence=evidence if route == "accelerated" else None,
        )


def run(tmp_path, *, executor=None, certifier=None):
    root, snapshot, identity, admission = fake_specimen(tmp_path)
    output = tmp_path / "output"
    result = run_equivalence_matrix(
        root,
        output,
        specimen_identity=identity,
        admission=admission,
        queries=queries(snapshot),
        airmass_certifier=certifier or FakeCertifier(),
        executor=executor or FakeExecutor(),
    )
    return result, root


def test_fake_matrix_publishes_strict_canonical_evidence(tmp_path):
    directory, root = run(tmp_path)

    report_bytes = (directory / "equivalence-report.json").read_bytes()
    report = json.loads(report_bytes)
    assert canonical_json_bytes(report) == report_bytes
    assert report["document_kind"] == MATRIX_DOCUMENT_KIND
    assert report["implementation_identity"] == CROSSING_MATRIX_IMPLEMENTATION
    assert report["field_count"] == 10
    assert report["warmup_count"] == 1
    assert report["measured_repetitions"] == 3
    assert report["equivalence"] == {
        "python_tuple_equality": True,
        "canonical_byte_equality": True,
        "per_field_digest_equality": True,
        "whole_matrix_digest_equality": True,
        "fallback_count": 0,
        "rejected_exhaustive_crossing_count": 0,
    }
    assert report["decision_totals"] == {
        "reject": 10,
        "retain": 10,
        "indeterminate": 10,
    }
    assert directory.name == sha256_hex(report_bytes)
    assert str(root) not in report_bytes.decode()
    assert len(json.loads(
        (directory / "resource-observations.json").read_text()
    )) == 60


def test_identical_existing_product_is_revalidated(tmp_path):
    directory, _root = run(tmp_path)
    root, snapshot, identity, admission = fake_specimen(tmp_path / "again")
    same = run_equivalence_matrix(
        root,
        directory.parent,
        specimen_identity=identity,
        admission=admission,
        queries=queries(snapshot),
        airmass_certifier=FakeCertifier(),
        executor=FakeExecutor(),
    )
    assert same == directory


def test_existing_manifest_tamper_fails_revalidation(tmp_path):
    directory, _root = run(tmp_path)
    (directory / "matrix-manifest.json").write_bytes(b"{}\n")
    root, snapshot, identity, admission = fake_specimen(tmp_path / "again")

    with pytest.raises(ValueError, match="matrix manifest"):
        run_equivalence_matrix(
            root,
            directory.parent,
            specimen_identity=identity,
            admission=admission,
            queries=queries(snapshot),
            airmass_certifier=FakeCertifier(),
            executor=FakeExecutor(),
        )


def test_result_mismatch_fails_closed_without_publication(tmp_path):
    root, snapshot, identity, admission = fake_specimen(tmp_path)
    output = tmp_path / "output"
    with pytest.raises(MatrixEquivalenceError, match="result tuples differ"):
        run_equivalence_matrix(
            root,
            output,
            specimen_identity=identity,
            admission=admission,
            queries=queries(snapshot),
            airmass_certifier=FakeCertifier(),
            executor=FakeExecutor(mismatch=True),
        )
    assert not output.exists()


def test_fallback_is_forbidden(tmp_path):
    root, snapshot, identity, admission = fake_specimen(tmp_path)
    with pytest.raises(MatrixEquivalenceError, match="fallback is forbidden"):
        run_equivalence_matrix(
            root,
            tmp_path / "output",
            specimen_identity=identity,
            admission=admission,
            queries=queries(snapshot),
            airmass_certifier=FakeCertifier(),
            executor=FakeExecutor(fallback=True),
        )


def test_airmass_admission_is_atomic_before_executor(tmp_path):
    root, snapshot, identity, admission = fake_specimen(tmp_path)
    executor = FakeExecutor()
    with pytest.raises(MatrixEquivalenceError, match="airmass admission"):
        run_equivalence_matrix(
            root,
            tmp_path / "output",
            specimen_identity=identity,
            admission=admission,
            queries=queries(snapshot),
            airmass_certifier=FakeCertifier(fail="field-08"),
            executor=executor,
        )
    assert executor.calls == []


def test_receipt_tamper_fails_before_any_matrix_work(tmp_path):
    root, snapshot, identity, admission = fake_specimen(tmp_path)
    (root / "selection-receipt.json").write_bytes(b"{}\n")
    executor = FakeExecutor()
    with pytest.raises(ValueError, match="receipt digest"):
        run_equivalence_matrix(
            root,
            tmp_path / "output",
            specimen_identity=identity,
            admission=admission,
            queries=queries(snapshot),
            airmass_certifier=FakeCertifier(),
            executor=executor,
        )
    assert executor.calls == []


# Production-path tests stay deliberately small: no real external specimen and
# no repeated scientific routes are executed here.
def test_frozen_production_fixture_uses_only_short_and_long_intervals():
    fields = MATRIX_REQUEST_FIXTURE["fields"]
    durations = {
        (
            datetime.fromisoformat(item["interval_stop"].replace("Z", "+00:00"))
            - datetime.fromisoformat(item["interval_start"].replace("Z", "+00:00"))
        ).total_seconds()
        for item in fields
    }
    assert len(fields) == 10
    assert durations == {15.0, 60.0}
    assert fields[0]["interval_start"] == fields[1]["interval_start"]
    assert fields[0]["interval_stop"] == fields[1]["interval_stop"]
    assert sha256_hex(canonical_json_bytes(MATRIX_REQUEST_FIXTURE)) == (
        MATRIX_REQUEST_FIXTURE_SHA256
    )


def test_production_queries_preserve_frozen_fixture(tmp_path):
    _root, snapshot, _identity, _admission = fake_specimen(tmp_path)
    built = build_matrix_queries(snapshot)
    assert [item.field_of_view.field_id for item in built] == [
        item["field_id"] for item in MATRIX_REQUEST_FIXTURE["fields"]
    ]
    assert {
        (
            datetime.fromisoformat(item.interval.stop.replace("Z", "+00:00"))
            - datetime.fromisoformat(item.interval.start.replace("Z", "+00:00"))
        ).total_seconds()
        for item in built
    } == {15.0, 60.0}


def test_accepted_receipt_constraints_are_exact():
    receipt = {
        "implementation_identity": "wenu.satellites.snapshot_evidence.medium/1",
        "bin_results": [
            {
                "membership_count": 2,
                "required_representative_count": 2,
            }
            for _index in range(24)
        ],
        "fill_norad_catalog_ids": list(range(208)),
        "actual_record_count": 256,
        "subset_canonical_records_sha256": (
            ACCEPTED_MEDIUM_IDENTITY.content_sha256
        ),
        "parent_identity": {
            "content_sha256": ACCEPTED_MEDIUM_IDENTITY.parent_content_sha256
        },
    }
    assert validate_accepted_medium_receipt(receipt) is receipt
    receipt["fill_norad_catalog_ids"].pop()
    with pytest.raises(ValueError, match="fill constraint"):
        validate_accepted_medium_receipt(receipt)


def test_production_entry_requires_acknowledgement_before_file_access(tmp_path):
    with pytest.raises(ValueError, match="acknowledgement"):
        run_production_equivalence_matrix(
            tmp_path / "does-not-exist",
            tmp_path / "output",
            specimen_identity=ACCEPTED_MEDIUM_IDENTITY,
            acknowledgement="not accepted",
        )


def test_fresh_subprocess_executor_uses_canonical_protocol(tmp_path, monkeypatch):
    root, snapshot, _identity, _admission = fake_specimen(tmp_path)
    query = queries(snapshot)[0]

    def fake_run(command, **kwargs):
        assert command[:3] == [
            command[0], "-m",
            "wenu.satellites.crossing_matrix_execution",
        ]
        request = json.loads(Path(command[-2]).read_bytes())
        assert request["protocol"] == MATRIX_WORKER_PROTOCOL
        response = {
            "protocol": MATRIX_WORKER_PROTOCOL,
            "results": [],
            "resource": {
                "route": "exhaustive",
                "field_id": query.field_of_view.field_id,
                "repetition": 0,
                "wall_seconds": 0.0,
                "cpu_seconds": 0.0,
                "peak_python_bytes": 0,
                "environment": {"python": "fake"},
                "implementation": "fresh-subprocess-per-route-query-run/1",
            },
            "acceleration_evidence": None,
        }
        Path(command[-1]).write_bytes(canonical_json_bytes(response))
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = FreshSubprocessMatrixExecutor(root)(
        "exhaustive", query, 0, True
    )
    assert result.results == ()
    assert result.resource.field_id == query.field_of_view.field_id


def test_fresh_subprocess_executor_timeout_is_fail_closed(tmp_path, monkeypatch):
    root, snapshot, _identity, _admission = fake_specimen(tmp_path)
    query = queries(snapshot)[0]

    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(TimeoutError, match="timed out"):
        FreshSubprocessMatrixExecutor(root, timeout_seconds=0.01)(
            "exhaustive", query, 0, True
        )


def test_complete_production_path_uses_one_fake_measured_run(tmp_path):
    root, snapshot, identity, _admission = fake_specimen(tmp_path)
    executor = FakeExecutor()
    destination = run_production_equivalence_matrix(
        root,
        tmp_path / "production-output",
        specimen_identity=identity,
        acknowledgement=REAL_EXECUTION_ACKNOWLEDGEMENT,
        policy=CrossingMatrixPolicy(warmup_count=0, measured_repetitions=1),
        certifier=FakeCertifier(),
        executor=executor,
        expected_specimen_identity=identity,
        expected_snapshot_identity=ExternalSnapshotIdentity.from_snapshot(
            snapshot
        ),
        receipt_validator=lambda receipt: receipt,
    )
    assert destination.is_dir()
    assert len(executor.calls) == 20
    assert all(call[2:] == (0, True) for call in executor.calls)
