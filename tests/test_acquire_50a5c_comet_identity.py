"""Contracts for deliberate 50A.5C identity discovery."""

import json
import base64

import pytest

from tools import acquire_50a5c_comet_identity as acquisition
from tools import acquire_50a5c_comet_evidence as evidence_acquisition


def _sbdb():
    return {
        "signature": {
            "source": "NASA/JPL Small-Body Database (SBDB) API",
            "version": "1.3",
        },
        "object": {
            "des": "161P",
            "kind": "cn",
            "spkid": "1000042",
            "fullname": "161P/Hartley-IRAS",
        },
        "orbit": {
            "orbit_id": "71",
            "soln_date": "2026-09-08 09:12:21",
            "model_pars": [
                {"name": "A1", "value": "1e-8", "units": "au/d^2"},
                {"name": "A2", "value": "-3e-10", "units": "au/d^2"},
            ],
        },
    }


def _horizons():
    return {
        "signature": {
            "source": "NASA/JPL Horizons API",
            "version": "1.2",
        },
        "result": (
            "Target body name: 161P/Hartley-IRAS\n"
            "Rec #:90001107 JPL#71 A1= 1 A2= 2 "
            "ALN= 3 NK= 4 NM= 5 NN= 6 R0= 7\n"
        ),
    }


def test_identity_request_does_not_guess_an_apparition_record():
    parameters = acquisition._horizons_parameters()

    assert parameters == {
        "format": "json",
        "COMMAND": "'161P'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'NO'",
    }


def test_identity_checks_require_the_exact_numbered_comet():
    _, obj, orbit = acquisition._sbdb_identity(_sbdb())
    assert obj["des"] == "161P"
    assert [value["name"] for value in orbit["model_pars"]] == ["A1", "A2"]

    wrong = _sbdb()
    wrong["object"]["des"] = "2P"
    with pytest.raises(ValueError, match="numbered comet 161P"):
        acquisition._sbdb_identity(wrong)


def test_acquisition_writes_both_raw_responses_before_record_selection(
    tmp_path, monkeypatch,
):
    responses = iter(((_sbdb(), "sbdb-url"), (_horizons(), "horizons-url")))
    monkeypatch.setattr(acquisition, "_request", lambda *_: next(responses))

    report_path = acquisition.acquire(tmp_path / "identity")
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["requested_designation"] == "161P"
    assert report["object"]["fullname"] == "161P/Hartley-IRAS"
    assert report["object"]["spk_id"] == "1000042"
    assert [item["filename"] for item in report["evidence"]] == [
        "sbdb-161p.json",
        "horizons-161p-identity.json",
    ]
    assert "before selecting a record" in report["next_action"]


def test_acquisition_never_replaces_existing_identity_evidence(tmp_path):
    output = tmp_path / "identity"
    output.mkdir()
    (output / "keep").write_text("unchanged", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        acquisition.acquire(output)


def _identity_directory(tmp_path, monkeypatch):
    responses = iter(((_sbdb(), "sbdb-url"), (_horizons(), "horizons-url")))
    monkeypatch.setattr(acquisition, "_request", lambda *_: next(responses))
    directory = tmp_path / "identity"
    acquisition.acquire(directory)
    return directory


def _table(name="161P/Hartley-IRAS", solution="JPL#71", tail=False):
    columns = "PsAng PsAMV\n" if tail else ""
    return {
        "signature": {
            "source": "NASA/JPL Horizons API",
            "version": "1.2",
        },
        "result": (
            f"Target body name: {name} {{source: {solution}}}\n"
            f"{columns}$$SOE\nsynthetic,row\n$$EOE\n"
        ),
    }


def test_full_acquisition_freezes_inspected_record_and_epoch_policy():
    assert evidence_acquisition.HORIZONS_RECORD == "90001107"
    assert evidence_acquisition.PROVIDER_SPK_ID == "1000042"
    assert evidence_acquisition.ORBIT_SOLUTION_ID == "71"
    assert evidence_acquisition.EPOCHS == (
        "2026-09-01T00:00:00Z",
        "2026-10-02T00:00:00Z",
        "2026-10-31T00:00:00Z",
    )
    tail = evidence_acquisition._tail_parameters()
    sun = evidence_acquisition._sun_parameters()
    assert tail["COMMAND"] == "'90001107;'"
    assert tail["QUANTITIES"] == "'27,45'"
    assert sun["COMMAND"] == "'10'"
    assert sun["QUANTITIES"] == "'1,45'"


def test_full_acquisition_is_bound_to_identity_and_provider_tables(
    tmp_path, monkeypatch,
):
    identity = _identity_directory(tmp_path, monkeypatch)
    spk = {
        "signature": _table()["signature"],
        "spk": base64.b64encode(b"DAF/synthetic").decode("ascii"),
    }
    tables = (
        _table(),
        _table(),
        _table(),
        _table(tail=True),
        _table(name="Sun (10)", solution="", tail=False),
    )
    responses = iter(
        [(spk, "spk-url")]
        + [(document, f"table-{index}-url") for index, document in enumerate(tables)]
    )
    monkeypatch.setattr(
        evidence_acquisition, "_request", lambda *_: next(responses)
    )
    monkeypatch.setattr(
        evidence_acquisition,
        "_spk_identity",
        lambda payload, target: {
            "target": target,
            "center": "10",
            "segment_type": 21,
            "coverage_start_jd_tdb": 2461200.5,
            "coverage_end_jd_tdb": 2461320.5,
        },
    )

    report_path = evidence_acquisition.acquire(
        tmp_path / "raw", identity_directory=identity
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["object"]["horizons_record"] == "90001107"
    assert report["object"]["spk_id"] == "1000042"
    assert report["object"]["orbit_id"] == "71"
    assert report["object"]["model_parameters"][0]["name"] == "A1"
    assert report["epochs_utc"] == list(evidence_acquisition.EPOCHS)
    assert {item["filename"] for item in report["evidence"]} >= {
        "161p-hartley-iras.bsp",
        "horizons-vectors.json",
        "horizons-geocentric.json",
        "horizons-topocentric.json",
        "horizons-comet-tail-topocentric.json",
        "horizons-sun-topocentric.json",
    }
