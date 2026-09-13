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
    return parameters


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

    parameters = _sun_parameters(EPOCHS)
    document, url = _request(HORIZONS_API, parameters)
    signature = _signature(document, "NASA/JPL Horizons API")
    _table_result(document, "topocentric Sun")
    evidence = {
        **_write_json(output_directory / "horizons-sun-topocentric.json", document),
        "request_url": url,
    }
    report = {
        "purpose": "Wenu Milestone 50A.5B raw antisolar-direction evidence",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "target": {"name": "Sun", "horizons_command": "10;"},
        "observer": OBSERVER,
        "epochs_utc": EPOCHS,
        "policy": {
            "reference_system": "ICRF",
            "apparent": "AIRLESS",
            "quantities": [1, 45],
            "position_angle_convention": "degrees east of celestial north",
        },
        "authority": {
            "source": signature["source"],
            "version": signature["version"],
        },
        "comet_reference": {
            "filename": comet_reference.name,
            "sha256": COMET_REFERENCE_SHA256,
        },
        "evidence": [evidence],
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
