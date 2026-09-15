"""Independent numerical and installed-composition crossing-oracle evidence."""

from datetime import datetime, timedelta, timezone
from math import cos, radians, sin

import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteCrossingCandidate,
    SatelliteFieldOfView,
    SatelliteIdentity,
    SatelliteObserver,
)
from wenu.satellites import load_snapshot
from wenu.satellites.crossing_oracle import (
    LocalSatelliteCrossingOracle,
    LocalSatelliteCrossingQuery,
    SatelliteCrossingConvergenceError,
    _TrajectoryState,
    _solve_trajectory,
)


START = datetime(2026, 9, 15, tzinfo=timezone.utc)


def instant(seconds):
    return START + timedelta(seconds=seconds)


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


def field(radius=10.0, *, frame="gcrs-axes", status=PositionStatus.GEOMETRIC):
    return SatelliteFieldOfView(
        field_id="analytic-field",
        center_longitude_deg=0.0,
        center_latitude_deg=0.0,
        angular_radius_deg=radius,
        coordinate_spec=CoordinateSpec(
            frame=frame,
            origin="topocentric-direction",
            position_status=status,
            instant=iso(START),
            time_scale="utc",
            provider="analytic test",
        ),
    )


def candidate(radius=10.0, stop_seconds=100.0):
    return SatelliteCrossingCandidate(
        satellite=SatelliteIdentity(900001, "ANALYTIC"),
        observer=observer(),
        field_of_view=field(radius),
        interval=InclusiveTimeInterval(iso(START), iso(instant(stop_seconds))),
        source_provider="independent analytic trajectory",
        snapshot_sha256="a" * 64,
        element_epoch=iso(START),
    )


def longitude_state(function, derivative):
    def evaluate(value):
        seconds = (value - START).total_seconds()
        longitude = function(seconds)
        angle = radians(longitude)
        return _TrajectoryState(
            instant=value,
            direction=(cos(angle), sin(angle), 0.0),
            range_km=1000.0,
            angular_rate_deg_per_s=abs(derivative(seconds)),
        )

    return evaluate


def solve(evaluator, *, radius=10.0, stop_seconds=100.0, limit=20000):
    return _solve_trajectory(
        evaluator,
        candidate=candidate(radius, stop_seconds),
        time_tolerance_seconds=0.01,
        angular_tolerance_deg=1e-5,
        max_evaluations=limit,
    )


def seconds(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (parsed - START).total_seconds()


def test_linear_great_circle_crossing_has_independent_known_roots():
    results = solve(longitude_state(lambda t: t - 50.0, lambda _t: 1.0))

    assert len(results) == 1
    result = results[0]
    assert seconds(result.entry_instant) == pytest.approx(40.0, abs=0.02)
    assert seconds(result.exit_instant) == pytest.approx(60.0, abs=0.02)
    assert seconds(result.closest_approach_instant) == pytest.approx(50.0, abs=0.02)
    assert result.closest_approach_deg == pytest.approx(0.0, abs=1e-5)
    assert result.angular_rate_deg_per_s == pytest.approx(1.0)


def test_fixed_outside_trajectory_is_certified_absent():
    results = solve(longitude_state(lambda _t: 30.0, lambda _t: 0.0))

    assert results == ()


def test_fixed_inside_trajectory_uses_inclusive_query_endpoints():
    results = solve(longitude_state(lambda _t: 2.0, lambda _t: 0.0))

    assert len(results) == 1
    assert results[0].entry_instant == iso(START)
    assert results[0].exit_instant == iso(instant(100.0))


def test_bounded_minimum_detects_zero_duration_tangent_without_sign_change():
    evaluator = longitude_state(
        lambda t: 10.0 + ((t - 50.0) / 10.0) ** 2,
        lambda t: 2.0 * (t - 50.0) / 100.0,
    )
    results = solve(evaluator)

    assert len(results) == 1
    result = results[0]
    assert seconds(result.entry_instant) == pytest.approx(50.0, abs=0.02)
    assert seconds(result.exit_instant) == pytest.approx(50.0, abs=0.02)
    assert result.closest_approach_deg == pytest.approx(10.0, abs=1e-5)


def test_disconnected_visits_remain_separate_and_ordered():
    evaluator = longitude_state(
        lambda t: 20.0 * sin(radians(7.2 * t)),
        lambda t: 0.8 * 3.141592653589793 * cos(radians(7.2 * t)),
    )
    results = solve(evaluator, radius=5.0, stop_seconds=50.0)

    assert len(results) >= 2
    assert tuple(item.entry_instant for item in results) == tuple(
        sorted(item.entry_instant for item in results)
    )
    assert all(
        left.exit_instant < right.entry_instant
        for left, right in zip(results, results[1:])
    )


def test_longitude_seam_is_absent_from_vector_predicate():
    seam_field = candidate(radius=2.0)
    seam_field = SatelliteCrossingCandidate(
        satellite=seam_field.satellite,
        observer=seam_field.observer,
        field_of_view=SatelliteFieldOfView(
            field_id="seam",
            center_longitude_deg=359.0,
            center_latitude_deg=0.0,
            angular_radius_deg=2.1,
            coordinate_spec=seam_field.field_of_view.coordinate_spec,
        ),
        interval=seam_field.interval,
        source_provider=seam_field.source_provider,
        snapshot_sha256=seam_field.snapshot_sha256,
        element_epoch=seam_field.element_epoch,
    )
    evaluator = longitude_state(lambda _t: 1.0, lambda _t: 0.0)

    results = _solve_trajectory(
        evaluator,
        candidate=seam_field,
        time_tolerance_seconds=0.01,
        angular_tolerance_deg=1e-5,
        max_evaluations=20000,
    )

    assert len(results) == 1
    assert results[0].closest_approach_deg == pytest.approx(2.0, abs=1e-10)


def test_tightening_tolerances_is_stable():
    evaluator = longitude_state(lambda t: t - 50.0, lambda _t: 1.0)
    coarse = _solve_trajectory(
        evaluator,
        candidate=candidate(),
        time_tolerance_seconds=0.1,
        angular_tolerance_deg=1e-3,
        max_evaluations=20000,
    )[0]
    fine = solve(evaluator)[0]

    assert abs(seconds(coarse.entry_instant) - seconds(fine.entry_instant)) <= 0.1
    assert abs(seconds(coarse.exit_instant) - seconds(fine.exit_instant)) <= 0.1


def test_resource_exhaustion_fails_closed_instead_of_returning_negative():
    evaluator = longitude_state(lambda t: t - 50.0, lambda _t: 1.0)

    with pytest.raises(SatelliteCrossingConvergenceError, match="NORAD 900001"):
        solve(evaluator, limit=3)


@pytest.mark.parametrize(
    ("frame", "status"),
    [
        ("icrs", PositionStatus.APPARENT),
        ("altaz", PositionStatus.GEOMETRIC),
    ],
)
def test_query_rejects_incompatible_coordinate_identity(frame, status):
    with pytest.raises(ValueError, match="GCRS axes"):
        LocalSatelliteCrossingQuery(
            snapshot=load_snapshot(),
            observer=observer(),
            field_of_view=field(frame=frame, status=status),
            interval=InclusiveTimeInterval(iso(START), iso(instant(60.0))),
            time_tolerance_seconds=0.1,
            angular_tolerance_deg=1e-4,
        )


def test_query_is_immutable_and_requires_positive_tolerances():
    query = LocalSatelliteCrossingQuery(
        snapshot=load_snapshot(),
        observer=observer(),
        field_of_view=field(180.0),
        interval=InclusiveTimeInterval(iso(START), iso(instant(60.0))),
        time_tolerance_seconds=1.0,
        angular_tolerance_deg=1e-3,
    )

    with pytest.raises(AttributeError):
        query.time_tolerance_seconds = 2.0
    with pytest.raises(ValueError, match="positive"):
        LocalSatelliteCrossingQuery(
            snapshot=query.snapshot,
            observer=query.observer,
            field_of_view=query.field_of_view,
            interval=query.interval,
            time_tolerance_seconds=0.0,
            angular_tolerance_deg=1e-3,
        )


def test_installed_snapshot_scan_is_complete_ordered_and_provenanced():
    snapshot = load_snapshot()
    query = LocalSatelliteCrossingQuery(
        snapshot=snapshot,
        observer=observer(),
        field_of_view=field(180.0),
        interval=InclusiveTimeInterval(iso(START), iso(instant(60.0))),
        time_tolerance_seconds=1.0,
        angular_tolerance_deg=1e-3,
    )

    results = LocalSatelliteCrossingOracle().solve(query)

    assert tuple(
        item.candidate.satellite.norad_catalog_id for item in results
    ) == tuple(record.norad_catalog_id for record in snapshot.records)
    assert all(
        item.candidate.snapshot_sha256 == snapshot.manifest.content_sha256
        for item in results
    )
    assert all(item.illumination is None for item in results)
    assert all("exhaustive adaptive" in item.provenance[0] for item in results)
