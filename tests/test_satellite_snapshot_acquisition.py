import csv
from io import StringIO
import json

import pytest

from wenu.satellites.snapshot_acquisition import (
    ACTIVE_GP_URL,
    POLICY_URL,
    TransportResponse,
    acquire_active_snapshot,
    freeze_policy_receipt,
)
from wenu.satellites.snapshots import load_snapshot_directory


POLICY = b"""<!doctype html><title>CelesTrak Usage Policy</title>
<h1>CelesTrak Usage Policy</h1><p>Updated 2026 May 22</p>
<p>Use the documented gp-data-formats.php query.</p>
<p>GP data updates every 2 hours.</p>
<p>Download once per update and cache the response.</p>
<p>Stop immediately after a non-200 response.</p>"""
HEADER = (
    "OBJECT_NAME", "OBJECT_ID", "EPOCH", "MEAN_MOTION", "ECCENTRICITY",
    "INCLINATION", "RA_OF_ASC_NODE", "ARG_OF_PERICENTER",
    "MEAN_ANOMALY", "EPHEMERIS_TYPE", "CLASSIFICATION_TYPE",
    "NORAD_CAT_ID", "ELEMENT_SET_NO", "REV_AT_EPOCH", "BSTAR",
    "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT",
)


def response(url, body, media_type):
    return TransportResponse(
        requested_url=url,
        resolved_url=url,
        status=200,
        media_type=media_type,
        body=body,
        started_utc="2026-09-17T10:00:00Z",
        stopped_utc="2026-09-17T10:00:01Z",
    )


class FakeTransport:
    def __init__(self, expected_url, result):
        self.expected_url = expected_url
        self.result = result
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        assert url == self.expected_url
        return self.result


def provider_csv(rows=None):
    if rows is None:
        rows = [
            (
                "SIX DIGIT", "2024-001A", "2026-09-17T09:00:00Z",
                "15.1", "0.001", "51.6", "20", "30", "40", "0", "U",
                "123456", "7", "100", "0.00001", "0.00002", "0",
            ),
            (
                "LOW ID", "1998-067A", "2026-09-17T08:00:00Z",
                "15.5", "0.002", "51.7", "21", "31", "41", "0", "U",
                "25544", "8", "101", "0.00003", "0.00004", "0",
            ),
        ]
    stream = StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\r\n")
    writer.writerow(HEADER)
    writer.writerows(rows)
    return stream.getvalue().encode()


def frozen_policy(tmp_path):
    transport = FakeTransport(
        POLICY_URL, response(POLICY_URL, POLICY, "text/html; charset=utf-8")
    )
    directory = freeze_policy_receipt(
        tmp_path / "policy", transport=transport
    )
    receipt = json.loads((directory / "policy-receipt.json").read_bytes())
    return directory, receipt["policy_response_sha256"], transport


def test_policy_preflight_makes_one_policy_request_and_no_gp_request(tmp_path):
    directory, digest, transport = frozen_policy(tmp_path)

    assert transport.calls == [POLICY_URL]
    assert len(digest) == 64
    assert (directory / "policy-response.html").read_bytes() == POLICY


def test_policy_preflight_uses_exact_official_policy_url():
    assert POLICY_URL == "https://celestrak.org/usage-policy.php"


@pytest.mark.parametrize(
    "change",
    [
        {"status": 503},
        {"resolved_url": POLICY_URL + "?redirected=1"},
        {"body": b"<h1>CelesTrak Usage Policy</h1>"},
    ],
)
def test_policy_preflight_fails_closed_without_receipt(tmp_path, change):
    values = response(POLICY_URL, POLICY, "text/html").__dict__ | change
    transport = FakeTransport(POLICY_URL, TransportResponse(**values))

    with pytest.raises(ValueError):
        freeze_policy_receipt(tmp_path / "policy", transport=transport)

    assert not (tmp_path / "policy").exists()


def test_wrong_policy_acknowledgement_stops_before_provider_request(tmp_path):
    policy, _digest, _ = frozen_policy(tmp_path)
    transport = FakeTransport(
        ACTIVE_GP_URL, response(ACTIVE_GP_URL, provider_csv(), "text/csv")
    )

    with pytest.raises(ValueError, match="acknowledgement"):
        acquire_active_snapshot(
            tmp_path / "snapshots",
            policy,
            accepted_policy_sha256="0" * 64,
            accepted_utc="2026-09-17T10:01:00Z",
            transport=transport,
        )

    assert transport.calls == []
    assert not (tmp_path / "snapshots").exists()


def test_one_bulk_response_is_normalized_and_published_atomically(tmp_path):
    policy, digest, _ = frozen_policy(tmp_path)
    transport = FakeTransport(
        ACTIVE_GP_URL, response(ACTIVE_GP_URL, provider_csv(), "text/csv")
    )

    directory = acquire_active_snapshot(
        tmp_path / "snapshots",
        policy,
        accepted_policy_sha256=digest,
        accepted_utc="2026-09-17T10:01:00Z",
        transport=transport,
    )

    assert transport.calls == [ACTIVE_GP_URL]
    assert directory.name == load_snapshot_directory(
        directory
    ).manifest.content_sha256
    snapshot = load_snapshot_directory(directory)
    assert tuple(snapshot.by_norad_catalog_id) == (25544, 123456)
    assert snapshot.records[1].center_name == "EARTH"
    assert snapshot.records[1].reference_frame == "TEME"
    assert set(path.name for path in directory.iterdir()) == {
        "manifest.json", "records.json", "acquisition-report.json",
        "policy-receipt.json", "policy-response.html",
        "provider-response.csv",
    }
    assert not tuple((tmp_path / "snapshots").glob(".snapshot-*"))


def test_fresh_validated_snapshot_is_reused_without_provider_request(tmp_path):
    policy, digest, _ = frozen_policy(tmp_path)
    first = FakeTransport(
        ACTIVE_GP_URL, response(ACTIVE_GP_URL, provider_csv(), "text/csv")
    )
    directory = acquire_active_snapshot(
        tmp_path / "snapshots",
        policy,
        accepted_policy_sha256=digest,
        accepted_utc="2026-09-17T10:01:00Z",
        transport=first,
    )
    forbidden = FakeTransport(ACTIVE_GP_URL, None)

    reused = acquire_active_snapshot(
        tmp_path / "snapshots",
        policy,
        accepted_policy_sha256=digest,
        accepted_utc="2026-09-17T11:59:59Z",
        transport=forbidden,
    )

    assert reused == directory
    assert forbidden.calls == []


def test_duplicate_identifier_fails_without_partial_publication(tmp_path):
    policy, digest, _ = frozen_policy(tmp_path)
    rows = [
        (
            "ONE", "2024-001A", "2026-09-17T09:00:00Z", "15.1",
            "0.001", "51.6", "20", "30", "40", "0", "U", "123456",
            "7", "100", "0.00001", "0.00002", "0",
        ),
        (
            "TWO", "2024-001B", "2026-09-17T09:00:00Z", "15.2",
            "0.002", "51.7", "21", "31", "41", "0", "U", "123456",
            "8", "101", "0.00003", "0.00004", "0",
        ),
    ]
    transport = FakeTransport(
        ACTIVE_GP_URL,
        response(ACTIVE_GP_URL, provider_csv(rows), "text/csv"),
    )

    with pytest.raises(ValueError, match="duplicate NORAD"):
        acquire_active_snapshot(
            tmp_path / "snapshots",
            policy,
            accepted_policy_sha256=digest,
            accepted_utc="2026-09-17T10:01:00Z",
            transport=transport,
        )

    root = tmp_path / "snapshots"
    assert not root.exists() or not tuple(root.iterdir())


def test_fixed_csv_header_rejects_unknown_or_reordered_contract(tmp_path):
    policy, digest, _ = frozen_policy(tmp_path)
    body = provider_csv().replace(
        b"OBJECT_NAME,OBJECT_ID", b"OBJECT_ID,OBJECT_NAME", 1
    )
    transport = FakeTransport(
        ACTIVE_GP_URL, response(ACTIVE_GP_URL, body, "text/csv")
    )

    with pytest.raises(ValueError, match="fixed contract"):
        acquire_active_snapshot(
            tmp_path / "snapshots",
            policy,
            accepted_policy_sha256=digest,
            accepted_utc="2026-09-17T10:01:00Z",
            transport=transport,
        )
