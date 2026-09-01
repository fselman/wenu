"""Validate a frozen-Earth Venus sequence against direct Skyfield vectors."""

from __future__ import annotations

from datetime import timezone
from math import asin, atan2, cos, degrees, hypot, radians, sin
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import (
    BarycentricMeanEcliptic,
    CartesianRepresentation,
    SkyCoord,
)
from astropy.time import Time

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.sky.frozen_earth_disk_sequences import (
    FrozenEarthDiskSequenceRealizer,
    FrozenEarthDiskSequenceRequest,
)
from wenu.sky.venus import VENUS_POINT
from wenu.sky.venus_disk import VENUS_RADIUS_MODEL
from wenu.solar_system_appearance import AU_KM, VENUS_MEAN_RADIUS_KM


START = "2026-08-30T00:00:00Z"
STEP_DAYS = 28.0
N_STEPS = 3
VECTOR_TOLERANCE_AU = 1.0e-11
DIRECTION_TOLERANCE_DEG = 1.0e-9
DISTANCE_TOLERANCE_AU = 1.0e-11
ANGULAR_DIAMETER_TOLERANCE_ARCSEC = 1.0e-8
PHASE_ANGLE_TOLERANCE_DEG = 1.0e-9
ILLUMINATED_FRACTION_TOLERANCE = 1.0e-11
POSITION_ANGLE_TOLERANCE_DEG = 1.0e-8


def _ecliptic_lon_lat(vector):
    cartesian = CartesianRepresentation(*(vector * u.au))
    coordinate = SkyCoord(
        cartesian,
        frame="icrs",
    ).transform_to(BarycentricMeanEcliptic(equinox=Time("J2000.0")))
    return float(coordinate.lon.deg), float(coordinate.lat.deg)


def _angle(left, right):
    return degrees(
        atan2(
            float(np.linalg.norm(np.cross(left, right))),
            float(np.dot(left, right)),
        )
    )


def _position_angle(target_lon, target_lat, sun_lon, sun_lat):
    target_lon = radians(target_lon)
    target_lat = radians(target_lat)
    sun_lon = radians(sun_lon)
    sun_lat = radians(sun_lat)
    delta = sun_lon - target_lon
    numerator = cos(sun_lat) * sin(delta)
    denominator = (
        sin(sun_lat) * cos(target_lat)
        - cos(sun_lat) * sin(target_lat) * cos(delta)
    )
    if hypot(numerator, denominator) <= 1.0e-15:
        raise ValueError("bright-limb direction is undefined.")
    return degrees(atan2(numerator, denominator)) % 360.0


def _wrapped(actual, reference):
    return (actual - reference + 180.0) % 360.0 - 180.0


def main():
    path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not path.is_file():
        raise SystemExit(
            f"Installed kernel required; refusing download because {path} "
            "does not exist."
        )

    sequence_request = FrozenEarthDiskSequenceRequest(
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
        result = FrozenEarthDiskSequenceRealizer().sequence(
            sequence_request,
            observer=observer,
        )
        earth = observer.ephemeris["earth"]
        sun = observer.ephemeris["sun"]
        venus = observer.ephemeris["venus"]
        start_time = Time(result.sample_instants[0], scale="utc")
        start_datetime = start_time.utc.to_datetime(timezone=timezone.utc)
        skyfield_start = observer.timescale.from_datetime(start_datetime)
        frozen_earth = (
            earth.at(skyfield_start).position.au
            - sun.at(skyfield_start).position.au
        )
        direct_sun_vector = -frozen_earth
        direct_sun_lon, direct_sun_lat = _ecliptic_lon_lat(
            direct_sun_vector
        )
        maxima = {
            "earth_vector": 0.0,
            "target_vector": 0.0,
            "lon": 0.0,
            "lat": 0.0,
            "distance": 0.0,
            "diameter": 0.0,
            "phase": 0.0,
            "fraction": 0.0,
            "position_angle": 0.0,
        }

        print(f"model: {result.frozen_earth_state.resource.model}")
        print(f"file: {result.frozen_earth_state.resource.filename}")
        print(f"sha256: {result.frozen_earth_state.resource.sha256}")
        print(
            "observer construction: Earth heliocentric position "
            "frozen at start"
        )
        print(f"start: {result.sample_instants[0]} UTC")
        print(f"step days: {sequence_request.step_days}")
        print(f"n steps: {sequence_request.n_steps}")
        print(f"samples: {len(result.disks)}")
        print(
            "fixed Sun ecliptic lon/lat deg: "
            f"{direct_sun_lon:.12f}, {direct_sun_lat:.12f}"
        )
        print("sample states:")

        for index, disk in enumerate(result.disks):
            sample = Time(disk.direction.instant, scale="utc")
            sample_datetime = sample.utc.to_datetime(timezone=timezone.utc)
            skyfield_time = observer.timescale.from_datetime(sample_datetime)
            planet = (
                venus.at(skyfield_time).position.au
                - sun.at(skyfield_time).position.au
            )
            vector = planet - frozen_earth
            distance = float(np.linalg.norm(vector))
            lon, lat = _ecliptic_lon_lat(vector)
            phase = _angle(vector, planet)
            fraction = 0.5 * (1.0 + cos(radians(phase)))
            diameter = (
                2.0
                * degrees(
                    asin((VENUS_MEAN_RADIUS_KM / AU_KM) / distance)
                )
                * 3600.0
            )
            position_angle = _position_angle(
                lon,
                lat,
                direct_sun_lon,
                direct_sun_lat,
            )
            residuals = {
                "earth_vector": float(
                    np.max(
                        np.abs(
                            np.asarray(
                                disk.direction
                                .frozen_earth_heliocentric_icrf_au
                            )
                            - frozen_earth
                        )
                    )
                ),
                "target_vector": float(
                    np.max(
                        np.abs(
                            np.asarray(disk.direction.vector_icrf_au)
                            - vector
                        )
                    )
                ),
                "lon": _wrapped(
                    float(disk.direction.geometry.lon_deg[0]),
                    lon,
                ),
                "lat": float(disk.direction.geometry.lat_deg[0]) - lat,
                "distance": disk.direction.distance_au - distance,
                "diameter": disk.angular_diameter_arcsec - diameter,
                "phase": disk.phase_angle_deg - phase,
                "fraction": disk.illuminated_fraction - fraction,
                "position_angle": _wrapped(
                    disk.bright_limb_position_angle_deg,
                    position_angle,
                ),
            }
            for name, value in residuals.items():
                maxima[name] = max(maxima[name], abs(value))
            print(
                f"  {index}: {disk.direction.instant} UTC, "
                f"ecliptic lon {lon:.9f} deg, lat {lat:.9f} deg, "
                f"distance {distance:.12f} AU, "
                f"diameter {diameter:.9f} arcsec, "
                f"phase {phase:.9f} deg, fraction {fraction:.9f}, "
                f"limb PA {position_angle:.9f} deg"
            )

        print("maximum direct-Skyfield residuals:")
        for name, value in maxima.items():
            print(f"  {name}: {value:.3e}")
        print(
            "distance origin/unit: "
            f"{result.distance_origin}/{result.distance_unit}"
        )
        print(
            "direction semantics: frozen-observer geometric; "
            "fixed J2000 mean ecliptic axes; not apparent"
        )

        assert maxima["earth_vector"] <= VECTOR_TOLERANCE_AU
        assert maxima["target_vector"] <= VECTOR_TOLERANCE_AU
        assert maxima["lon"] <= DIRECTION_TOLERANCE_DEG
        assert maxima["lat"] <= DIRECTION_TOLERANCE_DEG
        assert maxima["distance"] <= DISTANCE_TOLERANCE_AU
        assert maxima["diameter"] <= ANGULAR_DIAMETER_TOLERANCE_ARCSEC
        assert maxima["phase"] <= PHASE_ANGLE_TOLERANCE_DEG
        assert maxima["fraction"] <= ILLUMINATED_FRACTION_TOLERANCE
        assert maxima["position_angle"] <= POSITION_ANGLE_TOLERANCE_DEG


if __name__ == "__main__":
    main()
