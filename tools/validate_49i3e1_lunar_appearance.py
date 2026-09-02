"""Validate 49I.3E.1 output-neutral lunar appearance against Skyfield."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import asin, atan2, cos, degrees, radians, sin
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from astropy.time import Time

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.sky.moon import MOON_BODY, MOON_MEAN_RADIUS_KM
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
    skyfield_observer_barycentric_state,
)
from wenu.solar_system_appearance import AU_KM, SolarSystemAppearanceRealizer
from wenu.solar_system_directions import (
    ApparentCorrectionPolicy,
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)


START = datetime(2026, 1, 1, tzinfo=timezone.utc)
CANDIDATE_STEP_DAYS = 3
CANDIDATE_COUNT = 122
RA_TOLERANCE_DEG = 2.0e-7
DEC_TOLERANCE_DEG = 2.0e-7
DISTANCE_TOLERANCE_AU = 5.0e-12
DIAMETER_TOLERANCE_ARCSEC = 5.0e-6
PHASE_TOLERANCE_DEG = 2.0e-7
FRACTION_TOLERANCE = 1.0e-9
POSITION_ANGLE_TOLERANCE_DEG = 5.0e-6


def _sample_observer(base, instant):
    astropy_time = Time(instant, scale="utc")
    return SimpleNamespace(
        ephemeris=base.ephemeris,
        timescale=base.timescale,
        earth=base.earth,
        location=base.location,
        skyfield=base.skyfield,
        t=base.timescale.from_astropy(astropy_time),
        t_astropy=astropy_time,
        lat_deg=base.lat_deg,
        lon_deg=base.lon_deg,
        elevation_m=base.elevation_m,
        location_name=base.location_name,
    )


def _direction(observer, source, observer_state, *, target, policy):
    request = AstrometricDirectionRequest(
        target=target,
        centre="solar system barycenter",
        reception_instant=observer.t_astropy.isot,
        reception_time_scale=observer.t_astropy.scale,
    )
    astrometric = AstrometricDirectionRealizer().direction(
        source, request, observer_state
    )
    return SkyfieldApparentDirectionRealizer().direction(
        astrometric,
        observer=observer,
        source=source,
        policy=policy,
    )


def _position_angle_from_radec(target_ra, target_dec, sun_ra, sun_dec):
    ra = radians(float(target_ra))
    dec = radians(float(target_dec))
    sun_ra = radians(float(sun_ra))
    sun_dec = radians(float(sun_dec))
    delta_ra = sun_ra - ra
    return degrees(atan2(
        cos(sun_dec) * sin(delta_ra),
        sin(sun_dec) * cos(dec)
        - cos(sun_dec) * sin(dec) * cos(delta_ra),
    )) % 360.0


def _direct_values(observer):
    moon = observer.ephemeris["moon"]
    sun = observer.ephemeris["sun"]
    astrometric = observer.skyfield.at(observer.t).observe(moon)
    apparent = astrometric.apparent()
    direct_sun = observer.skyfield.at(observer.t).observe(sun).apparent()
    ra, dec, _ = apparent.radec()
    sun_ra, sun_dec, _ = direct_sun.radec()
    distance = float(astrometric.distance().au)
    phase = float(astrometric.phase_angle(sun).degrees)
    fraction = float(astrometric.fraction_illuminated(sun))
    diameter = 2.0 * degrees(asin(
        (MOON_MEAN_RADIUS_KM / AU_KM) / distance
    )) * 3600.0
    position_angle = _position_angle_from_radec(
        float(ra.hours) * 15.0,
        float(dec.degrees),
        float(sun_ra.hours) * 15.0,
        float(sun_dec.degrees),
    )
    geocentric = observer.earth.at(observer.t).observe(moon).apparent()
    parallax = float(apparent.separation_from(geocentric).degrees)
    return {
        "ra": float(ra.hours) * 15.0,
        "dec": float(dec.degrees),
        "distance": distance,
        "diameter": diameter,
        "phase": phase,
        "fraction": fraction,
        "position_angle": position_angle,
        "parallax": parallax,
    }


def _wrapped_residual(actual, reference):
    return (actual - reference + 180.0) % 360.0 - 180.0


def _candidate_indices(base):
    instants = tuple(
        START + timedelta(days=CANDIDATE_STEP_DAYS * index)
        for index in range(CANDIDATE_COUNT)
    )
    times = base.timescale.from_datetimes(instants)
    moon = base.ephemeris["moon"]
    sun = base.ephemeris["sun"]
    astrometric = base.skyfield.at(times).observe(moon)
    apparent = astrometric.apparent()
    direct_sun = base.skyfield.at(times).observe(sun).apparent()
    phase = np.asarray(astrometric.phase_angle(sun).degrees, dtype=float)
    distance = np.asarray(astrometric.distance().au, dtype=float)
    ra, dec, _ = apparent.radec()
    sun_ra, sun_dec, _ = direct_sun.radec()
    angles = np.asarray(tuple(
        _position_angle_from_radec(a * 15.0, d, sa * 15.0, sd)
        for a, d, sa, sd in zip(
            np.asarray(ra.hours),
            np.asarray(dec.degrees),
            np.asarray(sun_ra.hours),
            np.asarray(sun_dec.degrees),
        )
    ))

    selected = {
        int(np.argmin(abs(phase - target)))
        for target in (0.0, 45.0, 90.0, 135.0, 180.0)
    }
    selected.update((int(np.argmin(distance)), int(np.argmax(distance))))
    for target in (0.0, 90.0, 180.0, 270.0):
        residual = abs((angles - target + 180.0) % 360.0 - 180.0)
        selected.add(int(np.argmin(residual)))

    assert float(np.min(phase)) < 10.0
    assert float(np.max(phase)) > 170.0
    assert float(np.max(distance) - np.min(distance)) > 2.0e-4
    return tuple((instants[index], phase[index], distance[index], angles[index])
                 for index in sorted(selected))


def main():
    path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not path.is_file():
        raise SystemExit(
            f"Installed kernel required; refusing download because {path} "
            "does not exist."
        )

    maxima = {
        "ra": 0.0,
        "dec": 0.0,
        "distance": 0.0,
        "diameter": 0.0,
        "phase": 0.0,
        "fraction": 0.0,
        "position_angle": 0.0,
    }
    minimum_parallax = float("inf")

    with Observer(
        location="La Ligua",
        time=START,
        ephemeris_name=DEFAULT_EPHEMERIS,
        data_directory=DEFAULT_DATA_DIRECTORY,
    ) as base:
        source = SkyfieldEphemerisStateSource.from_observer(base)
        cases = _candidate_indices(base)
        print(f"model: {source.resource.model}")
        print(f"file: {source.resource.filename}")
        print(f"sha256: {source.resource.sha256}")
        print(
            "coverage: "
            f"{source.resource.coverage_start} through "
            f"{source.resource.coverage_end} "
            f"{source.resource.coverage_time_scale.upper()}"
        )
        print(
            "observer: La Ligua; "
            f"lat {base.lat_deg:.9f} deg; lon {base.lon_deg:.9f} deg; "
            f"height {base.elevation_m:.3f} m"
        )
        print(f"Moon physical body ID: {MOON_BODY.physical_body_id}")
        print(f"Moon mean radius km: {MOON_BODY.physical_radius_km:.1f}")
        print(f"radius model: {MOON_BODY.radius_model}")
        print(f"selected cases: {len(cases)}")

        for instant, candidate_phase, candidate_distance, candidate_angle in cases:
            observer = _sample_observer(base, instant)
            observer_state = skyfield_observer_barycentric_state(
                observer, source=source
            )
            moon_direction = _direction(
                observer,
                source,
                observer_state,
                target=MOON_BODY.target,
                policy=MOON_BODY.correction_policy,
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
                moon_direction,
                sun_direction,
                display_name=MOON_BODY.display_name,
                physical_radius_km=MOON_BODY.physical_radius_km,
                radius_model=MOON_BODY.radius_model,
            )
            direct = _direct_values(observer)
            residuals = {
                "ra": _wrapped_residual(
                    float(moon_direction.geometry.lon_deg[0]), direct["ra"]
                ),
                "dec": float(moon_direction.geometry.lat_deg[0]) - direct["dec"],
                "distance": (
                    moon_direction.astrometric.distance_au - direct["distance"]
                ),
                "diameter": result.angular_diameter_arcsec - direct["diameter"],
                "phase": result.phase_angle_deg - direct["phase"],
                "fraction": result.illuminated_fraction - direct["fraction"],
                "position_angle": _wrapped_residual(
                    result.bright_limb_position_angle_deg,
                    direct["position_angle"],
                ),
            }
            for name, value in residuals.items():
                maxima[name] = max(maxima[name], abs(float(value)))
            minimum_parallax = min(minimum_parallax, direct["parallax"])

            print(
                f"case {observer.t_astropy.isot}: "
                f"phase {candidate_phase:.6f} deg; "
                f"distance {candidate_distance:.12f} au; "
                f"PA {candidate_angle:.6f} deg; "
                f"parallax {direct['parallax']:.6f} deg"
            )
            assert moon_direction.astrometric.target_provider_id == "301"
            assert sun_direction.astrometric.target_provider_id == "10"

        print("maximum absolute residuals:")
        print(f"  apparent RA deg: {maxima['ra']:.3e}")
        print(f"  apparent Dec deg: {maxima['dec']:.3e}")
        print(f"  topocentric distance au: {maxima['distance']:.3e}")
        print(f"  angular diameter arcsec: {maxima['diameter']:.3e}")
        print(f"  phase angle deg: {maxima['phase']:.3e}")
        print(f"  illuminated fraction: {maxima['fraction']:.3e}")
        print(f"  bright-limb PA deg: {maxima['position_angle']:.3e}")
        print(f"minimum topocentric parallax deg: {minimum_parallax:.6f}")

        assert maxima["ra"] <= RA_TOLERANCE_DEG
        assert maxima["dec"] <= DEC_TOLERANCE_DEG
        assert maxima["distance"] <= DISTANCE_TOLERANCE_AU
        assert maxima["diameter"] <= DIAMETER_TOLERANCE_ARCSEC
        assert maxima["phase"] <= PHASE_TOLERANCE_DEG
        assert maxima["fraction"] <= FRACTION_TOLERANCE
        assert maxima["position_angle"] <= POSITION_ANGLE_TOLERANCE_DEG
        assert minimum_parallax > 0.1


if __name__ == "__main__":
    main()
