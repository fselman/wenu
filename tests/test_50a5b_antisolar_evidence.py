"""Contracts for the independent 50A.5B antisolar oracle."""

import json
from pathlib import Path

import pytest

from tools.acquire_50a5b_antisolar_evidence import (
    EPOCHS,
    _comet_tail_parameters,
    _comet_tail_table_identity,
    _sun_parameters,
    _sun_table_identity,
)
from tools.build_50a5b_antisolar_fixture import (
    ANTISOLAR_POSITION_ANGLE_TOLERANCE_DEG,
    build_fixture,
)
from wenu.antisolar import (
    antisolar_position_angle_deg,
    position_angle_deg,
)


def test_sun_request_matches_accepted_comet_epochs_and_observer():
    parameters = _sun_parameters(EPOCHS)

    assert parameters["COMMAND"] == "'10'"
    assert parameters["CENTER"] == "'coord@399'"
    assert parameters["SITE_COORD"] == "'-71.230289,-32.443342,0.052'"
    assert parameters["REF_SYSTEM"] == "'ICRF'"
    assert parameters["APPARENT"] == "'AIRLESS'"
    assert parameters["QUANTITIES"] == "'1,45'"
    assert parameters["TIME_TYPE"] == "'UT'"
    assert len(parameters["TLIST"].split(",")) == 3


def test_comet_tail_request_asks_horizons_for_psang_before_fallback():
    parameters = _comet_tail_parameters(EPOCHS)

    assert parameters["COMMAND"] == "'90000091;'"
    assert parameters["CENTER"] == "'coord@399'"
    assert parameters["SITE_COORD"] == "'-71.230289,-32.443342,0.052'"
    assert parameters["REF_SYSTEM"] == "'ICRF'"
    assert parameters["APPARENT"] == "'AIRLESS'"
    assert parameters["QUANTITIES"] == "'27,45'"


def test_comet_tail_identity_requires_psang_and_exact_solution():
    with pytest.raises(ValueError, match="PsAng/PsAMV"):
        _comet_tail_table_identity({
            "result": (
                "Target body name: 2P/Encke {source: JPL#K273/14}\n"
                "$$SOE\n2027-Feb-11 00:00:00.000,1,2,\n$$EOE"
            )
        })


def test_sun_identity_rejects_minor_planet_10_hygiea():
    with pytest.raises(ValueError, match=r"Sun \(NAIF 10\)"):
        _sun_table_identity({
            "result": (
                "Target body name: 10 Hygiea\n"
                "$$SOE\n2027-Feb-11 00:00:00.000,C,m,1,2,3,4,\n$$EOE"
            )
        })


@pytest.mark.parametrize(
    ("destination", "expected"),
    (
        ((0.0, 1.0), 0.0),
        ((1.0, 0.0), 90.0),
        ((0.0, -1.0), 180.0),
        ((359.0, 0.0), 270.0),
    ),
)
def test_position_angle_is_east_of_north_and_wrap_safe(destination, expected):
    assert position_angle_deg((0.0, 0.0), destination) == pytest.approx(
        expected
    )


def test_antisolar_position_angle_points_opposite_the_sun():
    sunward = position_angle_deg((347.16285, 11.56332), (230.0, -18.0))
    antisolar = antisolar_position_angle_deg(
        (347.16285, 11.56332), (230.0, -18.0)
    )

    assert (antisolar - sunward) % 360.0 == pytest.approx(180.0)


def test_acquisition_refuses_an_unaccepted_comet_reference(tmp_path):
    from tools.acquire_50a5b_antisolar_evidence import acquire

    reference = tmp_path / "reference.json"
    reference.write_text(json.dumps({"objects": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="accepted 50A.4 oracle"):
        acquire(tmp_path / "output", comet_reference=reference)


def test_acquisition_refuses_to_replace_existing_evidence(
    tmp_path, monkeypatch,
):
    from tools import acquire_50a5b_antisolar_evidence as acquisition

    reference = Path(
        "tests/fixtures/horizons_comet_validation_50a4.json"
    ).resolve()
    output = tmp_path / "evidence"
    output.mkdir()
    (output / "existing").write_text("preserve", encoding="utf-8")
    monkeypatch.setattr(
        acquisition,
        "COMET_REFERENCE_SHA256",
        acquisition._digest(reference),
    )

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        acquisition.acquire(output, comet_reference=reference)


def test_offline_builder_freezes_independent_sun_and_comet_directions(
    tmp_path,
):
    from tools import acquire_50a5b_antisolar_evidence as acquisition

    reference = Path(
        "tests/fixtures/horizons_comet_validation_50a4.json"
    ).resolve()
    assert acquisition._digest(reference) == acquisition.COMET_REFERENCE_SHA256
    rows = (
        " 2026-Nov-13 00:00:00.000,N,m,230.0,-18.0,230.1,-18.1,\n"
        " 2027-Feb-11 00:00:00.000,C,m,320.0,-16.0,320.1,-16.1,\n"
        " 2027-May-12 00:00:00.000, ,m,48.0,17.0,48.1,17.1,\n"
    )
    sun = {
        "signature": {
            "source": "NASA/JPL Horizons API",
            "version": "1.2",
        },
        "result": (
            "Target body name: Sun (10)\n$$SOE\n" + rows + "$$EOE\n"
        ),
    }
    sun_path = tmp_path / "horizons-sun-topocentric.json"
    sun_path.write_text(json.dumps(sun), encoding="utf-8")
    report = {
        "observer": {
            "name": "La Ligua",
            "longitude_deg_east": -71.230289,
            "latitude_deg": -32.443342,
            "elevation_km": 0.052,
        },
        "epochs_utc": EPOCHS,
        "comet_reference": {
            "sha256": acquisition.COMET_REFERENCE_SHA256,
        },
        "evidence": [{
            "filename": sun_path.name,
            "sha256": acquisition._digest(sun_path),
        }],
    }
    (tmp_path / "acquisition-report.json").write_text(
        json.dumps(report), encoding="utf-8"
    )

    fixture = build_fixture(tmp_path, reference)

    assert fixture["tolerances"] == {
        "antisolar_position_angle_deg": 2.0e-5,
    }
    assert ANTISOLAR_POSITION_ANGLE_TOLERANCE_DEG == 2.0e-5
    assert fixture["object"] == {
        "key": "2p-encke",
        "primary_designation": "2P",
        "provider_spk_id": "1000025",
        "orbit_solution_id": "K273/14",
    }
    assert len(fixture["epochs"]) == 3
    first = fixture["epochs"][0]
    assert first["comet_apparent_icrf_deg"] == [347.16285, 11.56332]
    assert first["sun_apparent_icrf_deg"] == [230.1, -18.1]
    assert first["antisolar_position_angle_deg"] == pytest.approx(
        antisolar_position_angle_deg(
            first["comet_apparent_icrf_deg"],
            first["sun_apparent_icrf_deg"],
        )
    )
