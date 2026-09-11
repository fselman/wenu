"""Acquire explicit offline Horizons resources for numbered asteroids."""

from __future__ import annotations

import argparse
import base64
import json
import re
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"
SBDB_API = "https://ssd-api.jpl.nasa.gov/sbdb.api"
_HEADER = re.compile(r"JPL/HORIZONS\s+(?P<number>\d+)(?:\s+(?P<name>.*?))?\s*\((?P<designation>[^)]+)\)")


def _number(value):
    text = str(value).strip()
    if not text.isdecimal() or int(text) <= 0:
        raise argparse.ArgumentTypeError(
            "asteroid identifiers must be positive permanent numbers"
        )
    return int(text)


def _json(url, parameters, *, timeout=120):
    with urlopen(url + "?" + urlencode(parameters), timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _horizons_identity(result, expected_number):
    match = _HEADER.search(result)
    if match is None or int(match.group("number")) != expected_number:
        raise ValueError("Horizons result does not identify the requested number.")
    if "ASTEROID comments:" not in result:
        raise ValueError("Horizons result is not an asteroid solution.")
    name = (match.group("name") or "").strip() or None
    designation = match.group("designation").strip()
    solution = re.search(r"soln ref\.=(?P<value>[^,\n]+)", result)
    solution_date = re.search(r"Soln\.date:\s*(?P<value>\S+)", result)
    epoch = re.search(r"EPOCH=\s*(?P<value>\S+).*?\((?P<scale>[^)]+)\)", result)
    if solution is None or solution_date is None or epoch is None:
        raise ValueError("Horizons result lacks required orbit-solution identity.")
    return {
        "name": name,
        "primary_designation": designation,
        "orbit_solution_id": solution.group("value").strip(),
        "solution_date": solution_date.group("value"),
        "osculating_epoch": f"{epoch.group('value')} {epoch.group('scale')}",
    }


def _download(number, start, stop):
    parameters = {
        "format": "json", "COMMAND": f"'{number};'", "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'YES'", "EPHEM_TYPE": "'SPK'",
        "START_TIME": f"'{start}'", "STOP_TIME": f"'{stop}'",
    }
    document = _json(HORIZONS_API, parameters)
    signature = document.get("signature")
    if not isinstance(signature, dict) or signature.get("source") != "NASA/JPL Horizons API":
        raise ValueError("Horizons response has no accepted API signature.")
    identity = _horizons_identity(document.get("result", ""), number)
    try:
        payload = base64.b64decode(
            "".join(document["spk"].split()).encode("ascii"), validate=True
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Horizons response has no valid SPK payload.") from error
    if not payload.startswith(b"DAF/"):
        raise ValueError("Horizons payload is not a binary DAF/SPK file.")
    target = str(document.get("spk_file_id"))
    sbdb = _json(SBDB_API, {"sstr": str(number), "full-prec": "true"})
    obj = sbdb.get("object", {})
    if str(obj.get("spkid")) != target or str(obj.get("des")) != str(number):
        raise ValueError("SBDB and Horizons asteroid identities differ.")
    orbit_class = obj.get("orbit_class", {})
    identity["classifications"] = tuple(
        value for value in (orbit_class.get("code"), orbit_class.get("name"))
        if isinstance(value, str) and value.strip()
    )
    return document, payload, identity, target


def acquire(numbers, output_directory, *, start="2025-01-01", stop="2030-01-01"):
    """Acquire a new immutable numbered-asteroid collection."""
    output_directory = Path(output_directory).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    manifest = output_directory / "acquisition-report.json"
    if manifest.exists() or any(output_directory.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite minor-body resources in {output_directory}"
        )
    records = []
    for number in numbers:
        document, payload, identity, target = _download(number, start, stop)
        filename = f"{number}-{identity['orbit_solution_id'].lower().replace('#', '')}-{start[:4]}-{stop[:4]}.bsp"
        path = output_directory / filename
        path.write_bytes(payload)
        records.append({
            "key": str(number), "filename": filename,
            "sha256": sha256(payload).hexdigest(), "bytes": len(payload),
            "spk_file_id": target, "horizons_result": document["result"],
            "identity": {
                "permanent_number": number,
                "primary_designation": identity["primary_designation"],
                "name": identity["name"], "object_class": "asteroid",
                "provider_spk_id": target,
                "classifications": list(identity["classifications"]),
            },
            "solution": {
                "provider": "NASA/JPL Horizons API",
                "service_version": str(document["signature"].get("version", "unknown")),
                "object_class": "asteroid",
                "primary_designation": identity["primary_designation"],
                "horizons_command": f"{number};", "provider_spk_id": target,
                "orbit_solution_id": identity["orbit_solution_id"],
                "solution_date": identity["solution_date"],
                "osculating_epoch": identity["osculating_epoch"],
                "reference_system": "ICRF/J2000",
                "provenance": ["Horizons SPK and SBDB identity acquired explicitly"],
            },
        })
    manifest.write_text(
        json.dumps({"purpose": "Wenu installed numbered asteroids", "resources": records}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("numbers", nargs="+", type=_number)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--stop", default="2030-01-01")
    arguments = parser.parse_args()
    print(acquire(arguments.numbers, arguments.output_directory, start=arguments.start, stop=arguments.stop))


if __name__ == "__main__":
    main()
