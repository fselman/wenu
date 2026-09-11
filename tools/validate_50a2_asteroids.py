"""Validate installed asteroid SPKs against frozen direct-Horizons evidence."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from math import acos, cos, radians, sin
from pathlib import Path
from types import SimpleNamespace

from wenu.ephemeris import EphemerisStateRequest
from wenu.minor_body_ephemeris import (
    MinorBodySolutionIdentity,
    SkyfieldMinorBodyStateSource,
    SpiceMinorBodyKernel,
)
from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
    skyfield_observer_barycentric_state,
)
from wenu.solar_system_directions import (
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)

REFERENCE = (
    Path(__file__).parents[1]
    / "tests"
    / "fixtures"
    / "horizons_asteroid_validation_50a2.json"
)
POSITION_TOLERANCE_AU = 5.0e-12
VELOCITY_TOLERANCE_AU_PER_DAY = 5.0e-13
DIRECTION_TOLERANCE_DEG = 5.0e-6
DISTANCE_TOLERANCE_AU = 1.0e-9
LIGHT_TIME_TOLERANCE_MIN = 1.0e-7
PARALLAX_TOLERANCE_DEG = 5.0e-6


def _require_within(value, tolerance, label):
    if value > tolerance:
        raise AssertionError(
            f"{label} residual {value:.16g} exceeds {tolerance:.16g}."
        )


def _digest(path):
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _wrapped(actual, reference):
    return (actual - reference + 180.0) % 360.0 - 180.0


def _separation_deg(first, second):
    ra1, dec1 = map(radians, first)
    ra2, dec2 = map(radians, second)
    cosine = sin(dec1) * sin(dec2) + cos(dec1) * cos(dec2) * cos(ra1 - ra2)
    return acos(max(-1.0, min(1.0, cosine))) * 180.0 / 3.141592653589793


def _solution(record, api_version):
    model_parameters = tuple(
        sorted(record.get("model_parameters", {}).items())
    )
    quality_fields = tuple(sorted(record["quality_fields"].items()))
    return MinorBodySolutionIdentity(
        provider="JPL Horizons",
        service_version=f"Horizons API {api_version}",
        wenu_target=record["key"],
        object_class=record["class"],
        primary_designation=record["primary_designation"],
        horizons_command=record["horizons_command"],
        provider_spk_id=record["provider_spk_id"],
        orbit_solution_id=record["orbit_solution_id"],
        solution_date=record["solution_date"],
        osculating_epoch=record["osculating_epoch"],
        reference_system="ICRF/J2000",
        iau_number=record.get(
            "iau_number",
            1 if record["key"] == "ceres" else 99942,
        ),
        name=record.get(
            "name",
            "Ceres" if record["key"] == "ceres" else "Apophis",
        ),
        aliases=tuple(record.get(
            "aliases",
            () if record["key"] == "ceres" else ("2004 MN4",),
        )),
        model_parameters=model_parameters,
        quality_fields=quality_fields,
        provenance=("frozen direct-Horizons 50A.2 evidence",),
    )


def _geocentric_observer(observer):
    return SimpleNamespace(
        ephemeris=observer.ephemeris,
        t=observer.t,
        t_astropy=observer.t_astropy,
        skyfield=observer.earth,
        location_name="Earth geocentre",
    )


def _direction(observer, minor_source, planetary_source):
    observer_state = skyfield_observer_barycentric_state(
        observer,
        source=planetary_source,
    )
    request = AstrometricDirectionRequest(
        target=minor_source.solution.wenu_target,
        centre="solar system barycenter",
        reception_instant=observer.t_astropy.isot,
        reception_time_scale=observer.t_astropy.scale,
    )
    astrometric = AstrometricDirectionRealizer().direction(
        minor_source,
        request,
        observer_state,
    )
    apparent = SkyfieldApparentDirectionRealizer().direction(
        astrometric,
        observer=observer,
        source=planetary_source,
    )
    return astrometric, apparent


def validate(
    *, resource_directory, planetary_ephemeris_path, reference_path,
    characterize=False,
):
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    tolerances = {
        "position_au": POSITION_TOLERANCE_AU,
        "velocity_au_per_day": VELOCITY_TOLERANCE_AU_PER_DAY,
        "direction_deg": DIRECTION_TOLERANCE_DEG,
        "distance_au": DISTANCE_TOLERANCE_AU,
        "light_time_min": LIGHT_TIME_TOLERANCE_MIN,
        "parallax_deg": PARALLAX_TOLERANCE_DEG,
    }
    for name, value in reference.get("tolerances", {}).items():
        if name not in tolerances:
            raise ValueError(f"unknown validation tolerance: {name}")
        tolerances[name] = float(value)
    manifest_path = resource_directory / "acquisition-report.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    acquired = {item["key"]: item for item in manifest["resources"]}
    planetary_path = planetary_ephemeris_path
    if not planetary_path.is_file():
        raise FileNotFoundError(
            f"missing planetary ephemeris: {planetary_path}"
        )
    results = []

    for record in reference["objects"]:
        key = record["key"]
        resource_record = acquired[key]
        spk_path = resource_directory / resource_record["filename"]
        actual_digest = _digest(spk_path)
        if actual_digest != resource_record["sha256"]:
            raise ValueError(
                f"{key} SPK digest differs from acquisition report."
            )
        if resource_record["spk_file_id"] != record["provider_spk_id"]:
            raise ValueError(
                f"{key} acquisition target differs from reference."
            )

        maxima = {
            "position_au": 0.0,
            "velocity_au_per_day": 0.0,
            "astrometric_ra_deg": 0.0,
            "astrometric_dec_deg": 0.0,
            "apparent_ra_deg": 0.0,
            "apparent_dec_deg": 0.0,
            "distance_au": 0.0,
            "light_time_min": 0.0,
            "parallax_deg": 0.0,
        }
        parallaxes = []
        with SpiceMinorBodyKernel(spk_path) as kernel:
            target_segments = [
                segment
                for segment in kernel.segments
                if segment.target == int(record["provider_spk_id"])
            ]
            if len(target_segments) != 1:
                raise ValueError(
                    f"{key} must have exactly one target segment."
                )
            segment = target_segments[0]
            expected_spk = record["spk"]
            if (
                segment.data_type != expected_spk["segment_type"]
                or segment.center != expected_spk["segment_centre_id"]
                or segment.start_jd != expected_spk["coverage_start_jd_tdb"]
                or segment.end_jd != expected_spk["coverage_end_jd_tdb"]
            ):
                raise ValueError(
                    f"{key} segment identity differs from reference."
                )

            for epoch in record["epochs"]:
                utc = epoch["calendar"] + "Z"
                with Observer(
                    location="La Ligua",
                    time=utc,
                    ephemeris_name=planetary_path.name,
                    data_directory=planetary_path.parent,
                ) as observer:
                    planetary = SkyfieldEphemerisStateSource.from_observer(
                        observer
                    )
                    source = SkyfieldMinorBodyStateSource.from_kernels(
                        small_body_kernel=kernel,
                        planetary_source=planetary,
                        timescale=observer.timescale,
                        solution=_solution(
                            record,
                            reference["authority"]["returned_version"],
                        ),
                        model=f"Horizons {record['orbit_solution_id']}",
                    )
                    geometric = source.state(
                        EphemerisStateRequest(
                            target=key,
                            centre="solar system barycenter",
                            frame="icrf",
                            instant=epoch["calendar"],
                            time_scale="tdb",
                        )
                    )
                    maxima["position_au"] = max(
                        maxima["position_au"],
                        *(
                            abs(a - b)
                            for a, b in zip(
                                geometric.position, epoch["position_au"]
                            )
                        ),
                    )
                    maxima["velocity_au_per_day"] = max(
                        maxima["velocity_au_per_day"],
                        *(
                            abs(a - b)
                            for a, b in zip(
                                geometric.velocity,
                                epoch["velocity_au_per_day"],
                            )
                        ),
                    )

                    top_astrometric, top_apparent = _direction(
                        observer,
                        source,
                        planetary,
                    )
                    geo_observer = _geocentric_observer(observer)
                    geo_astrometric, geo_apparent = _direction(
                        geo_observer,
                        source,
                        planetary,
                    )
                    realized = {
                        "topocentric": (top_astrometric, top_apparent),
                        "geocentric": (geo_astrometric, geo_apparent),
                    }
                    for site, (astrometric, apparent) in realized.items():
                        expected = epoch[site]
                        values = {
                            "astrometric_ra_deg": astrometric.geometry.lon_deg[
                                0
                            ],
                            "astrometric_dec_deg": astrometric.geometry.lat_deg[
                                0
                            ],
                            "apparent_ra_deg": apparent.geometry.lon_deg[0],
                            "apparent_dec_deg": apparent.geometry.lat_deg[0],
                            "distance_au": astrometric.distance_au,
                            "light_time_min": astrometric.light_time_days
                            * 1440.0,
                        }
                        for name, value in values.items():
                            residual = (
                                _wrapped(value, expected[name])
                                if name.endswith("ra_deg")
                                else value - expected[name]
                            )
                            maxima[name] = max(maxima[name], abs(residual))

                    top_pair = (
                        top_apparent.geometry.lon_deg[0],
                        top_apparent.geometry.lat_deg[0],
                    )
                    geo_pair = (
                        geo_apparent.geometry.lon_deg[0],
                        geo_apparent.geometry.lat_deg[0],
                    )
                    expected_top = epoch["topocentric"]
                    expected_geo = epoch["geocentric"]
                    actual_parallax = _separation_deg(top_pair, geo_pair)
                    expected_parallax = _separation_deg(
                        (
                            expected_top["apparent_ra_deg"],
                            expected_top["apparent_dec_deg"],
                        ),
                        (
                            expected_geo["apparent_ra_deg"],
                            expected_geo["apparent_dec_deg"],
                        ),
                    )
                    maxima["parallax_deg"] = max(
                        maxima["parallax_deg"],
                        abs(actual_parallax - expected_parallax),
                    )
                    parallaxes.append(actual_parallax)

        if not characterize:
            _require_within(
                maxima["position_au"], tolerances["position_au"], "position"
            )
            _require_within(
                maxima["velocity_au_per_day"],
                tolerances["velocity_au_per_day"],
                "velocity",
            )
            for label in (
                "astrometric_ra_deg",
                "astrometric_dec_deg",
                "apparent_ra_deg",
                "apparent_dec_deg",
            ):
                _require_within(maxima[label], tolerances["direction_deg"], label)
            _require_within(
                maxima["distance_au"], tolerances["distance_au"], "distance"
            )
            _require_within(
                maxima["light_time_min"],
                tolerances["light_time_min"],
                "light time",
            )
            _require_within(
                maxima["parallax_deg"], tolerances["parallax_deg"], "parallax"
            )
            if key == "apophis" and max(parallaxes) <= 0.1:
                raise AssertionError(
                    "Apophis validation must exhibit material parallax."
                )
        results.append(
            {
                "key": key,
                "spk_sha256": actual_digest,
                "segment_type": segment.data_type,
                "epochs": len(record["epochs"]),
                "maximum_residuals": maxima,
                "parallax_deg": parallaxes,
            }
        )

    return {
        "accepted": not characterize,
        "characterization": bool(characterize),
        "reference": str(reference_path),
        "planetary_ephemeris": {
            "filename": planetary_path.name,
            "sha256": _digest(planetary_path),
        },
        "tolerances": tolerances,
        "objects": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--resource-directory",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY / "minor_bodies" / "50a2",
    )
    parser.add_argument(
        "--planetary-ephemeris-path",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY / DEFAULT_EPHEMERIS,
    )
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--characterize", action="store_true",
        help="report all residuals without applying acceptance thresholds",
    )
    arguments = parser.parse_args()
    report = validate(
        resource_directory=arguments.resource_directory.expanduser().resolve(),
        planetary_ephemeris_path=(
            arguments.planetary_ephemeris_path.expanduser().resolve()
        ),
        reference_path=arguments.reference.expanduser().resolve(),
        characterize=arguments.characterize,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(arguments.output)


if __name__ == "__main__":
    main()
