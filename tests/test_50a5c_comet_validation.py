"""Focused contracts for the shared 161P fixture and validator adapters."""

from hashlib import sha256
import json

from tools.build_50a5c_comet_fixture import build_fixture


SIGNATURE = {
    "source": "NASA/JPL Horizons API",
    "version": "1.2",
}


def _write(path, document):
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(payload)
    return sha256(payload).hexdigest()


def _raw_evidence(tmp_path):
    sbdb = {
        "signature": {
            "source": "NASA/JPL Small-Body Database (SBDB) API",
            "version": "1.3",
        },
        "object": {
            "des": "161P", "kind": "cn", "spkid": "1000042",
            "fullname": "161P/Hartley-IRAS",
        },
        "orbit": {
            "orbit_id": "71",
            "soln_date": "2026-09-08 09:12:21",
            "epoch": "2455861.5",
            "equinox": "J2000",
            "model_pars": [{"name": "A1"}, {"name": "A2"}],
            "condition_code": "0",
            "data_arc": "15630",
            "first_obs": "1983-11-23",
            "last_obs": "2026-09-08",
            "n_obs_used": 519,
        },
    }
    vectors = {
        "signature": SIGNATURE,
        "result": (
            "Target body name: 161P/Hartley-IRAS {source: JPL#71}\n"
            "$$SOE\n"
            "2461284.500800725,A.D. 2026-Sep-01 00:01:09.1826,1,2,3,4,5,6,\n"
            "2461315.500800722,A.D. 2026-Oct-02 00:01:09.1824,2,3,4,5,6,7,\n"
            "2461344.500800725,A.D. 2026-Oct-31 00:01:09.1826,3,4,5,6,7,8,\n"
            "$$EOE\n"
        ),
    }
    observer_rows = (
        "2026-Sep-01 00:00:00.000,,,42,-18,1,-1,8,42.1,-18.1,\n"
        "2026-Oct-02 00:00:00.000,A,,348,-5,.5,-1,4,348.1,-5.1,\n"
        "2026-Oct-31 00:00:00.000,N,,299,13,.9,1,7,299.1,13.1,\n"
    )
    geocentric = {
        "signature": SIGNATURE,
        "result": "header\n$$SOE\n" + observer_rows + "$$EOE\n",
    }
    topocentric = json.loads(json.dumps(geocentric))
    tail = {
        "signature": SIGNATURE,
        "result": (
            "Target body name: 161P/Hartley-IRAS {source: JPL#71}\n"
            "PsAng PsAMV\n$$SOE\n"
            "2026-Sep-01 00:00:00.000,,,269.947,161.276,42.1,-18.1,\n"
            "2026-Oct-02 00:00:00.000,A,,65.412,146.113,348.1,-5.1,\n"
            "2026-Oct-31 00:00:00.000,N,,75.200,134.747,299.1,13.1,\n"
            "$$EOE\n"
        ),
    }
    sun = {
        "signature": SIGNATURE,
        "result": (
            "Target body name: Sun (10)\n$$SOE\n"
            "2026-Sep-01 00:00:00.000,,,159,8,159.1,8.1,\n"
            "2026-Oct-02 00:00:00.000,A,,187,-3,187.1,-3.1,\n"
            "2026-Oct-31 00:00:00.000,N,,214,-13,214.1,-13.1,\n"
            "$$EOE\n"
        ),
    }
    documents = {
        "sbdb-161p.json": sbdb,
        "horizons-vectors.json": vectors,
        "horizons-geocentric.json": geocentric,
        "horizons-topocentric.json": topocentric,
        "horizons-comet-tail-topocentric.json": tail,
        "horizons-sun-topocentric.json": sun,
    }
    evidence = []
    for filename, document in documents.items():
        digest = _write(tmp_path / filename, document)
        evidence.append({"filename": filename, "sha256": digest})
    spk = tmp_path / "161p-hartley-iras.bsp"
    spk.write_bytes(b"DAF/synthetic")
    evidence.append({
        "filename": spk.name,
        "sha256": sha256(spk.read_bytes()).hexdigest(),
        "spk_file_id": "1000042",
        "spk": {
            "target": "1000042",
            "center": "10",
            "segment_type": 21,
            "coverage_start_jd_tdb": 2461200.5,
            "coverage_end_jd_tdb": 2461400.5,
        },
    })
    report = {
        "object": {"horizons_record": "90001107"},
        "observer": {"name": "La Ligua"},
        "epochs_utc": [
            "2026-09-01T00:00:00Z",
            "2026-10-02T00:00:00Z",
            "2026-10-31T00:00:00Z",
        ],
        "evidence": evidence,
    }
    _write(tmp_path / "acquisition-report.json", report)
    return tmp_path


def test_second_comet_uses_shared_numerical_parser_and_freezes_orientation(
    tmp_path,
):
    fixture = build_fixture(_raw_evidence(tmp_path))
    record = fixture["objects"][0]

    assert fixture["tolerances"]["direction_deg"] == 1.0e-5
    assert record["primary_designation"] == "161P"
    assert record["provider_spk_id"] == "1000042"
    assert record["orbit_solution_id"] == "71"
    assert record["aliases"] == ["161P/Hartley-IRAS", "Hartley-IRAS"]
    assert [item["horizons_psang_deg"] for item in fixture["antisolar"]["epochs"]] == [
        269.947, 65.412, 75.2,
    ]
    assert fixture["antisolar"]["tolerances"] == {
        "antisolar_position_angle_deg": 0.01,
    }
