"""Acquire immutable SBDB/Horizons identity evidence for 161P."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

from wenu.observer import DEFAULT_DATA_DIRECTORY

try:
    from tools.acquire_50a4_comet_evidence import (
        HORIZONS_API,
        SBDB_API,
        _request,
        _signature,
        _write_json,
    )
except ModuleNotFoundError as error:
    if error.name != "tools":
        raise
    from acquire_50a4_comet_evidence import (
        HORIZONS_API,
        SBDB_API,
        _request,
        _signature,
        _write_json,
    )


DESIGNATION = "161P"
FULL_NAME_TOKEN = "Hartley-IRAS"


def _sbdb_identity(document):
    """Return unmodified SBDB identity records after bounded checks."""
    signature = _signature(
        document, "NASA/JPL Small-Body Database (SBDB) API"
    )
    obj = document.get("object")
    orbit = document.get("orbit")
    if not isinstance(obj, dict) or not isinstance(orbit, dict):
        raise ValueError("SBDB response has no object/orbit identity.")
    if obj.get("des") != DESIGNATION or obj.get("kind") != "cn":
        raise ValueError("SBDB did not return numbered comet 161P.")
    if FULL_NAME_TOKEN.casefold() not in str(obj.get("fullname", "")).casefold():
        raise ValueError("SBDB did not return 161P/Hartley-IRAS.")
    if not str(obj.get("spkid", "")).lstrip("-").isdigit():
        raise ValueError("SBDB returned no numeric comet SPK ID.")
    if not orbit.get("orbit_id"):
        raise ValueError("SBDB returned no orbit solution identifier.")
    parameters = orbit.get("model_pars")
    if parameters is not None and not isinstance(parameters, list):
        raise ValueError("SBDB model parameters are not a list or null.")
    return signature, obj, orbit


def _horizons_identity(document):
    """Retain either a unique identity or the provider's selection table."""
    signature = _signature(document, "NASA/JPL Horizons API")
    result = document.get("result")
    if document.get("error") or not isinstance(result, str):
        diagnostic = document.get("error") or result or "missing result"
        raise ValueError(f"Horizons 161P identity query failed: {diagnostic}")
    folded = result.casefold()
    if "161p" not in folded or "hartley-iras" not in folded:
        raise ValueError("Horizons did not identify 161P/Hartley-IRAS.")
    return signature, result


def _horizons_parameters():
    return {
        "format": "json",
        "COMMAND": f"'{DESIGNATION}'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'NO'",
    }


def acquire(output_directory):
    """Acquire discovery-only identity evidence without selecting an orbit."""
    output_directory = Path(output_directory).expanduser().resolve()
    if output_directory.exists() and any(output_directory.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite 50A.5C identity evidence in "
            f"{output_directory}"
        )

    sbdb_parameters = {
        "des": DESIGNATION,
        "full-prec": "true",
        "alt-des": "true",
        "alt-orbits": "true",
        "cov": "mat",
        "phys-par": "true",
    }
    sbdb, sbdb_url = _request(SBDB_API, sbdb_parameters)
    sbdb_signature, obj, orbit = _sbdb_identity(sbdb)
    horizons, horizons_url = _request(
        HORIZONS_API, _horizons_parameters()
    )
    horizons_signature, _ = _horizons_identity(horizons)

    output_directory.mkdir(parents=True, exist_ok=True)
    evidence = [
        {
            **_write_json(output_directory / "sbdb-161p.json", sbdb),
            "request_url": sbdb_url,
        },
        {
            **_write_json(
                output_directory / "horizons-161p-identity.json", horizons
            ),
            "request_url": horizons_url,
        },
    ]
    report = {
        "purpose": "Wenu Milestone 50A.5C 161P identity discovery",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "requested_designation": DESIGNATION,
        "object": {
            "designation": obj["des"],
            "fullname": obj.get("fullname"),
            "kind": obj["kind"],
            "spk_id": str(obj["spkid"]),
            "orbit_id": orbit["orbit_id"],
            "solution_date": orbit.get("soln_date"),
            "model_parameters": orbit.get("model_pars"),
        },
        "authority": {
            "sbdb": sbdb_signature,
            "horizons": horizons_signature,
        },
        "evidence": evidence,
        "next_action": (
            "inspect the complete SBDB object/orbit blocks and Horizons "
            "identity or record-selection result before selecting a record"
        ),
    }
    report_path = output_directory / "acquisition-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=(
            DEFAULT_DATA_DIRECTORY
            / "minor_bodies"
            / "50a5c-161p-identity-raw"
        ),
    )
    arguments = parser.parse_args()
    print(acquire(arguments.output_directory))


if __name__ == "__main__":
    main()
