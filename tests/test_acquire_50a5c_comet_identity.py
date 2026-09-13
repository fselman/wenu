"""Contracts for deliberate 50A.5C identity discovery."""

import json

import pytest

from tools import acquire_50a5c_comet_identity as acquisition


def _sbdb():
    return {
        "signature": {
            "source": "NASA/JPL Small-Body Database (SBDB) API",
            "version": "1.3",
        },
        "object": {
            "des": "161P",
            "kind": "cn",
            "spkid": "1000161",
            "fullname": "161P/Hartley-IRAS",
        },
        "orbit": {
            "orbit_id": "provider-result",
            "soln_date": "2026-09-13",
            "model_pars": None,
        },
    }


def _horizons():
    return {
        "signature": {
            "source": "NASA/JPL Horizons API",
            "version": "1.2",
        },
        "result": "Target body name: 161P/Hartley-IRAS\n",
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
    assert orbit["model_pars"] is None

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
    assert report["object"]["spk_id"] == "1000161"
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
