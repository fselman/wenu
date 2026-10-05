#!/usr/bin/env python3
"""Generate offline 50S.6H positive and zero-row review specimens."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from wenu import __version__
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
    ObservatoryPlanningContext,
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
CREATED_UTC = "2026-09-20T12:34:56.123456Z"


def iso(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def build_report():
    snapshot = load_snapshot("synthetic_50s4b_v1")
    observer = SatelliteObserver(
        observer_id="paranal-offline-review",
        longitude_deg=-70.4045,
        latitude_deg=-24.6272,
        elevation_m=2635.0,
        refraction_policy="vacuum",
        earth_orientation_policy="iers-a-bundled",
    )
    field = SatelliteFieldOfView(
        field_id="review-field",
        center_longitude_deg=10.0,
        center_latitude_deg=-20.0,
        angular_radius_deg=2.0,
        coordinate_spec=CoordinateSpec(
            frame="gcrs-axes",
            origin="topocentric-direction",
            position_status=PositionStatus.GEOMETRIC,
            instant=iso(START),
            time_scale="utc",
            provider="50S.6H offline validation",
        ),
    )
    query = LocalSatelliteCrossingQuery(
        snapshot=snapshot,
        observer=observer,
        field_of_view=field,
        interval=InclusiveTimeInterval(
            iso(START), iso(START + timedelta(seconds=60))
        ),
        time_tolerance_seconds=0.01,
        angular_tolerance_deg=1.0e-5,
    )
    record = snapshot.records[0]
    candidate = SatelliteCrossingCandidate(
        satellite=SatelliteIdentity(
            norad_catalog_id=record.norad_catalog_id,
            object_name=record.object_name,
            international_designator=record.international_designator,
            classification=record.classification,
        ),
        observer=observer,
        field_of_view=field,
        interval=query.interval,
        source_provider="wenu local crossing oracle",
        orbit_solution_id=record.source_identity,
        snapshot_sha256=snapshot.manifest.content_sha256,
        element_epoch=record.epoch_utc,
        provenance=("offline review fixture",),
    )
    crossing = SatelliteCrossingResult(
        candidate=candidate,
        entry_instant=iso(START + timedelta(seconds=10)),
        closest_approach_instant=iso(START + timedelta(seconds=12)),
        exit_instant=iso(START + timedelta(seconds=14)),
        closest_approach_deg=0.25,
        range_km=750.0,
        angular_rate_deg_per_s=0.8,
        provenance=("exact connected visit",),
    )
    identifiers = tuple(
        item.norad_catalog_id for item in snapshot.records
    )
    result = MultiFieldCrossingResult(
        query=query,
        crossings=(crossing,),
        airmass_admission=FieldAirmassAdmission(
            field_id=field.field_id,
            maximum_airmass=2.0,
            minimum_altitude_deg=30.0,
            certified_lower_bound_deg=31.0,
            evaluation_count=1,
            earth_orientation_sha256=("a" * 64,),
            provenance=("centre-only certificate",),
        ),
        acceleration_evidence=AcceleratedCrossingEvidence(
            snapshot_sha256=snapshot.manifest.content_sha256,
            field_id=field.field_id,
            interval_start=query.interval.start,
            interval_stop=query.interval.stop,
            rejected_norad_catalog_ids=(),
            exact_solver_norad_catalog_ids=identifiers,
            selection=None,
            fallback_to_exhaustive=True,
            fallback_reason="synthetic complete scan",
        ),
    )
    report = ExactSatelliteCrossingReport.from_results(
        (result,),
        policy=MultiFieldCrossingPolicy(),
        created_utc=CREATED_UTC,
        wenu_version=__version__,
        crossing_oracle_implementation="offline review oracle v1",
        acceleration_implementation="offline review acceleration v1",
        batch_coordinator_implementation="offline review batch v1",
    )
    return report, observer


def planning_context(observer, *, positive):
    if positive:
        identifier = "paranal-review-overlap"
        start = START + timedelta(seconds=11)
        stop = START + timedelta(seconds=13)
    else:
        identifier = "paranal-review-zero"
        start = START + timedelta(seconds=14)
        stop = START + timedelta(seconds=20)
    return ObservatoryPlanningContext(
        planning_context_id=identifier,
        observer=observer,
        observation_units=(
            PlanningObservationUnit(
                observation_unit_id="review-ob-1",
                field_id="review-field",
                start_utc=iso(start),
                stop_utc=iso(stop),
                labels=(
                    ("facility_label", "Paranal offline review only"),
                    ("operational_status", "not scheduler input"),
                ),
            ),
        ),
    )


def file_record(path):
    payload = path.read_bytes()
    return {
        "bytes": len(payload),
        "path": str(path.resolve()),
        "sha256": sha256(payload).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate one positive and one zero-row offline planning advisory."
        )
    )
    parser.add_argument("output_directory")
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()

    output = Path(args.output_directory)
    output.mkdir(parents=True, exist_ok=True)
    report, observer = build_report()
    positive = SatellitePlanningAdvisory.from_report(
        report,
        context=planning_context(observer, positive=True),
        created_utc=CREATED_UTC,
        wenu_version=__version__,
    )
    zero = SatellitePlanningAdvisory.from_report(
        report,
        context=planning_context(observer, positive=False),
        created_utc=CREATED_UTC,
        wenu_version=__version__,
    )
    paths = {
        "exact_report": output / "50s6h-exact-report.json",
        "positive": output / "50s6h-positive-advisory.json",
        "zero": output / "50s6h-zero-row-advisory.json",
    }
    paths["exact_report"].write_text(report.to_json(), encoding="utf-8")
    paths["positive"].write_text(positive.to_json(), encoding="utf-8")
    paths["zero"].write_text(zero.to_json(), encoding="utf-8")
    manifest = {
        "claim": "offline geometric interval-overlap advisory",
        "network_access": False,
        "outputs": [file_record(path) for path in paths.values()],
        "positive_identity_sha256": (
            positive.planning_advisory_identity_sha256
        ),
        "positive_row_count": positive.document["row_count"],
        "profile_id": "general",
        "source_report_identity_sha256": report.report_identity_sha256,
        "source_revision": args.source_revision,
        "zero_identity_sha256": zero.planning_advisory_identity_sha256,
        "zero_row_count": zero.document["row_count"],
    }
    manifest_path = output / "50s6h-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "OFFLINE_ADVISORY="
        f"positive rows {manifest['positive_row_count']}; "
        f"zero rows {manifest['zero_row_count']}; "
        f"source {manifest['source_report_identity_sha256']}"
    )
    for path in (*paths.values(), manifest_path):
        print(path.resolve())


if __name__ == "__main__":
    main()
