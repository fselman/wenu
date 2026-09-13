"""Acquire the missing direct-Horizons Sun evidence for 50A.5B."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from wenu.observer import DEFAULT_DATA_DIRECTORY

try:
    from tools.acquire_50a4_comet_evidence import (
        HORIZONS_API,
        OBSERVER,
        _horizons_parameters,
        _request,
        _signature,
        _table_result,
        _write_json,
    )
except ModuleNotFoundError as error:
    if error.name != "tools":
        raise
    from acquire_50a4_comet_evidence import (
        HORIZONS_API,
        OBSERVER,
        _horizons_parameters,
        _request,
        _signature,
        _table_result,
        _write_json,
    )


EPOCHS = (
    "2026-11-13T00:00:00Z",
    "2027-02-11T00:00:00Z",
    "2027-05-12T00:00:00Z",
)
HORIZONS_RECORD = "90000091"
COMET_REFERENCE_SHA256 = (
    "d440eb4b7a56ed4aff79cd062308e8a81463afec5c6055517865c5c033abb4e1"
)


def _digest(path):
    return sha256(path.read_bytes()).hexdigest()


def _sun_parameters(epochs):
    parameters = _horizons_parameters(
        "observer", epochs, "10", topocentric=True
    )
    parameters["QUANTITIES"] = "'1,45'"
    parameters["COMMAND"] = "'10'"
    return parameters


def _comet_tail_parameters(epochs):
    """Request provider gas/dust-tail angles and apparent comet direction."""
    parameters = _horizons_parameters(
        "observer", epochs, HORIZONS_RECORD, topocentric=True
    )
    parameters["QUANTITIES"] = "'27,45'"
    return parameters


def _sun_table_identity(document):
    result = _table_result(document, "topocentric Sun")
    if "Target body name: Sun (10)" not in result:
        raise ValueError("Horizons did not return the Sun (NAIF 10).")
    return result


def _comet_tail_table_identity(document):
    result = _table_result(document, "topocentric 2P/Encke tail")
    if (
        "Target body name: 2P/Encke" not in result
        or "JPL#K273/14" not in result
        or "PsAng" not in result
        or "PsAMV" not in result
    ):
        raise ValueError(
            "Horizons did not return 2P/Encke K273/14 with PsAng/PsAMV."
        )
    return result


def acquire(output_directory, *, comet_reference):
    """Acquire one immutable Sun table tied to the accepted comet oracle."""
    output_directory = Path(output_directory).expanduser().resolve()
    comet_reference = Path(comet_reference).expanduser().resolve(strict=True)
    if _digest(comet_reference) != COMET_REFERENCE_SHA256:
        raise ValueError("comet reference is not the accepted 50A.4 oracle.")
    output_directory.mkdir(parents=True, exist_ok=True)
    if any(output_directory.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite 50A.5B evidence in {output_directory}"
        )

    requests = (
        (
            "horizons-sun-topocentric.json",
            _sun_parameters(EPOCHS),
            _sun_table_identity,
        ),
        (
            "horizons-comet-tail-topocentric.json",
            _comet_tail_parameters(EPOCHS),
            _comet_tail_table_identity,
        ),
    )
    evidence = []
    signature = None
    for filename, parameters, identity in requests:
        document, url = _request(HORIZONS_API, parameters)
        current_signature = _signature(document, "NASA/JPL Horizons API")
        identity(document)
        if signature is not None and current_signature != signature:
            raise ValueError("Horizons evidence signatures do not match.")
        signature = current_signature
        evidence.append({
            **_write_json(output_directory / filename, document),
            "request_url": url,
        })
    report = {
        "purpose": "Wenu Milestone 50A.5B raw antisolar-direction evidence",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "targets": (
            {"name": "Sun", "horizons_command": "10"},
            {
                "name": "2P/Encke",
                "horizons_record": HORIZONS_RECORD,
                "solution": "K273/14",
            },
        ),
        "observer": OBSERVER,
        "epochs_utc": EPOCHS,
        "policy": {
            "reference_system": "ICRF",
            "apparent": "AIRLESS",
            "sun_quantities": [1, 45],
            "comet_quantities": [27, 45],
            "position_angle_convention": "degrees east of celestial north",
            "gas_tail_authority": "Horizons PsAng",
            "dust_tail_diagnostic": "Horizons PsAMV",
        },
        "authority": {
            "source": signature["source"],
            "version": signature["version"],
        },
        "comet_reference": {
            "filename": comet_reference.name,
            "sha256": COMET_REFERENCE_SHA256,
        },
        "evidence": evidence,
    }
    report_path = output_directory / "acquisition-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comet-reference", type=Path, required=True)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=(
            DEFAULT_DATA_DIRECTORY / "minor_bodies" / "50a5b-antisolar-raw"
        ),
    )
    arguments = parser.parse_args()
    print(acquire(
        arguments.output_directory,
        comet_reference=arguments.comet_reference,
    ))


if __name__ == "__main__":
    main()
