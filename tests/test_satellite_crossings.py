from dataclasses import FrozenInstanceError

import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteCrossingCandidate,
    SatelliteCrossingResult,
    SatelliteFieldOfView,
    SatelliteIdentity,
    SatelliteObserver,
)


def field_spec():
    return CoordinateSpec(
        frame="icrs",
        origin="topocentric-direction",
        position_status=PositionStatus.APPARENT,
        instant="2026-09-15T01:00:00Z",
        time_scale="utc",
        provider="satchecker",
    )


def query_contracts():
    satellite = SatelliteIdentity(
        norad_catalog_id=25544,
        object_name="ISS (ZARYA)",
        international_designator="1998-067A",
        classification="U",
    )
    observer = SatelliteObserver(
        observer_id="la-ligua",
        longitude_deg=288.769711,
        latitude_deg=-32.443342,
        elevation_m=52.0,
    )
    field = SatelliteFieldOfView(
        field_id="science-field-1",
        center_longitude_deg=190.0,
        center_latitude_deg=-62.0,
        angular_radius_deg=1.0,
        coordinate_spec=field_spec(),
    )
    interval = InclusiveTimeInterval(
        start="2026-09-15T01:00:00Z",
        stop="2026-09-15T01:10:00+00:00",
    )
    candidate = SatelliteCrossingCandidate(
        satellite=satellite,
        observer=observer,
        field_of_view=field,
        interval=interval,
        source_provider="SatChecker",
        orbit_solution_id="provider-solution-1",
        snapshot_sha256="a" * 64,
        element_epoch="2026-09-14T12:00:00Z",
        provenance=("cached response",),
        warnings=("provider illumination only",),
    )
    return satellite, observer, field, interval, candidate


def test_satellite_identity_preserves_large_catalogue_identifiers():
    identity = SatelliteIdentity(
        norad_catalog_id=123456789,
        object_name="  Example  ",
        international_designator=" 2026-001A ",
    )

    assert identity.norad_catalog_id == 123456789
    assert identity.object_name == "Example"
    assert identity.international_designator == "2026-001A"
    with pytest.raises(FrozenInstanceError):
        identity.object_name = "changed"


@pytest.mark.parametrize("value", [True, 0, -1, "25544"])
def test_satellite_identity_rejects_invalid_catalogue_identifiers(value):
    error = TypeError if value in (True, "25544") else ValueError
    with pytest.raises(error):
        SatelliteIdentity(norad_catalog_id=value)


def test_satellite_observer_normalizes_site_and_policy():
    observer = SatelliteObserver(
        observer_id=" La Ligua ",
        longitude_deg=288.769711,
        latitude_deg=-32.443342,
        elevation_m=52,
        refraction_policy=" VACUUM ",
        earth_orientation_policy=" IERS ",
    )

    assert observer.observer_id == "La Ligua"
    assert observer.longitude_deg == pytest.approx(-71.230289)
    assert observer.latitude_deg == pytest.approx(-32.443342)
    assert observer.elevation_m == 52.0
    assert observer.refraction_policy == "vacuum"
    assert observer.earth_orientation_policy == "iers"


def test_satellite_field_is_closed_spherical_geometry():
    field = SatelliteFieldOfView(
        field_id="field",
        center_longitude_deg=-10.0,
        center_latitude_deg=90.0,
        angular_radius_deg=180.0,
        coordinate_spec=field_spec(),
    )

    assert field.center_longitude_deg == 350.0
    assert field.boundary == "closed"
    with pytest.raises(ValueError, match="boundary"):
        SatelliteFieldOfView(
            field_id="field",
            center_longitude_deg=0.0,
            center_latitude_deg=0.0,
            angular_radius_deg=1.0,
            coordinate_spec=field_spec(),
            boundary="open",
        )


@pytest.mark.parametrize("radius", [0.0, -1.0, 180.1])
def test_satellite_field_rejects_invalid_radius(radius):
    with pytest.raises(ValueError, match="angular_radius_deg"):
        SatelliteFieldOfView(
            field_id="field",
            center_longitude_deg=0.0,
            center_latitude_deg=0.0,
            angular_radius_deg=radius,
            coordinate_spec=field_spec(),
        )


def test_inclusive_interval_normalizes_utc_and_includes_endpoints():
    interval = InclusiveTimeInterval(
        start="2026-09-15T01:00:00Z",
        stop="2026-09-15T01:10:00+00:00",
    )

    assert interval.start == "2026-09-15T01:00:00.000000Z"
    assert interval.stop == "2026-09-15T01:10:00.000000Z"
    assert interval.contains(interval.start)
    assert interval.contains(interval.stop)
    assert not interval.contains("2026-09-15T01:10:00.000001Z")


def test_inclusive_interval_rejects_non_utc_and_reversed_values():
    with pytest.raises(ValueError, match="UTC"):
        InclusiveTimeInterval(
            start="2026-09-15T01:00:00",
            stop="2026-09-15T01:10:00Z",
        )
    with pytest.raises(ValueError, match="precede"):
        InclusiveTimeInterval(
            start="2026-09-15T01:10:00Z",
            stop="2026-09-15T01:00:00Z",
        )


def test_candidate_binds_identity_query_context_and_provenance():
    satellite, observer, field, interval, candidate = query_contracts()

    assert candidate.satellite is satellite
    assert candidate.observer is observer
    assert candidate.field_of_view is field
    assert candidate.interval is interval
    assert candidate.source_provider == "SatChecker"
    assert candidate.snapshot_sha256 == "a" * 64
    assert candidate.element_epoch == "2026-09-14T12:00:00.000000Z"
    assert candidate.provenance == ("cached response",)


def test_candidate_rejects_malformed_snapshot_digest():
    satellite, observer, field, interval, _ = query_contracts()
    with pytest.raises(ValueError, match="64 hexadecimal"):
        SatelliteCrossingCandidate(
            satellite=satellite,
            observer=observer,
            field_of_view=field,
            interval=interval,
            source_provider="provider",
            snapshot_sha256="not-a-digest",
        )


def test_normalized_result_retains_one_connected_closed_field_visit():
    *_, candidate = query_contracts()
    result = SatelliteCrossingResult(
        candidate=candidate,
        entry_instant="2026-09-15T01:02:00Z",
        closest_approach_instant="2026-09-15T01:02:30Z",
        exit_instant="2026-09-15T01:03:00Z",
        closest_approach_deg=0.25,
        range_km=500.0,
        angular_rate_deg_per_s=0.5,
        illumination="sunlit",
        provider_event_id="event-1",
        provenance=("normalized provider result",),
    )

    assert result.time_in_field_seconds == 60.0
    assert result.closest_approach_deg == 0.25
    assert result.range_km == 500.0
    assert result.angular_rate_deg_per_s == 0.5
    assert result.illumination == "sunlit"
    with pytest.raises(FrozenInstanceError):
        result.range_km = 400.0


def test_boundary_touch_is_a_valid_crossing_result():
    *_, candidate = query_contracts()
    result = SatelliteCrossingResult(
        candidate=candidate,
        entry_instant=candidate.interval.start,
        closest_approach_instant=candidate.interval.start,
        exit_instant=candidate.interval.start,
        closest_approach_deg=candidate.field_of_view.angular_radius_deg,
    )

    assert result.time_in_field_seconds == 0.0


def test_result_rejects_events_outside_query_interval():
    *_, candidate = query_contracts()
    with pytest.raises(ValueError, match="query interval"):
        SatelliteCrossingResult(
            candidate=candidate,
            entry_instant="2026-09-15T00:59:59Z",
            closest_approach_instant="2026-09-15T01:02:00Z",
            exit_instant="2026-09-15T01:03:00Z",
            closest_approach_deg=0.25,
        )


def test_result_rejects_unordered_or_outside_field_values():
    *_, candidate = query_contracts()
    with pytest.raises(ValueError, match="must be ordered"):
        SatelliteCrossingResult(
            candidate=candidate,
            entry_instant="2026-09-15T01:03:00Z",
            closest_approach_instant="2026-09-15T01:02:00Z",
            exit_instant="2026-09-15T01:04:00Z",
            closest_approach_deg=0.25,
        )
    with pytest.raises(ValueError, match="closed field"):
        SatelliteCrossingResult(
            candidate=candidate,
            entry_instant="2026-09-15T01:02:00Z",
            closest_approach_instant="2026-09-15T01:02:30Z",
            exit_instant="2026-09-15T01:03:00Z",
            closest_approach_deg=1.1,
        )
