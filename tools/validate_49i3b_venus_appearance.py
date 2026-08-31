"""Validate the 49I.3B Venus physical appearance against Skyfield."""

from __future__ import annotations

from math import asin, atan2, cos, degrees, radians, sin
from pathlib import Path

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.sky.venus import VENUS_POINT
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
    skyfield_observer_barycentric_state,
)
from wenu.solar_system_appearance import (
    AU_KM,
    SolarSystemAppearanceRealizer,
    VENUS_MEAN_RADIUS_KM,
)
from wenu.solar_system_directions import (
    ApparentCorrectionPolicy,
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)

INSTANT = "2026-08-30T00:00:00Z"
ANGULAR_DIAMETER_TOLERANCE_ARCSEC = 1.0e-8
PHASE_ANGLE_TOLERANCE_DEG = 1.0e-9
ILLUMINATED_FRACTION_TOLERANCE = 1.0e-11
POSITION_ANGLE_TOLERANCE_DEG = 1.0e-9


def _direction(observer, source, observer_state, *, target, policy):
    request = AstrometricDirectionRequest(
        target=target,
        centre="solar system barycenter",
        reception_instant=observer.t_astropy.isot,
        reception_time_scale=observer.t_astropy.scale,
    )
    astrometric = AstrometricDirectionRealizer().direction(
        source,
        request,
        observer_state,
    )
    return SkyfieldApparentDirectionRealizer().direction(
        astrometric,
        observer=observer,
        source=source,
        policy=policy,
    )


def _bright_limb_position_angle(target, sun):
    target_ra, target_dec, _ = target.radec()
    sun_ra, sun_dec, _ = sun.radec()
    ra = radians(float(target_ra.hours) * 15.0)
    dec = radians(float(target_dec.degrees))
    sun_ra_rad = radians(float(sun_ra.hours) * 15.0)
    sun_dec_rad = radians(float(sun_dec.degrees))

    target_vector = (
        cos(dec) * cos(ra),
        cos(dec) * sin(ra),
        sin(dec),
    )
    sun_vector = (
        cos(sun_dec_rad) * cos(sun_ra_rad),
        cos(sun_dec_rad) * sin(sun_ra_rad),
        sin(sun_dec_rad),
    )
    north = (-sin(dec) * cos(ra), -sin(dec) * sin(ra), cos(dec))
    east = (-sin(ra), cos(ra), 0.0)
    dot = sum(a * b for a, b in zip(sun_vector, target_vector))
    tangent = tuple(
        sun_component - dot * target_component
        for sun_component, target_component in zip(
            sun_vector,
            target_vector,
        )
    )
    north_component = sum(a * b for a, b in zip(tangent, north))
    east_component = sum(a * b for a, b in zip(tangent, east))
    return degrees(atan2(east_component, north_component)) % 360.0


def _wrapped_angle_residual(actual, reference):
    return (actual - reference + 180.0) % 360.0 - 180.0


def main():
    path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not path.is_file():
        raise SystemExit(
            f"Installed kernel required; refusing download because {path} "
            "does not exist."
        )

    with Observer(
        location="La Ligua",
        time=INSTANT,
        ephemeris_name=DEFAULT_EPHEMERIS,
        data_directory=DEFAULT_DATA_DIRECTORY,
    ) as observer:
        source = SkyfieldEphemerisStateSource.from_observer(observer)
        observer_state = skyfield_observer_barycentric_state(
            observer,
            source=source,
        )
        venus_direction = _direction(
            observer,
            source,
            observer_state,
            target=VENUS_POINT.target,
            policy=VENUS_POINT.correction_policy,
        )
        sun_direction = _direction(
            observer,
            source,
            observer_state,
            target="sun",
            policy=ApparentCorrectionPolicy(),
        )
        result = SolarSystemAppearanceRealizer().appearance(
            source,
            venus_direction,
            sun_direction,
            display_name=VENUS_POINT.display_name,
            physical_radius_km=VENUS_MEAN_RADIUS_KM,
            radius_model=(
                "JPL Planetary Physical Parameters mean radius 6051.8 km"
            ),
        )

        sun = observer.ephemeris["sun"]
        venus = observer.ephemeris["venus"]
        direct_astrometric = observer.skyfield.at(observer.t).observe(venus)
        direct_venus = direct_astrometric.apparent()
        direct_sun = observer.skyfield.at(observer.t).observe(sun).apparent()
        direct_phase_deg = float(
            direct_astrometric.phase_angle(sun).degrees
        )
        direct_fraction = float(
            direct_astrometric.fraction_illuminated(sun)
        )
        direct_distance_au = float(direct_astrometric.distance().au)
        direct_diameter_arcsec = (
            2.0
            * degrees(
                asin(
                    (VENUS_MEAN_RADIUS_KM / AU_KM)
                    / direct_distance_au
                )
            )
            * 3600.0
        )
        direct_position_angle_deg = _bright_limb_position_angle(
            direct_venus,
            direct_sun,
        )

        diameter_residual = (
            result.angular_diameter_arcsec - direct_diameter_arcsec
        )
        phase_residual = result.phase_angle_deg - direct_phase_deg
        fraction_residual = (
            result.illuminated_fraction - direct_fraction
        )
        position_angle_residual = _wrapped_angle_residual(
            result.bright_limb_position_angle_deg,
            direct_position_angle_deg,
        )

        print(f"model: {source.resource.model}")
        print(f"file: {source.resource.filename}")
        print(f"sha256: {source.resource.sha256}")
        print(f"observer: {observer.location_name}")
        print(f"reception: {observer.t_astropy.isot} {observer.t_astropy.scale.upper()}")
        print(f"target NAIF ID: {venus_direction.astrometric.target_provider_id}")
        print(f"Sun NAIF ID: {sun_direction.astrometric.target_provider_id}")
        print(f"Venus mean radius km: {result.physical_radius_km:.1f}")
        print(f"observer-target distance AU: {venus_direction.astrometric.distance_au:.16g}")
        print(f"angular diameter arcsec: {result.angular_diameter_arcsec:.12f}")
        print(f"phase angle deg: {result.phase_angle_deg:.12f}")
        print(f"illuminated fraction: {result.illuminated_fraction:.12f}")
        print(
            "bright-limb position angle deg: "
            f"{result.bright_limb_position_angle_deg:.12f}"
        )
        print(f"angular-diameter residual arcsec: {diameter_residual:.3e}")
        print(f"phase-angle residual deg: {phase_residual:.3e}")
        print(f"illuminated-fraction residual: {fraction_residual:.3e}")
        print(
            "bright-limb position-angle residual deg: "
            f"{position_angle_residual:.3e}"
        )
        print(f"position-angle convention: {result.position_angle_convention}")

        assert venus_direction.astrometric.target_provider_id == "299"
        assert sun_direction.astrometric.target_provider_id == "10"
        assert (
            abs(diameter_residual)
            <= ANGULAR_DIAMETER_TOLERANCE_ARCSEC
        )
        assert abs(phase_residual) <= PHASE_ANGLE_TOLERANCE_DEG
        assert (
            abs(fraction_residual)
            <= ILLUMINATED_FRACTION_TOLERANCE
        )
        assert (
            abs(position_angle_residual)
            <= POSITION_ANGLE_TOLERANCE_DEG
        )


if __name__ == "__main__":
    main()
