"""Acquire immutable raw JPL evidence for 50A.4 comet validation."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlencode
from urllib.request import urlopen

from astropy.time import Time

from wenu.minor_body_ephemeris import SpiceMinorBodyKernel
from wenu.observer import DEFAULT_DATA_DIRECTORY


HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"
SBDB_API = "https://ssd-api.jpl.nasa.gov/sbdb.api"
DESIGNATION = "2P"
OBSERVER = {
    "name": "La Ligua",
    "longitude_deg_east": -71.230289,
    "latitude_deg": -32.443342,
    "elevation_km": 0.052,
}


def _request(url, parameters, *, timeout=120):
    request_url = url + "?" + urlencode(parameters)
    with urlopen(request_url, timeout=timeout) as response:
        document = json.loads(response.read().decode("utf-8"))
    return document, request_url


def _signature(document, source):
    signature = document.get("signature")
    if not isinstance(signature, dict) or signature.get("source") != source:
        raise ValueError(f"response has no accepted {source} signature.")
    return signature


def _model_parameters(orbit):
    parameters = orbit.get("model_pars")
    if not isinstance(parameters, list):
        raise ValueError("SBDB orbit has no model-parameter list.")
    names = {
        str(value.get("name", "")).upper()
        for value in parameters
        if isinstance(value, dict)
    }
    if not names.intersection({"A1", "A2", "A3", "DT"}):
        raise ValueError(
            "2P solution declares no accepted non-gravitational parameter."
        )
    return parameters


def _sbdb_identity(document):
    _signature(document, "NASA/JPL Small-Body Database (SBDB) API")
    obj = document.get("object", {})
    orbit = document.get("orbit", {})
    if obj.get("des") != DESIGNATION or obj.get("kind") != "cn":
        raise ValueError("SBDB did not return numbered comet 2P.")
    if not str(obj.get("spkid", "")).lstrip("-").isdigit():
        raise ValueError("SBDB returned no numeric comet SPK ID.")
    _model_parameters(orbit)
    perihelion = next(
        (
            value.get("value")
            for value in orbit.get("elements", ())
            if isinstance(value, dict) and value.get("name") == "tp"
        ),
        None,
    )
    if perihelion is None:
        raise ValueError("SBDB orbit has no perihelion epoch.")
    return obj, orbit, float(perihelion)


def _epochs(perihelion_jd_tdb):
    middle = Time(perihelion_jd_tdb, format="jd", scale="tdb").utc.to_datetime(
        timezone=timezone.utc
    )
    middle = middle.replace(hour=0, minute=0, second=0, microsecond=0)
    return tuple(
        (middle + timedelta(days=offset)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for offset in (-90, 0, 90)
    )


def _horizons_parameters(kind, epochs, *, topocentric=False):
    common = {
        "format": "json",
        "COMMAND": f"'{DESIGNATION};'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'YES'",
        "TLIST": ",".join(
            f"'{value.removesuffix('Z')}'" for value in epochs
        ),
        "TLIST_TYPE": "'CAL'",
        "TIME_DIGITS": "'FRACSEC'",
        "CSV_FORMAT": "'YES'",
    }
    if kind == "vectors":
        return {
            **common,
            "EPHEM_TYPE": "'VECTORS'",
            "CENTER": "'@0'",
            "REF_PLANE": "'FRAME'",
            "REF_SYSTEM": "'ICRF'",
            "VEC_CORR": "'NONE'",
            "VEC_TABLE": "'2'",
            "OUT_UNITS": "'AU-D'",
            "TIME_TYPE": "'TDB'",
        }
    centre = "'coord@399'" if topocentric else "'500@399'"
    parameters = {
        **common,
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": centre,
        "REF_SYSTEM": "'ICRF'",
        "CAL_FORMAT": "'CAL'",
        "ANG_FORMAT": "'DEG'",
        "APPARENT": "'AIRLESS'",
        "QUANTITIES": "'1,20,21,45'",
        "RANGE_UNITS": "'AU'",
        "TIME_TYPE": "'UT'",
    }
    if topocentric:
        parameters.update({
            "COORD_TYPE": "'GEODETIC'",
            "SITE_COORD": (
                "'-71.230289,-32.443342,0.052'"
            ),
        })
    return parameters


def _digest(payload):
    return sha256(payload).hexdigest()


def _write_json(path, document):
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(payload)
    return {"filename": path.name, "bytes": len(payload), "sha256": _digest(payload)}


def _spk_identity(payload, expected_target):
    """Read authoritative target identity from the returned SPK segment."""
    with TemporaryDirectory(prefix="wenu-50a4-spk-") as directory:
        path = Path(directory) / "2p-encke.bsp"
        path.write_bytes(payload)
        with SpiceMinorBodyKernel(path) as kernel:
            segments = tuple(kernel.segments)
    matching = tuple(
        segment for segment in segments
        if segment.target == int(expected_target)
    )
    if len(matching) != 1 or len(segments) != 1:
        targets = tuple(segment.target for segment in segments)
        raise ValueError(
            "Horizons SPK does not contain exactly one SBDB target segment: "
            f"expected={expected_target!r}, targets={targets!r}."
        )
    segment = matching[0]
    return {
        "target": str(segment.target),
        "center": str(segment.center),
        "segment_type": segment.data_type,
        "coverage_start_jd_tdb": segment.start_jd,
        "coverage_end_jd_tdb": segment.end_jd,
    }


def _spk_payload(document):
    encoded = document.get("spk")
    if not isinstance(encoded, str):
        diagnostic = document.get("error") or document.get("result") or ""
        diagnostic = " ".join(str(diagnostic).split())[:2000]
        raise ValueError(
            "Horizons returned no SPK payload; "
            f"keys={tuple(sorted(document))!r}; diagnostic={diagnostic!r}."
        )
    try:
        return base64.b64decode(
            "".join(encoded.split()).encode("ascii"),
            validate=True,
        )
    except (TypeError, ValueError) as error:
        raise ValueError("Horizons returned an invalid SPK payload.") from error


def acquire(output_directory):
    """Acquire one new evidence directory without replacing prior evidence."""
    output_directory = Path(output_directory).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    if any(output_directory.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite 50A.4 evidence in {output_directory}"
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
    obj, orbit, perihelion = _sbdb_identity(sbdb)
    epochs = _epochs(perihelion)
    start = (
        Time(epochs[0]).to_datetime(timezone=timezone.utc)
        - timedelta(days=30)
    ).date()
    stop = (
        Time(epochs[-1]).to_datetime(timezone=timezone.utc)
        + timedelta(days=30)
    ).date()
    spk_parameters = {
        "format": "json",
        "COMMAND": f"'{DESIGNATION};'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'SPK'",
        "START_TIME": f"'{start.isoformat()}'",
        "STOP_TIME": f"'{stop.isoformat()}'",
    }
    spk_document, spk_url = _request(HORIZONS_API, spk_parameters)
    _signature(spk_document, "NASA/JPL Horizons API")
    sbdb_spk_id = str(obj["spkid"])
    spk = _spk_payload(spk_document)
    if not spk.startswith(b"DAF/"):
        raise ValueError("Horizons payload is not a DAF/SPK file.")
    spk_identity = _spk_identity(spk, sbdb_spk_id)

    tables = []
    for name, parameters in (
        ("vectors", _horizons_parameters("vectors", epochs)),
        ("geocentric", _horizons_parameters("observer", epochs)),
        ("topocentric", _horizons_parameters(
            "observer", epochs, topocentric=True
        )),
    ):
        document, url = _request(HORIZONS_API, parameters)
        _signature(document, "NASA/JPL Horizons API")
        tables.append((name, document, url))

    evidence = [{
        **_write_json(output_directory / "sbdb-2p.json", sbdb),
        "request_url": sbdb_url,
    }]
    evidence.append({
        **_write_json(
            output_directory / "horizons-spk.json", spk_document
        ),
        "request_url": spk_url,
    })
    spk_path = output_directory / "2p-encke.bsp"
    spk_path.write_bytes(spk)
    evidence.append({
        "filename": spk_path.name,
        "bytes": len(spk),
        "sha256": _digest(spk),
        "request_url": spk_url,
        "spk_file_id": spk_identity["target"],
        "spk": spk_identity,
    })
    for name, document, url in tables:
        evidence.append({
            **_write_json(output_directory / f"horizons-{name}.json", document),
            "request_url": url,
        })

    report = {
        "purpose": "Wenu Milestone 50A.4 raw comet validation evidence",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "object": {
            "designation": DESIGNATION,
            "fullname": obj.get("fullname"),
            "kind": obj.get("kind"),
            "spk_id": str(obj["spkid"]),
            "orbit_id": orbit.get("orbit_id"),
            "solution_date": orbit.get("soln_date"),
            "perihelion_jd_tdb": perihelion,
            "model_parameters": orbit["model_pars"],
        },
        "observer": OBSERVER,
        "epochs_utc": epochs,
        "coverage": {"start": start.isoformat(), "stop": stop.isoformat()},
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
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY / "minor_bodies" / "50a4-raw",
    )
    arguments = parser.parse_args()
    print(acquire(arguments.output_directory))


if __name__ == "__main__":
    main()
