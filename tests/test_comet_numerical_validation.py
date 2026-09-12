"""Offline 2P/Encke fixture and characterization contracts."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.build_50a4_comet_fixture import (
    _observer_rows,
    _vector_rows,
)
from tools.validate_50a2_asteroids import _solution
from tools.validate_50a4_comet import REFERENCE, characterize, validate_comet


def _result(row):
    return {
        "result": f"header\n$$SOE\n{row}\n$$EOE\n",
    }


def test_comet_validator_can_run_as_a_repository_script():
    result = subprocess.run(
        [sys.executable, "tools/validate_50a4_comet.py", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--characterize" in result.stdout


def test_offline_parser_reads_vector_state_and_spaced_negative_declination():
    vectors = _vector_rows(_result(
        "2461447.500800753, A.D. 2027-Feb-11 00:01:09.1851,"
        " -3.298092036139844E-01, 7.488257212259450E-02,"
        " 1.674295558096740E-02, -1.061519003822313E-02,"
        " -3.169484101896915E-02, -2.221552218873262E-02,"
    ))
    observer = _observer_rows(_result(
        "2027-Feb-11 00:00:00.000,C,m,312.65481,-18.92070,"
        "0.69358577369992,33.3280349,5.76837698,312.64901,"
        "-        18.92222,"
    ), "topocentric")

    assert vectors["2027-02-11"]["position_au"][0] == pytest.approx(
        -0.3298092036139844
    )
    assert vectors["2027-02-11"]["velocity_au_per_day"][2] == pytest.approx(
        -0.02221552218873262
    )
    assert observer["2027-02-11"]["apparent_dec_deg"] == -18.92222


def test_compact_fixture_preserves_comet_model_and_three_oracle_epochs():
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    record = reference["objects"][0]
    identity = _solution(record, reference["authority"]["horizons_version"])

    assert record["provider_spk_id"] == "1000025"
    assert record["horizons_command"] == "90000091;"
    assert record["orbit_solution_id"] == "K273/14"
    assert record["spk"]["segment_type"] == 21
    assert record["spk"]["segment_centre_id"] == 10
    assert reference["tolerances"] == {
        "position_au": 1.0e-10,
        "velocity_au_per_day": 5.0e-12,
        "direction_deg": 5.0e-6,
        "distance_au": 1.0e-9,
        "light_time_min": 1.0e-7,
        "parallax_deg": 1.0e-5,
    }
    assert [epoch["calendar"] for epoch in record["epochs"]] == [
        "2026-11-13T00:00:00",
        "2027-02-11T00:00:00",
        "2027-05-12T00:00:00",
    ]
    assert identity.object_class == "comet"
    assert tuple(name for name, _ in identity.model_parameters) == ("A1", "A2")
    assert dict(identity.quality_fields)["pe_used"] == "DE441"
    assert dict(identity.quality_fields)["not_valid_after"] == "null"


def test_comet_validator_is_characterization_only(monkeypatch, tmp_path):
    def fake_validate(**arguments):
        assert arguments["characterize"] is True
        return {
            "accepted": False,
            "characterization": True,
            "tolerances": {"direction_deg": 1.0},
            "objects": [{
                "key": "2p-encke",
                "solution": {
                    "object_class": "comet",
                    "model_parameters": {"A1": "...", "A2": "..."},
                },
            }],
        }

    monkeypatch.setattr("tools.validate_50a4_comet.validate", fake_validate)
    report = characterize(
        resource_directory=tmp_path,
        planetary_ephemeris_path=tmp_path / "de440s.bsp",
        reference_path=Path("fixture.json"),
    )

    assert report["accepted"] is False
    assert report["characterization"] is True
    assert report["tolerances"] is None
    assert report["tolerance_status"] == "not enforced during characterization"
    assert report["objects"][0]["solution"]["object_class"] == "comet"


def test_comet_validator_enforces_accepted_tolerances(monkeypatch, tmp_path):
    def fake_validate(**arguments):
        assert arguments["characterize"] is False
        return {
            "accepted": True,
            "characterization": False,
            "tolerances": {"position_au": 1.0e-10},
            "objects": [{
                "solution": {
                    "object_class": "comet",
                    "model_parameters": {"A1": "...", "A2": "..."},
                },
            }],
        }

    monkeypatch.setattr("tools.validate_50a4_comet.validate", fake_validate)
    report = validate_comet(
        resource_directory=tmp_path,
        planetary_ephemeris_path=tmp_path / "de440s.bsp",
        reference_path=Path("fixture.json"),
    )

    assert report["accepted"] is True
    assert report["tolerance_status"] == "accepted and enforced"
