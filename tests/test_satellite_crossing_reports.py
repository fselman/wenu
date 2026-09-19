"""Canonical exact local satellite-crossing report tests."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

import wenu.satellite_crossing_reports as report_module
from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossing_reports import (
    EXACT_REPORT_PRODUCT,
    EXACT_REPORT_STATUS,
    ExactSatelliteCrossingReport,
)
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteCrossingCandidate,
    SatelliteCrossingResult,
    SatelliteFieldOfView,
    SatelliteIdentity,
    SatelliteObserver,
)
from wenu.satellites import load_snapshot
from wenu.satellites.crossing_acceleration import AcceleratedCrossingEvidence
from wenu.satellites.crossing_batch import (
    FieldAirmassAdmission,
    MultiFieldCrossingPolicy,
    MultiFieldCrossingResult,
)
from wenu.satellites.crossing_oracle import LocalSatelliteCrossingQuery


START = datetime(2026, 9, 15, tzinfo=timezone.utc)


def iso(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def resign(document):
    payload = dict(document)
    payload.pop("report_identity_sha256")
    document["report_identity_sha256"] = sha256(
        canonical(payload).encode("utf-8")
    ).hexdigest()
    return json.dumps(document, ensure_ascii=False)


def observer():
    return SatelliteObserver(
        observer_id="la-ligua",
        longitude_deg=-71.230289,
        latitude_deg=-32.443342,
        elevation_m=52.0,
        refraction_policy="vacuum",
        earth_orientation_policy="iers-a-bundled",
    )


def query(identifier, *, offset=0):
    start = START + timedelta(seconds=offset)
    return LocalSatelliteCrossingQuery(
        snapshot=load_snapshot("synthetic_50s4b_v1"),
        observer=observer(),
        field_of_view=SatelliteFieldOfView(
            field_id=identifier,
            center_longitude_deg=10.0 + offset,
            center_latitude_deg=-20.0,
            angular_radius_deg=2.0,
            coordinate_spec=CoordinateSpec(
                frame="gcrs-axes",
                origin="topocentric-direction",
                position_status=PositionStatus.GEOMETRIC,
                instant=iso(start),
                time_scale="utc",
                provider="exact-report test",
            ),
        ),
        interval=InclusiveTimeInterval(
            iso(start), iso(start + timedelta(seconds=60))
        ),
        time_tolerance_seconds=0.01,
        angular_tolerance_deg=1.0e-5,
    )


def exact_result(request, *, record_index=0, entry=10):
    record = request.snapshot.records[record_index]
    candidate = SatelliteCrossingCandidate(
        satellite=SatelliteIdentity(
            norad_catalog_id=record.norad_catalog_id,
            object_name=record.object_name,
            international_designator=record.international_designator,
            classification=record.classification,
        ),
        observer=request.observer,
        field_of_view=request.field_of_view,
        interval=request.interval,
        source_provider="wenu local crossing oracle",
        orbit_solution_id=record.source_identity,
        snapshot_sha256=request.snapshot.manifest.content_sha256,
        element_epoch=record.epoch_utc,
        provenance=("oracle candidate",),
        warnings=("synthetic warning — retained",),
    )
    start = datetime.fromisoformat(request.interval.start.replace("Z", "+00:00"))
    return SatelliteCrossingResult(
        candidate=candidate,
        entry_instant=iso(start + timedelta(seconds=entry)),
        closest_approach_instant=iso(start + timedelta(seconds=entry + 2)),
        exit_instant=iso(start + timedelta(seconds=entry + 4)),
        closest_approach_deg=0.25,
        range_km=750.0,
        angular_rate_deg_per_s=0.8,
        provenance=("exact connected visit",),
    )


def field_result(identifier, *, offset=0, crossings=True):
    request = query(identifier, offset=offset)
    values = (exact_result(request),) if crossings else ()
    identifiers = tuple(
        item.norad_catalog_id for item in request.snapshot.records
    )
    return MultiFieldCrossingResult(
        query=request,
        crossings=values,
        airmass_admission=FieldAirmassAdmission(
            field_id=identifier,
            maximum_airmass=2.0,
            minimum_altitude_deg=30.0,
            certified_lower_bound_deg=31.0,
            evaluation_count=1,
            earth_orientation_sha256=("a" * 64,),
            provenance=("centre-only complete-interval certificate",),
        ),
        acceleration_evidence=AcceleratedCrossingEvidence(
            snapshot_sha256=request.snapshot.manifest.content_sha256,
            field_id=identifier,
            interval_start=request.interval.start,
            interval_stop=request.interval.stop,
            rejected_norad_catalog_ids=(),
            exact_solver_norad_catalog_ids=identifiers,
            selection=None,
            fallback_to_exhaustive=True,
            fallback_reason="synthetic complete scan",
        ),
    )


def report(*results):
    return ExactSatelliteCrossingReport.from_results(
        results,
        policy=MultiFieldCrossingPolicy(),
        created_utc="2026-09-19T12:34:56.123456Z",
        wenu_version="0.9.test",
        crossing_oracle_implementation="oracle v1",
        acceleration_implementation="acceleration v1",
        batch_coordinator_implementation="batch v1",
    )


def test_positive_and_zero_crossing_fields_are_explicit_and_ordered():
    value = report(
        field_result("positive"),
        field_result("validated-zero", offset=120, crossings=False),
    )
    document = value.document

    assert document["product"] == EXACT_REPORT_PRODUCT
    assert document["scientific_status"] == EXACT_REPORT_STATUS
    assert [item["field_id"] for item in document["fields"]] == [
        "positive", "validated-zero"
    ]
    assert document["fields"][0]["crossing_count"] == 1
    assert document["fields"][1]["crossing_count"] == 0
    assert document["fields"][1]["crossings"] == []
    crossing = document["fields"][0]["crossings"][0]
    assert crossing["norad_catalog_id"] == 300001
    assert crossing["illumination"] is None
    assert crossing["apparent_magnitude"] is None
    assert crossing["detector_effect"] is None
    assert crossing["exact_track_samples"] is None


def test_serialization_is_byte_stable_and_document_is_detached():
    value = report(field_result("one"))
    first = value.to_json()
    detached = value.document
    detached["fields"].clear()

    assert value.to_json() == first
    assert first.endswith("\n")
    assert "synthetic warning — retained" in first
    assert "\\u2014" not in first
    with pytest.raises(FrozenInstanceError):
        value._canonical_document = "{}"


def test_typed_and_byte_identical_round_trip_accepts_text_and_bytes():
    value = report(field_result("one"))
    encoded = value.to_json()

    assert ExactSatelliteCrossingReport.from_json(encoded) == value
    assert ExactSatelliteCrossingReport.from_json(encoded.encode()) == value
    assert ExactSatelliteCrossingReport.from_json(encoded).to_json() == encoded


def test_decode_and_reencode_do_not_consult_filesystem(monkeypatch):
    value = report(field_result("one"))
    encoded = value.to_json()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("runtime service access is forbidden")

    monkeypatch.setattr(report_module.resources, "files", forbidden)

    decoded = ExactSatelliteCrossingReport.from_json(encoded)

    assert decoded.to_json() == encoded


@pytest.mark.parametrize(
    "mutation, message",
    (
        (lambda d: d.update(extra=True), "unknown keys"),
        (lambda d: d.update(schema_version=2), "schema constant"),
        (lambda d: d.update(product="wenu.satchecker_sampled_candidate_evidence"), "schema constant"),
        (lambda d: d.update(scientific_status="visible"), "schema constant"),
        (lambda d: d["fields"][0].update(crossing_count=9), "crossing_count"),
        (lambda d: d["fields"][0]["crossings"][0].update(illumination="sunlit"), "wrong JSON type"),
        (lambda d: d["fields"][0]["crossings"][0].update(field_id="other"), "another field"),
    ),
)
def test_strict_decode_rejects_schema_and_semantic_corruption(mutation, message):
    document = report(field_result("one")).document
    mutation(document)

    with pytest.raises(ValueError, match=message):
        ExactSatelliteCrossingReport.from_json(resign(document))


def test_digest_detects_payload_change_without_resigning():
    document = report(field_result("one")).document
    document["observer"]["elevation_m"] += 1

    with pytest.raises(ValueError, match="does not match"):
        ExactSatelliteCrossingReport.from_json(json.dumps(document))


def test_duplicate_keys_nonfinite_numbers_and_invalid_utf8_fail():
    encoded = report(field_result("one")).to_json()
    duplicate = encoded.replace(
        '"schema_version": 1,',
        '"schema_version": 1, "schema_version": 1,',
        1,
    )
    with pytest.raises(ValueError, match="duplicate"):
        ExactSatelliteCrossingReport.from_json(duplicate)
    with pytest.raises(ValueError, match="non-finite"):
        ExactSatelliteCrossingReport.from_json(encoded.replace("750.0", "NaN"))
    with pytest.raises(ValueError, match="UTF-8"):
        ExactSatelliteCrossingReport.from_json(b"\xff")


def test_invalid_calendar_instant_fails_after_schema_validation():
    document = report(field_result("one")).document
    document["fields"][0]["interval"]["start_utc"] = (
        "2026-99-15T00:00:00.000000Z"
    )
    with pytest.raises(ValueError, match="UTC instant"):
        ExactSatelliteCrossingReport.from_json(resign(document))


def test_constructor_rejects_duplicate_fields_and_context_mismatch():
    one = field_result("same")
    with pytest.raises(ValueError, match="unique"):
        report(one, one)

    other = field_result("other", offset=120)
    other = replace(other, query=replace(other.query, observer=replace(observer(), observer_id="other")))
    with pytest.raises(ValueError, match="share observer"):
        report(one, other)


def test_crossing_order_and_query_context_are_enforced():
    result = field_result("one")
    later = exact_result(result.query, record_index=1, entry=20)
    unordered = replace(result, crossings=(later, result.crossings[0]))
    with pytest.raises(ValueError, match="oracle order"):
        report(unordered)

    wrong = replace(
        result.crossings[0],
        candidate=replace(result.crossings[0].candidate, field_of_view=query("other").field_of_view),
    )
    with pytest.raises(ValueError, match="context"):
        report(replace(result, crossings=(wrong,)))
def test_ecsv_and_votable_round_trips_preserve_exact_logical_identity():
    value = report(
        field_result("positive"),
        field_result("validated-zero", offset=120, crossings=False),
    )

    ecsv = value.to_ecsv()
    votable = value.to_votable()
    ecsv_decoded = ExactSatelliteCrossingReport.from_ecsv(ecsv)
    votable_decoded = ExactSatelliteCrossingReport.from_votable(votable)

    assert isinstance(ecsv, str)
    assert isinstance(votable, bytes)
    assert ecsv_decoded == value
    assert votable_decoded == value
    assert ecsv_decoded.to_json() == value.to_json()
    assert votable_decoded.to_json() == value.to_json()
    assert ecsv_decoded.report_identity_sha256 == value.report_identity_sha256
    assert votable_decoded.report_identity_sha256 == value.report_identity_sha256


def test_tabular_encoders_are_deterministic_and_retain_unicode_and_empty_values():
    value = report(field_result("field — unicode"))

    assert value.to_ecsv() == value.to_ecsv()
    assert value.to_votable() == value.to_votable()
    assert "field — unicode" in value.to_ecsv()
    assert ExactSatelliteCrossingReport.from_ecsv(value.to_ecsv().encode()) == value
    assert ExactSatelliteCrossingReport.from_votable(value.to_votable().decode()) == value


def test_ecsv_declares_fixed_metadata_units_and_explicit_masks():
    encoded = report(field_result("one")).to_ecsv()

    assert encoded.startswith("# %ECSV 1.0")
    assert "wenu_tabular_schema_version: 1" in encoded
    assert "report_identity_sha256:" in encoded
    assert "deg / s" in encoded
    assert "serialize_method" in encoded
    assert "data_mask" in encoded


def test_votable_declares_version_binary2_timesys_and_three_tables():
    encoded = report(field_result("one")).to_votable()

    assert b'VOTABLE version="1.5"' in encoded
    assert b"<BINARY2>" in encoded
    assert b'timescale="UTC"' in encoded
    assert b'refposition="TOPOCENTER"' in encoded
    assert encoded.count(b"<TABLE") == 3


@pytest.mark.parametrize("method", ("from_ecsv", "from_votable"))
def test_tabular_decoders_reject_paths_file_objects_and_invalid_utf8(method):
    decoder = getattr(ExactSatelliteCrossingReport, method)

    with pytest.raises(TypeError, match="text or UTF-8 bytes"):
        decoder(object())
    with pytest.raises(ValueError, match="UTF-8"):
        decoder(b"\xff")


def test_votable_decoder_rejects_doctype_and_external_entity_before_parsing():
    unsafe = b'''<?xml version="1.0"?>
<!DOCTYPE x [<!ENTITY external SYSTEM "file:///etc/passwd">]>
<VOTABLE version="1.5">&external;</VOTABLE>'''

    with pytest.raises(ValueError, match="unsafe XML"):
        ExactSatelliteCrossingReport.from_votable(unsafe)
