"""Build the compact offline 50A.5B antisolar-direction oracle."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path

from wenu.antisolar import (
    antisolar_position_angle_deg,
)

try:
    from tools.acquire_50a5b_antisolar_evidence import (
        COMET_REFERENCE_SHA256,
        _sun_table_identity,
    )
    from tools.build_50a4_comet_fixture import _calendar, _data_rows, _number
except ModuleNotFoundError as error:
    if error.name != "tools":
        raise
    from acquire_50a5b_antisolar_evidence import (
        COMET_REFERENCE_SHA256,
        _sun_table_identity,
    )
    from build_50a4_comet_fixture import _calendar, _data_rows, _number


def _digest(path):
    return sha256(path.read_bytes()).hexdigest()


def _document(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain one JSON object.")
    return value


def _sun_rows(document):
    records = {}
    for row in _data_rows(document, "topocentric Sun observer table", 7):
        calendar = _calendar(row[0])
        records[calendar[:10]] = {
            "calendar_utc": calendar,
            "astrometric_ra_deg": _number(row[3]),
            "astrometric_dec_deg": _number(row[4]),
            "apparent_ra_deg": _number(row[5]),
            "apparent_dec_deg": _number(row[6]),
        }
    return records


def build_fixture(raw_directory, comet_reference):
    """Combine independent Sun evidence with accepted comet directions."""
    raw_directory = Path(raw_directory).expanduser().resolve()
    comet_reference = Path(comet_reference).expanduser().resolve(strict=True)
    if _digest(comet_reference) != COMET_REFERENCE_SHA256:
        raise ValueError("comet reference is not the accepted 50A.4 oracle.")
    comet = _document(comet_reference)
    report = _document(raw_directory / "acquisition-report.json")
    sun_path = raw_directory / "horizons-sun-topocentric.json"
    sun_document = _document(sun_path)
    signature = sun_document.get("signature", {})
    if signature.get("source") != "NASA/JPL Horizons API":
        raise ValueError("Sun response has no accepted Horizons signature.")
    _sun_table_identity(sun_document)
    evidence = {item["filename"]: item for item in report["evidence"]}
    if evidence[sun_path.name]["sha256"] != _digest(sun_path):
        raise ValueError("Sun evidence differs from the acquisition report.")
    if report["comet_reference"]["sha256"] != COMET_REFERENCE_SHA256:
        raise ValueError("acquisition report names another comet reference.")

    comet_record = comet["objects"][0]
    comet_epochs = {
        epoch["calendar"][:10]: epoch for epoch in comet_record["epochs"]
    }
    sun_epochs = _sun_rows(sun_document)
    expected_dates = tuple(value[:10] for value in report["epochs_utc"])
    if tuple(sun_epochs) != expected_dates or tuple(comet_epochs) != expected_dates:
        raise ValueError("Sun and comet evidence epochs do not match.")
    epochs = []
    for date in expected_dates:
        comet_apparent = comet_epochs[date]["topocentric"]
        sun_apparent = sun_epochs[date]
        comet_direction = [
            comet_apparent["apparent_ra_deg"],
            comet_apparent["apparent_dec_deg"],
        ]
        sun_direction = [
            sun_apparent["apparent_ra_deg"],
            sun_apparent["apparent_dec_deg"],
        ]
        epochs.append({
            "calendar_utc": comet_epochs[date]["calendar"],
            "comet_apparent_icrf_deg": comet_direction,
            "sun_apparent_icrf_deg": sun_direction,
            "antisolar_position_angle_deg": antisolar_position_angle_deg(
                comet_direction, sun_direction
            ),
        })
    return {
        "authority": {
            "horizons_api": signature["source"],
            "horizons_version": signature["version"],
            "reference_system": "ICRF",
            "apparent_policy": "AIRLESS",
            "position_angle_convention": "degrees east of celestial north",
        },
        "observer": report["observer"],
        "object": {
            "key": "2p-encke",
            "primary_designation": "2P",
            "provider_spk_id": "1000025",
            "orbit_solution_id": "K273/14",
        },
        "source_evidence_sha256": {
            comet_reference.name: COMET_REFERENCE_SHA256,
            sun_path.name: evidence[sun_path.name]["sha256"],
        },
        "tolerances": None,
        "epochs": epochs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-directory", type=Path, required=True)
    parser.add_argument("--comet-reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    fixture = build_fixture(arguments.raw_directory, arguments.comet_reference)
    arguments.output.write_text(
        json.dumps(fixture, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(arguments.output)


if __name__ == "__main__":
    main()
