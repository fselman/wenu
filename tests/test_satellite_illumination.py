"""Direct-Sun occultation and observer-night geometry tests."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from math import acos, asin, cos, pi, sin

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, ITRS
from astropy.time import Time

from wenu.ephemeris import (
    EphemerisResourceIdentity,
    EphemerisState,
)
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteObserver,
)
import wenu.satellites.illumination as illumination_module
from wenu.satellites import (
    LunarOccultorStatus,
    ObserverTwilightClass,
    ShadowTransitionKind,
    ShadowTransitionSearchPolicy,
    SatelliteIlluminationFailureCode,
    SatelliteIlluminationGeometryError,
    SatelliteGeocentricItrsTransformer,
    SatelliteIlluminationGeometryEvaluator,
    SatelliteShadowTransitionFinder,
    SatelliteShadowTransitionQuery,
    SolarOccultationClass,
    SolarOccultationContactGeometry,
    SolarOccultationPolicy,
    Sgp4TemePropagator,
    classify_observer_twilight,
    evaluate_solar_occultation,
    evaluate_solar_occultation_contact,
)
from wenu.satellites.elements import SatelliteElementRecord
from wenu.satellites.snapshots import (
    SatelliteElementSnapshot,
    SatelliteSnapshotManifest,
)
from wenu.satellites.topocentric import SatelliteTopocentricTransformer


SPHERE_RADIUS_KM = 6378.0


def spherical_policy(*, solar_radius_km=695700.0):
    return SolarOccultationPolicy(
        earth_equatorial_radius_km=SPHERE_RADIUS_KM,
        earth_polar_radius_km=SPHERE_RADIUS_KM,
        solar_radius_km=solar_radius_km,
        radial_samples=128,
        azimuth_samples=512,
    )


def synthetic_geometry(*, satellite_radius, alpha, separation):
    satellite = np.asarray((satellite_radius, 0.0, 0.0))
    direction = np.asarray(
        (-cos(separation), sin(separation), 0.0),
    )
    sun_distance = 100_000_000.0
    solar_radius = sun_distance * sin(alpha)
    earth_to_sun = satellite + sun_distance * direction
    result = evaluate_solar_occultation(
        satellite,
        earth_to_sun,
        policy=spherical_policy(solar_radius_km=solar_radius),
    )
    return result


def circle_overlap_area(radius_a, radius_b, separation):
    if separation >= radius_a + radius_b:
        return 0.0
    if separation <= abs(radius_b - radius_a):
        return pi * min(radius_a, radius_b) ** 2
    term_a = (
        radius_a**2
        * acos(
            (separation**2 + radius_a**2 - radius_b**2)
            / (2.0 * separation * radius_a)
        )
    )
    term_b = (
        radius_b**2
        * acos(
            (separation**2 + radius_b**2 - radius_a**2)
            / (2.0 * separation * radius_b)
        )
    )
    radicand = (
        (-separation + radius_a + radius_b)
        * (separation + radius_a - radius_b)
        * (separation - radius_a + radius_b)
        * (separation + radius_a + radius_b)
    )
    return term_a + term_b - 0.5 * np.sqrt(max(radicand, 0.0))


@pytest.mark.parametrize(
    ("altitude", "expected"),
    (
        (0.0, ObserverTwilightClass.DAY),
        (-1.0e-12, ObserverTwilightClass.CIVIL_TWILIGHT),
        (-6.0, ObserverTwilightClass.CIVIL_TWILIGHT),
        (-6.000000001, ObserverTwilightClass.NAUTICAL_TWILIGHT),
        (-12.0, ObserverTwilightClass.NAUTICAL_TWILIGHT),
        (-12.000000001, ObserverTwilightClass.ASTRONOMICAL_TWILIGHT),
        (-18.0, ObserverTwilightClass.ASTRONOMICAL_TWILIGHT),
        (-18.000000001, ObserverTwilightClass.ASTRONOMICAL_NIGHT),
    ),
)
def test_twilight_boundaries_are_geometric_and_stable(altitude, expected):
    assert classify_observer_twilight(altitude) is expected


def test_spherical_exterior_contact_is_stably_sunlit():
    satellite_radius = 1_000_000.0
    beta = asin(SPHERE_RADIUS_KM / satellite_radius)
    alpha = 0.004

    result = synthetic_geometry(
        satellite_radius=satellite_radius,
        alpha=alpha,
        separation=alpha + beta,
    )

    assert result.occultation_class is SolarOccultationClass.SUNLIT
    assert result.visible_disk_fraction == 1.0


def test_spherical_interior_contact_is_stably_umbra():
    satellite_radius = 1_000_000.0
    beta = asin(SPHERE_RADIUS_KM / satellite_radius)
    alpha = 0.004

    result = synthetic_geometry(
        satellite_radius=satellite_radius,
        alpha=alpha,
        separation=beta - alpha,
    )

    assert result.occultation_class is SolarOccultationClass.UMBRA
    assert result.visible_disk_fraction == 0.0


def test_spherical_partial_fraction_matches_analytic_disk_overlap():
    satellite_radius = 1_000_000.0
    beta = asin(SPHERE_RADIUS_KM / satellite_radius)
    alpha = 0.004
    separation = beta
    result = synthetic_geometry(
        satellite_radius=satellite_radius,
        alpha=alpha,
        separation=separation,
    )
    blocked_area = circle_overlap_area(alpha, beta, separation)
    expected_visible = 1.0 - blocked_area / (pi * alpha**2)

    assert result.occultation_class is SolarOccultationClass.PENUMBRA
    assert result.visible_disk_fraction == pytest.approx(
        expected_visible,
        abs=2.0e-3,
    )
    assert result.quadrature_absolute_difference <= (
        spherical_policy().fraction_convergence_tolerance
    )
    assert result.evaluated_ray_count == 256 * 1024


def test_partial_geometry_fails_closed_when_quadrature_does_not_converge():
    satellite_radius = 1_000_000.0
    beta = asin(SPHERE_RADIUS_KM / satellite_radius)
    alpha = 0.004
    separation = beta
    satellite = np.asarray((satellite_radius, 0.0, 0.0))
    direction = np.asarray(
        (-cos(separation), sin(separation), 0.0),
    )
    sun_distance = 100_000_000.0
    earth_to_sun = satellite + sun_distance * direction
    policy = SolarOccultationPolicy(
        earth_equatorial_radius_km=SPHERE_RADIUS_KM,
        earth_polar_radius_km=SPHERE_RADIUS_KM,
        solar_radius_km=sun_distance * sin(alpha),
        radial_samples=8,
        azimuth_samples=32,
        maximum_refinements=1,
        fraction_convergence_tolerance=1.0e-12,
    )

    with pytest.raises(SatelliteIlluminationGeometryError) as caught:
        evaluate_solar_occultation(
            satellite,
            earth_to_sun,
            policy=policy,
        )

    assert (
        caught.value.code
        is SatelliteIlluminationFailureCode.QUADRATURE_NOT_CONVERGED
    )


def test_spherical_annular_geometry_is_typed_antumbra():
    result = synthetic_geometry(
        satellite_radius=1_000_000.0,
        alpha=0.01,
        separation=0.0,
    )

    assert result.occultation_class is SolarOccultationClass.ANTUMBRA
    assert 0.0 < result.visible_disk_fraction < 1.0


@pytest.mark.parametrize(
    "satellite_radius",
    (7000.0, 26560.0, 42164.0, 100000.0),
)
def test_aligned_leo_meo_geo_and_high_orbit_states_are_umbra(
    satellite_radius,
):
    result = evaluate_solar_occultation(
        (satellite_radius, 0.0, 0.0),
        (-149_597_870.7, 0.0, 0.0),
    )

    assert result.occultation_class is SolarOccultationClass.UMBRA
    assert result.visible_disk_fraction == 0.0


@pytest.mark.parametrize(
    "satellite",
    ((7000.0, 0.0, 0.0), (0.0, 0.0, 7000.0)),
)
def test_equatorial_and_polar_clear_states_are_sunlit(satellite):
    satellite = np.asarray(satellite)
    direction = satellite / np.linalg.norm(satellite)
    earth_to_sun = satellite + direction * 149_597_870.7

    result = evaluate_solar_occultation(satellite, earth_to_sun)

    assert result.occultation_class is SolarOccultationClass.SUNLIT
    assert result.visible_disk_fraction == 1.0


def test_occultation_rejects_a_state_inside_the_earth():
    with pytest.raises(SatelliteIlluminationGeometryError) as caught:
        evaluate_solar_occultation((0.0, 0.0, 0.0), (1.0e8, 0.0, 0.0))

    assert (
        caught.value.code
        is SatelliteIlluminationFailureCode.NON_FINITE_GEOMETRY
    )


def vanguard_record():
    return SatelliteElementRecord(
        object_name="VANGUARD 1",
        international_designator="1958-002B",
        norad_catalog_id=5,
        classification="U",
        epoch_utc="2000-06-27T18:50:19.733568Z",
        mean_motion_rev_per_day=10.82419157,
        eccentricity=0.1859667,
        inclination_deg=34.2682,
        ra_of_ascending_node_deg=348.7242,
        argument_of_pericenter_deg=331.7664,
        mean_anomaly_deg=19.3264,
        bstar=2.8098e-5,
        mean_motion_dot=0.00000023,
        mean_motion_ddot=0.0,
        ephemeris_type=0,
        element_set_number=1,
        revolution_number_at_epoch=1,
        source_identity="Vallado SGP4 verification case",
        source_record_sha256="0" * 64,
        provenance=("AIAA 2006-6753 SGP4 verification input.",),
    )


def transformed_state():
    teme = Sgp4TemePropagator(vanguard_record()).propagate(
        "2000-06-27T18:50:19.733568Z"
    )
    observer = SatelliteObserver(
        "test-site",
        -71.230289,
        -32.443342,
        52.0,
        refraction_policy="vacuum",
        earth_orientation_policy="iers-a-bundled",
    )
    return SatelliteTopocentricTransformer().transform(teme, observer)


def resource():
    return EphemerisResourceIdentity(
        provider="test",
        model="synthetic-sun",
        filename="synthetic.bsp",
        sha256="1" * 64,
        coverage_start="JD 2400000",
        coverage_end="JD 2500000",
        coverage_time_scale="tdb",
    )


class SyntheticSunSource:
    def __init__(self, position_au=(1.0, 0.0, 0.0)):
        self.position_au = position_au
        self.request = None

    def state(self, request):
        self.request = request
        return EphemerisState(
            request=request,
            position=self.position_au,
            velocity=(0.0, 0.0, 0.0),
            position_unit="au",
            velocity_unit="au/day",
            resource=resource(),
            provider_target_id="10",
            provider_centre_id="399",
            provenance=("synthetic same-instant geometric state",),
        )


def test_evaluator_composes_exact_instant_identity_and_provenance():
    topocentric = transformed_state()
    source = SyntheticSunSource()
    result = SatelliteIlluminationGeometryEvaluator(source).evaluate(
        topocentric
    )

    assert result.evaluation_utc == topocentric.teme_state.evaluation_utc
    assert result.sun_ephemeris_state.request is source.request
    assert source.request.target == "sun"
    assert source.request.centre == "earth"
    assert source.request.frame == "icrf"
    assert source.request.time_scale == "utc"
    assert result.common_frame == "itrs"
    assert result.lunar_occultor_status is LunarOccultorStatus.NOT_EVALUATED
    assert result.policy.earth_shape_model == "WGS-84 ellipsoid"
    assert 0.0 <= result.solar_occultation.visible_disk_fraction <= 1.0
    assert "not a brightness or visibility claim" in result.warnings[0]


def test_evaluator_sun_altitude_matches_independent_astropy_altaz():
    topocentric = transformed_state()
    result = SatelliteIlluminationGeometryEvaluator(
        SyntheticSunSource()
    ).evaluate(topocentric)
    time = Time(result.evaluation_utc, scale="utc")
    location = EarthLocation.from_geodetic(
        lon=topocentric.observer.longitude_deg * u.deg,
        lat=topocentric.observer.latitude_deg * u.deg,
        height=topocentric.observer.elevation_m * u.m,
        ellipsoid="WGS84",
    )
    earth_to_sun = np.asarray(result.earth_to_sun_itrs_km)
    observer_to_sun = (
        earth_to_sun
        - np.asarray(topocentric.observer_itrs_position_km)
    )
    direction = ITRS(
        x=observer_to_sun[0] * u.km,
        y=observer_to_sun[1] * u.km,
        z=observer_to_sun[2] * u.km,
        obstime=time,
        location=location,
    )
    independent = direction.transform_to(
        AltAz(
            obstime=time,
            location=location,
            pressure=0.0 * u.hPa,
        )
    )

    assert result.observer_sun_altitude_deg == pytest.approx(
        independent.alt.to_value(u.deg),
        abs=1.0e-10,
    )


def test_geometry_and_policy_are_immutable():
    result = SatelliteIlluminationGeometryEvaluator(
        SyntheticSunSource()
    ).evaluate(transformed_state())

    with pytest.raises(FrozenInstanceError):
        result.observer_sun_altitude_deg = 0.0
    with pytest.raises(FrozenInstanceError):
        result.policy.radial_samples = 8


def test_evaluator_fails_closed_on_mismatched_request():
    class WrongRequestSource(SyntheticSunSource):
        def state(self, request):
            state = super().state(request)
            wrong = replace(request, frame="ecliptic")
            return replace(state, request=wrong)

    with pytest.raises(SatelliteIlluminationGeometryError) as caught:
        SatelliteIlluminationGeometryEvaluator(
            WrongRequestSource()
        ).evaluate(transformed_state())

    assert caught.value.code is SatelliteIlluminationFailureCode.FRAME_MISMATCH

def test_geocentric_itrs_seam_matches_topocentric_source_state():
    teme = Sgp4TemePropagator(vanguard_record()).propagate(
        "2000-06-27T18:50:19.733568Z"
    )
    geocentric = SatelliteGeocentricItrsTransformer().transform(teme)
    topocentric = transformed_state()

    assert geocentric.teme_state == topocentric.teme_state
    assert geocentric.earth_orientation == topocentric.earth_orientation
    assert geocentric.satellite_itrs_position_km == pytest.approx(
        topocentric.satellite_itrs_position_km,
        abs=1.0e-12,
    )
    assert geocentric.satellite_itrs_velocity_km_per_s == pytest.approx(
        topocentric.satellite_itrs_velocity_km_per_s,
        abs=1.0e-12,
    )
    assert geocentric.frame == "ITRS"
    assert not hasattr(geocentric, "observer")


@pytest.mark.parametrize(
    ("alpha", "separation_offset", "expected"),
    (
        (0.004, 1.0e-4, SolarOccultationClass.SUNLIT),
        (0.004, 0.0, SolarOccultationClass.PENUMBRA),
        (0.004, None, SolarOccultationClass.UMBRA),
        (0.010, None, SolarOccultationClass.ANTUMBRA),
    ),
)
def test_continuous_spherical_contact_geometry(
    alpha,
    separation_offset,
    expected,
):
    satellite_radius = 1_000_000.0
    beta = asin(SPHERE_RADIUS_KM / satellite_radius)
    if separation_offset is None:
        separation = 0.0
    elif separation_offset == 0.0:
        separation = beta
    else:
        separation = alpha + beta + separation_offset
    satellite = np.asarray((satellite_radius, 0.0, 0.0))
    direction = np.asarray(
        (-cos(separation), sin(separation), 0.0),
    )
    sun_distance = 100_000_000.0
    earth_to_sun = satellite + sun_distance * direction
    result = evaluate_solar_occultation_contact(
        satellite,
        earth_to_sun,
        occultation_policy=spherical_policy(
            solar_radius_km=sun_distance * sin(alpha)
        ),
    )

    assert result.occultation_class is expected
    assert result.minimum_limb_separation_rad <= (
        result.maximum_limb_separation_rad
    )
    if expected is SolarOccultationClass.PENUMBRA:
        assert result.nearest_limb_contact_margin_rad < 0.0
    elif expected is SolarOccultationClass.ANTUMBRA:
        assert result.solar_contains_earth_margin_rad > 0.0
    else:
        assert result.nearest_limb_contact_margin_rad > 0.0


@pytest.mark.parametrize(
    "satellite",
    (
        (7000.0, 0.0, 0.0),
        (0.0, 0.0, 7000.0),
        (4510.0, 4510.0, 1200.0),
    ),
)
def test_continuous_wgs84_contact_agrees_with_ordinary_clear_geometry(
    satellite,
):
    satellite = np.asarray(satellite, dtype=float)
    earth_to_sun = satellite + satellite / np.linalg.norm(satellite) * 1.0e8

    contact = evaluate_solar_occultation_contact(satellite, earth_to_sun)
    ordinary = evaluate_solar_occultation(satellite, earth_to_sun)

    assert contact.occultation_class is SolarOccultationClass.SUNLIT
    assert contact.occultation_class is ordinary.occultation_class
    assert contact.nearest_limb_contact_margin_rad > 0.0


def test_all_six_directed_adjacent_transition_kinds_are_closed():
    expected = {
        (SolarOccultationClass.SUNLIT, SolarOccultationClass.PENUMBRA):
            ShadowTransitionKind.SUNLIT_TO_PENUMBRA,
        (SolarOccultationClass.PENUMBRA, SolarOccultationClass.SUNLIT):
            ShadowTransitionKind.PENUMBRA_TO_SUNLIT,
        (SolarOccultationClass.PENUMBRA, SolarOccultationClass.UMBRA):
            ShadowTransitionKind.PENUMBRA_TO_UMBRA,
        (SolarOccultationClass.UMBRA, SolarOccultationClass.PENUMBRA):
            ShadowTransitionKind.UMBRA_TO_PENUMBRA,
        (SolarOccultationClass.PENUMBRA, SolarOccultationClass.ANTUMBRA):
            ShadowTransitionKind.PENUMBRA_TO_ANTUMBRA,
        (SolarOccultationClass.ANTUMBRA, SolarOccultationClass.PENUMBRA):
            ShadowTransitionKind.ANTUMBRA_TO_PENUMBRA,
    }

    assert {
        pair: illumination_module._TRANSITION_KIND[pair]
        for pair in expected
    } == expected


def test_non_adjacent_transition_topology_fails_closed():
    left = _analytic_shadow_sample(
        datetime(2026, 9, 21, tzinfo=timezone.utc),
        datetime(2026, 9, 21, tzinfo=timezone.utc),
    )
    right = replace(
        left,
        contact=replace(
            left.contact,
            occultation_class=SolarOccultationClass.UMBRA,
            central_ray_blocked=True,
        ),
    )

    with pytest.raises(SatelliteIlluminationGeometryError) as caught:
        illumination_module._transition_kind(left, right)

    assert (
        caught.value.code
        is SatelliteIlluminationFailureCode.DEGENERATE_SHADOW_TOPOLOGY
    )


def _analytic_shadow_sample(instant, start):
    seconds = (instant - start).total_seconds()
    nearest_margin = 0.01 * (seconds - 4.123) * (seconds - 6.287)
    occultation_class = (
        SolarOccultationClass.PENUMBRA
        if nearest_margin < 0.0
        else SolarOccultationClass.SUNLIT
    )
    contact = SolarOccultationContactGeometry(
        occultation_class=occultation_class,
        nearest_limb_contact_margin_rad=nearest_margin,
        solar_contains_earth_margin_rad=-0.4,
        minimum_limb_separation_rad=0.1 + nearest_margin,
        maximum_limb_separation_rad=0.5,
        solar_angular_radius_rad=0.1,
        central_ray_blocked=False,
    )
    return illumination_module._ShadowSample(
        instant=instant,
        contact=contact,
    )


def test_complete_search_finds_two_transitions_between_initial_endpoints():
    start = datetime(2026, 9, 21, tzinfo=timezone.utc)
    stop = start + timedelta(seconds=10)
    policy = ShadowTransitionSearchPolicy(
        time_tolerance_seconds=0.01,
        maximum_interval_seconds=20.0,
    )
    cache = illumination_module._ShadowEvaluationCache(
        lambda instant: _analytic_shadow_sample(instant, start),
        policy,
        5,
    )

    brackets = illumination_module._collect_transition_brackets(
        cache,
        start,
        stop,
        policy,
    )

    assert len(brackets) == 2
    assert tuple(item[2] for item in brackets) == (
        ShadowTransitionKind.SUNLIT_TO_PENUMBRA,
        ShadowTransitionKind.PENUMBRA_TO_SUNLIT,
    )
    for left, right, _ in brackets:
        assert (right.instant - left.instant).total_seconds() <= 0.01


def test_complete_search_certifies_empty_interval():
    start = datetime(2026, 9, 21, tzinfo=timezone.utc)
    stop = start + timedelta(seconds=10)
    policy = ShadowTransitionSearchPolicy(
        maximum_interval_seconds=20.0,
    )
    contact = SolarOccultationContactGeometry(
        occultation_class=SolarOccultationClass.SUNLIT,
        nearest_limb_contact_margin_rad=0.5,
        solar_contains_earth_margin_rad=-0.8,
        minimum_limb_separation_rad=0.6,
        maximum_limb_separation_rad=0.9,
        solar_angular_radius_rad=0.1,
        central_ray_blocked=False,
    )
    cache = illumination_module._ShadowEvaluationCache(
        lambda instant: illumination_module._ShadowSample(
            instant=instant,
            contact=contact,
        ),
        policy,
        5,
    )

    assert illumination_module._collect_transition_brackets(
        cache,
        start,
        stop,
        policy,
    ) == ()
    assert cache.evaluation_count == 3


def test_complete_search_fails_closed_when_budget_is_exhausted():
    start = datetime(2026, 9, 21, tzinfo=timezone.utc)
    stop = start + timedelta(seconds=10)
    policy = ShadowTransitionSearchPolicy(
        time_tolerance_seconds=0.01,
        maximum_interval_seconds=20.0,
        maximum_evaluations=3,
    )
    cache = illumination_module._ShadowEvaluationCache(
        lambda instant: _analytic_shadow_sample(instant, start),
        policy,
        5,
    )

    with pytest.raises(SatelliteIlluminationGeometryError) as caught:
        illumination_module._collect_transition_brackets(
            cache,
            start,
            stop,
            policy,
        )

    assert (
        caught.value.code
        is SatelliteIlluminationFailureCode.TRANSITION_SEARCH_EXHAUSTED
    )


def test_tangent_contact_fails_closed_at_subdivision_depth():
    start = datetime(2026, 9, 21, tzinfo=timezone.utc)
    stop = start + timedelta(seconds=2)
    policy = ShadowTransitionSearchPolicy(
        maximum_interval_seconds=3.0,
        maximum_subdivision_depth=5,
        maximum_evaluations=1000,
    )

    def tangent(instant):
        seconds = (instant - start).total_seconds() - 1.0
        margin = seconds * seconds
        return illumination_module._ShadowSample(
            instant=instant,
            contact=SolarOccultationContactGeometry(
                occultation_class=SolarOccultationClass.SUNLIT,
                nearest_limb_contact_margin_rad=margin,
                solar_contains_earth_margin_rad=-0.5,
                minimum_limb_separation_rad=0.1 + margin,
                maximum_limb_separation_rad=1.5,
                solar_angular_radius_rad=0.1,
                central_ray_blocked=False,
            ),
        )

    cache = illumination_module._ShadowEvaluationCache(
        tangent,
        policy,
        5,
    )
    with pytest.raises(SatelliteIlluminationGeometryError) as caught:
        illumination_module._collect_transition_brackets(
            cache,
            start,
            stop,
            policy,
        )

    assert (
        caught.value.code
        is SatelliteIlluminationFailureCode.TRANSITION_SEARCH_EXHAUSTED
    )


def _transition_snapshot():
    record = vanguard_record()
    manifest = SatelliteSnapshotManifest(
        schema_version=1,
        snapshot_id="transition_test",
        created_utc="2026-09-21T00:00:00Z",
        source_identity="synthetic transition test",
        source_url="https://example.invalid/transition-test",
        source_format="OMM JSON",
        records_file="records.json",
        content_sha256="2" * 64,
        record_count=1,
        builder_identity="test builder",
        provider_policy_url="https://example.invalid/policy",
        provider_policy_checked_utc="2026-09-21T00:00:00Z",
    )
    return SatelliteElementSnapshot(manifest, (record,))


def test_transition_query_is_observer_independent_and_bounded():
    snapshot = _transition_snapshot()
    query = SatelliteShadowTransitionQuery(
        snapshot=snapshot,
        norad_catalog_id=5,
        interval=InclusiveTimeInterval(
            "2026-09-21T00:00:00Z",
            "2026-09-21T00:00:10Z",
        ),
    )

    assert query.snapshot is snapshot
    assert not hasattr(query, "observer")
    with pytest.raises(SatelliteIlluminationGeometryError) as caught:
        SatelliteShadowTransitionQuery(
            snapshot=snapshot,
            norad_catalog_id=6,
            interval=query.interval,
        )
    assert (
        caught.value.code
        is SatelliteIlluminationFailureCode.INVALID_TRANSITION_QUERY
    )


def test_transition_finder_returns_identity_bound_directed_events(monkeypatch):
    snapshot = _transition_snapshot()
    start = datetime(2026, 9, 21, tzinfo=timezone.utc)
    base_teme = Sgp4TemePropagator(vanguard_record()).propagate(
        "2000-06-27T18:50:19.733568Z"
    )
    base_geocentric = SatelliteGeocentricItrsTransformer().transform(
        base_teme
    )

    class FakePropagator:
        def __init__(self, record, *, snapshot_sha256):
            assert record is snapshot.records[0]
            assert snapshot_sha256 == snapshot.manifest.content_sha256

        def propagate(self, instant):
            return replace(base_teme, evaluation_utc=instant)

    class FakeTransformer:
        def transform(self, state):
            return replace(base_geocentric, teme_state=state)

    def fake_sun_state(source, instant, earth_orientation):
        request = illumination_module.EphemerisStateRequest(
            target="sun",
            centre="earth",
            frame="icrf",
            instant=instant,
            time_scale="utc",
        )
        return source.state(request), np.asarray((1.0e8, 0.0, 0.0))

    def fake_contact(
        satellite,
        earth_to_sun,
        *,
        occultation_policy,
        search_policy,
    ):
        instant = illumination_module._utc_datetime(
            fake_source.request.instant,
            name="instant",
        )
        return _analytic_shadow_sample(instant, start).contact

    monkeypatch.setattr(
        illumination_module,
        "Sgp4TemePropagator",
        FakePropagator,
    )
    monkeypatch.setattr(
        illumination_module,
        "SatelliteGeocentricItrsTransformer",
        FakeTransformer,
    )
    monkeypatch.setattr(
        illumination_module,
        "_sun_state_and_itrs",
        fake_sun_state,
    )
    monkeypatch.setattr(
        illumination_module,
        "evaluate_solar_occultation_contact",
        fake_contact,
    )
    fake_source = SyntheticSunSource()
    query = SatelliteShadowTransitionQuery(
        snapshot=snapshot,
        norad_catalog_id=5,
        interval=InclusiveTimeInterval(
            "2026-09-21T00:00:00Z",
            "2026-09-21T00:00:10Z",
        ),
        search_policy=ShadowTransitionSearchPolicy(
            time_tolerance_seconds=0.01,
            maximum_interval_seconds=20.0,
        ),
    )

    results = SatelliteShadowTransitionFinder(fake_source).find(query)

    assert tuple(item.kind for item in results) == (
        ShadowTransitionKind.SUNLIT_TO_PENUMBRA,
        ShadowTransitionKind.PENUMBRA_TO_SUNLIT,
    )
    assert all(item.record is snapshot.records[0] for item in results)
    assert all(
        item.snapshot_sha256 == snapshot.manifest.content_sha256
        for item in results
    )
    assert all(item.query_interval == query.interval for item in results)
    assert all(item.identity == item.identity for item in results)
    assert all(item.evaluation_count == results[0].evaluation_count for item in results)
    assert all(item.achieved_bracket_width_seconds <= 0.01 for item in results)
    assert all("not a brightness" in item.warnings[0] for item in results)
