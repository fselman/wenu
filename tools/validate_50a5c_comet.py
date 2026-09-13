"""Characterize 161P numerical state and orientation without tolerances."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS

try:
    from tools.validate_50a2_asteroids import validate
    from tools.validate_50a5b_antisolar import validate_antisolar
except ModuleNotFoundError as error:
    if error.name != "tools":
        raise
    from validate_50a2_asteroids import validate
    from validate_50a5b_antisolar import validate_antisolar


def validate_comet(
    *, resource_directory, planetary_ephemeris_path, reference_path,
    characterize=False,
):
    """Run shared numerical and orientation validators for one fixture."""
    numerical = validate(
        resource_directory=resource_directory,
        planetary_ephemeris_path=planetary_ephemeris_path,
        reference_path=reference_path,
        characterize=characterize,
    )
    orientation = validate_antisolar(
        resource_directory=resource_directory,
        planetary_ephemeris_path=planetary_ephemeris_path,
        reference_path=reference_path,
        characterize=characterize,
    )
    if len(numerical["objects"]) != 1:
        raise ValueError("50A.5C requires exactly one comet record.")
    solution = numerical["objects"][0]["solution"]
    if solution["object_class"] != "comet":
        raise AssertionError("50A.5C solution identity is not a comet.")
    if not {"A1", "A2"}.issubset(solution["model_parameters"]):
        raise AssertionError("50A.5C solution discarded A1 or A2.")
    return {
        "accepted": not characterize,
        "characterization": bool(characterize),
        "tolerance_status": (
            "not enforced during characterization"
            if characterize else "accepted and enforced"
        ),
        "numerical": numerical,
        "antisolar": orientation,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-directory", type=Path, required=True)
    parser.add_argument(
        "--planetary-ephemeris-path",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY / DEFAULT_EPHEMERIS,
    )
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--characterize", action="store_true")
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
