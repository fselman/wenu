"""Direct-Sun occultation and observer-night geometry tests."""

from dataclasses import FrozenInstanceError, replace
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
from wenu.satellite_crossings import SatelliteObserver
from wenu.satellites import (
    LunarOccultorStatus,
    ObserverTwilightClass,
    SatelliteIlluminationFailureCode,
    SatelliteIlluminationGeometryError,
    SatelliteIlluminationGeometryEvaluator,
    SolarOccultationClass,
    SolarOccultationPolicy,
    Sgp4TemePropagator,
    classify_observer_twilight,
    evaluate_solar_occultation,
)
from wenu.satellites.elements import SatelliteElementRecord
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
