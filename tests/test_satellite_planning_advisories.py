"""Offline observatory-neutral satellite planning advisory tests."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossing_reports import ExactSatelliteCrossingReport
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteCrossingCandidate,
    SatelliteCrossingResult,
    SatelliteFieldOfView,
    SatelliteIdentity,
    SatelliteObserver,
)
from wenu.satellite_planning_advisories import (
    GENERAL_PLANNING_PROFILE,
    ObservatoryPlanningContext,
    PlanningAdvisoryValidationError,
    PlanningObservationUnit,
    SatellitePlanningAdvisory,
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


def observer():
    return SatelliteObserver(
        observer_id="la-ligua",
        longitude_deg=-71.230289,
        latitude_deg=-32.443342,
        elevation_m=52.0,
        refraction_policy="vacuum",
        earth_orientation_policy="iers-a-bundled",
    )


def field_result(identifier="field-a", *, crossings=True):
    snapshot = load_snapshot("synthetic_50s4b_v1")
    field = SatelliteFieldOfView(
        field_id=identifier,
        center_longitude_deg=10.0,
        center_latitude_deg=-20.0,
        angular_radius_deg=2.0,
        coordinate_spec=CoordinateSpec(
            frame="gcrs-axes",
            origin="topocentric-direction",
            position_status=PositionStatus.GEOMETRIC,
            instant=iso(START),
            time_scale="utc",
            provider="planning advisory test",
        ),
    )
    query = LocalSatelliteCrossingQuery(
        snapshot=snapshot,
        observer=observer(),
        field_of_view=field,
        interval=InclusiveTimeInterval(
            iso(START), iso(START + timedelta(seconds=60))
        ),
        time_tolerance_seconds=0.01,
        angular_tolerance_deg=1.0e-5,
    )
    values = ()
    if crossings:
        record = snapshot.records[0]
        candidate = SatelliteCrossingCandidate(
            satellite=SatelliteIdentity(
                norad_catalog_id=record.norad_catalog_id,
                object_name=record.object_name,
                international_designator=record.international_designator,
                classification=record.classification,
            ),
            observer=query.observer,
            field_of_view=query.field_of_view,
            interval=query.interval,
            source_provider="wenu local crossing oracle",
            orbit_solution_id=record.source_identity,
            snapshot_sha256=snapshot.manifest.content_sha256,
            element_epoch=record.epoch_utc,
            provenance=("oracle candidate",),
        )
        values = (
            SatelliteCrossingResult(
                candidate=candidate,
                entry_instant=iso(START + timedelta(seconds=10)),
                closest_approach_instant=iso(
                    START + timedelta(seconds=12)
                ),
                exit_instant=iso(START + timedelta(seconds=14)),
                closest_approach_deg=0.25,
                range_km=750.0,
                angular_rate_deg_per_s=0.8,
                provenance=("exact connected visit",),
            ),
        )
    identifiers = tuple(
        item.norad_catalog_id for item in snapshot.records
    )
    return MultiFieldCrossingResult(
        query=query,
        crossings=values,
        airmass_admission=FieldAirmassAdmission(
            field_id=identifier,
            maximum_airmass=2.0,
            minimum_altitude_deg=30.0,
            certified_lower_bound_deg=31.0,
            evaluation_count=1,
            earth_orientation_sha256=("a" * 64,),
            provenance=("centre-only certificate",),
        ),
        acceleration_evidence=AcceleratedCrossingEvidence(
            snapshot_sha256=snapshot.manifest.content_sha256,
            field_id=identifier,
            interval_start=query.interval.start,
            interval_stop=query.interval.stop,
            rejected_norad_catalog_ids=(),
            exact_solver_norad_catalog_ids=identifiers,
            selection=None,
            fallback_to_exhaustive=True,
            fallback_reason="synthetic complete scan",
        ),
    )


def report(*results):
    if not results:
        results = (field_result(),)
    return ExactSatelliteCrossingReport.from_results(
        results,
        policy=MultiFieldCrossingPolicy(),
        created_utc="2026-09-19T12:34:56.123456Z",
        wenu_version="0.9.test",
        crossing_oracle_implementation="oracle v1",
        acceleration_implementation="acceleration v1",
        batch_coordinator_implementation="batch v1",
    )


def unit(
    identifier="ob-1",
    *,
    field_id="field-a",
    start=11,
    stop=13,
    labels=(("programme", "test — retained"),),
):
    return PlanningObservationUnit(
        observation_unit_id=identifier,
        field_id=field_id,
        start_utc=iso(START + timedelta(seconds=start)),
        stop_utc=iso(START + timedelta(seconds=stop)),
        labels=labels,
    )


def context(*units, site=None, profile=GENERAL_PLANNING_PROFILE, version=1):
    return ObservatoryPlanningContext(
        planning_context_id="night-plan-1",
        observer=observer() if site is None else site,
        observation_units=units or (unit(),),
        profile_id=profile,
        profile_schema_version=version,
    )


def advisory(source=None, planning=None):
    return SatellitePlanningAdvisory.from_report(
        report() if source is None else source,
        context=context() if planning is None else planning,
        created_utc="2026-09-20T12:34:56.123456Z",
        wenu_version="0.9.test",
    )


def resign(document):
    payload = dict(document)
    payload.pop("planning_advisory_identity_sha256")
    document["planning_advisory_identity_sha256"] = sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def test_half_open_overlap_and_complete_advisory_identity():
    value = advisory()
    document = value.document

    assert document["document_kind"] == (
        "wenu.observatory-planning-advisory"
    )
    assert document["row_count"] == 1
    row = document["rows"][0]
    assert row["planned_start_utc"] == iso(
        START + timedelta(seconds=11)
    )
    assert row["overlap_start_utc"] == iso(
        START + timedelta(seconds=11)
    )
    assert row["overlap_stop_utc"] == iso(
        START + timedelta(seconds=13)
    )
    assert row["overlap_duration_seconds"] == 2.0
    assert row["closest_approach_deg"] == 0.25
    assert row["report_identity_sha256"] == report().report_identity_sha256
    assert len(row["field_geometry_sha256"]) == 64
    assert "unknown" in row["scientific_status"]
    assert value.to_json().endswith("\n")
    assert value.planning_advisory_identity_sha256 == document[
        "planning_advisory_identity_sha256"
    ]


@pytest.mark.parametrize(
    ("start", "stop"),
    ((0, 10), (14, 20), (30, 40)),
)
def test_touching_and_disjoint_intervals_produce_identified_zero_rows(
    start, stop
):
    value = advisory(planning=context(unit(start=start, stop=stop)))
    assert value.document["rows"] == []
    assert value.document["row_count"] == 0
    assert len(value.planning_advisory_identity_sha256) == 64


def test_observation_unit_order_is_preserved():
    planning = context(
        unit("later", start=12, stop=14),
        unit("earlier", start=10, stop=12),
    )
    rows = advisory(planning=planning).document["rows"]
    assert [row["observation_unit_id"] for row in rows] == [
        "later",
        "earlier",
    ]


def test_json_is_deterministic_detached_and_strictly_round_trips():
    first = advisory()
    second = advisory()
    encoded = first.to_json()

    assert encoded == second.to_json()
    assert SatellitePlanningAdvisory.from_json(encoded).to_json() == encoded
    assert SatellitePlanningAdvisory.from_json(
        encoded.encode("utf-8")
    ).to_json() == encoded
    detached = first.document
    detached["rows"].clear()
    assert first.document["row_count"] == 1
    with pytest.raises(FrozenInstanceError):
        first._canonical_document = "{}"


def test_all_exact_report_decoders_produce_identical_advisory():
    source = report()
    variants = (
        ExactSatelliteCrossingReport.from_json(source.to_json()),
        ExactSatelliteCrossingReport.from_ecsv(source.to_ecsv()),
        ExactSatelliteCrossingReport.from_votable(source.to_votable()),
    )
    outputs = [
        advisory(source=value).to_json()
        for value in variants
    ]
    assert outputs == [outputs[0]] * 3


def test_inputs_remain_unchanged():
    source = report()
    planning = context()
    before_report = source.to_json()
    before_context = repr(planning)

    advisory(source=source, planning=planning)

    assert source.to_json() == before_report
    assert repr(planning) == before_context


@pytest.mark.parametrize(
    ("kwargs", "code"),
    (
        ({"profile": "elt"}, "unsupported_profile"),
        ({"profile": "paranal"}, "unsupported_profile"),
        ({"version": 2}, "unsupported_profile"),
    ),
)
def test_unsupported_profiles_fail_closed(kwargs, code):
    with pytest.raises(PlanningAdvisoryValidationError) as error:
        context(**kwargs)
    assert error.value.code == code


def test_context_rejects_empty_duplicate_invalid_and_control_values():
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="invalid_observation_units",
    ):
        ObservatoryPlanningContext(
            planning_context_id="empty",
            observer=observer(),
            observation_units=(),
        )
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="duplicate_observation_unit",
    ):
        context(unit("same"), unit("same"))
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="invalid_interval",
    ):
        unit(start=11, stop=11)
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="invalid_utc",
    ):
        PlanningObservationUnit(
            "ob", "field-a", "2026-09-20T01:00:00", iso(START)
        )
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="invalid_text",
    ):
        unit(labels=(("bad\nkey", "value"),))


def test_observer_and_field_mismatch_fail_atomically():
    other = SatelliteObserver(
        observer_id="other",
        longitude_deg=-70.0,
        latitude_deg=-30.0,
        elevation_m=1.0,
    )
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="observer_mismatch",
    ):
        advisory(planning=context(site=other))
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="unknown_field",
    ):
        advisory(planning=context(unit(field_id="absent")))


@pytest.mark.parametrize(
    ("mutate", "code"),
    (
        (lambda d: d.update({"unknown": 1}), "unknown_key"),
        (
            lambda d: d.update({"schema_version": 2}),
            "unsupported_version",
        ),
        (
            lambda d: d["rows"][0].update(
                {"overlap_duration_seconds": 99.0}
            ),
            "invalid_overlap",
        ),
        (
            lambda d: d.update(
                {"source_report_identity_sha256": "0" * 64}
            ),
            "identity_mismatch",
        ),
    ),
)
def test_resigned_semantic_corruption_fails_closed(mutate, code):
    document = advisory().document
    mutate(document)
    encoded = resign(document)
    with pytest.raises(PlanningAdvisoryValidationError) as error:
        SatellitePlanningAdvisory.from_json(encoded)
    assert error.value.code == code


def test_digest_duplicate_nonfinite_utf8_and_noncanonical_json_fail():
    value = advisory()
    document = value.document
    document["row_count"] = 0
    encoded = json.dumps(
        document, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="identity_mismatch",
    ):
        SatellitePlanningAdvisory.from_json(encoded)

    duplicate = value.to_json().replace(
        '"row_count": 1,',
        '"row_count": 1,\n  "row_count": 1,',
        1,
    )
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="duplicate_key",
    ):
        SatellitePlanningAdvisory.from_json(duplicate)
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="nonfinite_number",
    ):
        SatellitePlanningAdvisory.from_json(
            value.to_json().replace(
                '"row_count": 1', '"row_count": NaN', 1
            )
        )
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="invalid_utf8",
    ):
        SatellitePlanningAdvisory.from_json(b"\xff")
    with pytest.raises(
        PlanningAdvisoryValidationError,
        match="noncanonical_json",
    ):
        SatellitePlanningAdvisory.from_json(
            json.dumps(value.document, sort_keys=True)
        )


def test_public_contexts_and_advisories_are_frozen():
    planning_unit = unit()
    planning_context = context(planning_unit)
    with pytest.raises(FrozenInstanceError):
        planning_unit.field_id = "changed"
    with pytest.raises(FrozenInstanceError):
        planning_context.profile_id = "changed"


def test_module_has_no_network_or_facility_write_surface():
    import inspect
    import wenu.satellite_planning_advisories as module

    source = inspect.getsource(module)
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "www.eso.org",
        "createOB",
        "saveOB",
        "verifyOB",
        "deleteOB",
    ):
        assert forbidden not in source
