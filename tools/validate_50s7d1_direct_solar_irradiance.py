"""Independently validate 50S.7D.1 against installed no-download geometry.

The receipt builds representative synthetic LEO, MEO, and GEO element
records, uses Wenu's accepted installed DE440/IERS/SGP4 geometry chain to find
sunlit, penumbral, and umbral instants, and independently recomputes the
declared IAU-nominal irradiance formula.  It performs no download.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.satellite_crossings import SatelliteObserver
from wenu.satellites import (
    DirectSolarIrradianceEvaluator,
    SatelliteGeocentricItrsTransformer,
    SatelliteIlluminationGeometryEvaluator,
    SatelliteTopocentricTransformer,
    SolarOccultationClass,
    Sgp4TemePropagator,
    evaluate_solar_occultation_contact,
)
from wenu.satellites import illumination as illumination_module
from wenu.satellites.elements import SatelliteElementRecord
from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource


IAU_SOURCE_ID = "IAU 2015 Resolution B3 nominal total solar irradiance"
INDEPENDENT_NOMINAL_IRRADIANCE_W_M2 = 1361.0
INDEPENDENT_AU_KM = 149_597_870.7
START = datetime(2000, 3, 20, 12, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class OrbitCase:
    name: str
    norad_catalog_id: int
    mean_motion_rev_per_day: float
    period_seconds: float


CASES = (
    OrbitCase("LEO", 90001, 14.82366876, 86400.0 / 14.82366876),
    OrbitCase("MEO", 90002, 2.00567549, 86400.0 / 2.00567549),
    OrbitCase("GEO", 90003, 1.00273791, 86400.0 / 1.00273791),
)


def _utc(instant):
    return instant.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _record(case):
    return SatelliteElementRecord(
        object_name=f"WENU {case.name} RADIOMETRY VALIDATOR",
        international_designator=f"2000-{case.norad_catalog_id % 1000:03d}A",
        norad_catalog_id=case.norad_catalog_id,
        classification="U",
        epoch_utc=_utc(START),
        mean_motion_rev_per_day=case.mean_motion_rev_per_day,
        eccentricity=0.0001,
        inclination_deg=0.1,
        ra_of_ascending_node_deg=0.0,
        argument_of_pericenter_deg=0.0,
        mean_anomaly_deg=0.0,
        bstar=0.0,
        mean_motion_dot=0.0,
        mean_motion_ddot=0.0,
        ephemeris_type=0,
        element_set_number=1,
        revolution_number_at_epoch=1,
        source_identity="Wenu offline 50S.7D.1 validation specimen",
        source_record_sha256=f"{case.norad_catalog_id:064x}",
        provenance=("Synthetic circular-orbit validation input.",),
    )


def _class_at(instant, propagator, source):
    state = propagator.propagate(_utc(instant))
    geocentric = SatelliteGeocentricItrsTransformer().transform(state)
    _, earth_to_sun = illumination_module._sun_state_and_itrs(
        source,
        state.evaluation_utc,
        geocentric.earth_orientation,
    )
    contact = evaluate_solar_occultation_contact(
        geocentric.satellite_itrs_position_km,
        earth_to_sun,
    )
    return contact.occultation_class


def _penumbral_instant(left, right, propagator, source):
    for _ in range(60):
        midpoint = left + (right - left) / 2
        state = _class_at(midpoint, propagator, source)
        if state is SolarOccultationClass.PENUMBRA:
            return midpoint
        left_state = _class_at(left, propagator, source)
        if state is left_state:
            left = midpoint
        else:
            right = midpoint
    raise AssertionError("could not isolate a penumbral validation instant")


def _representative_instants(case, propagator, source):
    samples = tuple(
        START + timedelta(seconds=case.period_seconds * index / 144.0)
        for index in range(145)
    )
    classes = tuple(_class_at(item, propagator, source) for item in samples)
    selected = {}
    for instant, state in zip(samples, classes, strict=True):
        if state in {
            SolarOccultationClass.SUNLIT,
            SolarOccultationClass.UMBRA,
        }:
            selected.setdefault(state, instant)
    for left, right, left_state, right_state in zip(
        samples,
        samples[1:],
        classes,
        classes[1:],
        strict=True,
    ):
        if left_state is right_state:
            continue
        if SolarOccultationClass.PENUMBRA in {left_state, right_state}:
            selected[SolarOccultationClass.PENUMBRA] = (
                left if left_state is SolarOccultationClass.PENUMBRA else right
            )
        else:
            selected[SolarOccultationClass.PENUMBRA] = _penumbral_instant(
                left,
                right,
                propagator,
                source,
            )
        break
    required = {
        SolarOccultationClass.SUNLIT,
        SolarOccultationClass.PENUMBRA,
        SolarOccultationClass.UMBRA,
    }
    if set(selected) != required:
        raise AssertionError(
            f"{case.name} did not supply sunlit, penumbral, and umbral states: "
            f"{sorted(item.value for item in selected)}"
        )
    return tuple(
        (state, selected[state])
        for state in sorted(required, key=lambda item: item.value)
    )


def _validate_case(case, source, observer):
    propagator = Sgp4TemePropagator(
        _record(case),
        snapshot_sha256="7" * 64,
    )
    transformer = SatelliteTopocentricTransformer()
    geometry_evaluator = SatelliteIlluminationGeometryEvaluator(source)
    irradiance_evaluator = DirectSolarIrradianceEvaluator()
    for expected_class, instant in _representative_instants(
        case,
        propagator,
        source,
    ):
        topocentric = transformer.transform(
            propagator.propagate(_utc(instant)),
            observer,
        )
        geometry = geometry_evaluator.evaluate(topocentric)
        actual = irradiance_evaluator.evaluate(geometry)
        if actual.occultation_class is not expected_class:
            raise AssertionError(
                f"{case.name} class changed during ordinary evaluation: "
                f"{expected_class.value} -> {actual.occultation_class.value}"
            )
        distance = geometry.solar_occultation.satellite_to_sun_distance_km
        fraction = geometry.solar_occultation.visible_disk_fraction
        expected_clear = (
            INDEPENDENT_NOMINAL_IRRADIANCE_W_M2
            * (INDEPENDENT_AU_KM / distance) ** 2
        )
        expected_incident = fraction * expected_clear
        clear_residual = abs(
            actual.unocculted_normal_irradiance_w_m2 - expected_clear
        )
        incident_residual = abs(
            actual.incident_normal_irradiance_w_m2 - expected_incident
        )
        if clear_residual > 1.0e-12 or incident_residual > 1.0e-12:
            raise AssertionError(
                f"{case.name} {expected_class.value} independent "
                "recomputation mismatch"
            )
        identity = sha256(repr(actual.geometry_identity).encode()).hexdigest()
        print(
            f"{case.name} {expected_class.value}: utc={actual.evaluation_utc}; "
            f"geometry_identity_sha256={identity}; distance_km={distance:.9f}; "
            f"visible_fraction={fraction:.12f}; "
            f"expected_clear_w_m2={expected_clear:.12f}; "
            f"actual_clear_w_m2={actual.unocculted_normal_irradiance_w_m2:.12f}; "
            f"clear_abs_residual={clear_residual:.3e}; "
            f"expected_incident_w_m2={expected_incident:.12f}; "
            f"actual_incident_w_m2={actual.incident_normal_irradiance_w_m2:.12f}; "
            f"incident_abs_residual={incident_residual:.3e}"
        )


def main():
    kernel = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not kernel.is_file():
        raise SystemExit(
            f"Installed kernel required; refusing download because {kernel} "
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
    print(f"iau_source={IAU_SOURCE_ID}")
    print(f"nominal_irradiance_w_m2={INDEPENDENT_NOMINAL_IRRADIANCE_W_M2}")
    print(f"astronomical_unit_km={INDEPENDENT_AU_KM}")
    print(f"kernel={kernel.name}")
    print(f"kernel_sha256={sha256(kernel.read_bytes()).hexdigest()}")
    print("network_access=false")
    print(
        "versions="
        f"wenu={version('wenu')}; astropy={version('astropy')}; "
        f"astropy-iers-data={version('astropy-iers-data')}; "
        f"sgp4={version('sgp4')}; skyfield={version('skyfield')}"
    )
    with Observer(
        location="La Ligua",
        time=START,
        ephemeris_name=DEFAULT_EPHEMERIS,
        data_directory=DEFAULT_DATA_DIRECTORY,
    ) as base:
        source = SkyfieldEphemerisStateSource.from_observer(base)
        for case in CASES:
            _validate_case(case, source, observer)


if __name__ == "__main__":
    main()
