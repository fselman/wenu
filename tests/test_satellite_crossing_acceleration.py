"""Conservative cone/shell selector and exact-oracle equivalence."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

import wenu.satellites.crossing_acceleration as acceleration_module

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteFieldOfView,
    SatelliteObserver,
)
from wenu.satellites import load_snapshot
from wenu.satellites.crossing_acceleration import (
    AcceleratedCrossingPolicy,
    AcceleratedLocalSatelliteCrossingOracle,
    ConeShellDecision,
    ConeShellPolicy,
    ConeShellSelection,
    ConservativeConeShellSelector,
)
from wenu.satellites.crossing_oracle import (
    LocalSatelliteCrossingOracle,
    LocalSatelliteCrossingQuery,
    SatelliteCrossingConvergenceError,
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
    assert " deg > " in decision.provenance[-1]


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



def test_recorded_speed_bound_encloses_installed_relative_displacement():
    snapshot = load_snapshot("synthetic_50s4b_v1")
    selector = ConservativeConeShellSelector()

    for record in snapshot.records:
        initial = start_state(snapshot, record)
        request = query(
            snapshot,
            field(
                initial.gcrs_axis_longitude_deg,
                initial.gcrs_axis_latitude_deg,
            ),
        )
        decision = next(
            item
            for item in selector.select(request).decisions
            if item.norad_catalog_id == record.norad_catalog_id
        )
        assert decision.outcome in {"retain", "reject"}
        initial_vector = np.asarray(
            initial.topocentric_itrs_position_km, dtype=float
        )
        propagator = Sgp4TemePropagator(
            record,
            snapshot_sha256=snapshot.manifest.content_sha256,
        )
        transformer = SatelliteTopocentricTransformer()
        for seconds in range(0, 61, 5):
            state = transformer.transform(
                propagator.propagate(
                    iso(START + timedelta(seconds=seconds))
                ),
                observer(),
            )
            displacement = np.linalg.norm(
                np.asarray(
                    state.topocentric_itrs_position_km, dtype=float
                )
                - initial_vector
            )
            assert displacement <= (
                decision.relative_speed_bound_km_per_s * seconds + 1.0e-9
            )


def test_unadmitted_snapshot_identity_is_indeterminate():
    snapshot = load_snapshot("synthetic_50s4b_v1")
    unadmitted = SatelliteElementSnapshot(
        manifest=replace(snapshot.manifest, snapshot_id="unadmitted_snapshot"),
        records=snapshot.records,
    )
    selection = ConservativeConeShellSelector().select(
        query(unadmitted, field(0.0, 0.0))
    )

    assert {item.outcome for item in selection.decisions} == {
        "indeterminate"
    }
    assert all(
        "snapshot is outside" in item.reason
        for item in selection.decisions
    )


def test_selector_rejects_non_query_input():
    with pytest.raises(TypeError, match="LocalSatelliteCrossingQuery"):
        ConservativeConeShellSelector().select(object())



class FakeSelector:
    def __init__(self, selection=None, error=None):
        self.selection = selection
        self.error = error

    def select(self, request):
        if self.error is not None:
            raise self.error
        return self.selection


def fake_selection(request, outcomes):
    return ConeShellSelection(
        snapshot_sha256=request.snapshot.manifest.content_sha256,
        field_id=request.field_of_view.field_id,
        interval_start=request.interval.start,
        interval_stop=request.interval.stop,
        decisions=tuple(
            ConeShellDecision(
                norad_catalog_id=record.norad_catalog_id,
                outcome=outcome,
                reason=f"fake {outcome}",
            )
            for record, outcome in zip(
                request.snapshot.records, outcomes, strict=True
            )
        ),
    )


def test_accelerated_policy_and_evidence_are_immutable_and_validated():
    policy = AcceleratedCrossingPolicy()
    with pytest.raises(FrozenInstanceError):
        policy.max_interval_seconds = 30.0
    with pytest.raises(ValueError, match="selector_failure_mode"):
        AcceleratedCrossingPolicy(selector_failure_mode="ignore")

    snapshot = load_snapshot("synthetic_50s4b_v1")
    request = query(snapshot, field(0.0, 0.0))
    results, evidence = AcceleratedLocalSatelliteCrossingOracle(
        selector=FakeSelector(
            fake_selection(request, ("retain", "retain", "retain"))
        )
    ).solve_with_evidence(request)

    assert evidence.exact_solver_norad_catalog_ids == tuple(
        record.norad_catalog_id for record in snapshot.records
    )
    assert evidence.rejected_norad_catalog_ids == ()
    assert not evidence.fallback_to_exhaustive
    with pytest.raises(FrozenInstanceError):
        evidence.field_id = "changed"
    assert results == LocalSatelliteCrossingOracle().solve(request)


def test_mixed_decisions_call_shared_exact_seam_once_per_non_reject(
    monkeypatch,
):
    snapshot = load_snapshot("synthetic_50s4b_v1")
    request = query(snapshot, field(0.0, 0.0))
    selection = fake_selection(
        request, ("reject", "retain", "indeterminate")
    )
    calls = []

    def solve_record(request_value, record, *, max_evaluations_per_record):
        assert request_value is request
        assert max_evaluations_per_record == 20000
        calls.append(record.norad_catalog_id)
        return ()

    monkeypatch.setattr(acceleration_module, "_solve_record", solve_record)
    results, evidence = AcceleratedLocalSatelliteCrossingOracle(
        selector=FakeSelector(selection)
    ).solve_with_evidence(request)

    assert results == ()
    assert tuple(calls) == selection.exact_solver_norad_catalog_ids
    assert selection.rejected_norad_catalog_ids[0] not in calls
    assert evidence.selection is selection


@pytest.mark.parametrize(
    "outcomes",
    [
        ("reject", "reject", "reject"),
        ("retain", "retain", "retain"),
        ("indeterminate", "indeterminate", "indeterminate"),
    ],
)
def test_coordinator_preserves_all_ordered_decision_modes(monkeypatch, outcomes):
    snapshot = load_snapshot("synthetic_50s4b_v1")
    request = query(snapshot, field(0.0, 0.0))
    selection = fake_selection(request, outcomes)
    calls = []

    def solve_record(_request, record, *, max_evaluations_per_record):
        calls.append(record.norad_catalog_id)
        return ()

    monkeypatch.setattr(acceleration_module, "_solve_record", solve_record)
    _results, evidence = AcceleratedLocalSatelliteCrossingOracle(
        selector=FakeSelector(selection)
    ).solve_with_evidence(request)

    assert tuple(calls) == selection.exact_solver_norad_catalog_ids
    assert evidence.rejected_norad_catalog_ids == (
        selection.rejected_norad_catalog_ids
    )


def test_selector_exception_falls_back_to_complete_exhaustive_route(
    monkeypatch,
):
    snapshot = load_snapshot("synthetic_50s4b_v1")
    request = query(snapshot, field(0.0, 0.0))
    sentinel = ("complete exhaustive result",)
    calls = []

    def exhaustive(_self, request_value):
        calls.append(request_value)
        return sentinel

    monkeypatch.setattr(LocalSatelliteCrossingOracle, "solve", exhaustive)
    results, evidence = AcceleratedLocalSatelliteCrossingOracle(
        selector=FakeSelector(error=RuntimeError("selector unavailable"))
    ).solve_with_evidence(request)

    assert results == sentinel
    assert calls == [request]
    assert evidence.fallback_to_exhaustive
    assert evidence.selection is None
    assert evidence.rejected_norad_catalog_ids == ()
    assert evidence.exact_solver_norad_catalog_ids == tuple(
        record.norad_catalog_id for record in snapshot.records
    )
    assert "RuntimeError" in evidence.fallback_reason


def test_selector_exception_can_fail_closed_by_explicit_policy():
    snapshot = load_snapshot("synthetic_50s4b_v1")
    request = query(snapshot, field(0.0, 0.0))
    oracle = AcceleratedLocalSatelliteCrossingOracle(
        selector=FakeSelector(error=RuntimeError("selector unavailable")),
        policy=AcceleratedCrossingPolicy(
            selector_failure_mode="fail_closed"
        ),
    )

    with pytest.raises(
        SatelliteCrossingConvergenceError, match="selector failed closed"
    ):
        oracle.solve(request)


@pytest.mark.parametrize(
    "change",
    ["field", "missing", "duplicate", "reordered", "unknown"],
)
def test_inconsistent_selector_evidence_fails_closed(change):
    snapshot = load_snapshot("synthetic_50s4b_v1")
    request = query(snapshot, field(0.0, 0.0))
    selection = fake_selection(
        request, ("retain", "retain", "retain")
    )
    if change == "field":
        selection = replace(selection, field_id="wrong-field")
    else:
        decisions = list(selection.decisions)
        if change == "missing":
            decisions = decisions[:-1]
        elif change == "duplicate":
            decisions[-1] = decisions[0]
        elif change == "reordered":
            decisions[0], decisions[1] = decisions[1], decisions[0]
        elif change == "unknown":
            decisions[-1] = replace(
                decisions[-1], norad_catalog_id=999999
            )
        object.__setattr__(selection, "decisions", tuple(decisions))

    with pytest.raises(SatelliteCrossingConvergenceError):
        AcceleratedLocalSatelliteCrossingOracle(
            selector=FakeSelector(selection)
        ).solve(request)


def test_reject_outside_coordinator_domain_fails_closed():
    snapshot = load_snapshot("synthetic_50s4b_v1")
    request = query(
        snapshot, field(0.0, 0.0), seconds=61.0
    )
    selection = fake_selection(
        request, ("reject", "retain", "retain")
    )

    with pytest.raises(
        SatelliteCrossingConvergenceError,
        match="outside the coordinator's admitted domain",
    ):
        AcceleratedLocalSatelliteCrossingOracle(
            selector=FakeSelector(selection)
        ).solve(request)


def test_real_selector_results_are_exactly_exhaustive():
    snapshot = load_snapshot("synthetic_50s4b_v1")
    request = query(snapshot, field(0.0, 0.0))
    exhaustive = LocalSatelliteCrossingOracle().solve(request)
    accelerated, evidence = (
        AcceleratedLocalSatelliteCrossingOracle().solve_with_evidence(request)
    )

    assert accelerated == exhaustive
    assert AcceleratedLocalSatelliteCrossingOracle().solve(request) == exhaustive
    assert evidence.selection == ConservativeConeShellSelector().select(request)
    assert set(evidence.rejected_norad_catalog_ids).isdisjoint(
        evidence.exact_solver_norad_catalog_ids
    )



def test_candidate_coordinator_contracts_are_package_exports():
    from wenu.satellites import (
        AcceleratedCrossingEvidence as ExportedEvidence,
        AcceleratedCrossingPolicy as ExportedPolicy,
        AcceleratedLocalSatelliteCrossingOracle as ExportedOracle,
    )

    assert ExportedEvidence is acceleration_module.AcceleratedCrossingEvidence
    assert ExportedPolicy is AcceleratedCrossingPolicy
    assert ExportedOracle is AcceleratedLocalSatelliteCrossingOracle


def test_exact_selector_and_default_track_routes_consume_kernel_states_and_refuse(monkeypatch):
    """Synthetic installed snapshot; real kernel, SGP4 and observer services."""
    from wenu_kernel.kernel import KernelSession
    from wenu_kernel.errors import UnsupportedCapability
    from wenu.satellites.exact_tracks import ExactLocalSatelliteTrackRealizer, ExactLocalTrackError
    snapshot = load_snapshot()
    state = start_state(snapshot, snapshot.records[0])
    request = query(snapshot, field(state.gcrs_axis_longitude_deg, state.gcrs_axis_latitude_deg), seconds=0.)
    identifier = snapshot.records[0].norad_catalog_id
    original = KernelSession.evaluate
    queries = []
    def tracked(session, value):
        queries.append(value)
        return original(session, value)
    monkeypatch.setattr(KernelSession, 'evaluate', tracked)
    oracle = LocalSatelliteCrossingOracle()
    selector = ConservativeConeShellSelector()
    visits = oracle.solve(request)
    visit = next(item for item in visits if item.candidate.satellite.norad_catalog_id == identifier)
    assert selector.select(request).decisions[0].outcome == 'retain'
    realizer = ExactLocalSatelliteTrackRealizer()
    before = realizer.realize(visit, snapshot)
    assert queries and all(item.reference.frame_id == 'teme' for item in queries)
    assert all(item.evaluation_policy == 'full_model' for item in queries)
    def mirrored(session, value):
        batch = tracked(session, value)
        return replace(batch, states=tuple(replace(row,
            position_m=tuple(-x for x in row.position_m),
            velocity_m_s=tuple(-x for x in row.velocity_m_s)) for row in batch.states))
    monkeypatch.setattr(KernelSession, 'evaluate', mirrored)
    moved = oracle.solve(request)
    assert identifier not in tuple(item.candidate.satellite.norad_catalog_id for item in moved)
    assert selector.select(request).decisions[0].outcome == 'reject'
    after = realizer.realize(visit, snapshot)
    assert not np.allclose(before.samples[0].direction, after.samples[0].direction, rtol=0, atol=1e-6)
    assert after.samples[0].instant_utc == before.samples[0].instant_utc
    assert after.crossing is before.crossing is visit
    assert after.crossing.candidate.snapshot_sha256 == snapshot.manifest.content_sha256
    def unavailable(*args, **kwargs):
        raise UnsupportedCapability('exact satellite state unavailable')
    monkeypatch.setattr(KernelSession, 'evaluate', unavailable)
    selection = selector.select(request)
    assert all(item.outcome == 'indeterminate' for item in selection.decisions)
    assert selection.exact_solver_norad_catalog_ids == tuple(record.norad_catalog_id for record in snapshot.records)
    with pytest.raises(SatelliteCrossingConvergenceError, match='evaluation failed'):
        oracle.solve(request)
    with pytest.raises(SatelliteCrossingConvergenceError, match='evaluation failed'):
        AcceleratedLocalSatelliteCrossingOracle().solve(request)
    with pytest.raises(ExactLocalTrackError, match='evaluation failed'):
        realizer.realize(visit, snapshot)


def test_narrow_positive_duration_synthetic_pass_matches_exhaustive():
    """Real SGP4/observer events on a canonical one-record synthetic snapshot."""
    from dataclasses import asdict
    from wenu.satellites.elements import canonical_json_bytes, sha256_hex
    from wenu.satellites.snapshots import snapshot_from_bytes
    from test_satellite_crossing_matrix import mapping
    installed = load_snapshot()
    record = installed.records[0]
    payload = canonical_json_bytes([mapping(record)])
    manifest = replace(installed.manifest, record_count=1, content_sha256=sha256_hex(payload))
    snapshot = snapshot_from_bytes(canonical_json_bytes(asdict(manifest)), payload)
    midpoint = START + timedelta(seconds=3.)
    state = SatelliteTopocentricTransformer().transform(
        Sgp4TemePropagator(record,snapshot_sha256=snapshot.manifest.content_sha256).propagate(iso(midpoint)),observer())
    request = query(snapshot,field(state.gcrs_axis_longitude_deg,state.gcrs_axis_latitude_deg,radius=.005),seconds=6.)
    exhaustive = LocalSatelliteCrossingOracle().solve(request)
    accelerated,evidence = AcceleratedLocalSatelliteCrossingOracle().solve_with_evidence(request)
    assert len(exhaustive) == 1 and accelerated == exhaustive
    visit = exhaustive[0]
    assert request.interval.start < visit.entry_instant < visit.closest_approach_instant < visit.exit_instant < request.interval.stop
    assert visit.time_in_field_seconds > 0.
    assert abs((datetime.fromisoformat(visit.closest_approach_instant.replace('Z','+00:00'))-midpoint).total_seconds()) < .02
    assert visit.closest_approach_deg <= request.angular_tolerance_deg
    assert evidence.fallback_to_exhaustive is False
    assert evidence.rejected_norad_catalog_ids == ()
    assert evidence.exact_solver_norad_catalog_ids == (record.norad_catalog_id,)
