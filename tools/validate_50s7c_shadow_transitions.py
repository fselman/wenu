"""Validate 50S.7C event times against installed SPICE and Skyfield.

This offline receipt writes a temporary sampled observer SPK, asks SPICE
``gfoclt`` for exterior plus full/annular contacts, and compares those event
times with Wenu's continuous contact search.  It performs no download and
does not modify an installed kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from importlib.metadata import version
from math import cos, sin
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import spiceypy
from spiceypy.utils.support_types import SPICEDOUBLE_CELL
from skyfield.api import EarthSatellite

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.satellite_crossings import SatelliteObserver
from wenu.satellites import (
    ShadowTransitionKind,
    ShadowTransitionSearchPolicy,
    SatelliteIlluminationGeometryEvaluator,
    SatelliteTopocentricTransformer,
    SolarOccultationPolicy,
    Sgp4TemePropagator,
    evaluate_solar_occultation_contact,
)
from wenu.satellites import illumination as illumination_module
from wenu.satellites.elements import SatelliteElementRecord
from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource


CENTER = datetime(2000, 6, 28, 0, 0, tzinfo=timezone.utc)
LINE1 = (
    "1 00005U 58002B   00179.78495062  .00000023  00000-0  "
    "28098-4 0  4753"
)
LINE2 = (
    "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 "
    "10.82419157413667"
)
OBSERVER_ID = -150070
EARTH_RADIUS_KM = 6378.0


@dataclass(frozen=True)
class Scenario:
    name: str
    radius_km: float
    angular_rate_rad_per_s: float
    inner_kind: str


SCENARIOS = (
    Scenario("full", 42_164.0, 0.002, "FULL"),
    Scenario("annular", 2_000_000.0, 0.0002, "ANNULAR"),
)


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


def _installed_kernel():
    path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not path.is_file():
        raise SystemExit(
            f"Installed kernel required; refusing download because {path} "
            "does not exist."
        )
    return path


def _et_from_datetime(timescale, instant):
    tdb_jd = float(timescale.from_datetime(instant).tdb)
    return (tdb_jd - 2451545.0) * 86400.0


def _basis(et):
    earth_to_sun, _ = spiceypy.spkpos(
        "SUN",
        et,
        "J2000",
        "NONE",
        "EARTH",
    )
    sun = np.asarray(earth_to_sun, dtype=float)
    sun /= np.linalg.norm(sun)
    helper = np.zeros(3)
    helper[int(np.argmin(np.abs(sun)))] = 1.0
    transverse = np.cross(sun, helper)
    transverse /= np.linalg.norm(transverse)
    return sun, transverse


def _observer_state(scenario, seconds, sun, transverse):
    angle = scenario.angular_rate_rad_per_s * seconds
    position = scenario.radius_km * (
        -cos(angle) * sun + sin(angle) * transverse
    )
    velocity = scenario.radius_km * scenario.angular_rate_rad_per_s * (
        sin(angle) * sun + cos(angle) * transverse
    )
    return np.concatenate((position, velocity))


def _write_observer_spk(path, scenario, center_et, sun, transverse):
    seconds = np.linspace(-120.0, 120.0, 961)
    epochs = center_et + seconds
    states = np.asarray(
        [
            _observer_state(scenario, value, sun, transverse)
            for value in seconds
        ]
    )
    handle = spiceypy.spkopn(str(path), "WENU 50S7C VALIDATOR", 0)
    try:
        spiceypy.spkw09(
            handle,
            OBSERVER_ID,
            399,
            "J2000",
            float(epochs[0]),
            float(epochs[-1]),
            f"WENU 50S7C {scenario.name}",
            7,
            len(epochs),
            states,
            epochs,
        )
    finally:
        spiceypy.spkcls(handle)


def _gf_intervals(kind, start_et, stop_et):
    confinement = SPICEDOUBLE_CELL(2)
    result = SPICEDOUBLE_CELL(100)
    spiceypy.wninsd(start_et, stop_et, confinement)
    spiceypy.gfoclt(
        kind,
        "EARTH",
        "ELLIPSOID",
        "WENU_EARTH_FIXED",
        "SUN",
        "ELLIPSOID",
        "WENU_SUN_FIXED",
        "NONE",
        str(OBSERVER_ID),
        1.0,
        confinement,
        result,
    )
    return tuple(
        spiceypy.wnfetd(result, index)
        for index in range(spiceypy.wncard(result))
    )


def _install_validation_frames():
    """Install identity-orientation body-centred frames for spherical cases."""
    spiceypy.lmpool(
        [
            "FRAME_WENU_EARTH_FIXED = 1500701",
            "FRAME_1500701_NAME = 'WENU_EARTH_FIXED'",
            "FRAME_1500701_CLASS = 4",
            "FRAME_1500701_CLASS_ID = 1500701",
            "FRAME_1500701_CENTER = 399",
            "TKFRAME_1500701_RELATIVE = 'J2000'",
            "TKFRAME_1500701_SPEC = 'MATRIX'",
            "TKFRAME_1500701_MATRIX = ( 1 0 0 0 1 0 0 0 1 )",
            "FRAME_WENU_SUN_FIXED = 1500702",
            "FRAME_1500702_NAME = 'WENU_SUN_FIXED'",
            "FRAME_1500702_CLASS = 4",
            "FRAME_1500702_CLASS_ID = 1500702",
            "FRAME_1500702_CENTER = 10",
            "TKFRAME_1500702_RELATIVE = 'J2000'",
            "TKFRAME_1500702_SPEC = 'MATRIX'",
            "TKFRAME_1500702_MATRIX = ( 1 0 0 0 1 0 0 0 1 )",
        ]
    )


def _spice_events(scenario, start_et, stop_et):
    exterior = _gf_intervals("ANY", start_et, stop_et)
    interior = _gf_intervals(scenario.inner_kind, start_et, stop_et)
    if len(exterior) != 1 or len(interior) != 1:
        raise AssertionError(
            f"SPICE {scenario.name} topology was not one nested interval: "
            f"ANY={exterior}, {scenario.inner_kind}={interior}"
        )
    if scenario.inner_kind == "FULL":
        ingress = ShadowTransitionKind.PENUMBRA_TO_UMBRA
        egress = ShadowTransitionKind.UMBRA_TO_PENUMBRA
    else:
        ingress = ShadowTransitionKind.PENUMBRA_TO_ANTUMBRA
        egress = ShadowTransitionKind.ANTUMBRA_TO_PENUMBRA
    return (
        (ShadowTransitionKind.SUNLIT_TO_PENUMBRA, exterior[0][0]),
        (ingress, interior[0][0]),
        (egress, interior[0][1]),
        (ShadowTransitionKind.PENUMBRA_TO_SUNLIT, exterior[0][1]),
    )


def _wenu_events(scenario, center_et, sun, transverse):
    policy = SolarOccultationPolicy(
        earth_equatorial_radius_km=EARTH_RADIUS_KM,
        earth_polar_radius_km=EARTH_RADIUS_KM,
    )
    minimum_altitude = scenario.radius_km - EARTH_RADIUS_KM
    maximum_speed = (
        scenario.radius_km * scenario.angular_rate_rad_per_s * 1.01
    )
    search = ShadowTransitionSearchPolicy(
        time_tolerance_seconds=0.01,
        maximum_interval_seconds=300.0,
        maximum_subdivision_depth=48,
        maximum_evaluations=100_000,
        minimum_altitude_km=minimum_altitude * 0.99,
        maximum_speed_km_per_s=maximum_speed,
        contact_rate_bound_rad_per_s=(
            2.0 * maximum_speed / (minimum_altitude * 0.99) + 0.002
        ),
    )
    start = CENTER - timedelta(seconds=120)
    stop = CENTER + timedelta(seconds=120)

    def evaluate(instant):
        seconds = (instant - CENTER).total_seconds()
        state = _observer_state(scenario, seconds, sun, transverse)
        earth_to_sun, _ = spiceypy.spkpos(
            "SUN",
            center_et + seconds,
            "J2000",
            "NONE",
            "EARTH",
        )
        contact = evaluate_solar_occultation_contact(
            state[:3],
            earth_to_sun,
            occultation_policy=policy,
            search_policy=search,
        )
        return illumination_module._ShadowSample(
            instant=instant,
            contact=contact,
        )

    cache = illumination_module._ShadowEvaluationCache(
        evaluate,
        search,
        OBSERVER_ID,
    )
    brackets = illumination_module._collect_transition_brackets(
        cache,
        start,
        stop,
        search,
    )
    return tuple(
        (
            kind,
            center_et + (left.instant - CENTER).total_seconds(),
            center_et + (right.instant - CENTER).total_seconds(),
        )
        for left, right, kind in brackets
    ), cache.evaluation_count


def validate_spice_events(kernel, timescale):
    center_et = _et_from_datetime(timescale, CENTER)
    spiceypy.furnsh(str(kernel))
    spiceypy.boddef("WENU_50S7C_OBSERVER", OBSERVER_ID)
    _install_validation_frames()
    spiceypy.pdpool(
        "BODY399_RADII",
        [EARTH_RADIUS_KM, EARTH_RADIUS_KM, EARTH_RADIUS_KM],
    )
    spiceypy.pdpool(
        "BODY10_RADII",
        [695_700.0, 695_700.0, 695_700.0],
    )
    spiceypy.gfstol(1.0e-7)
    try:
        sun, transverse = _basis(center_et)
        for scenario in SCENARIOS:
            with TemporaryDirectory(prefix="wenu-50s7c-") as directory:
                path = Path(directory) / f"{scenario.name}.bsp"
                _write_observer_spk(
                    path,
                    scenario,
                    center_et,
                    sun,
                    transverse,
                )
                spiceypy.furnsh(str(path))
                try:
                    oracle = _spice_events(
                        scenario,
                        center_et - 120.0,
                        center_et + 120.0,
                    )
                    wenu, count = _wenu_events(
                        scenario,
                        center_et,
                        sun,
                        transverse,
                    )
                finally:
                    spiceypy.unload(str(path))
            if tuple(item[0] for item in wenu) != tuple(
                item[0] for item in oracle
            ):
                raise AssertionError(
                    f"{scenario.name}: directed sequence mismatch"
                )
            for (kind, event), (_, left, right) in zip(
                oracle,
                wenu,
                strict=True,
            ):
                if not left - 0.02 <= event <= right + 0.02:
                    raise AssertionError(
                        f"{scenario.name} {kind.value}: SPICE event "
                        "outside Wenu bracket"
                    )
            print(
                f"SPICE gfoclt {scenario.name}: 4 directed contacts; "
                f"Wenu evaluations={count}"
            )
    finally:
        spiceypy.kclear()


def validate_skyfield_binary(kernel):
    start = datetime(2000, 6, 27, 18, 50, 19, 733568, tzinfo=timezone.utc)
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
        time=start,
        ephemeris_name=kernel.name,
        data_directory=str(kernel.parent),
    ) as base:
        source = SkyfieldEphemerisStateSource.from_observer(base)
        evaluator = SatelliteIlluminationGeometryEvaluator(source)
        satellite = EarthSatellite(LINE1, LINE2, "VANGUARD 1", base.timescale)
        for step in range(145):
            instant = start + timedelta(minutes=10 * step)
            utc = instant.isoformat(timespec="microseconds").replace(
                "+00:00",
                "Z",
            )
            result = evaluator.evaluate(
                transformer.transform(propagator.propagate(utc), observer)
            )
            value = result.solar_occultation.occultation_class.value
            if value not in {"sunlit", "umbra"}:
                continue
            skyfield_sunlit = bool(
                satellite.at(base.timescale.from_datetime(instant)).is_sunlit(
                    base.ephemeris
                )
            )
            if (value == "sunlit") != skyfield_sunlit:
                raise AssertionError(f"Skyfield binary mismatch at {utc}")
            matched[skyfield_sunlit] += 1
            if min(matched.values()) >= 5:
                break
        if min(matched.values()) < 5:
            raise AssertionError("insufficient Skyfield binary side evidence")
        print(f"Skyfield full-light matches: {matched[True]}")
        print(f"Skyfield full-shadow matches: {matched[False]}")


def main():
    kernel = _installed_kernel()
    with Observer(
        location="La Ligua",
        time=CENTER,
        ephemeris_name=kernel.name,
        data_directory=str(kernel.parent),
    ) as base:
        validate_spice_events(kernel, base.timescale)
    validate_skyfield_binary(kernel)
    print(f"spiceypy: {version('spiceypy')}")
    print(f"CSPICE: {spiceypy.tkvrsn('TOOLKIT')}")
    print(f"kernel: {kernel.name}")
    print(f"kernel sha256: {sha256(kernel.read_bytes()).hexdigest()}")
    print("SPICE aberration: NONE")
    print("SPICE search step seconds: 1.0")
    print("SPICE convergence tolerance seconds: 1e-7")


if __name__ == "__main__":
    main()
