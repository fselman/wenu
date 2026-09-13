"""Acquire immutable raw JPL evidence for the accepted 161P specimen."""

from __future__ import annotations

import argparse
import base64
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path

from astropy.time import Time

from wenu.observer import DEFAULT_DATA_DIRECTORY

try:
    from tools.acquire_50a4_comet_evidence import (
        HORIZONS_API,
        OBSERVER,
        _horizons_parameters,
        _request,
        _signature,
        _spk_identity,
        _spk_payload,
        _table_result,
        _write_json,
    )
    from tools.acquire_50a5c_comet_identity import (
        _horizons_identity,
        _sbdb_identity,
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
        _spk_identity,
        _spk_payload,
        _table_result,
        _write_json,
    )
    from acquire_50a5c_comet_identity import (
        _horizons_identity,
        _sbdb_identity,
    )


DESIGNATION = "161P"
FULL_NAME = "161P/Hartley-IRAS"
HORIZONS_RECORD = "90001107"
PROVIDER_SPK_ID = "1000042"
ORBIT_SOLUTION_ID = "71"
SOLUTION_DATE = "2026-09-08 09:12:21"
EPOCHS = (
    "2026-09-01T00:00:00Z",
    "2026-10-02T00:00:00Z",
    "2026-10-31T00:00:00Z",
)


def _digest(path):
    return sha256(path.read_bytes()).hexdigest()


def _document(path):
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise TypeError(f"{path.name} must contain one JSON object.")
    return document


def _identity_evidence(identity_directory):
    identity_directory = Path(identity_directory).expanduser().resolve(
        strict=True
    )
    report_path = identity_directory / "acquisition-report.json"
    sbdb_path = identity_directory / "sbdb-161p.json"
    horizons_path = identity_directory / "horizons-161p-identity.json"
    report = _document(report_path)
    evidence = {
        item["filename"]: item for item in report.get("evidence", ())
    }
    for path in (sbdb_path, horizons_path):
        if evidence.get(path.name, {}).get("sha256") != _digest(path):
            raise ValueError(
                f"{path.name} differs from its identity acquisition report."
            )
    sbdb = _document(sbdb_path)
    horizons = _document(horizons_path)
    _, obj, orbit = _sbdb_identity(sbdb)
    _, result = _horizons_identity(horizons)
    if (
        str(obj["spkid"]) != PROVIDER_SPK_ID
        or str(orbit["orbit_id"]) != ORBIT_SOLUTION_ID
        or orbit.get("soln_date") != SOLUTION_DATE
    ):
        raise ValueError("SBDB identity is not the inspected 161P solution.")
    required = (
        f"Rec #:{HORIZONS_RECORD}",
        "JPL#71",
        "A1=",
        "A2=",
        "ALN=",
        "NK=",
        "NM=",
        "NN=",
        "R0=",
    )
    if any(token not in result for token in required):
        raise ValueError(
            "Horizons identity lacks the inspected record, solution, or "
            "force-law fields."
        )
    return identity_directory, report, sbdb, horizons, obj, orbit


def _tail_parameters():
    parameters = _horizons_parameters(
        "observer", EPOCHS, HORIZONS_RECORD, topocentric=True
    )
    parameters["QUANTITIES"] = "'27,45'"
    return parameters


def _sun_parameters():
    parameters = _horizons_parameters(
        "observer", EPOCHS, "10", topocentric=True
    )
    parameters["COMMAND"] = "'10'"
    parameters["QUANTITIES"] = "'1,45'"
    return parameters


def _target_table(document, name, *, tail=False):
    result = _table_result(document, name)
    required = (FULL_NAME, "JPL#71")
    if any(token not in result for token in required):
        raise ValueError(f"Horizons {name} is not 161P solution 71.")
    if tail and ("PsAng" not in result or "PsAMV" not in result):
        raise ValueError("Horizons 161P tail table lacks PsAng/PsAMV.")
    return result


def _sun_table(document):
    result = _table_result(document, "topocentric Sun")
    if "Target body name: Sun (10)" not in result:
        raise ValueError("Horizons did not return the Sun (NAIF 10).")
    return result


def acquire(output_directory, *, identity_directory):
    """Acquire one complete evidence set tied to inspected identity evidence."""
    (
        identity_directory,
        identity_report,
        sbdb,
        horizons_identity,
        obj,
        orbit,
    ) = _identity_evidence(identity_directory)
    output_directory = Path(output_directory).expanduser().resolve()
    if output_directory.exists() and any(output_directory.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite 50A.5C evidence in {output_directory}"
        )

    start = (
        Time(EPOCHS[0]).to_datetime(timezone=UTC) - timedelta(days=30)
    ).date()
    stop = (
        Time(EPOCHS[-1]).to_datetime(timezone=UTC) + timedelta(days=30)
    ).date()
    spk_parameters = {
        "format": "json",
        "COMMAND": f"'{HORIZONS_RECORD};'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'SPK'",
        "START_TIME": f"'{start.isoformat()}'",
        "STOP_TIME": f"'{stop.isoformat()}'",
    }
    spk_document, spk_url = _request(HORIZONS_API, spk_parameters)
    signature = _signature(spk_document, "NASA/JPL Horizons API")
    spk = _spk_payload(spk_document)
    if not spk.startswith(b"DAF/"):
        raise ValueError("Horizons payload is not a DAF/SPK file.")
    spk_identity = _spk_identity(spk, PROVIDER_SPK_ID)

    requests = (
        (
            "horizons-vectors.json",
            _horizons_parameters("vectors", EPOCHS, HORIZONS_RECORD),
            lambda value: _target_table(value, "vector table"),
        ),
        (
            "horizons-geocentric.json",
            _horizons_parameters("observer", EPOCHS, HORIZONS_RECORD),
            lambda value: _target_table(value, "geocentric table"),
        ),
        (
            "horizons-topocentric.json",
            _horizons_parameters(
                "observer", EPOCHS, HORIZONS_RECORD, topocentric=True
            ),
            lambda value: _target_table(value, "topocentric table"),
        ),
        (
            "horizons-comet-tail-topocentric.json",
            _tail_parameters(),
            lambda value: _target_table(value, "tail table", tail=True),
        ),
        (
            "horizons-sun-topocentric.json",
            _sun_parameters(),
            _sun_table,
        ),
    )
    tables = []
    for filename, parameters, validate in requests:
        document, url = _request(HORIZONS_API, parameters)
        if _signature(document, "NASA/JPL Horizons API") != signature:
            raise ValueError("Horizons evidence signatures do not match.")
        validate(document)
        tables.append((filename, document, url))

    output_directory.mkdir(parents=True, exist_ok=True)
    evidence = []
    for filename, document, source_path in (
        ("sbdb-161p.json", sbdb, identity_directory / "sbdb-161p.json"),
        (
            "horizons-161p-identity.json",
            horizons_identity,
            identity_directory / "horizons-161p-identity.json",
        ),
    ):
        record = _write_json(output_directory / filename, document)
        record["source_sha256"] = _digest(source_path)
        evidence.append(record)
    evidence.append({
        **_write_json(output_directory / "horizons-spk.json", spk_document),
        "request_url": spk_url,
    })
    spk_path = output_directory / "161p-hartley-iras.bsp"
    spk_path.write_bytes(spk)
    evidence.append({
        "filename": spk_path.name,
        "bytes": len(spk),
        "sha256": sha256(spk).hexdigest(),
        "request_url": spk_url,
        "spk_file_id": spk_identity["target"],
        "spk": spk_identity,
    })
    for filename, document, url in tables:
        evidence.append({
            **_write_json(output_directory / filename, document),
            "request_url": url,
        })
    report = {
        "purpose": "Wenu Milestone 50A.5C raw 161P validation evidence",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "object": {
            "designation": DESIGNATION,
            "fullname": obj["fullname"],
            "kind": obj["kind"],
            "spk_id": PROVIDER_SPK_ID,
            "horizons_record": HORIZONS_RECORD,
            "orbit_id": ORBIT_SOLUTION_ID,
            "solution_date": SOLUTION_DATE,
            "model_parameters": orbit.get("model_pars"),
            "quality_fields": {
                key: orbit.get(key) for key in (
                    "condition_code", "data_arc", "first_obs", "last_obs",
                    "n_del_obs_used", "n_dop_obs_used", "n_obs_used",
                    "not_valid_after", "not_valid_before", "pe_used",
                    "producer", "rms", "sb_used", "source",
                )
            },
        },
        "observer": OBSERVER,
        "epochs_utc": EPOCHS,
        "coverage": {"start": start.isoformat(), "stop": stop.isoformat()},
        "authority": signature,
        "identity_evidence": {
            "report_sha256": _digest(
                identity_directory / "acquisition-report.json"
            ),
            "retrieved_at_utc": identity_report["retrieved_at_utc"],
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
    parser.add_argument("--identity-directory", type=Path, required=True)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=(
            DEFAULT_DATA_DIRECTORY / "minor_bodies" / "50a5c-161p-raw"
        ),
    )
    arguments = parser.parse_args()
    print(acquire(
        arguments.output_directory,
        identity_directory=arguments.identity_directory,
    ))


if __name__ == "__main__":
    main()
