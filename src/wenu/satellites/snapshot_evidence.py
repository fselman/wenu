"""Deterministic offline evidence specimens derived from admitted snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile

from .elements import canonical_json_bytes, sha256_hex
from .snapshot_admission import ExternalSnapshotAdmission
from .snapshots import load_snapshot_directory


MEDIUM_SPECIMEN_IMPLEMENTATION = "wenu.satellites.snapshot_evidence.medium/1"
MEDIUM_SPECIMEN_DOCUMENT_KIND = "satellite-medium-selection-receipt"
REPRESENTATIVES_PER_BIN = 2

_AXIS_ORDER = (
    "mean_motion",
    "inclination",
    "eccentricity",
    "bstar",
    "signed_element_age",
    "norad_identifier_width",
)
_BIN_ORDER = {
    "mean_motion": ("geo_deep_like", "meo_like", "leo_like"),
    "inclination": (
        "i_0_30", "i_30_60", "i_60_90", "i_90_120", "i_120_180"
    ),
    "eccentricity": (
        "e_0_0p01", "e_0p01_0p1", "e_0p1_0p25", "e_over_0p25"
    ),
    "bstar": (
        "bstar_negative_large", "bstar_negative_small", "bstar_zero",
        "bstar_positive_small", "bstar_positive_large",
    ),
    "signed_element_age": (
        "age_future", "age_0_1", "age_1_7", "age_7_14", "age_over_14"
    ),
    "norad_identifier_width": (
        "norad_five_or_fewer", "norad_more_than_five"
    ),
}
_BIN_DEFINITIONS = {
    "mean_motion": {
        "units": "revolutions/day",
        "bins": (
            {"name": "geo_deep_like", "condition": "0 < n < 1.2"},
            {"name": "meo_like", "condition": "1.2 <= n < 8"},
            {"name": "leo_like", "condition": "n >= 8"},
        ),
    },
    "inclination": {
        "units": "degrees",
        "bins": (
            {"name": "i_0_30", "condition": "0 <= i < 30"},
            {"name": "i_30_60", "condition": "30 <= i < 60"},
            {"name": "i_60_90", "condition": "60 <= i < 90"},
            {"name": "i_90_120", "condition": "90 <= i < 120"},
            {"name": "i_120_180", "condition": "120 <= i <= 180"},
        ),
    },
    "eccentricity": {
        "units": "dimensionless",
        "bins": (
            {"name": "e_0_0p01", "condition": "0 <= e < 0.01"},
            {"name": "e_0p01_0p1", "condition": "0.01 <= e < 0.1"},
            {"name": "e_0p1_0p25", "condition": "0.1 <= e <= 0.25"},
            {"name": "e_over_0p25", "condition": "0.25 < e < 1"},
        ),
    },
    "bstar": {
        "units": "inverse Earth radii",
        "bins": (
            {"name": "bstar_negative_large", "condition": "BSTAR < -0.0001"},
            {"name": "bstar_negative_small", "condition": "-0.0001 <= BSTAR < 0"},
            {"name": "bstar_zero", "condition": "BSTAR == 0"},
            {"name": "bstar_positive_small", "condition": "0 < BSTAR <= 0.0001"},
            {"name": "bstar_positive_large", "condition": "BSTAR > 0.0001"},
        ),
    },
    "signed_element_age": {
        "units": "days",
        "bins": (
            {"name": "age_future", "condition": "age < 0"},
            {"name": "age_0_1", "condition": "0 <= age <= 1"},
            {"name": "age_1_7", "condition": "1 < age <= 7"},
            {"name": "age_7_14", "condition": "7 < age <= 14"},
            {"name": "age_over_14", "condition": "age > 14"},
        ),
    },
    "norad_identifier_width": {
        "units": "decimal digits",
        "bins": (
            {"name": "norad_five_or_fewer", "condition": "NORAD <= 99999"},
            {"name": "norad_more_than_five", "condition": "NORAD > 99999"},
        ),
    },
}


def _regular_bytes(path, *, name):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{name} must be an existing non-symlink file.")
    return path.read_bytes()


def _json_object(data, *, name):
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{name} must be valid UTF-8 JSON.") from error
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object.")
    return value


def _utc_datetime(value, *, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.")
    return parsed.astimezone(timezone.utc)


def _bin(record, axis, reference):
    if axis == "mean_motion":
        value = record.mean_motion_rev_per_day
        return "geo_deep_like" if value < 1.2 else (
            "meo_like" if value < 8.0 else "leo_like"
        )
    if axis == "inclination":
        value = record.inclination_deg
        if value < 30.0:
            return "i_0_30"
        if value < 60.0:
            return "i_30_60"
        if value < 90.0:
            return "i_60_90"
        if value < 120.0:
            return "i_90_120"
        return "i_120_180"
    if axis == "eccentricity":
        value = record.eccentricity
        if value < 0.01:
            return "e_0_0p01"
        if value < 0.1:
            return "e_0p01_0p1"
        if value <= 0.25:
            return "e_0p1_0p25"
        return "e_over_0p25"
    if axis == "bstar":
        value = record.bstar
        if value < -0.0001:
            return "bstar_negative_large"
        if value < 0.0:
            return "bstar_negative_small"
        if value == 0.0:
            return "bstar_zero"
        if value <= 0.0001:
            return "bstar_positive_small"
        return "bstar_positive_large"
    if axis == "signed_element_age":
        epoch = _utc_datetime(record.epoch_utc, name="record epoch")
        value = (reference - epoch).total_seconds() / 86400.0
        if value < 0.0:
            return "age_future"
        if value <= 1.0:
            return "age_0_1"
        if value <= 7.0:
            return "age_1_7"
        if value <= 14.0:
            return "age_7_14"
        return "age_over_14"
    return (
        "norad_five_or_fewer"
        if record.norad_catalog_id <= 99999
        else "norad_more_than_five"
    )


def _rank(parent_digest, *parts):
    payload = "\0".join((parent_digest, *(str(part) for part in parts)))
    return sha256(payload.encode("utf-8")).hexdigest()


def _validate_report(report, report_bytes, snapshot, parent_directory):
    required = {
        "schema_version", "document_kind", "source_url",
        "retrieved_started_utc", "retrieved_stopped_utc", "http_status",
        "provider_response_file", "provider_response_bytes",
        "provider_response_sha256", "canonical_records_sha256",
        "record_count", "status",
    }
    missing = sorted(required - set(report))
    if missing:
        raise ValueError(f"acquisition report is missing required fields: {missing}.")
    manifest = snapshot.manifest
    if report["schema_version"] != 1:
        raise ValueError("acquisition report schema_version must be 1.")
    if report["status"] != "success" or report["http_status"] != 200:
        raise ValueError("acquisition report must record successful HTTP 200 acquisition.")
    if report["canonical_records_sha256"] != manifest.content_sha256:
        raise ValueError("acquisition report canonical digest does not match parent.")
    if report["source_url"] != manifest.source_url:
        raise ValueError("acquisition report source URL does not match parent.")
    if report["record_count"] != len(snapshot.records):
        raise ValueError("acquisition report record count does not match parent.")
    started = _utc_datetime(
        report["retrieved_started_utc"], name="retrieved_started_utc"
    )
    stopped = _utc_datetime(
        report["retrieved_stopped_utc"], name="retrieved_stopped_utc"
    )
    if stopped < started:
        raise ValueError("acquisition retrieval interval is reversed.")
    digest = report["provider_response_sha256"]
    if not isinstance(digest, str) or len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError("provider_response_sha256 must be lowercase SHA-256.")
    filename = report["provider_response_file"]
    if (
        not isinstance(filename, str)
        or not filename
        or "/" in filename
        or "\\" in filename
    ):
        raise ValueError("provider_response_file must be a local resource name.")
    response_bytes = _regular_bytes(
        Path(parent_directory) / filename,
        name="provider response",
    )
    if report["provider_response_bytes"] != len(response_bytes):
        raise ValueError("provider response byte count does not match report.")
    if sha256_hex(response_bytes) != digest:
        raise ValueError("provider response digest does not match report.")
    return stopped, sha256_hex(report_bytes)


def _source_mappings(parent_directory, snapshot):
    path = Path(parent_directory) / snapshot.manifest.records_file
    data = _regular_bytes(path, name="parent records")
    try:
        mappings = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("parent records must be valid UTF-8 JSON.") from error
    if not isinstance(mappings, list) or canonical_json_bytes(mappings) != data:
        raise ValueError("parent records must be a canonical JSON list.")
    identifiers = tuple(item.get("NORAD_CAT_ID") for item in mappings)
    expected = tuple(record.norad_catalog_id for record in snapshot.records)
    if identifiers != expected:
        raise ValueError("parent record mappings do not match validated snapshot.")
    return mappings


def _validate_existing(directory, expected_receipt):
    snapshot = load_snapshot_directory(directory)
    receipt_bytes = _regular_bytes(
        Path(directory) / "selection-receipt.json",
        name="selection receipt",
    )
    receipt = _json_object(receipt_bytes, name="selection receipt")
    if canonical_json_bytes(receipt) != receipt_bytes:
        raise ValueError("selection receipt is not canonical JSON.")
    if receipt != expected_receipt:
        raise ValueError("existing medium specimen does not match selection receipt.")
    if receipt["subset_canonical_records_sha256"] != snapshot.manifest.content_sha256:
        raise ValueError("selection receipt digest does not match derived snapshot.")
    receipt_digest = sha256_hex(receipt_bytes)
    if f"selection-receipt-sha256:{receipt_digest}" not in snapshot.manifest.provenance:
        raise ValueError("derived manifest does not bind the selection receipt.")
    return snapshot


def select_medium_snapshot(
    parent_directory,
    output_root,
    *,
    admission,
    target_count=256,
):
    """Select and atomically publish one deterministic external specimen."""
    if not isinstance(target_count, int) or isinstance(target_count, bool):
        raise TypeError("target_count must be an integer.")
    if target_count <= 0:
        raise ValueError("target_count must be positive.")
    if not isinstance(admission, ExternalSnapshotAdmission):
        raise TypeError("admission must be an ExternalSnapshotAdmission.")

    parent_directory = Path(parent_directory).expanduser()
    snapshot = load_snapshot_directory(parent_directory)
    admission.require(snapshot)

    report_bytes = _regular_bytes(
        parent_directory / "acquisition-report.json",
        name="acquisition report",
    )
    report = _json_object(report_bytes, name="acquisition report")
    reference, report_digest = _validate_report(
        report, report_bytes, snapshot, parent_directory
    )
    mappings = _source_mappings(parent_directory, snapshot)
    parent_digest = snapshot.manifest.content_sha256

    memberships = {
        axis: {name: [] for name in _BIN_ORDER[axis]} for axis in _AXIS_ORDER
    }
    by_id = {record.norad_catalog_id: record for record in snapshot.records}
    for record in snapshot.records:
        for axis in _AXIS_ORDER:
            memberships[axis][_bin(record, axis, reference)].append(
                record.norad_catalog_id
            )

    selected = set()
    bin_receipts = []
    empty_bins = []
    for axis in _AXIS_ORDER:
        for name in _BIN_ORDER[axis]:
            members = memberships[axis][name]
            ranked = sorted(
                members,
                key=lambda identifier: (
                    _rank(parent_digest, axis, name, identifier), identifier
                ),
            )
            representatives = ranked[:REPRESENTATIVES_PER_BIN]
            selected.update(representatives)
            if not members:
                empty_bins.append({"axis": axis, "bin": name})
            bin_receipts.append({
                "axis": axis,
                "bin": name,
                "membership_count": len(members),
                "required_representative_count": min(
                    REPRESENTATIVES_PER_BIN, len(members)
                ),
                "selected_representative_norad_catalog_ids": representatives,
            })

    minimum_target = len(selected)
    if minimum_target > target_count:
        raise ValueError(
            "mandatory coverage exceeds target_count; "
            f"minimum admissible target is {minimum_target}."
        )

    actual_target = min(target_count, len(snapshot.records))
    fill_candidates = sorted(
        set(by_id) - selected,
        key=lambda identifier: (
            _rank(parent_digest, "fill", identifier), identifier
        ),
    )
    fill_used = fill_candidates[: max(0, actual_target - len(selected))]
    selected.update(fill_used)
    selected_ids = sorted(selected)
    selected_mappings = [
        mapping for mapping in mappings if mapping["NORAD_CAT_ID"] in selected
    ]
    records_bytes = canonical_json_bytes(selected_mappings)
    subset_digest = sha256_hex(records_bytes)
    warnings = [
        "Deterministic coverage specimen; not a complete or statistical population."
    ]
    if target_count > len(snapshot.records):
        warnings.append(
            "Parent exhausted before requested target; every parent record selected."
        )

    receipt = {
        "schema_version": 1,
        "document_kind": MEDIUM_SPECIMEN_DOCUMENT_KIND,
        "implementation_identity": MEDIUM_SPECIMEN_IMPLEMENTATION,
        "admission_policy_identity": admission.policy_identity,
        "parent_identity": {
            "schema_version": admission.identity.schema_version,
            "snapshot_id": admission.identity.snapshot_id,
            "content_sha256": admission.identity.content_sha256,
            "source_identity": admission.identity.source_identity,
            "source_url": admission.identity.source_url,
            "builder_identity": admission.identity.builder_identity,
        },
        "parent_record_count": len(snapshot.records),
        "parent_acquisition_report_sha256": report_digest,
        "provider_response_sha256": report["provider_response_sha256"],
        "age_reference_utc": report["retrieved_stopped_utc"],
        "requested_target_count": target_count,
        "actual_record_count": len(selected_ids),
        "representatives_per_nonempty_bin": REPRESENTATIVES_PER_BIN,
        "axis_order": list(_AXIS_ORDER),
        "axis_definitions": [
            {
                "axis": axis,
                "units": _BIN_DEFINITIONS[axis]["units"],
                "bins": list(_BIN_DEFINITIONS[axis]["bins"]),
            }
            for axis in _AXIS_ORDER
        ],
        "representative_rank_recipe": (
            "sha256(parent_digest + NUL + axis + NUL + bin + NUL + "
            "decimal_full_norad_id), then full NORAD integer"
        ),
        "fill_rank_recipe": (
            "sha256(parent_digest + NUL + fill + NUL + "
            "decimal_full_norad_id), then full NORAD integer"
        ),
        "bin_results": bin_receipts,
        "empty_bins": empty_bins,
        "fill_norad_catalog_ids": fill_used,
        "selected_norad_catalog_ids": selected_ids,
        "subset_canonical_records_sha256": subset_digest,
        "warnings": warnings,
        "population_statement": (
            "This deterministic coverage specimen does not represent "
            "population frequencies."
        ),
    }
    receipt_bytes = canonical_json_bytes(receipt)
    receipt_digest = sha256_hex(receipt_bytes)
    manifest = {
        "schema_version": 1,
        "snapshot_id": f"medium_{subset_digest[:16]}",
        "created_utc": report["retrieved_stopped_utc"],
        "source_identity": snapshot.manifest.source_identity,
        "source_url": snapshot.manifest.source_url,
        "source_format": (
            "Deterministic subset of canonical OMM JSON"
        ),
        "records_file": "records.json",
        "content_sha256": subset_digest,
        "record_count": len(selected_ids),
        "builder_identity": MEDIUM_SPECIMEN_IMPLEMENTATION,
        "provider_policy_url": snapshot.manifest.provider_policy_url,
        "provider_policy_checked_utc": (
            snapshot.manifest.provider_policy_checked_utc
        ),
        "provenance": [
            f"parent-canonical-records-sha256:{parent_digest}",
            f"parent-acquisition-report-sha256:{report_digest}",
            f"selection-receipt-sha256:{receipt_digest}",
        ],
        "warnings": warnings,
    }

    output_root = Path(output_root).expanduser()
    output_root.mkdir(parents=True, exist_ok=True)
    if output_root.is_symlink() or not output_root.is_dir():
        raise ValueError("output_root must be a non-symlink directory.")
    destination = output_root / subset_digest
    if destination.exists():
        _validate_existing(destination, receipt)
        return destination

    stage = Path(tempfile.mkdtemp(prefix=".medium-", dir=output_root))
    try:
        (stage / "manifest.json").write_bytes(canonical_json_bytes(manifest))
        (stage / "records.json").write_bytes(records_bytes)
        (stage / "selection-receipt.json").write_bytes(receipt_bytes)
        _validate_existing(stage, receipt)
        try:
            os.rename(stage, destination)
        except FileExistsError:
            _validate_existing(destination, receipt)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return destination
