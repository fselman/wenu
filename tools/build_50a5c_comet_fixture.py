"""Build the compact offline 161P numerical and orientation oracle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from wenu.antisolar import antisolar_position_angle_deg

try:
    from tools.acquire_50a5c_comet_evidence import (
        DESIGNATION,
        EPOCHS,
        FULL_NAME,
        HORIZONS_RECORD,
        ORBIT_SOLUTION_ID,
        PROVIDER_SPK_ID,
        _sun_table,
        _target_table,
    )
    from tools.build_50a4_comet_fixture import (
        _digest,
        _document,
        build_fixture as build_numerical_fixture,
    )
    from tools.build_50a5b_antisolar_fixture import (
        _comet_tail_rows,
        _sun_rows,
    )
except ModuleNotFoundError as error:
    if error.name != "tools":
        raise
    from acquire_50a5c_comet_evidence import (
        DESIGNATION,
        EPOCHS,
        FULL_NAME,
        HORIZONS_RECORD,
        ORBIT_SOLUTION_ID,
        PROVIDER_SPK_ID,
        _sun_table,
        _target_table,
    )
    from build_50a4_comet_fixture import (
        _digest,
        _document,
        build_fixture as build_numerical_fixture,
    )
    from build_50a5b_antisolar_fixture import (
        _comet_tail_rows,
        _sun_rows,
    )


RAW_FILES = {
    "sbdb": "sbdb-161p.json",
    "vectors": "horizons-vectors.json",
    "geocentric": "horizons-geocentric.json",
    "topocentric": "horizons-topocentric.json",
}
SPEC = {
    "raw_files": RAW_FILES,
    "designation": DESIGNATION,
    "kind": "cn",
    "provider_spk_id": PROVIDER_SPK_ID,
    "horizons_record": HORIZONS_RECORD,
    "orbit_solution_id": ORBIT_SOLUTION_ID,
    "required_model_parameters": frozenset({"A1", "A2"}),
    "spk_filename": "161p-hartley-iras.bsp",
    "key": "161p-hartley-iras",
    "name": "Hartley-IRAS",
    "iau_number": 161,
}


def build_fixture(raw_directory):
    """Parse inspected 161P evidence without network access or tolerances."""
    raw_directory = Path(raw_directory).expanduser().resolve()
    fixture = build_numerical_fixture(
        raw_directory, spec=SPEC, tolerances=None
    )
    record = fixture["objects"][0]
    record["aliases"] = [FULL_NAME, "Hartley-IRAS"]

    report = _document(raw_directory / "acquisition-report.json")
    evidence = {item["filename"]: item for item in report["evidence"]}
    sun_path = raw_directory / "horizons-sun-topocentric.json"
    tail_path = raw_directory / "horizons-comet-tail-topocentric.json"
    sun_document = _document(sun_path)
    tail_document = _document(tail_path)
    _sun_table(sun_document)
    _target_table(tail_document, "tail table", tail=True)
    for path in (sun_path, tail_path):
        if evidence[path.name]["sha256"] != _digest(path):
            raise ValueError(f"{path.name} differs from the acquisition report.")

    sun_epochs = _sun_rows(sun_document)
    tail_epochs = _comet_tail_rows(tail_document)
    numerical_epochs = {
        epoch["calendar"][:10]: epoch for epoch in record["epochs"]
    }
    expected_dates = tuple(value[:10] for value in EPOCHS)
    if (
        tuple(sun_epochs) != expected_dates
        or tuple(tail_epochs) != expected_dates
        or tuple(numerical_epochs) != expected_dates
    ):
        raise ValueError("161P numerical, Sun, and tail epochs do not match.")

    orientation_epochs = []
    for date in expected_dates:
        numerical = numerical_epochs[date]
        comet = numerical["topocentric"]
        sun = sun_epochs[date]
        tail = tail_epochs[date]
        comet_direction = [
            comet["apparent_ra_deg"], comet["apparent_dec_deg"]
        ]
        if [tail["apparent_ra_deg"], tail["apparent_dec_deg"]] != comet_direction:
            raise ValueError("161P tail row differs from its apparent direction.")
        sun_direction = [sun["apparent_ra_deg"], sun["apparent_dec_deg"]]
        orientation_epochs.append({
            "calendar_utc": numerical["calendar"],
            "comet_apparent_icrf_deg": comet_direction,
            "sun_apparent_icrf_deg": sun_direction,
            "horizons_psang_deg": tail["horizons_psang_deg"],
            "horizons_psamv_deg": tail["horizons_psamv_deg"],
            "calculated_antisolar_position_angle_deg": (
                antisolar_position_angle_deg(comet_direction, sun_direction)
            ),
            "antisolar_position_angle_deg": tail["horizons_psang_deg"],
        })

    fixture["authority"].update({
        "position_angle_convention": "degrees east of celestial north",
        "gas_tail_orientation": "Horizons quantity 27 PsAng",
        "dust_tail_diagnostic": "Horizons quantity 27 PsAMV",
    })
    fixture["antisolar"] = {
        "object": {
            "key": record["key"],
            "primary_designation": DESIGNATION,
            "provider_spk_id": PROVIDER_SPK_ID,
            "orbit_solution_id": ORBIT_SOLUTION_ID,
        },
        "tolerances": None,
        "source_evidence_sha256": {
            sun_path.name: evidence[sun_path.name]["sha256"],
            tail_path.name: evidence[tail_path.name]["sha256"],
        },
        "epochs": orientation_epochs,
    }
    return fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    fixture = build_fixture(arguments.raw_directory)
    arguments.output.write_text(
        json.dumps(fixture, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(arguments.output)


if __name__ == "__main__":
    main()
