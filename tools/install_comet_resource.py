"""Install one accepted compact comet fixture as an offline resource."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from wenu.comet_designations import parse_comet_designation
from wenu.minor_body_ephemeris import SpiceMinorBodyKernel


def _digest(path):
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _document(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON evidence: {path}") from error


def _model_parameters(parameters):
    return {
        value["name"]: json.dumps(
            value, sort_keys=True, separators=(",", ":")
        )
        for value in parameters
    }


def _safe_filename(record):
    solution = "".join(
        character if character.isalnum() else "-"
        for character in record["orbit_solution_id"].casefold()
    ).strip("-")
    years = sorted({epoch["calendar"][:4] for epoch in record["epochs"]})
    return "-".join((record["key"], solution, *years)) + ".bsp"


def _validate_sources(raw_directory, fixture, record):
    declared = {
        **record["source_evidence_sha256"],
        **fixture["antisolar"]["source_evidence_sha256"],
    }
    for filename, expected in declared.items():
        path = (raw_directory / filename).resolve(strict=True)
        if path.parent != raw_directory or _digest(path) != expected:
            raise ValueError(f"raw evidence digest differs for {filename}.")
    spk = record["spk"]
    path = (raw_directory / spk["filename"]).resolve(strict=True)
    if path.parent != raw_directory or _digest(path) != spk["sha256"]:
        raise ValueError("comet SPK digest differs from the compact fixture.")
    with SpiceMinorBodyKernel(path) as kernel:
        matching = tuple(
            segment for segment in kernel.segments
            if segment.target == int(record["provider_spk_id"])
        )
        if len(matching) != 1:
            raise ValueError("comet SPK must contain exactly one target segment.")
        segment = matching[0]
        if (
            segment.center != spk["segment_centre_id"]
            or segment.data_type != spk["segment_type"]
            or segment.frame_id != 1
            or segment.start_jd != spk["coverage_start_jd_tdb"]
            or segment.end_jd != spk["coverage_end_jd_tdb"]
        ):
            raise ValueError("comet SPK segment differs from the compact fixture.")
    return path


def install(fixture_path, raw_directory, output_directory, *, filename=None):
    """Validate and atomically publish one fixture-bound comet resource."""
    fixture_path = Path(fixture_path).expanduser().resolve(strict=True)
    raw_directory = Path(raw_directory).expanduser().resolve(strict=True)
    output_directory = Path(output_directory).expanduser().resolve()
    if output_directory.exists():
        raise FileExistsError(
            f"refusing to overwrite comet resources in {output_directory}"
        )
    fixture = _document(fixture_path)
    records = fixture.get("objects")
    if not isinstance(records, list) or len(records) != 1:
        raise ValueError("compact comet fixture must contain exactly one object.")
    record = records[0]
    if record.get("class") != "comet":
        raise ValueError("compact fixture object must be a comet.")
    parsed = parse_comet_designation(record["primary_designation"])
    if parsed.permanent_number != record.get("iau_number"):
        raise ValueError("comet designation and permanent number differ.")
    if not record.get("name"):
        raise ValueError("installed comet fixture requires an official name.")
    if not fixture.get("tolerances") or not fixture.get("antisolar", {}).get(
        "tolerances"
    ):
        raise ValueError("installed comet fixture requires accepted tolerances.")
    source = _validate_sources(raw_directory, fixture, record)

    topocentric = raw_directory / "horizons-topocentric.json"
    topocentric_result = _document(topocentric).get("result", "")
    for expected in (
        record["primary_designation"],
        f"JPL#{record['orbit_solution_id']}",
    ):
        if expected not in topocentric_result:
            raise ValueError("topocentric evidence has different comet identity.")
    date_match = re.search(r"Soln\.date:\s*(\S+)", topocentric_result)
    if date_match is None:
        raise ValueError("topocentric evidence lacks the solution date.")

    aliases = list(record.get("aliases", ()))
    canonical = f"{parsed.canonical}/{record['name']}"
    if canonical not in aliases or record["name"] not in aliases:
        raise ValueError("comet fixture must preserve canonical exact aliases.")
    classifications = ["comet"]
    if parsed.designation_class == "P":
        classifications.append("periodic_comet")
    destination_name = filename or _safe_filename(record)
    if Path(destination_name).name != destination_name:
        raise ValueError("installed SPK filename must be a plain filename.")
    spk = record["spk"]
    manifest_record = {
        "key": parsed.canonical.casefold(),
        "filename": destination_name,
        "sha256": spk["sha256"],
        "bytes": source.stat().st_size,
        "spk_file_id": record["provider_spk_id"],
        "horizons_result": topocentric_result,
        "actual_coverage": {
            "start_jd_tdb": spk["coverage_start_jd_tdb"],
            "stop_jd_tdb": spk["coverage_end_jd_tdb"],
        },
        "identity": {
            "primary_designation": parsed.canonical,
            "designation_class": parsed.designation_class,
            "permanent_number": parsed.permanent_number,
            "name": record["name"],
            "object_class": "comet",
            "provider_spk_id": record["provider_spk_id"],
            "classifications": classifications,
        },
        "solution": {
            "provider": fixture["authority"]["horizons_api"],
            "service_version": fixture["authority"]["horizons_version"],
            "object_class": "comet",
            "primary_designation": parsed.canonical,
            "horizons_command": record["horizons_command"],
            "provider_spk_id": record["provider_spk_id"],
            "orbit_solution_id": record["orbit_solution_id"],
            "solution_date": date_match.group(1),
            "osculating_epoch": record["osculating_epoch"],
            "reference_system": record["reference_system"],
            "aliases": aliases,
            "model_parameters": _model_parameters(record["model_parameters"]),
            "quality_fields": {
                key: "null" if value is None else str(value)
                for key, value in record["quality_fields"].items()
            },
            "provenance": [
                "offline conversion of an accepted Wenu compact comet fixture",
                f"fixture SHA-256: {_digest(fixture_path)}",
            ],
        },
        "provider_gas_tail_position_angles": [
            {
                "calendar_utc": epoch["calendar_utc"],
                "position_angle_deg": epoch["horizons_psang_deg"],
            }
            for epoch in fixture["antisolar"]["epochs"]
        ],
        "receipt": {
            "installed_at_utc": datetime.now(UTC).isoformat(),
            "source_directory": str(raw_directory),
            "source_fixture": str(fixture_path),
            "source_evidence_sha256": record["source_evidence_sha256"],
        },
    }
    document = {
        "purpose": f"Wenu installed {canonical} production resource",
        "resources": [manifest_record],
    }
    output_directory.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix=f".{output_directory.name}-", dir=output_directory.parent
    ) as temporary:
        staging = Path(temporary) / output_directory.name
        staging.mkdir()
        shutil.copyfile(source, staging / destination_name)
        manifest = staging / "acquisition-report.json"
        manifest.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        staging.replace(output_directory)
    return output_directory / "acquisition-report.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--raw-directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--filename")
    arguments = parser.parse_args()
    print(install(
        arguments.fixture,
        arguments.raw_directory,
        arguments.output_directory,
        filename=arguments.filename,
    ))


if __name__ == "__main__":
    main()
