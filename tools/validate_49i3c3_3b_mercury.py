"""Validate descriptor-driven frozen-Earth Mercury state against Skyfield."""

from datetime import timezone
from math import asin, atan2, cos, degrees, hypot, radians, sin
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import BarycentricMeanEcliptic, CartesianRepresentation, SkyCoord
from astropy.time import Time

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.sky.frozen_earth_disk_sequences import (
    FrozenEarthDiskSequenceRealizer,
    FrozenEarthDiskSequenceRequest,
)
from wenu.sky.mercury import MERCURY_BODY, MERCURY_MEAN_RADIUS_KM
from wenu.solar_system_appearance import AU_KM


START = "2026-08-30T00:00:00Z"
STEP_DAYS = 2.0
N_STEPS = 60
TOLERANCES = {
    "earth_vector": 1.0e-11,
    "target_vector": 1.0e-11,
    "lon": 1.0e-9,
    "lat": 1.0e-9,
    "distance": 1.0e-11,
    "diameter": 1.0e-8,
    "phase": 1.0e-9,
    "fraction": 1.0e-11,
    "position_angle": 1.0e-8,
}


def _ecliptic_lon_lat(vector):
    coordinate = SkyCoord(
        CartesianRepresentation(*(vector * u.au)), frame="icrs"
    ).transform_to(BarycentricMeanEcliptic(equinox=Time("J2000.0")))
    return float(coordinate.lon.deg), float(coordinate.lat.deg)


def _angle(left, right):
    return degrees(atan2(
        float(np.linalg.norm(np.cross(left, right))),
        float(np.dot(left, right)),
    ))


def _position_angle(target_lon, target_lat, sun_lon, sun_lat):
    target_lon, target_lat = radians(target_lon), radians(target_lat)
    sun_lon, sun_lat = radians(sun_lon), radians(sun_lat)
    delta = sun_lon - target_lon
    numerator = cos(sun_lat) * sin(delta)
    denominator = (
        sin(sun_lat) * cos(target_lat)
        - cos(sun_lat) * sin(target_lat) * cos(delta)
    )
    if hypot(numerator, denominator) <= 1.0e-15:
        raise ValueError("bright-limb direction is undefined at exact alignment")
    return degrees(atan2(numerator, denominator)) % 360.0


def _wrapped(actual, reference):
    return (actual - reference + 180.0) % 360.0 - 180.0


def main():
    path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not path.is_file():
        raise SystemExit(
            f"Installed DE440 kernel required; refusing download because {path} "
            "does not exist."
        )
    request = FrozenEarthDiskSequenceRequest(
        descriptor=MERCURY_BODY,
        start_instant=START,
        start_time_scale="utc",
        step_days=STEP_DAYS,
        n_steps=N_STEPS,
        display_name=MERCURY_BODY.display_name,
        physical_radius_km=MERCURY_BODY.physical_radius_km,
        radius_model=MERCURY_BODY.radius_model,
    )
    with Observer(
        location="La Ligua",
        time=START,
        ephemeris_name=DEFAULT_EPHEMERIS,
        data_directory=DEFAULT_DATA_DIRECTORY,
    ) as observer:
        result = FrozenEarthDiskSequenceRealizer().sequence(request, observer=observer)
        earth = observer.ephemeris["earth"]
        sun = observer.ephemeris["sun"]
        mercury = observer.ephemeris["mercury"]
        start = Time(result.sample_instants[0], scale="utc")
        start_sf = observer.timescale.from_datetime(
            start.utc.to_datetime(timezone=timezone.utc)
        )
        frozen_earth = earth.at(start_sf).position.au - sun.at(start_sf).position.au
        sun_lon, sun_lat = _ecliptic_lon_lat(-frozen_earth)
        maxima = {name: 0.0 for name in TOLERANCES}
        phases, earth_distances, solar_distances = [], [], []

        resource = result.frozen_earth_state.resource
        target_ids = sorted({disk.direction.provider_target_id for disk in result.disks})
        centre_ids = sorted({disk.direction.provider_centre_id for disk in result.disks})
        print(f"model: {resource.model}")
        print(f"file: {resource.filename}")
        print(f"sha256: {resource.sha256}")
        print(
            f"coverage: {resource.coverage_start} through {resource.coverage_end} "
            f"{resource.coverage_time_scale}"
        )
        print(
            f"physical body: {MERCURY_BODY.display_name}, NAIF "
            f"{MERCURY_BODY.physical_body_id}"
        )
        print(
            "provider IDs: frozen Earth target/centre "
            f"{result.frozen_earth_state.provider_target_id}/"
            f"{result.frozen_earth_state.provider_centre_id}; "
            f"Mercury target/centre {target_ids}/{centre_ids}"
        )
        assert set(target_ids) <= {"1", "199"}
        print(f"radius: {MERCURY_BODY.physical_radius_km} km ({MERCURY_BODY.radius_model})")
        print(f"frozen Earth heliocentric ICRF AU: {tuple(frozen_earth)}")
        print(f"start/step/n_steps: {result.sample_instants[0]} / {STEP_DAYS} / {N_STEPS}")
        print(f"fixed Sun ecliptic lon/lat deg: {sun_lon:.12f}, {sun_lat:.12f}")
        print("sample states:")

        for index, disk in enumerate(result.disks):
            sample = Time(disk.direction.instant, scale="utc")
            sf_time = observer.timescale.from_datetime(
                sample.utc.to_datetime(timezone=timezone.utc)
            )
            planet = mercury.at(sf_time).position.au - sun.at(sf_time).position.au
            vector = planet - frozen_earth
            distance = float(np.linalg.norm(vector))
            solar_distance = float(np.linalg.norm(planet))
            lon, lat = _ecliptic_lon_lat(vector)
            phase = _angle(vector, planet)
            fraction = 0.5 * (1.0 + cos(radians(phase)))
            diameter = 2.0 * degrees(asin(
                (MERCURY_MEAN_RADIUS_KM / AU_KM) / distance
            )) * 3600.0
            position_angle = _position_angle(lon, lat, sun_lon, sun_lat)
            residuals = {
                "earth_vector": float(np.max(np.abs(
                    np.asarray(disk.direction.frozen_earth_heliocentric_icrf_au)
                    - frozen_earth
                ))),
                "target_vector": float(np.max(np.abs(
                    np.asarray(disk.direction.vector_icrf_au) - vector
                ))),
                "lon": _wrapped(float(disk.direction.geometry.lon_deg[0]), lon),
                "lat": float(disk.direction.geometry.lat_deg[0]) - lat,
                "distance": disk.direction.distance_au - distance,
                "diameter": disk.angular_diameter_arcsec - diameter,
                "phase": disk.phase_angle_deg - phase,
                "fraction": disk.illuminated_fraction - fraction,
                "position_angle": _wrapped(
                    disk.bright_limb_position_angle_deg, position_angle
                ),
            }
            for name, value in residuals.items():
                maxima[name] = max(maxima[name], abs(value))
            phases.append(phase)
            earth_distances.append(distance)
            solar_distances.append(solar_distance)
            print(
                f"  {index}: {disk.direction.instant} UTC, Mercury ICRF AU "
                f"{tuple(planet)}, relative AU {tuple(vector)}, lon/lat "
                f"{lon:.9f}/{lat:.9f} deg, distances Earth {distance:.12f}/"
                f"Sun {solar_distance:.12f} AU, diameter {diameter:.9f} arcsec, "
                f"phase {phase:.9f} deg, fraction {fraction:.9f}, "
                f"limb PA {position_angle:.9f} deg"
            )

        peak = int(np.argmax(phases))
        print(f"thin-phase peak sample: {peak}, phase {phases[peak]:.9f} deg")
        print(
            f"distance spans AU: frozen Earth-Mercury {min(earth_distances):.12f}.."
            f"{max(earth_distances):.12f}; Sun-Mercury {min(solar_distances):.12f}.."
            f"{max(solar_distances):.12f}"
        )
        print("maximum direct-Skyfield residuals:")
        for name, value in maxima.items():
            print(f"  {name}: {value:.3e} (tolerance {TOLERANCES[name]:.3e})")
        assert 0 < peak < len(phases) - 1
        assert phases[peak] >= 150.0
        assert max(earth_distances) - min(earth_distances) >= 0.1
        assert max(solar_distances) - min(solar_distances) >= 0.05
        for name, tolerance in TOLERANCES.items():
            assert maxima[name] <= tolerance


if __name__ == "__main__":
    main()
