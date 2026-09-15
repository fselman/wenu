"""Conservative cone/shell selector and exact-oracle equivalence."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteFieldOfView,
    SatelliteObserver,
)
from wenu.satellites import load_snapshot
from wenu.satellites.crossing_acceleration import (
    ConeShellPolicy,
    ConservativeConeShellSelector,
)
from wenu.satellites.crossing_oracle import (
    LocalSatelliteCrossingOracle,
    LocalSatelliteCrossingQuery,
)
from wenu.satellites.sgp4 import Sgp4TemePropagator
from wenu.satellites.snapshots import SatelliteElementSnapshot
from wenu.satellites.topocentric import SatelliteTopocentricTransformer


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


def field(longitude_deg, latitude_deg, *, radius=0.1):
    return SatelliteFieldOfView(
        field_id="selector-field",
        center_longitude_deg=longitude_deg,
        center_latitude_deg=latitude_deg,
        angular_radius_deg=radius,
        coordinate_spec=CoordinateSpec(
            frame="gcrs-axes",
            origin="topocentric-direction",
            position_status=PositionStatus.GEOMETRIC,
            instant=iso(START),
            time_scale="utc",
            provider="selector test",
        ),
    )


def query(snapshot, field_of_view, *, seconds=60.0):
    return LocalSatelliteCrossingQuery(
        snapshot=snapshot,
        observer=observer(),
        field_of_view=field_of_view,
        interval=InclusiveTimeInterval(
            iso(START), iso(START + timedelta(seconds=seconds))
        ),
        time_tolerance_seconds=0.01,
        angular_tolerance_deg=1.0e-5,
    )


def start_state(snapshot, record):
    return SatelliteTopocentricTransformer().transform(
        Sgp4TemePropagator(
            record,
            snapshot_sha256=snapshot.manifest.content_sha256,
        ).propagate(iso(START)),
        observer(),
    )


def one_record_snapshot(snapshot, record):
    return SatelliteElementSnapshot(
        manifest=replace(
            snapshot.manifest,
            snapshot_id=f"{snapshot.manifest.snapshot_id}-one",
            record_count=1,
        ),
        records=(record,),
    )


def test_policy_and_decisions_are_immutable_and_validated():
    policy = ConeShellPolicy()
    with pytest.raises(FrozenInstanceError):
        policy.max_interval_seconds = 1.0
    with pytest.raises(ValueError, match="less than 1"):
        ConeShellPolicy(max_eccentricity=1.0)
    with pytest.raises(TypeError, match="policy"):
        ConservativeConeShellSelector(policy="fast")


def test_field_at_initial_direction_is_retained_even_below_horizon():
    snapshot = load_snapshot("synthetic_50s4b_v1")
    record = snapshot.records[0]
    state = start_state(snapshot, record)
    assert state.altitude_deg < 0.0

    selection = ConservativeConeShellSelector().select(
        query(
            snapshot,
            field(
                state.gcrs_axis_longitude_deg,
                state.gcrs_axis_latitude_deg,
            ),
        )
    )
    decision = selection.decisions[0]

    assert decision.outcome == "retain"
    assert "reachable cone overlaps" in decision.reason
    assert record.norad_catalog_id in selection.exact_solver_norad_catalog_ids


def test_opposite_short_interval_is_rejected_with_complete_evidence():
    snapshot = load_snapshot("synthetic_50s4b_v1")
    record = snapshot.records[0]
    state = start_state(snapshot, record)
    opposite = field(
        state.gcrs_axis_longitude_deg + 180.0,
        -state.gcrs_axis_latitude_deg,
    )
    decision = ConservativeConeShellSelector().select(
        query(snapshot, opposite)
    ).decisions[0]

    assert decision.outcome == "reject"
    assert decision.initial_field_separation_deg == pytest.approx(180.0)
    assert decision.reachable_cap_deg < 180.0
    assert decision.initial_field_separation_deg > (
        decision.rejection_threshold_deg
    )
    assert decision.semimajor_axis_km > 0.0
    assert decision.perigee_radius_km > 6378.137
    assert decision.apogee_radius_km >= decision.perigee_radius_km
    assert decision.relative_speed_bound_km_per_s > 0.0
    assert decision.provenance[-1].startswith("180")


def test_rejected_record_has_no_exact_crossing():
    snapshot = load_snapshot("synthetic_50s4b_v1")
    record = snapshot.records[0]
    state = start_state(snapshot, record)
    single = one_record_snapshot(snapshot, record)
    request = query(
        single,
        field(
            state.gcrs_axis_longitude_deg + 180.0,
            -state.gcrs_axis_latitude_deg,
        ),
    )
    selection = ConservativeConeShellSelector().select(request)

    assert selection.rejected_norad_catalog_ids == (
        record.norad_catalog_id,
    )
    assert LocalSatelliteCrossingOracle().solve(request) == ()


def test_interval_outside_validated_domain_is_indeterminate():
    snapshot = load_snapshot("synthetic_50s4b_v1")
    selection = ConservativeConeShellSelector().select(
        query(snapshot, field(0.0, 0.0), seconds=61.0)
    )

    assert {item.outcome for item in selection.decisions} == {
        "indeterminate"
    }
    assert selection.rejected_norad_catalog_ids == ()
    assert selection.exact_solver_norad_catalog_ids == tuple(
        record.norad_catalog_id for record in snapshot.records
    )


def test_selection_is_ordered_deterministic_and_retains_snapshot_identity():
    snapshot = load_snapshot("synthetic_50s4b_v1")
    request = query(snapshot, field(0.0, 0.0))
    selector = ConservativeConeShellSelector()

    first = selector.select(request)
    second = selector.select(request)

    assert first == second
    assert first.snapshot_sha256 == snapshot.manifest.content_sha256
    assert tuple(item.norad_catalog_id for item in first.decisions) == tuple(
        record.norad_catalog_id for record in snapshot.records
    )
    with pytest.raises(FrozenInstanceError):
        first.field_id = "changed"


def test_selector_rejects_non_query_input():
    with pytest.raises(TypeError, match="LocalSatelliteCrossingQuery"):
        ConservativeConeShellSelector().select(object())
