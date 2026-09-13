"""Characterize Wenu's apparent antisolar direction against Horizons."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from wenu.antisolar import antisolar_position_angle_deg
from wenu.minor_body_ephemeris import (
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

try:
    from tools.validate_50a2_asteroids import _digest, _solution
except ModuleNotFoundError as error:
    if error.name != "tools":
        raise
    from validate_50a2_asteroids import _digest, _solution


REFERENCE = (
    Path(__file__).parents[1]
    / "tests"
    / "fixtures"
    / "horizons_antisolar_validation_50a5b.json"
)


def _apparent_direction(observer, target_source, observer_source, target):
    observer_state = skyfield_observer_barycentric_state(
        observer, source=observer_source
    )
    request = AstrometricDirectionRequest(
        target=target,
        centre="solar system barycenter",
        reception_instant=observer.t_astropy.isot,
        reception_time_scale=observer.t_astropy.scale,
    )
    astrometric = AstrometricDirectionRealizer().direction(
        target_source, request, observer_state
    )
    apparent = SkyfieldApparentDirectionRealizer().direction(
        astrometric, observer=observer, source=observer_source
    )
    return (
        apparent.geometry.lon_deg[0],
        apparent.geometry.lat_deg[0],
    )


def _wrapped(actual, reference):
    return (actual - reference + 180.0) % 360.0 - 180.0


def validate_antisolar(
    *, resource_directory, planetary_ephemeris_path, reference_path,
    characterize=False,
):
    """Validate or characterize Wenu's apparent antisolar direction."""
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    tolerances = reference.get("tolerances")
    if not isinstance(tolerances, dict) or set(tolerances) != {
        "antisolar_position_angle_deg"
    }:
        raise ValueError("50A.5B reference must set only its accepted tolerance.")
    tolerance = float(tolerances["antisolar_position_angle_deg"])
    if tolerance <= 0:
        raise ValueError("antisolar position-angle tolerance must be positive.")
    record = reference["object"]
    comet_reference = json.loads(
        (
            Path(__file__).parents[1]
            / "tests/fixtures/horizons_comet_validation_50a4.json"
        ).read_text(encoding="utf-8")
    )["objects"][0]
    manifest = json.loads(
        (resource_directory / "acquisition-report.json").read_text(
            encoding="utf-8"
        )
    )
    spk_record = next(
        item for item in manifest["evidence"]
        if item.get("filename") == comet_reference["spk"]["filename"]
    )
    spk_path = resource_directory / spk_record["filename"]
    if _digest(spk_path) != comet_reference["spk"]["sha256"]:
        raise ValueError("2P/Encke SPK differs from the accepted 50A.4 oracle.")
    solution = _solution(
        comet_reference,
        reference["authority"]["horizons_version"],
    )
    residuals = []
    with SpiceMinorBodyKernel(spk_path) as kernel:
        for epoch in reference["epochs"]:
            with Observer(
                location="La Ligua",
                time=epoch["calendar_utc"] + "Z",
                ephemeris_name=planetary_ephemeris_path.name,
                data_directory=planetary_ephemeris_path.parent,
            ) as observer:
                planetary = SkyfieldEphemerisStateSource.from_observer(observer)
                comet_source = SkyfieldMinorBodyStateSource.from_kernels(
                    small_body_kernel=kernel,
                    planetary_source=planetary,
                    timescale=observer.timescale,
                    solution=solution,
                    model=f"Horizons {record['orbit_solution_id']}",
                )
                comet = _apparent_direction(
                    observer, comet_source, planetary, record["key"]
                )
                sun = _apparent_direction(
                    observer, planetary, planetary, "sun"
                )
                actual = antisolar_position_angle_deg(comet, sun)
                residuals.append({
                    "calendar_utc": epoch["calendar_utc"],
                    "wenu_comet_apparent_icrf_deg": comet,
                    "wenu_sun_apparent_icrf_deg": sun,
                    "wenu_antisolar_position_angle_deg": actual,
                    "reference_antisolar_position_angle_deg": (
                        epoch["antisolar_position_angle_deg"]
                    ),
                    "residual_deg": _wrapped(
                        actual, epoch["antisolar_position_angle_deg"]
                    ),
                })
    maximum = max(abs(item["residual_deg"]) for item in residuals)
    if not characterize and maximum > tolerance:
        raise AssertionError(
            "antisolar position-angle residual "
            f"{maximum:.16g} exceeds {tolerance:.16g}."
        )
    return {
        "accepted": not characterize,
        "characterization": bool(characterize),
        "tolerance_status": (
            "not enforced during characterization"
            if characterize else "accepted and enforced"
        ),
        "tolerances": None if characterize else tolerances,
        "object": record,
        "epochs": residuals,
        "maximum_residual_deg": maximum,
    }


def characterize(*, resource_directory, planetary_ephemeris_path, reference_path):
    """Report residuals without applying the accepted threshold."""
    return validate_antisolar(
        resource_directory=resource_directory,
        planetary_ephemeris_path=planetary_ephemeris_path,
        reference_path=reference_path,
        characterize=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--resource-directory",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY / "minor_bodies" / "50a4-raw-v2",
    )
    parser.add_argument(
        "--planetary-ephemeris-path",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY / DEFAULT_EPHEMERIS,
    )
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--characterize", action="store_true")
    arguments = parser.parse_args()
    report = validate_antisolar(
        resource_directory=arguments.resource_directory.expanduser().resolve(),
        planetary_ephemeris_path=(
            arguments.planetary_ephemeris_path.expanduser().resolve()
        ),
        reference_path=arguments.reference.expanduser().resolve(),
        characterize=arguments.characterize,
    )
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(arguments.output)


if __name__ == "__main__":
    main()
