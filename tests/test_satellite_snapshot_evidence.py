"""Deterministic medium satellite evidence specimens (fake data only)."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from wenu.satellites.elements import canonical_json_bytes, sha256_hex, source_record_digest
from wenu.satellites.snapshot_admission import (
    ExternalSnapshotAdmissionPolicy,
    ExternalSnapshotIdentity,
)
from wenu.satellites.snapshot_evidence import (
    MEDIUM_SPECIMEN_DOCUMENT_KIND,
    MEDIUM_SPECIMEN_IMPLEMENTATION,
    select_medium_snapshot,
)
from wenu.satellites.snapshots import (
    SatelliteSnapshotManifest,
    load_snapshot_directory,
)


REFERENCE = datetime(2026, 9, 17, 12, tzinfo=timezone.utc)


def iso(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def record(identifier, *, motion, inclination, eccentricity, bstar, age):
    mapping = {
        "OBJECT_NAME": f"FAKE {identifier}",
        "OBJECT_ID": f"2026-{identifier:03d}A",
        "NORAD_CAT_ID": identifier,
        "CLASSIFICATION_TYPE": "U",
        "EPOCH": iso(REFERENCE - timedelta(days=age)),
        "MEAN_MOTION": motion,
        "ECCENTRICITY": eccentricity,
        "INCLINATION": inclination,
        "RA_OF_ASC_NODE": 10.0,
        "ARG_OF_PERICENTER": 20.0,
        "MEAN_ANOMALY": 30.0,
        "EPHEMERIS_TYPE": 0,
        "ELEMENT_SET_NO": 1,
        "REV_AT_EPOCH": 1,
        "BSTAR": bstar,
        "MEAN_MOTION_DOT": 0.0,
        "MEAN_MOTION_DDOT": 0.0,
        "CENTER_NAME": "EARTH",
        "REF_FRAME": "TEME",
        "TIME_SYSTEM": "UTC",
        "MEAN_ELEMENT_THEORY": "SGP4",
        "source_identity": "Fake external source",
        "provenance": ["hand-authored-test-record"],
    }
    mapping["source_record_sha256"] = source_record_digest(mapping)
    return mapping


def records():
    return [
        record(900, motion=1.0, inclination=0, eccentricity=0, bstar=-0.001, age=-1),
        record(1000, motion=1.2, inclination=30, eccentricity=0.01, bstar=-0.0001, age=0),
        record(2000, motion=7.9, inclination=60, eccentricity=0.1, bstar=-0.00001, age=1),
        record(3000, motion=8, inclination=90, eccentricity=0.25, bstar=0, age=2),
        record(4000, motion=15, inclination=120, eccentricity=0.3, bstar=0.00001, age=7),
        record(5000, motion=14, inclination=180, eccentricity=0.02, bstar=0.0001, age=8),
        record(100000, motion=13, inclination=45, eccentricity=0.2, bstar=0.001, age=14),
        record(100001, motion=12, inclination=75, eccentricity=0.001, bstar=0.002, age=15),
    ]


def parent(tmp_path, *, reverse=False):
    root = tmp_path / ("parent-reversed" if reverse else "parent")
    root.mkdir(parents=True)
    payload = records()
    if reverse:
        payload.reverse()
    # A canonical snapshot requires full-NORAD ordering. Reversal tests selection
    # independence by assigning the same records to a separately canonical parent.
    payload.sort(key=lambda item: item["NORAD_CAT_ID"])
    records_bytes = canonical_json_bytes(payload)
    digest = sha256_hex(records_bytes)
    manifest = SatelliteSnapshotManifest(
        schema_version=1,
        snapshot_id="fake_external_parent",
        created_utc=iso(REFERENCE),
        source_identity="Fake external source",
        source_url="https://example.test/fake.csv",
        source_format="hand-authored canonical OMM JSON",
        records_file="records.json",
        content_sha256=digest,
        record_count=len(payload),
        builder_identity="wenu.test.fake-parent/1",
        provider_policy_url="https://example.test/policy",
        provider_policy_checked_utc=iso(REFERENCE),
        provenance=("fake-data-only",),
        warnings=("not real provider data",),
    )
    (root / "manifest.json").write_bytes(
        canonical_json_bytes({
            "schema_version": manifest.schema_version,
            "snapshot_id": manifest.snapshot_id,
            "created_utc": manifest.created_utc,
            "source_identity": manifest.source_identity,
            "source_url": manifest.source_url,
            "source_format": manifest.source_format,
            "records_file": manifest.records_file,
            "content_sha256": manifest.content_sha256,
            "record_count": manifest.record_count,
            "builder_identity": manifest.builder_identity,
            "provider_policy_url": manifest.provider_policy_url,
            "provider_policy_checked_utc": manifest.provider_policy_checked_utc,
            "provenance": list(manifest.provenance),
            "warnings": list(manifest.warnings),
        })
    )
    (root / "records.json").write_bytes(records_bytes)
    report = {
        "schema_version": 1,
        "document_kind": "fake-acquisition-report",
        "source_url": manifest.source_url,
        "retrieved_started_utc": iso(REFERENCE - timedelta(seconds=1)),
        "retrieved_stopped_utc": iso(REFERENCE),
        "http_status": 200,
        "provider_response_sha256": "a" * 64,
        "canonical_records_sha256": digest,
        "record_count": len(payload),
        "status": "success",
    }
    (root / "acquisition-report.json").write_bytes(canonical_json_bytes(report))
    snapshot = load_snapshot_directory(root)
    identity = ExternalSnapshotIdentity.from_snapshot(snapshot)
    admission = ExternalSnapshotAdmissionPolicy(
        "wenu.test.medium-admission/1", (identity,)
    ).admit(snapshot)
    return root, admission


def test_fake_medium_selection_publishes_canonical_bound_product(tmp_path):
    root, admission = parent(tmp_path)
    output = tmp_path / "output"

    directory = select_medium_snapshot(
        root, output, admission=admission, target_count=8
    )

    snapshot = load_snapshot_directory(directory)
    receipt_bytes = (directory / "selection-receipt.json").read_bytes()
    receipt = json.loads(receipt_bytes)
    assert canonical_json_bytes(receipt) == receipt_bytes
    assert snapshot.manifest.builder_identity == MEDIUM_SPECIMEN_IMPLEMENTATION
    assert receipt["document_kind"] == MEDIUM_SPECIMEN_DOCUMENT_KIND
    assert receipt["selected_norad_catalog_ids"] == [
        900, 1000, 2000, 3000, 4000, 5000, 100000, 100001
    ]
    assert receipt["age_reference_utc"] == iso(REFERENCE)
    assert receipt["actual_record_count"] == 8
    assert receipt["empty_bins"] == []
    assert str(root) not in receipt_bytes.decode()
    assert directory.name == snapshot.manifest.content_sha256
    assert select_medium_snapshot(
        root, output, admission=admission, target_count=8
    ) == directory


def test_every_boundary_enters_exactly_one_bin(tmp_path):
    root, admission = parent(tmp_path)
    directory = select_medium_snapshot(
        root, tmp_path / "output", admission=admission, target_count=8
    )
    receipt = json.loads((directory / "selection-receipt.json").read_text())
    totals = {}
    for result in receipt["bin_results"]:
        totals[result["axis"]] = (
            totals.get(result["axis"], 0) + result["membership_count"]
        )
    assert set(totals.values()) == {8}
    assert len(receipt["axis_definitions"]) == 6


def test_mandatory_coverage_reports_minimum_target(tmp_path):
    root, admission = parent(tmp_path)
    with pytest.raises(ValueError, match="minimum admissible target"):
        select_medium_snapshot(
            root, tmp_path / "output", admission=admission, target_count=1
        )


def test_parent_exhaustion_is_explicit_and_deterministic(tmp_path):
    root, admission = parent(tmp_path)
    directory = select_medium_snapshot(
        root, tmp_path / "output", admission=admission, target_count=20
    )
    receipt = json.loads((directory / "selection-receipt.json").read_text())
    assert receipt["actual_record_count"] == 8
    assert any("Parent exhausted" in warning for warning in receipt["warnings"])


def test_report_and_admission_mismatches_fail_before_publication(tmp_path):
    root, admission = parent(tmp_path)
    report_path = root / "acquisition-report.json"
    report = json.loads(report_path.read_text())
    report["canonical_records_sha256"] = "f" * 64
    report_path.write_bytes(canonical_json_bytes(report))

    with pytest.raises(ValueError, match="canonical digest"):
        select_medium_snapshot(
            root, tmp_path / "output", admission=admission, target_count=8
        )
    assert not (tmp_path / "output").exists()

    clean_root, clean_admission = parent(tmp_path / "other")
    other_snapshot = load_snapshot_directory(clean_root)
    wrong = ExternalSnapshotAdmissionPolicy(
        "wenu.test.wrong/1",
        (replace(
            ExternalSnapshotIdentity.from_snapshot(other_snapshot),
            source_identity="Another source",
        ),),
    )
    with pytest.raises(ValueError, match="not admitted"):
        wrong.admit(other_snapshot)
    assert clean_admission.require(other_snapshot) is other_snapshot


def test_existing_destination_is_fully_revalidated(tmp_path):
    root, admission = parent(tmp_path)
    output = tmp_path / "output"
    directory = select_medium_snapshot(
        root, output, admission=admission, target_count=8
    )
    receipt_path = directory / "selection-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["requested_target_count"] = 7
    receipt_path.write_bytes(canonical_json_bytes(receipt))

    with pytest.raises(ValueError, match="does not match selection receipt"):
        select_medium_snapshot(
            root, output, admission=admission, target_count=8
        )
