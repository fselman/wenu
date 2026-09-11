"""Explicitly acquire the bounded Horizons SPKs used by Milestone 50A.2."""

from __future__ import annotations

import argparse
import base64
import json
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from wenu.observer import DEFAULT_DATA_DIRECTORY

HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"
REQUESTS = (
    {
        "key": "ceres",
        "filename": "ceres-jpl48-2025-2030.bsp",
        "spk_id": "20000001",
        "parameters": {
            "format": "json",
            "COMMAND": "'1;'",
            "OBJ_DATA": "'YES'",
            "MAKE_EPHEM": "'YES'",
            "EPHEM_TYPE": "'SPK'",
            "START_TIME": "'2025-01-01'",
            "STOP_TIME": "'2030-01-01'",
        },
    },
    {
        "key": "apophis",
        "filename": "apophis-jpl220-2028-2030.bsp",
        "spk_id": "20099942",
        "parameters": {
            "format": "json",
            "COMMAND": "'99942;'",
            "OBJ_DATA": "'YES'",
            "MAKE_EPHEM": "'YES'",
            "EPHEM_TYPE": "'SPK'",
            "START_TIME": "'2028-01-01'",
            "STOP_TIME": "'2030-01-01'",
        },
    },
)


def _download(request, *, timeout=120):
    url = HORIZONS_API + "?" + urlencode(request["parameters"])
    with urlopen(url, timeout=timeout) as response:
        document = json.loads(response.read().decode("utf-8"))
    signature = document.get("signature")
    if not isinstance(signature, dict) or signature.get("source") != (
        "NASA/JPL Horizons API"
    ):
        raise ValueError("Horizons response has no accepted API signature.")
    if str(document.get("spk_file_id")) != request["spk_id"]:
        raise ValueError("Horizons returned an unexpected SPK target ID.")
    try:
        payload = base64.b64decode(document["spk"], validate=True)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            "Horizons response has no valid SPK payload."
        ) from error
    if not payload.startswith(b"DAF/"):
        raise ValueError("Horizons payload is not a binary DAF/SPK file.")
    return document, payload, url


def acquire(output_directory):
    """Acquire both resources without overwriting an existing evidence set."""
    output_directory = Path(output_directory).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    paths = tuple(
        output_directory / request["filename"] for request in REQUESTS
    )
    manifest_path = output_directory / "acquisition-report.json"
    existing = tuple(
        path for path in paths + (manifest_path,) if path.exists()
    )
    if existing:
        names = ", ".join(path.name for path in existing)
        raise FileExistsError(
            f"refusing to overwrite existing 50A.2 evidence: {names}"
        )

    downloads = []
    for request, path in zip(REQUESTS, paths):
        document, payload, url = _download(request)
        downloads.append((request, path, document, payload, url))

    records = []
    for request, path, document, payload, url in downloads:
        path.write_bytes(payload)
        records.append(
            {
                "key": request["key"],
                "filename": path.name,
                "sha256": sha256(payload).hexdigest(),
                "bytes": len(payload),
                "spk_file_id": request["spk_id"],
                "request_url": url,
                "signature": document["signature"],
                "horizons_result": document.get("result", ""),
            }
        )
    report = {
        "purpose": "Wenu Milestone 50A.2 bounded asteroid validation",
        "resources": records,
    }
    manifest_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY / "minor_bodies" / "50a2",
    )
    arguments = parser.parse_args()
    report = acquire(arguments.output_directory)
    print(report)


if __name__ == "__main__":
    main()
