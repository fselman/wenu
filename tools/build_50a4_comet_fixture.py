"""Build the compact offline 50A.4 oracle from inspected raw evidence."""

from __future__ import annotations

import argparse
import csv
import json
from hashlib import sha256
from pathlib import Path
from time import strftime, strptime

RAW_FILES = {
    "sbdb": "sbdb-2p.json",
    "vectors": "horizons-vectors.json",
    "geocentric": "horizons-geocentric.json",
    "topocentric": "horizons-topocentric.json",
}
TOLERANCES = {
    "position_au": 1.0e-10,
    "velocity_au_per_day": 5.0e-12,
    "direction_deg": 5.0e-6,
    "distance_au": 1.0e-9,
    "light_time_min": 1.0e-7,
    "parallax_deg": 1.0e-5,
}
ENCKE_SPEC = {
    "raw_files": RAW_FILES,
    "designation": "2P",
    "kind": "cn",
    "provider_spk_id": "1000025",
    "horizons_record": "90000091",
    "orbit_solution_id": "K273/14",
    "required_model_parameters": frozenset({"A1", "A2"}),
    "spk_filename": "2p-encke.bsp",
    "key": "2p-encke",
    "name": "Encke",
    "iau_number": 2,
    "aliases": ("2P/Encke", "Encke"),
}


def _digest(path):
    return sha256(path.read_bytes()).hexdigest()


def _document(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain one JSON object.")
    return value


def _data_rows(document, name, width):
    result = document.get("result")
    if not isinstance(result, str):
        raise TypeError(f"{name} has no Horizons result text.")
    if result.count("$$SOE") != 1 or result.count("$$EOE") != 1:
        raise ValueError(f"{name} has no unique SOE/EOE data block.")
    block = result.split("$$SOE", 1)[1].split("$$EOE", 1)[0]
    rows = []
    for row in csv.reader(block.strip().splitlines()):
        values = tuple(value.strip() for value in row)
        if values and values[-1] == "":
            values = values[:-1]
        if len(values) != width:
            raise ValueError(
                f"{name} row has {len(values)} fields; expected {width}."
            )
        rows.append(values)
    if not rows:
        raise ValueError(f"{name} contains no data rows.")
    return tuple(rows)


def _number(value):
    return float("".join(value.split()))


def _calendar(value):
    value = value.removeprefix("A.D. ")
    parsed = strptime(value.split(".", 1)[0], "%Y-%b-%d %H:%M:%S")
    return strftime("%Y-%m-%dT%H:%M:%S", parsed)


def _vector_rows(document):
    records = {}
    for row in _data_rows(document, "vector table", 8):
        calendar = _calendar(row[1])
        records[calendar[:10]] = {
            "calendar_tdb": calendar,
            "vector_jd_tdb": _number(row[0]),
            "position_au": [_number(value) for value in row[2:5]],
            "velocity_au_per_day": [_number(value) for value in row[5:8]],
        }
    return records


def _observer_rows(document, name):
    records = {}
    for row in _data_rows(document, f"{name} observer table", 10):
        calendar = _calendar(row[0])
        records[calendar[:10]] = {
            "calendar_utc": calendar,
            "astrometric_ra_deg": _number(row[3]),
            "astrometric_dec_deg": _number(row[4]),
            "distance_au": _number(row[5]),
            "light_time_min": _number(row[7]),
            "apparent_ra_deg": _number(row[8]),
            "apparent_dec_deg": _number(row[9]),
        }
    return records


def _require_signature(document, source):
    signature = document.get("signature")
    if not isinstance(signature, dict) or signature.get("source") != source:
        raise ValueError(f"response has no accepted {source} signature.")
    return signature


def build_fixture(raw_directory, *, spec=None, tolerances=TOLERANCES):
    """Parse one inspected acquisition directory without network access."""
    spec = ENCKE_SPEC if spec is None else spec
    raw_files = spec["raw_files"]
    raw_directory = Path(raw_directory).expanduser().resolve()
    report = _document(raw_directory / "acquisition-report.json")
    documents = {
        key: _document(raw_directory / filename)
        for key, filename in raw_files.items()
    }
    sbdb = documents["sbdb"]
    sbdb_signature = _require_signature(
        sbdb, "NASA/JPL Small-Body Database (SBDB) API"
    )
    horizons_signatures = tuple(
        _require_signature(
            documents[name], "NASA/JPL Horizons API"
        )
        for name in ("vectors", "geocentric", "topocentric")
    )
    if len({value.get("version") for value in horizons_signatures}) != 1:
        raise ValueError("Horizons tables do not share one API version.")

    obj = sbdb.get("object", {})
    orbit = sbdb.get("orbit", {})
    acquired_object = report.get("object", {})
    if (
        obj.get("des") != spec["designation"]
        or obj.get("kind") != spec["kind"]
        or str(obj.get("spkid")) != spec["provider_spk_id"]
        or acquired_object.get("horizons_record") != spec["horizons_record"]
        or str(orbit.get("orbit_id")) != spec["orbit_solution_id"]
    ):
        raise ValueError("raw evidence is not the accepted comet solution.")

    model_parameters = orbit.get("model_pars")
    names = {
        value.get("name")
        for value in model_parameters or ()
        if isinstance(value, dict)
    }
    if not set(spec["required_model_parameters"]).issubset(names):
        raise ValueError("comet evidence discarded required model parameters.")

    evidence = {value["filename"]: value for value in report["evidence"]}
    for filename in raw_files.values():
        if evidence[filename]["sha256"] != _digest(raw_directory / filename):
            raise ValueError(f"{filename} differs from the acquisition report.")
    spk = evidence.get(spec["spk_filename"], {})
    if (
        spk.get("spk_file_id") != spec["provider_spk_id"]
        or spk.get("spk", {}).get("center") != "10"
        or spk.get("spk", {}).get("segment_type") != 21
    ):
        raise ValueError("comet SPK identity differs from the accepted one.")
    spk_path = raw_directory / spk["filename"]
    if not spk_path.is_file() or _digest(spk_path) != spk["sha256"]:
        raise ValueError("comet SPK differs from the acquisition report.")

    vectors = _vector_rows(documents["vectors"])
    geocentric = _observer_rows(documents["geocentric"], "geocentric")
    topocentric = _observer_rows(documents["topocentric"], "topocentric")
    expected_dates = tuple(value[:10] for value in report["epochs_utc"])
    if not (
        tuple(vectors) == expected_dates
        and tuple(geocentric) == expected_dates
        and tuple(topocentric) == expected_dates
    ):
        raise ValueError("Horizons table epochs differ from the acquisition report.")

    quality_names = (
        "condition_code", "data_arc", "first_obs", "last_obs",
        "n_obs_used", "n_del_obs_used", "n_dop_obs_used", "rms",
        "pe_used", "sb_used", "producer", "source",
        "not_valid_before", "not_valid_after",
    )
    epochs = []
    for date in expected_dates:
        epochs.append({
            "calendar": report["epochs_utc"][len(epochs)].removesuffix("Z"),
            **vectors[date],
            "geocentric": geocentric[date],
            "topocentric": topocentric[date],
        })

    return {
        "authority": {
            "sbdb_api": sbdb_signature["source"],
            "sbdb_version": sbdb_signature["version"],
            "horizons_api": horizons_signatures[0]["source"],
            "horizons_version": horizons_signatures[0]["version"],
            "observer_quantities": [1, 20, 21, 45],
            "observer_reference_system": "ICRF",
            "observer_apparent_policy": "AIRLESS",
            "vector_centre": "solar system barycenter",
            "vector_corrections": "NONE",
            "vector_reference_plane": "FRAME",
            "vector_units": "AU-D",
        },
        "observer": report["observer"],
        "tolerances": tolerances,
        "objects": [{
            "key": spec["key"],
            "class": "comet",
            "primary_designation": obj["des"],
            "name": spec["name"],
            "iau_number": spec["iau_number"],
            "horizons_command": spec["horizons_record"] + ";",
            "provider_spk_id": str(obj["spkid"]),
            "orbit_solution_id": orbit["orbit_id"],
            "solution_date": orbit["soln_date"],
            "osculating_epoch": f"{orbit['epoch']} TDB",
            "reference_system": f"{orbit['equinox']} ecliptic and equinox",
            "model_parameters": model_parameters,
            "quality_fields": {
                name: orbit.get(name) for name in quality_names
            },
            "spk": {
                "filename": spk["filename"],
                "sha256": spk["sha256"],
                "coverage_start_jd_tdb": spk["spk"]["coverage_start_jd_tdb"],
                "coverage_end_jd_tdb": spk["spk"]["coverage_end_jd_tdb"],
                "segment_type": spk["spk"]["segment_type"],
                "segment_centre_id": int(spk["spk"]["center"]),
            },
            "source_evidence_sha256": {
                filename: evidence[filename]["sha256"]
                for filename in raw_files.values()
            },
            "epochs": epochs,
        }],
    }


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
