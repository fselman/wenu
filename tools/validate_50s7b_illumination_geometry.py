"""Validate 50S.7B geometry against installed Skyfield and SPICE."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import asin, cos, sin
from pathlib import Path

import numpy as np
import spiceypy
from skyfield.api import EarthSatellite

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.satellite_crossings import SatelliteObserver
from wenu.satellites import (
    SatelliteIlluminationGeometryEvaluator,
    SatelliteTopocentricTransformer,
    SolarOccultationClass,
    SolarOccultationPolicy,
    Sgp4TemePropagator,
    evaluate_solar_occultation,
)
from wenu.satellites.elements import SatelliteElementRecord
from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource


LINE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
LINE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"
START = datetime(2000, 6, 27, 18, 50, 19, 733568, tzinfo=timezone.utc)
EARTH_RADIUS_KM = 6378.0


def record():
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


def _solar_rays(center, angular_radius):
    axis = np.zeros(3)
    axis[int(np.argmin(np.abs(center)))] = 1.0
    first = np.cross(center, axis)
    first /= np.linalg.norm(first)
    second = np.cross(first, center)
    rays = []
    for radial_index in range(32):
        theta = angular_radius * (radial_index + 0.5) / 32.0
        for azimuth_index in range(128):
            phi = 2.0 * np.pi * azimuth_index / 128.0
            rays.append(
                cos(theta) * center
                + sin(theta)
                * (
                    cos(phi) * first
                    + sin(phi) * second
                )
            )
    return tuple(rays)


def _spice_classification(satellite, sun, policy):
    satellite = np.asarray(satellite, dtype=float)
    satellite_to_sun = np.asarray(sun, dtype=float) - satellite
    distance = float(np.linalg.norm(satellite_to_sun))
    center = satellite_to_sun / distance
    angular_radius = asin(policy.solar_radius_km / distance)
    hits = []
    for ray in _solar_rays(center, angular_radius):
        _, found = spiceypy.surfpt(
            satellite,
            ray,
            policy.earth_equatorial_radius_km,
            policy.earth_equatorial_radius_km,
            policy.earth_polar_radius_km,
        )
        hits.append(bool(found))
    if not any(hits):
        return SolarOccultationClass.SUNLIT
    if all(hits):
        return SolarOccultationClass.UMBRA

    limb = spiceypy.edlimb(
        policy.earth_equatorial_radius_km,
        policy.earth_equatorial_radius_km,
        policy.earth_polar_radius_km,
        satellite,
    )
    limb_center, semi_major, semi_minor = spiceypy.el2cgv(limb)
    limb_inside = True
    for angle in np.linspace(0.0, 2.0 * np.pi, 2048, endpoint=False):
        point = (
            limb_center
            + cos(angle) * semi_major
            + sin(angle) * semi_minor
        )
        direction = point - satellite
        direction /= np.linalg.norm(direction)
        separation = np.arccos(
            np.clip(float(direction @ center), -1.0, 1.0)
        )
        if separation > angular_radius:
            limb_inside = False
            break
    return (
        SolarOccultationClass.ANTUMBRA
        if limb_inside
        else SolarOccultationClass.PENUMBRA
    )


def validate_spice_classification():
    policy = SolarOccultationPolicy(
        earth_equatorial_radius_km=EARTH_RADIUS_KM,
        earth_polar_radius_km=EARTH_RADIUS_KM,
        radial_samples=48,
        azimuth_samples=192,
    )
    satellite = np.asarray((1_000_000.0, 0.0, 0.0))
    beta = asin(EARTH_RADIUS_KM / np.linalg.norm(satellite))
    distance = 100_000_000.0
    cases = (
        ("clear", 0.004, beta + 0.006, SolarOccultationClass.SUNLIT),
        ("partial", 0.004, beta, SolarOccultationClass.PENUMBRA),
        ("umbra", 0.004, 0.0, SolarOccultationClass.UMBRA),
        ("annular", 0.010, 0.0, SolarOccultationClass.ANTUMBRA),
    )
    for name, alpha, separation, expected in cases:
        direction = np.asarray(
            (-cos(separation), sin(separation), 0.0),
        )
        sun = satellite + distance * direction
        case_policy = SolarOccultationPolicy(
            earth_equatorial_radius_km=EARTH_RADIUS_KM,
            earth_polar_radius_km=EARTH_RADIUS_KM,
            solar_radius_km=distance * sin(alpha),
            radial_samples=policy.radial_samples,
            azimuth_samples=policy.azimuth_samples,
        )
        result = evaluate_solar_occultation(
            satellite,
            sun,
            policy=case_policy,
        )
        oracle = _spice_classification(
            satellite,
            sun,
            case_policy,
        )
        if result.occultation_class is not expected or oracle is not expected:
            raise AssertionError(
                f"{name}: Wenu={result.occultation_class.value}, "
                f"SPICE={oracle.value}, expected={expected.value}"
            )
        print(
            f"SPICE {name}: {oracle.value}; "
            f"visible_fraction={result.visible_disk_fraction:.9f}"
        )


def validate_skyfield_binary():
    path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not path.is_file():
        raise SystemExit(
            f"Installed kernel required; refusing download because {path} "
            "does not exist."
        )
    observer = SatelliteObserver(
        "La Ligua",
        -71.230289,
        -32.443342,
        52.0,
        refraction_policy="vacuum",
        earth_orientation_policy="iers-a-bundled",
    )
    propagator = Sgp4TemePropagator(record())
    transformer = SatelliteTopocentricTransformer()
    matched = {True: 0, False: 0}
    with Observer(
        location="La Ligua",
        time=START,
        ephemeris_name=DEFAULT_EPHEMERIS,
        data_directory=DEFAULT_DATA_DIRECTORY,
    ) as base:
        source = SkyfieldEphemerisStateSource.from_observer(base)
        evaluator = SatelliteIlluminationGeometryEvaluator(source)
        satellite = EarthSatellite(
            LINE1,
            LINE2,
            "VANGUARD 1",
            base.timescale,
        )
        for step in range(145):
            instant = START + timedelta(minutes=10 * step)
            utc = instant.isoformat(timespec="microseconds").replace(
                "+00:00",
                "Z",
            )
            topocentric = transformer.transform(
                propagator.propagate(utc),
                observer,
            )
            result = evaluator.evaluate(topocentric)
            if result.solar_occultation.occultation_class not in {
                SolarOccultationClass.SUNLIT,
                SolarOccultationClass.UMBRA,
            }:
                continue
            skyfield_sunlit = bool(
                satellite.at(
                    base.timescale.from_datetime(instant)
                ).is_sunlit(base.ephemeris)
            )
            wenu_sunlit = (
                result.solar_occultation.occultation_class
                is SolarOccultationClass.SUNLIT
            )
            if wenu_sunlit != skyfield_sunlit:
                raise AssertionError(
                    f"binary sunlight mismatch at {utc}: "
                    f"Wenu={wenu_sunlit}, Skyfield={skyfield_sunlit}"
                )
            matched[skyfield_sunlit] += 1
            if min(matched.values()) >= 5:
                break
        if min(matched.values()) < 5:
            raise AssertionError(
                "Skyfield comparison did not collect five full-light and "
                "five full-shadow cases."
            )
        print(f"model: {source.resource.model}")
        print(f"file: {source.resource.filename}")
        print(f"sha256: {source.resource.sha256}")
        print(f"Skyfield full-light matches: {matched[True]}")
        print(f"Skyfield full-shadow matches: {matched[False]}")


def main():
    validate_spice_classification()
    validate_skyfield_binary()


if __name__ == "__main__":
    main()
