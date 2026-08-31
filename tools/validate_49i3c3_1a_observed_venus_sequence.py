"""Validate observed Venus disk sequences against direct Skyfield."""

from __future__ import annotations

from datetime import timezone
from math import asin, atan2, cos, degrees, radians, sin
from pathlib import Path

from astropy.time import Time

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.sky.solar_system_disk_sequences import (
    ObservedSolarSystemDiskSequenceRealizer,
    ObservedSolarSystemDiskSequenceRequest,
)
from wenu.sky.venus import VENUS_POINT
from wenu.solar_system_appearance import AU_KM, VENUS_MEAN_RADIUS_KM
from wenu.sky.venus_disk import VENUS_RADIUS_MODEL


START = "2026-08-30T00:00:00Z"
STEP_DAYS = 28.0
N_STEPS = 3
DIRECTION_TOLERANCE_DEG = 1.0e-9
DISTANCE_TOLERANCE_AU = 1.0e-12
ANGULAR_DIAMETER_TOLERANCE_ARCSEC = 1.0e-8
PHASE_ANGLE_TOLERANCE_DEG = 1.0e-9
ILLUMINATED_FRACTION_TOLERANCE = 1.0e-11
POSITION_ANGLE_TOLERANCE_DEG = 1.0e-9


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

    sequence_request = ObservedSolarSystemDiskSequenceRequest(
        descriptor=VENUS_POINT,
        start_instant=START,
        start_time_scale="utc",
        step_days=STEP_DAYS,
        n_steps=N_STEPS,
        display_name=VENUS_POINT.display_name,
        physical_radius_km=VENUS_MEAN_RADIUS_KM,
        radius_model=VENUS_RADIUS_MODEL,
    )
    with Observer(
        location="La Ligua",
        time=START,
        ephemeris_name=DEFAULT_EPHEMERIS,
        data_directory=DEFAULT_DATA_DIRECTORY,
    ) as observer:
        result = ObservedSolarSystemDiskSequenceRealizer().sequence(
            sequence_request,
            observer=observer,
        )
        sun = observer.ephemeris["sun"]
        venus = observer.ephemeris["venus"]
        maxima = {
            "ra": 0.0,
            "dec": 0.0,
            "distance": 0.0,
            "diameter": 0.0,
            "phase": 0.0,
            "fraction": 0.0,
            "position_angle": 0.0,
        }

        print(f"model: {result.appearances[0].apparent_direction.astrometric.observer_state.resource.model}")
        print(f"file: {result.appearances[0].apparent_direction.astrometric.observer_state.resource.filename}")
        print(f"sha256: {result.appearances[0].apparent_direction.astrometric.observer_state.resource.sha256}")
        print(f"observer: {observer.location_name}")
        print(f"start: {result.sample_instants[0]} {result.sample_time_scale.upper()}")
        print(f"step days: {sequence_request.step_days}")
        print(f"n steps: {sequence_request.n_steps}")
        print(f"samples: {len(result.sample_instants)}")
        print("sample states:")

        for index, (instant, appearance, distance) in enumerate(zip(
            result.sample_instants,
            result.appearances,
            result.distances,
        )):
            sample = Time(instant, scale=result.sample_time_scale)
            sample_datetime = sample.utc.to_datetime(timezone=timezone.utc)
            skyfield_time = observer.timescale.from_datetime(sample_datetime)
            direct_astrometric = observer.skyfield.at(
                skyfield_time
            ).observe(venus)
            direct_venus = direct_astrometric.apparent()
            direct_sun = observer.skyfield.at(
                skyfield_time
            ).observe(sun).apparent()
            direct_ra, direct_dec, _ = direct_venus.radec()
            direct_ra_deg = float(direct_ra.hours) * 15.0
            direct_dec_deg = float(direct_dec.degrees)
            direct_distance = float(direct_astrometric.distance().au)
            direct_diameter = (
                2.0
                * degrees(
                    asin(
                        (VENUS_MEAN_RADIUS_KM / AU_KM)
                        / direct_distance
                    )
                )
                * 3600.0
            )
            direct_phase = float(
                direct_astrometric.phase_angle(sun).degrees
            )
            direct_fraction = float(
                direct_astrometric.fraction_illuminated(sun)
            )
            direct_position_angle = _bright_limb_position_angle(
                direct_venus,
                direct_sun,
            )
            actual_ra = float(
                appearance.apparent_direction.geometry.lon_deg[0]
            )
            actual_dec = float(
                appearance.apparent_direction.geometry.lat_deg[0]
            )
            residuals = {
                "ra": _wrapped_angle_residual(actual_ra, direct_ra_deg),
                "dec": actual_dec - direct_dec_deg,
                "distance": distance - direct_distance,
                "diameter": (
                    appearance.angular_diameter_arcsec - direct_diameter
                ),
                "phase": appearance.phase_angle_deg - direct_phase,
                "fraction": (
                    appearance.illuminated_fraction - direct_fraction
                ),
                "position_angle": _wrapped_angle_residual(
                    appearance.bright_limb_position_angle_deg,
                    direct_position_angle,
                ),
            }
            for name, value in residuals.items():
                maxima[name] = max(maxima[name], abs(value))
            print(
                f"  {index}: {instant} UTC, "
                f"distance {distance:.12f} AU, "
                f"diameter {appearance.angular_diameter_arcsec:.9f} arcsec, "
                f"phase {appearance.phase_angle_deg:.9f} deg, "
                f"fraction {appearance.illuminated_fraction:.9f}, "
                f"limb PA {appearance.bright_limb_position_angle_deg:.9f} deg"
            )

        print("maximum direct-Skyfield residuals:")
        print(f"  RA deg: {maxima['ra']:.3e}")
        print(f"  Dec deg: {maxima['dec']:.3e}")
        print(f"  distance AU: {maxima['distance']:.3e}")
        print(f"  angular diameter arcsec: {maxima['diameter']:.3e}")
        print(f"  phase angle deg: {maxima['phase']:.3e}")
        print(f"  illuminated fraction: {maxima['fraction']:.3e}")
        print(
            "  bright-limb position angle deg: "
            f"{maxima['position_angle']:.3e}"
        )
        print(f"distance origin/unit: {result.distance_origin}/{result.distance_unit}")

        assert maxima["ra"] <= DIRECTION_TOLERANCE_DEG
        assert maxima["dec"] <= DIRECTION_TOLERANCE_DEG
        assert maxima["distance"] <= DISTANCE_TOLERANCE_AU
        assert (
            maxima["diameter"]
            <= ANGULAR_DIAMETER_TOLERANCE_ARCSEC
        )
        assert maxima["phase"] <= PHASE_ANGLE_TOLERANCE_DEG
        assert (
            maxima["fraction"]
            <= ILLUMINATED_FRACTION_TOLERANCE
        )
        assert (
            maxima["position_angle"]
            <= POSITION_ANGLE_TOLERANCE_DEG
        )


if __name__ == "__main__":
    main()
