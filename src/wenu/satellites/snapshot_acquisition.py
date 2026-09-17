"""Provider-governed construction of external satellite snapshots.

This module deliberately has no network client.  Callers must inject the one
transport operation, which keeps policy acknowledgement and live access under
separate authorization.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Callable

from wenu import __version__

from .elements import (
    _utc,
    canonical_json_bytes,
    sha256_hex,
    source_record_digest,
)
from .snapshots import load_snapshot_directory


POLICY_URL = "https://celestrak.org/usage-policy.php"
ACTIVE_GP_URL = (
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=CSV"
)
SOURCE_IDENTITY = "CelesTrak GP GROUP=active"
BUILDER_IDENTITY = "wenu.satellites.snapshot_acquisition/1"
POLICY_IDENTITY = "wenu.satellites.snapshot_acquisition.policy/1"
_CSV_HEADER = (
    "OBJECT_NAME",
    "OBJECT_ID",
    "EPOCH",
    "MEAN_MOTION",
    "ECCENTRICITY",
    "INCLINATION",
    "RA_OF_ASC_NODE",
    "ARG_OF_PERICENTER",
    "MEAN_ANOMALY",
    "EPHEMERIS_TYPE",
    "CLASSIFICATION_TYPE",
    "NORAD_CAT_ID",
    "ELEMENT_SET_NO",
    "REV_AT_EPOCH",
    "BSTAR",
    "MEAN_MOTION_DOT",
    "MEAN_MOTION_DDOT",
)
_REQUIRED_POLICY_CLAUSES = {
    "documented_query": "gp-data-formats.php",
    "two_hour_cadence": "2 hours",
    "one_download_per_update": "once per update",
    "caching": "cache",
    "stop_on_non_200": "non-http 200",
}
_PUBLICATION_FILES = (
    "manifest.json",
    "records.json",
    "acquisition-report.json",
    "policy-receipt.json",
    "policy-response.html",
    "provider-response.csv",
)


@dataclass(frozen=True)
class TransportResponse:
    """Exact response returned by an injected single-request transport."""

    requested_url: str
    resolved_url: str
    status: int
    media_type: str
    body: bytes
    started_utc: str
    stopped_utc: str


Transport = Callable[[str], TransportResponse]


class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def _response(response, expected_url, media_prefix):
    if not isinstance(response, TransportResponse):
        raise TypeError("transport must return TransportResponse.")
    if response.requested_url != expected_url:
        raise ValueError("transport requested an unexpected URL.")
    if response.resolved_url != expected_url:
        raise ValueError(
            "redirects and unexpected resolved URLs are forbidden."
        )
    if response.status != 200:
        raise ValueError("provider response must have HTTP status 200.")
    if not isinstance(response.body, bytes) or not response.body:
        raise ValueError("provider response body must be non-empty bytes.")
    if (
        not isinstance(response.media_type, str)
        or not response.media_type.lower().startswith(media_prefix)
    ):
        raise ValueError("provider response has an unexpected media type.")
    started = _utc(response.started_utc, name="started_utc")
    stopped = _utc(response.stopped_utc, name="stopped_utc")
    if stopped < started:
        raise ValueError("response stop instant precedes start instant.")
    return started, stopped


def _read_regular(path, name):
    candidate = path / name
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError(f"{name} must be a non-symlink regular file.")
    return candidate.read_bytes()


def _policy_document(response):
    try:
        document = response.body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("policy response must be UTF-8 HTML.") from error
    parser = _VisibleText()
    parser.feed(document)
    text = " ".join(" ".join(parser.parts).split())
    lower = text.lower()
    if "celestrak usage policy" not in lower:
        raise ValueError("policy title is absent.")
    missing = [
        name
        for name, phrase in _REQUIRED_POLICY_CLAUSES.items()
        if phrase.lower() not in lower
    ]
    if missing:
        raise ValueError(f"policy clauses are absent: {missing}.")
    import re

    dates = re.findall(
        r"(?:updated|published)\s+"
        r"(\d{4}[- ](?:\d{2}|[A-Za-z]{3,9})[- ]\d{1,2})",
        text,
        flags=re.IGNORECASE,
    )
    if len(set(dates)) != 1:
        raise ValueError(
            "policy published/updated date is absent or ambiguous."
        )
    return text, dates[0]


def freeze_policy_receipt(directory, *, transport: Transport):
    """Fetch exactly one policy response and freeze its immutable receipt."""
    root = Path(directory).expanduser()
    if root.exists():
        raise FileExistsError("policy receipt directory already exists.")
    root.parent.mkdir(parents=True, exist_ok=True)
    if root.parent.is_symlink():
        raise ValueError("policy receipt parent must not be a symlink.")
    response = transport(POLICY_URL)
    started, stopped = _response(response, POLICY_URL, "text/html")
    _text, policy_date = _policy_document(response)
    digest = sha256_hex(response.body)
    receipt = {
        "schema_version": 1,
        "document_kind": "celestrak-policy-receipt",
        "policy_url": POLICY_URL,
        "retrieved_started_utc": started,
        "retrieved_stopped_utc": stopped,
        "http_status": response.status,
        "media_type": response.media_type,
        "response_bytes": len(response.body),
        "policy_response_sha256": digest,
        "policy_response_file": "policy-response.html",
        "policy_title": "CelesTrak Usage Policy",
        "policy_date": policy_date,
        "required_clauses": sorted(_REQUIRED_POLICY_CLAUSES),
        "wenu_version": __version__,
        "implementation_identity": POLICY_IDENTITY,
    }
    staging = Path(tempfile.mkdtemp(prefix=f".{root.name}.", dir=root.parent))
    try:
        (staging / "policy-response.html").write_bytes(response.body)
        (staging / "policy-receipt.json").write_bytes(
            canonical_json_bytes(receipt)
        )
        _load_policy_receipt(staging)
        os.rename(staging, root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return root


def _load_policy_receipt(directory):
    root = Path(directory).expanduser()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("policy receipt must be a non-symlink directory.")
    raw = _read_regular(root, "policy-response.html")
    receipt_bytes = _read_regular(root, "policy-receipt.json")
    try:
        receipt = json.loads(receipt_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("policy receipt must be valid UTF-8 JSON.") from error
    expected = {
        "schema_version", "document_kind", "policy_url",
        "retrieved_started_utc", "retrieved_stopped_utc", "http_status",
        "media_type", "response_bytes", "policy_response_sha256",
        "policy_response_file", "policy_title", "policy_date",
        "required_clauses", "wenu_version", "implementation_identity",
    }
    if set(receipt) != expected:
        raise ValueError("policy receipt keys do not match schema version 1.")
    if receipt["schema_version"] != 1 or receipt["document_kind"] != (
        "celestrak-policy-receipt"
    ):
        raise ValueError("unsupported policy receipt.")
    if receipt["policy_url"] != POLICY_URL:
        raise ValueError("policy receipt URL does not match CelesTrak.")
    if receipt["policy_response_file"] != "policy-response.html":
        raise ValueError("policy response filename is unsupported.")
    if receipt["http_status"] != 200:
        raise ValueError("policy receipt does not record HTTP 200.")
    if receipt["response_bytes"] != len(raw):
        raise ValueError("policy response byte count does not match receipt.")
    if receipt["policy_response_sha256"] != sha256_hex(raw):
        raise ValueError("policy response digest does not match receipt.")
    if receipt["required_clauses"] != sorted(_REQUIRED_POLICY_CLAUSES):
        raise ValueError("policy receipt clause set is unsupported.")
    _utc(receipt["retrieved_started_utc"], name="retrieved_started_utc")
    _utc(receipt["retrieved_stopped_utc"], name="retrieved_stopped_utc")
    _policy_document(TransportResponse(
        POLICY_URL, POLICY_URL, 200, "text/html", raw,
        receipt["retrieved_started_utc"], receipt["retrieved_stopped_utc"],
    ))
    return receipt, raw, receipt_bytes


def _number(value, kind, name):
    if value == "":
        raise ValueError(f"{name} must not be blank.")
    try:
        return kind(value)
    except ValueError as error:
        raise ValueError(f"{name} has an invalid value.") from error


def _normalize_csv(body, raw_digest):
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("provider response must be UTF-8 CSV.") from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != list(_CSV_HEADER):
        raise ValueError(
            "provider CSV header does not match the fixed contract."
        )
    records = []
    identifiers = set()
    for row_number, row in enumerate(reader, start=2):
        if None in row or any(row[name] is None for name in _CSV_HEADER):
            raise ValueError(
                f"CSV row {row_number} has the wrong field count."
            )
        if any(row[name].strip() == "" for name in _CSV_HEADER):
            raise ValueError(f"CSV row {row_number} contains a blank value.")
        mapping = {
            "OBJECT_NAME": row["OBJECT_NAME"].strip(),
            "OBJECT_ID": row["OBJECT_ID"].strip(),
            "NORAD_CAT_ID": _number(row["NORAD_CAT_ID"], int, "NORAD_CAT_ID"),
            "CLASSIFICATION_TYPE": row["CLASSIFICATION_TYPE"].strip(),
            "EPOCH": row["EPOCH"].strip(),
            "MEAN_MOTION": _number(row["MEAN_MOTION"], float, "MEAN_MOTION"),
            "ECCENTRICITY": _number(
                row["ECCENTRICITY"], float, "ECCENTRICITY"
            ),
            "INCLINATION": _number(row["INCLINATION"], float, "INCLINATION"),
            "RA_OF_ASC_NODE": _number(
                row["RA_OF_ASC_NODE"], float, "RA_OF_ASC_NODE"
            ),
            "ARG_OF_PERICENTER": _number(
                row["ARG_OF_PERICENTER"], float, "ARG_OF_PERICENTER"
            ),
            "MEAN_ANOMALY": _number(
                row["MEAN_ANOMALY"], float, "MEAN_ANOMALY"
            ),
            "EPHEMERIS_TYPE": _number(
                row["EPHEMERIS_TYPE"], int, "EPHEMERIS_TYPE"
            ),
            "ELEMENT_SET_NO": _number(
                row["ELEMENT_SET_NO"], int, "ELEMENT_SET_NO"
            ),
            "REV_AT_EPOCH": _number(row["REV_AT_EPOCH"], int, "REV_AT_EPOCH"),
            "BSTAR": _number(row["BSTAR"], float, "BSTAR"),
            "MEAN_MOTION_DOT": _number(
                row["MEAN_MOTION_DOT"], float, "MEAN_MOTION_DOT"
            ),
            "MEAN_MOTION_DDOT": _number(
                row["MEAN_MOTION_DDOT"], float, "MEAN_MOTION_DDOT"
            ),
            "CENTER_NAME": "EARTH",
            "REF_FRAME": "TEME",
            "TIME_SYSTEM": "UTC",
            "MEAN_ELEMENT_THEORY": "SGP4",
            "source_identity": SOURCE_IDENTITY,
            "provenance": [
                ACTIVE_GP_URL,
                f"provider-response-sha256:{raw_digest}",
            ],
        }
        mapping["source_record_sha256"] = source_record_digest(mapping)
        from .elements import SatelliteElementRecord
        SatelliteElementRecord.from_mapping(mapping)
        identifier = mapping["NORAD_CAT_ID"]
        if identifier in identifiers:
            raise ValueError(
                "provider response contains duplicate NORAD identifiers."
            )
        identifiers.add(identifier)
        records.append(mapping)
    if not records:
        raise ValueError("provider response contains no records.")
    records.sort(key=lambda item: item["NORAD_CAT_ID"])
    return records


def _validate_publication(directory):
    snapshot = load_snapshot_directory(directory)
    report = json.loads(_read_regular(directory, "acquisition-report.json"))
    policy, raw_policy, _receipt = _load_policy_receipt(directory)
    raw_provider = _read_regular(directory, "provider-response.csv")
    records = _read_regular(directory, "records.json")
    if report["canonical_records_sha256"] != sha256_hex(records):
        raise ValueError("acquisition report records digest does not match.")
    if report["provider_response_sha256"] != sha256_hex(raw_provider):
        raise ValueError("acquisition report provider digest does not match.")
    if report["accepted_policy_sha256"] != sha256_hex(raw_policy):
        raise ValueError("acquisition report policy digest does not match.")
    if report["accepted_policy_sha256"] != policy["policy_response_sha256"]:
        raise ValueError("policy receipt and acquisition report disagree.")
    if report["record_count"] != len(snapshot.records):
        raise ValueError("acquisition report record count does not match.")
    return snapshot


def _parsed_utc(value):
    return datetime.fromisoformat(
        _utc(value, name="UTC instant").replace("Z", "+00:00")
    )


def _fresh_cached_snapshot(root, policy_digest, accepted_utc):
    accepted = _parsed_utc(accepted_utc)
    matches = []
    for candidate in root.iterdir():
        if candidate.name.startswith(".") or not candidate.is_dir():
            continue
        try:
            _validate_publication(candidate)
            report = json.loads(
                _read_regular(candidate, "acquisition-report.json")
            )
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            continue
        if (
            report.get("source_url") != ACTIVE_GP_URL
            or report.get("accepted_policy_sha256") != policy_digest
        ):
            continue
        age = accepted - _parsed_utc(report["retrieved_stopped_utc"])
        if 0 <= age.total_seconds() < 2 * 60 * 60:
            matches.append(candidate)
    if len(matches) > 1:
        raise ValueError("multiple fresh cached Active snapshots exist.")
    return matches[0] if matches else None


def acquire_active_snapshot(
    snapshot_root,
    policy_directory,
    *,
    accepted_policy_sha256,
    accepted_utc,
    transport: Transport,
):
    """Acquire one injected Active-group response and publish atomically."""
    policy, policy_raw, policy_receipt_bytes = _load_policy_receipt(
        policy_directory
    )
    if accepted_policy_sha256 != policy["policy_response_sha256"]:
        raise ValueError("policy acknowledgement does not match exact bytes.")
    accepted_utc = _utc(accepted_utc, name="accepted_utc")
    root = Path(snapshot_root).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("snapshot root must be a non-symlink directory.")
    cached = _fresh_cached_snapshot(
        root, accepted_policy_sha256, accepted_utc
    )
    if cached is not None:
        return cached
    response = transport(ACTIVE_GP_URL)
    started, stopped = _response(response, ACTIVE_GP_URL, "text/csv")
    raw_digest = sha256_hex(response.body)
    records = _normalize_csv(response.body, raw_digest)
    records_bytes = canonical_json_bytes(records)
    content_digest = sha256_hex(records_bytes)
    destination = root / content_digest
    manifest = {
        "schema_version": 1,
        "snapshot_id": f"celestrak_active_{content_digest[:16]}",
        "created_utc": stopped,
        "source_identity": SOURCE_IDENTITY,
        "source_url": ACTIVE_GP_URL,
        "source_format": "CelesTrak GP CSV normalized to canonical OMM JSON",
        "records_file": "records.json",
        "content_sha256": content_digest,
        "record_count": len(records),
        "builder_identity": BUILDER_IDENTITY,
        "provider_policy_url": POLICY_URL,
        "provider_policy_checked_utc": policy["retrieved_stopped_utc"],
        "provenance": [
            f"provider-response-sha256:{raw_digest}",
            f"accepted-policy-sha256:{accepted_policy_sha256}",
        ],
        "warnings": [
            "CelesTrak GROUP=active is not the complete "
            "resident-space-object population."
        ],
    }
    epochs = [record["EPOCH"] for record in records]
    identifiers = [record["NORAD_CAT_ID"] for record in records]
    report = {
        "schema_version": 1,
        "document_kind": "celestrak-active-acquisition-report",
        "source_url": ACTIVE_GP_URL,
        "ordered_query": [["GROUP", "active"], ["FORMAT", "CSV"]],
        "retrieved_started_utc": started,
        "retrieved_stopped_utc": stopped,
        "http_status": 200,
        "media_type": response.media_type,
        "provider_response_file": "provider-response.csv",
        "provider_response_bytes": len(response.body),
        "provider_response_sha256": raw_digest,
        "canonical_records_sha256": content_digest,
        "record_count": len(records),
        "minimum_epoch": min(epochs),
        "maximum_epoch": max(epochs),
        "minimum_norad_catalog_id": min(identifiers),
        "maximum_norad_catalog_id": max(identifiers),
        "population": SOURCE_IDENTITY,
        "accepted_policy_sha256": accepted_policy_sha256,
        "operator_acknowledgement": accepted_policy_sha256,
        "accepted_utc": accepted_utc,
        "implementation_identity": BUILDER_IDENTITY,
        "wenu_version": __version__,
        "status": "success",
        "warnings": manifest["warnings"],
    }
    payloads = {
        "manifest.json": canonical_json_bytes(manifest),
        "records.json": records_bytes,
        "acquisition-report.json": canonical_json_bytes(report),
        "policy-receipt.json": policy_receipt_bytes,
        "policy-response.html": policy_raw,
        "provider-response.csv": response.body,
    }
    staging = Path(tempfile.mkdtemp(prefix=".snapshot-", dir=root))
    try:
        for name, payload in payloads.items():
            (staging / name).write_bytes(payload)
        _validate_publication(staging)
        if destination.exists():
            _validate_publication(destination)
            if any(_read_regular(destination, name) != payloads[name]
                   for name in _PUBLICATION_FILES):
                raise FileExistsError(
                    "content-addressed snapshot exists with different "
                    "evidence."
                )
            shutil.rmtree(staging)
            return destination
        os.rename(staging, destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return destination
