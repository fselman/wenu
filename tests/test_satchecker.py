"""SatChecker provider boundary, normalization, and exact-cache tests."""

from datetime import datetime, timezone
import json

import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteFieldOfView,
    SatelliteObserver,
)
from wenu.satchecker import (
    SATCHECKER_PROVIDER,
    SatCheckerCache,
    SatCheckerQuery,
    SatCheckerReceipt,
    SatCheckerTaskState,
    parse_response,
    poll,
    submit,
)


def query():
    observer = SatelliteObserver(
        "la-ligua", -71.230289, -32.443342, 52.0,
        earth_orientation_policy="iers-a-bundled",
    )
    field = SatelliteFieldOfView(
        "test-field",
        157.5,
        20.0,
        3.0,
        CoordinateSpec(
            frame="icrs",
            origin="topocentric-direction",
            position_status=PositionStatus.GEOMETRIC,
            instant="2026-09-15T01:00:00Z",
            time_scale="utc",
            provider="wenu request",
        ),
    )
    interval = InclusiveTimeInterval(
        "2026-09-15T01:00:00Z", "2026-09-15T01:00:02Z"
    )
    return SatCheckerQuery.from_domain(
        observer,
        field,
        interval,
        earth_orientation_identity="astropy bundled IERS-A 2026-09-15",
        utc_to_ut1_jd=lambda value: 2461298.5416667,
    )


def receipt(payload, *, endpoint=None, status=200, media="application/json"):
    return SatCheckerReceipt(
        endpoint=endpoint or query().endpoint,
        retrieved_at_utc="2026-09-15T12:00:00Z",
        http_status=status,
        media_type=media,
        headers=(("Content-Type", media), ("X-Test", "fixed")),
        body=json.dumps(payload, separators=(",", ":")).encode(),
    )


def success_payload(*, task_id="task-1"):
    return {
        "status": "SUCCESS",
        "task_id": task_id,
        "message": "complete",
        "result": {
            "source": SATCHECKER_PROVIDER,
            "version": "1.8.0",
            "data": {
                "satellites": {
                    "TEST SAT (123456)": {
                        "name": "TEST SAT",
                        "norad_id": 123456,
                        "orbital_data": {
                            "OBJECT_ID": "2026-001A",
                        },
                        "positions": [
                            {
                                "ra": 157.0,
                                "dec": 19.5,
                                "angle": 0.7,
                                "altitude": 45.0,
                                "azimuth": 120.0,
                                "range_km": 550.0,
                                "julian_date": 2461298.5416667,
                                "orbital_data_epoch":
                                    "2026-09-15 00:00:00 UTC",
                                "orbital_data_source": "omm",
                            },
                            {
                                "ra": 157.2,
                                "dec": 19.7,
                                "angle": 0.4,
                                "altitude": 45.2,
                                "azimuth": 120.2,
                                "range_km": 549.0,
                                "julian_date": 2461298.5416783,
                                "orbital_data_epoch":
                                    "2026-09-15 00:00:00 UTC",
                                "orbital_data_source": "omm",
                            },
                        ],
                    }
                },
                "total_satellites": 1,
                "total_position_results": 2,
            },
        },
    }


def sample_time(jd):
    offset = 0 if jd < 2461298.54167 else 1
    return f"2026-09-15T01:00:0{offset}Z"


def test_query_maps_only_accepted_satchecker_parameters():
    value = query()
    parameters = dict(value.parameters)

    assert value.endpoint.endswith("/v1/fov/satellite-passes/")
    assert parameters["group_by"] == "satellite"
    assert parameters["include_orbital_data"] == "true"
    assert parameters["illuminated_only"] == "false"
    assert parameters["async"] == "true"
    assert parameters["convert_omm_to_tle"] == "false"
    assert value.duration_seconds == 2.0
    assert len(value.cache_key) == 64


def test_query_rejects_non_geometric_or_non_icrs_field():
    value = query()
    bad_field = SatelliteFieldOfView(
        "apparent",
        157.5,
        20.0,
        3.0,
        CoordinateSpec(
            frame="icrs",
            origin="topocentric-direction",
            position_status=PositionStatus.APPARENT,
        ),
    )
    with pytest.raises(ValueError, match="geometric"):
        SatCheckerQuery.from_domain(
            value.observer,
            bad_field,
            value.interval,
            earth_orientation_identity="test",
            utc_to_ut1_jd=lambda unused: 1.0,
        )


def test_query_requires_positive_interval_and_https():
    value = query()
    instant = InclusiveTimeInterval(
        "2026-09-15T01:00:00Z", "2026-09-15T01:00:00Z"
    )
    with pytest.raises(ValueError, match="positive"):
        SatCheckerQuery.from_domain(
            value.observer,
            value.field_of_view,
            instant,
            earth_orientation_identity="test",
            utc_to_ut1_jd=lambda unused: 1.0,
        )
    with pytest.raises(ValueError, match="HTTPS"):
        SatCheckerQuery(
            value.observer,
            value.field_of_view,
            value.interval,
            1.0,
            2.0,
            "test",
            base_url="http://example.test",
        )


def test_receipt_preserves_exact_bytes_and_normalizes_metadata():
    body = b'{"status":"PENDING","task_id":"task-1"}'
    value = SatCheckerReceipt(
        query().endpoint,
        "2026-09-15T12:00:00+00:00",
        200,
        "Application/JSON; charset=utf-8",
        (("X-B", "2"), ("X-A", "1")),
        body,
    )

    assert value.body is body
    assert value.media_type == "application/json"
    assert value.headers == (("x-a", "1"), ("x-b", "2"))
    assert len(value.body_sha256) == 64


@pytest.mark.parametrize(
    ("payload", "state", "progress"),
    [
        ({"status": "PENDING", "task_id": "task-1"}, "PENDING", None),
        (
            {"status": "PROGRESS", "task_id": "task-1", "progress": 25},
            "PROGRESS",
            25.0,
        ),
        (
            {"status": "FAILURE", "task_id": "task-1", "error": "failed"},
            "FAILURE",
            None,
        ),
        (
            {"status": "ERROR", "task_id": "task-1", "error": "error"},
            "ERROR",
            None,
        ),
    ],
)
def test_task_states_are_explicit(payload, state, progress):
    result = parse_response(query(), receipt(payload))

    assert result.state is SatCheckerTaskState(state)
    assert result.progress == progress
    assert not result.evidence


def test_provider_list_wrapper_is_accepted():
    result = parse_response(
        query(), receipt([{"status": "PENDING", "task_id": "task-1"}])
    )
    assert result.state is SatCheckerTaskState.PENDING


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"status": "UNKNOWN", "task_id": "task-1"}, "unknown"),
        ({"status": "PENDING"}, "task_id"),
        (
            {"status": "PROGRESS", "task_id": "task-1", "progress": 101},
            "between 0 and 100",
        ),
    ],
)
def test_task_schema_drift_fails_closed(payload, message):
    with pytest.raises(ValueError, match=message):
        parse_response(query(), receipt(payload))


def test_http_media_and_json_failures_are_distinct():
    with pytest.raises(ValueError, match="HTTP status 503"):
        parse_response(query(), receipt({}, status=503))
    with pytest.raises(ValueError, match="media type"):
        parse_response(query(), receipt({}, media="text/html"))
    bad = SatCheckerReceipt(
        query().endpoint,
        "2026-09-15T12:00:00Z",
        200,
        "application/json",
        (),
        b"{bad",
    )
    with pytest.raises(ValueError, match="valid UTF-8 JSON"):
        parse_response(query(), bad)


def test_success_normalizes_candidate_and_ordered_sample_evidence():
    raw = receipt(success_payload())
    result = parse_response(
        query(),
        raw,
        expected_task_id="task-1",
        ut1_jd_to_utc=sample_time,
    )

    assert result.state is SatCheckerTaskState.SUCCESS
    assert result.terminal
    assert len(result.evidence) == 1
    evidence = result.evidence[0]
    assert evidence.candidate.satellite.norad_catalog_id == 123456
    assert evidence.candidate.satellite.international_designator == "2026-001A"
    assert evidence.candidate.element_epoch == "2026-09-15T00:00:00Z"
    assert evidence.response_sha256 == raw.body_sha256
    assert len(evidence.samples) == 2
    assert evidence.samples[0].julian_date_ut1 == 2461298.5416667
    assert "1.2-radius candidate envelope" in evidence.candidate.warnings[1]
    assert any(
        "Earth-orientation identity" in value
        for value in evidence.candidate.provenance
    )


def test_success_does_not_construct_exact_crossing_result():
    result = parse_response(
        query(),
        receipt(success_payload()),
        expected_task_id="task-1",
        ut1_jd_to_utc=sample_time,
    )
    evidence = result.evidence[0]

    assert not hasattr(evidence, "entry_time")
    assert not hasattr(evidence, "closest_approach_time")
    assert not hasattr(evidence, "exit_time")


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (("source", "changed"), "provider identity"),
        (("total_satellites", 2), "satellite total"),
        (("total_position_results", 3), "position total"),
    ],
)
def test_success_rejects_provider_identity_and_count_drift(change, message):
    payload = success_payload()
    key, value = change
    if key == "source":
        payload["result"]["source"] = value
    else:
        payload["result"]["data"][key] = value
    with pytest.raises(ValueError, match=message):
        parse_response(
            query(),
            receipt(payload),
            expected_task_id="task-1",
            ut1_jd_to_utc=sample_time,
        )


def test_success_rejects_changed_task_id_and_out_of_interval_sample():
    with pytest.raises(ValueError, match="identifier changed"):
        parse_response(
            query(),
            receipt(success_payload(task_id="changed")),
            expected_task_id="task-1",
            ut1_jd_to_utc=sample_time,
        )
    with pytest.raises(ValueError, match="outside the query interval"):
        parse_response(
            query(),
            receipt(success_payload()),
            expected_task_id="task-1",
            ut1_jd_to_utc=lambda unused: "2026-09-15T01:00:03Z",
        )


def test_submit_and_poll_each_make_exactly_one_injected_request():
    calls = []

    def fetch(endpoint, parameters, *, timeout):
        calls.append((endpoint, tuple(parameters), timeout))
        payload = {"status": "PENDING", "task_id": "task-1"}
        if "task-status" in endpoint:
            payload = {
                "status": "PROGRESS",
                "task_id": "task-1",
                "progress": 50,
            }
        return receipt(payload, endpoint=endpoint)

    submitted = submit(query(), timeout=7, fetch=fetch)
    progressed = poll(query(), submitted.task_id, timeout=8, fetch=fetch)

    assert submitted.state is SatCheckerTaskState.PENDING
    assert progressed.state is SatCheckerTaskState.PROGRESS
    assert len(calls) == 2
    assert calls[0][1]
    assert calls[1][1] == ()
    assert calls[0][2] == 7
    assert calls[1][2] == 8


def test_poll_rejects_unsafe_task_identifier_before_transport():
    with pytest.raises(ValueError, match="safe"):
        poll(query(), "../other", fetch=lambda *args, **kwargs: None)


def terminal_response():
    return parse_response(
        query(),
        receipt(success_payload()),
        expected_task_id="task-1",
        ut1_jd_to_utc=sample_time,
    )


def test_exact_cache_round_trip_preserves_receipts_and_normalization(tmp_path):
    pending = parse_response(
        query(), receipt({"status": "PENDING", "task_id": "task-1"})
    )
    terminal = terminal_response()
    cache = SatCheckerCache(tmp_path)

    destination = cache.store(query(), (pending, terminal))
    loaded = cache.load(query())

    assert destination.name == query().cache_key
    assert tuple(value.body for value in loaded.receipts) == (
        pending.receipt.body,
        terminal.receipt.body,
    )
    assert json.loads(loaded.normalized_json)[0]["norad_catalog_id"] == 123456
    assert not list(tmp_path.glob(".satchecker-*"))


def test_exact_cache_miss_is_network_free(tmp_path):
    assert SatCheckerCache(tmp_path).load(query()) is None


def test_exact_cache_rejects_corrupt_raw_response(tmp_path):
    cache = SatCheckerCache(tmp_path)
    terminal = terminal_response()
    cache.store(query(), (terminal,))
    blob = tmp_path / "blobs" / terminal.receipt.body_sha256
    blob.write_bytes(b"corrupt")

    with pytest.raises(ValueError, match="corrupt"):
        cache.load(query())


def test_exact_cache_rejects_conflicting_same_query_chain(tmp_path):
    cache = SatCheckerCache(tmp_path)
    terminal = terminal_response()
    cache.store(query(), (terminal,))
    changed = SatCheckerReceipt(
        terminal.receipt.endpoint,
        datetime.now(timezone.utc).isoformat(),
        terminal.receipt.http_status,
        terminal.receipt.media_type,
        terminal.receipt.headers,
        terminal.receipt.body,
    )
    changed_response = parse_response(
        query(),
        changed,
        expected_task_id="task-1",
        ut1_jd_to_utc=sample_time,
    )

    with pytest.raises(FileExistsError, match="different exact receipts"):
        cache.store(query(), (changed_response,))
