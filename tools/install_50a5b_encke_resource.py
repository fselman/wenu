"""Install accepted 2P/Encke evidence as an offline production resource."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from wenu.observer import DEFAULT_DATA_DIRECTORY

try:
    from tools.build_50a4_comet_fixture import build_fixture
except ModuleNotFoundError as error:
    if error.name != "tools":
        raise
    from build_50a4_comet_fixture import build_fixture


EXPECTED_SPK_SHA256 = (
    "6d83534f66d06490449851f1255c1a624d6cd4a4658716478edd41ee9448507b"
)


def _model_parameters(parameters):
    return {
        value["name"]: json.dumps(
            value, sort_keys=True, separators=(",", ":")
        )
        for value in parameters
    }


def install(raw_directory, output_directory):
    """Convert inspected raw evidence without network access or mutation."""
    raw_directory = Path(raw_directory).expanduser().resolve(strict=True)
    output_directory = Path(output_directory).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    if any(output_directory.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite Encke resources in {output_directory}"
        )
    fixture = build_fixture(raw_directory)
    record = fixture["objects"][0]
    spk = record["spk"]
    if (
        record["primary_designation"] != "2P"
        or record["provider_spk_id"] != "1000025"
        or record["orbit_solution_id"] != "K273/14"
        or spk["sha256"] != EXPECTED_SPK_SHA256
        or spk["segment_type"] != 21
        or spk["segment_centre_id"] != 10
    ):
        raise ValueError("raw evidence is not the accepted Encke resource.")
    names = {value["name"] for value in record["model_parameters"]}
    if not {"A1", "A2"}.issubset(names):
        raise ValueError("Encke resource must preserve A1 and A2.")

    source = raw_directory / spk["filename"]
    destination = output_directory / "2p-encke-k273-14-2026-2027.bsp"
    shutil.copyfile(source, destination)
    identity_document = json.loads(
        (raw_directory / "horizons-topocentric.json").read_text(
            encoding="utf-8"
        )
    )
    manifest_record = {
        "key": "2p",
        "filename": destination.name,
        "sha256": spk["sha256"],
        "bytes": destination.stat().st_size,
        "spk_file_id": record["provider_spk_id"],
        "horizons_result": identity_document.get("result", ""),
        "actual_coverage": {
            "start_jd_tdb": spk["coverage_start_jd_tdb"],
            "stop_jd_tdb": spk["coverage_end_jd_tdb"],
        },
        "identity": {
            "primary_designation": "2P",
            "designation_class": "P",
            "permanent_number": 2,
            "name": "Encke",
            "object_class": "comet",
            "provider_spk_id": record["provider_spk_id"],
            "classifications": ["comet", "periodic_comet"],
        },
        "solution": {
            "provider": "NASA/JPL Horizons API",
            "service_version": fixture["authority"]["horizons_version"],
            "object_class": "comet",
            "primary_designation": "2P",
            "horizons_command": record["horizons_command"],
            "provider_spk_id": record["provider_spk_id"],
            "orbit_solution_id": record["orbit_solution_id"],
            "solution_date": "2026-Sep-08_14:23:39",
            "osculating_epoch": record["osculating_epoch"],
            "reference_system": record["reference_system"],
            "aliases": ["2P/Encke", "Encke"],
            "model_parameters": _model_parameters(
                record["model_parameters"]
            ),
            "quality_fields": {
                key: "null" if value is None else str(value)
                for key, value in record["quality_fields"].items()
            },
            "provenance": [
                "offline conversion of accepted Wenu 50A.4 evidence"
            ],
        },
        "receipt": {
            "installed_at_utc": datetime.now(UTC).isoformat(),
            "source_directory": str(raw_directory),
            "source_evidence_sha256": record["source_evidence_sha256"],
        },
    }
    manifest = output_directory / "acquisition-report.json"
    manifest.write_text(
        json.dumps(
            {
                "purpose": "Wenu installed 2P/Encke production resource",
                "resources": [manifest_record],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-directory", type=Path, required=True)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY / "minor_bodies" / "2p-encke",
    )
    arguments = parser.parse_args()
    print(install(arguments.raw_directory, arguments.output_directory))


if __name__ == "__main__":
    main()
