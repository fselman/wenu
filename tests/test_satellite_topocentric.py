"""Satellite Earth-orientation and topocentric-state tests."""

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import (
    AltAz,
    CartesianDifferential,
    CartesianRepresentation,
    EarthLocation,
    ITRS,
    TEME,
)
from astropy.time import Time
from astropy.utils import iers
from skyfield.api import EarthSatellite, load, wgs84

from wenu.coordinates import PositionStatus
from wenu.satellite_crossings import SatelliteObserver
from wenu.satellites import (
    SatelliteEarthOrientationError,
    SatelliteTopocentricState,
    SatelliteTopocentricTransformer,
    Sgp4TemePropagator,
)
from wenu.satellites.elements import SatelliteElementRecord


SKYFIELD_ANGLE_TOLERANCE_DEG = 0.002
SKYFIELD_RANGE_TOLERANCE_KM = 0.05


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


def observer(longitude=-71.230289, latitude=-32.443342, elevation=52.0):
    return SatelliteObserver(
        "test-site",
        longitude,
        latitude,
        elevation,
        refraction_policy="vacuum",
        earth_orientation_policy="iers-a-bundled",
    )


def transformed(site=None):
    state = Sgp4TemePropagator(vanguard_record()).propagate(
        "2000-06-27T18:50:19.733568Z"
    )
    return SatelliteTopocentricTransformer().transform(
        state, site or observer()
    )


def test_topocentric_state_is_immutable_and_preserves_source_identity():
    result = transformed()

    assert isinstance(result, SatelliteTopocentricState)
    assert result.teme_state.norad_catalog_id == 5
    assert result.observer.observer_id == "test-site"
    with pytest.raises(FrozenInstanceError):
        result.range_km = 1.0


def test_observer_subtraction_and_range_are_direct_cartesian_evidence():
    result = transformed()
    satellite = np.asarray(result.satellite_itrs_position_km)
    observer_position = np.asarray(result.observer_itrs_position_km)
    topocentric = np.asarray(result.topocentric_itrs_position_km)

    assert topocentric == pytest.approx(
        satellite - observer_position, abs=1e-9
    )
    assert result.range_km == pytest.approx(
        np.linalg.norm(topocentric), abs=1e-9
    )
    assert result.topocentric_itrs_velocity_km_per_s == pytest.approx(
        result.satellite_itrs_velocity_km_per_s, abs=1e-12
    )


def test_separately_expressed_astropy_chain_matches_wenu_result():
    state = Sgp4TemePropagator(vanguard_record()).propagate(
        "2000-06-27T18:50:19.733568Z"
    )
    site = observer()
    result = SatelliteTopocentricTransformer().transform(state, site)
    time = Time(state.evaluation_utc, scale="utc")
    location = EarthLocation.from_geodetic(
        site.longitude_deg * u.deg,
        site.latitude_deg * u.deg,
        site.elevation_m * u.m,
        ellipsoid="WGS84",
    )
    position = CartesianRepresentation(np.asarray(state.position_km) * u.km)
    velocity = CartesianDifferential(
        np.asarray(state.velocity_km_per_s) * u.km / u.s
    )
    table = iers.IERS_A.open(result.earth_orientation.source_path)

    with iers.conf.set_temp("auto_download", False):
        with iers.conf.set_temp("iers_degraded_accuracy", "error"):
            with iers.earth_orientation_table.set(table):
                geocentric = TEME(
                    position.with_differentials(velocity),
                    obstime=time,
                ).transform_to(ITRS(obstime=time))
                topocentric = (
                    geocentric.cartesian.without_differentials()
                    - location.get_itrs(time).cartesian
                )
                horizontal = ITRS(
                    topocentric,
                    obstime=time,
                    location=location,
                ).transform_to(
                    AltAz(
                        obstime=time,
                        location=location,
                        pressure=0.0 * u.hPa,
                    )
                )

    assert horizontal.az.to_value(u.deg) == pytest.approx(
        result.azimuth_deg, abs=1e-12
    )
    assert horizontal.alt.to_value(u.deg) == pytest.approx(
        result.altitude_deg, abs=1e-12
    )
    assert horizontal.distance.to_value(u.km) == pytest.approx(
        result.range_km, abs=1e-9
    )


def test_skyfield_independent_high_level_direction_and_range_agree():
    line1 = (
        "1 00005U 58002B   00179.78495062  .00000023  "
        "00000-0  28098-4 0  4753"
    )
    line2 = (
        "2 00005  34.2682 348.7242 1859667 331.7664  "
        "19.3264 10.82419157413667"
    )
    timescale = load.timescale(builtin=True)
    satellite = EarthSatellite(line1, line2, "VANGUARD 1", timescale)
    site = observer()
    skyfield_site = wgs84.latlon(
        site.latitude_deg,
        site.longitude_deg,
        elevation_m=site.elevation_m,
    )
    time = timescale.utc(2000, 6, 27, 18, 50, 19.733568)
    altitude, azimuth, distance = (
        satellite - skyfield_site
    ).at(time).altaz()
    result = transformed(site)

    assert result.altitude_deg == pytest.approx(
        altitude.degrees, abs=SKYFIELD_ANGLE_TOLERANCE_DEG
    )
    delta_azimuth = (
        (result.azimuth_deg - azimuth.degrees + 180.0) % 360.0 - 180.0
    )
    assert delta_azimuth == pytest.approx(
        0.0, abs=SKYFIELD_ANGLE_TOLERANCE_DEG
    )
    assert result.range_km == pytest.approx(
        distance.km, abs=SKYFIELD_RANGE_TOLERANCE_KM
    )


@pytest.mark.parametrize(
    ("longitude", "latitude"),
    [
        (0.0, 0.0),
        (-71.230289, -32.443342),
        (45.0, 89.999),
        (179.999, 0.0),
        (-179.999, 0.0),
    ],
)
def test_pathological_site_geometry_remains_finite(longitude, latitude):
    result = transformed(observer(longitude, latitude, 0.0))

    values = (
        *result.topocentric_itrs_position_km,
        result.range_km,
        result.azimuth_deg,
        result.altitude_deg,
        result.gcrs_axis_longitude_deg,
        result.gcrs_axis_latitude_deg,
    )
    assert all(np.isfinite(values))
    assert result.range_km > 0.0
    assert 0.0 <= result.azimuth_deg < 360.0
    assert -90.0 <= result.altitude_deg <= 90.0


def test_coordinate_identity_is_geometric_vacuum_and_not_apparent_icrs():
    result = transformed()
    horizontal = result.horizontal_coordinate_spec
    celestial = result.celestial_axis_coordinate_spec

    assert horizontal.frame == "altaz"
    assert horizontal.origin == "observer"
    assert horizontal.position_status is PositionStatus.GEOMETRIC
    assert "refraction" not in horizontal.corrections
    assert celestial.frame == "gcrs-axes"
    assert celestial.origin == "topocentric-direction"
    assert celestial.position_status is PositionStatus.GEOMETRIC
    assert "apparent" not in celestial.model.lower()
    assert any("not an ICRS/GCRS" in item for item in result.warnings)


def test_gcrs_axis_rotation_preserves_topocentric_vector_norm():
    result = transformed()
    assert result.range_km == pytest.approx(
        np.linalg.norm(result.topocentric_itrs_position_km), abs=1e-9
    )


def test_earth_orientation_evidence_identifies_exact_local_resource():
    result = transformed()
    evidence = result.earth_orientation
    source = Path(evidence.source_path)

    assert source.is_file()
    assert sha256(source.read_bytes()).hexdigest() == evidence.source_sha256
    assert len(evidence.source_sha256) == 64
    assert evidence.coverage_start_mjd <= 51722.0
    assert evidence.coverage_stop_mjd >= 51722.0
    assert evidence.astropy_version
    assert evidence.astropy_iers_data_version
    assert np.isfinite(evidence.ut1_minus_utc_s)
    assert np.isfinite(evidence.polar_motion_x_arcsec)
    assert np.isfinite(evidence.polar_motion_y_arcsec)
    assert evidence.ut1_status >= 0
    assert evidence.polar_motion_status >= 0


def test_out_of_coverage_instant_fails_closed():
    state = Sgp4TemePropagator(vanguard_record()).propagate(
        "2000-06-27T18:50:19.733568Z"
    )
    outside = replace(
        state,
        evaluation_utc="1960-01-01T00:00:00.000000Z",
        julian_day=2436934.5,
        julian_fraction=0.0,
    )

    with pytest.raises(
        SatelliteEarthOrientationError, match="outside installed IERS-A"
    ):
        SatelliteTopocentricTransformer().transform(outside, observer())


def test_policy_rejects_refraction_and_unknown_earth_orientation():
    state = Sgp4TemePropagator(vanguard_record()).propagate(
        "2000-06-27T18:50:19.733568Z"
    )
    refracted = SatelliteObserver(
        "bad", 0.0, 0.0, 0.0, refraction_policy="standard"
    )
    unknown = SatelliteObserver(
        "bad",
        0.0,
        0.0,
        0.0,
        earth_orientation_policy="greenwich-shortcut",
    )

    with pytest.raises(ValueError, match="vacuum"):
        SatelliteTopocentricTransformer().transform(state, refracted)
    with pytest.raises(ValueError, match="Earth-orientation policy"):
        SatelliteTopocentricTransformer().transform(state, unknown)
