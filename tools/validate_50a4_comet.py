"""Characterize 2P/Encke against the frozen direct-Horizons oracle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS

try:
    from tools.validate_50a2_asteroids import validate
except ModuleNotFoundError as error:
    if error.name != "tools":
        raise
    from validate_50a2_asteroids import validate

REFERENCE = (
    Path(__file__).parents[1]
    / "tests"
    / "fixtures"
    / "horizons_comet_validation_50a4.json"
)


def validate_comet(
    *, resource_directory, planetary_ephemeris_path, reference_path,
    characterize=False,
):
    """Run the shared minor-body oracle in enforcing or characterization mode."""
    report = validate(
        resource_directory=resource_directory,
        planetary_ephemeris_path=planetary_ephemeris_path,
        reference_path=reference_path,
        characterize=characterize,
    )
    for result in report["objects"]:
        solution = result["solution"]
        if solution["object_class"] != "comet":
            raise AssertionError("50A.4 solution identity is not a comet.")
        if not {"A1", "A2"}.issubset(solution["model_parameters"]):
            raise AssertionError("50A.4 solution identity discarded A1 or A2.")
    if characterize:
        report["tolerances"] = None
        report["tolerance_status"] = "not enforced during characterization"
    else:
        report["tolerance_status"] = "accepted and enforced"
    return report


def characterize(*, resource_directory, planetary_ephemeris_path, reference_path):
    """Run the shared minor-body oracle without applying accepted thresholds."""
    return validate_comet(
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
    parser.add_argument(
        "--characterize",
        action="store_true",
        help="report residuals without applying acceptance thresholds",
    )
    arguments = parser.parse_args()
    report = validate_comet(
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
