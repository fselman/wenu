"""Tests for the bounded offline propagated-specimen builder."""

from __future__ import annotations

import json
from pathlib import Path
import socket

import pytest

from tools.build_50s4_satellite_specimens import (
    OUTPUT_NAME,
    SPECIMEN_LABEL,
    build_specimens,
)


@pytest.fixture(scope="module")
def built_specimen(tmp_path_factory, monkeypatch_module):
    def reject_network(*args, **kwargs):
        raise AssertionError("50S.4E builder attempted network access.")

    monkeypatch_module.setattr(socket.socket, "connect", reject_network)
    directory = tmp_path_factory.mktemp("satellite-specimens")
    output = build_specimens(directory)
    return output, output.read_bytes(), json.loads(output.read_text())


@pytest.fixture(scope="module")
def monkeypatch_module():
    patch = pytest.MonkeyPatch()
    try:
        yield patch
    finally:
        patch.undo()


def test_builder_writes_only_bounded_output_to_selected_directory(
    built_specimen,
):
    output, _, document = built_specimen

    assert output.name == OUTPUT_NAME
    assert tuple(output.parent.iterdir()) == (output,)
    assert document["label"] == SPECIMEN_LABEL
    assert document["schema_version"] == 1
    assert document["snapshot"]["snapshot_id"] == "synthetic_50s4b_v1"
    assert document["snapshot"]["record_order"] == [300001, 300002, 300003]
    assert document["evaluation_grid"]["sample_count"] == 3
    assert len(document["tracks"]) == 3
    assert all(len(track["samples"]) == 3 for track in document["tracks"])


def test_specimen_records_reproducible_inputs_and_exact_authorities(
    built_specimen,
):
    _, _, document = built_specimen

    assert document["observer"] == {
        "observer_id": "la-ligua",
        "longitude_deg": pytest.approx(-71.230289),
        "latitude_deg": pytest.approx(-32.443342),
        "elevation_m": pytest.approx(52.0),
        "refraction_policy": "vacuum",
        "earth_orientation_policy": "iers-a-bundled",
    }
    assert len(document["snapshot"]["content_sha256"]) == 64
    assert len(document["earth_orientation"]["source_sha256"]) == 64
    assert document["earth_orientation"]["astropy_version"]
    assert document["earth_orientation"]["astropy_iers_data_version"]
    assert document["software"]["wenu_version"]
    for track in document["tracks"]:
        assert len(track["identity"]["source_record_sha256"]) == 64
        assert track["propagator"]["gravity_model"] == "WGS-72"
        assert track["propagator"]["operation_mode"] == "improved"
        for sample in track["samples"]:
            assert sample["teme"]["status_code"] == 0
            assert sample["topocentric"]["direction_identity"] == (
                "topocentric geometric direction expressed in GCRS axes"
            )


def test_query_inputs_make_no_crossing_claim(built_specimen):
    _, raw, document = built_specimen
    text = raw.decode("utf-8")

    assert "SatelliteCrossingResult" not in text
    assert "entry_utc" not in text
    assert "exit_utc" not in text
    assert "closest_approach" not in text
    assert "not a verified crossing" in text
    assert "not a complete catalogue search" in document["prohibitions"]
    for track in document["tracks"]:
        query = track["query_input"]
        assert query["claim"] == "sampled query input only; no crossing result"
        assert query["interval_start_utc"] <= query["interval_stop_utc"]


def test_same_inputs_produce_identical_bytes(tmp_path, built_specimen):
    _, expected, _ = built_specimen
    output = build_specimens(tmp_path / "second")

    assert output.read_bytes() == expected


@pytest.mark.parametrize(
    ("keyword", "value", "exception"),
    [
        ("sample_count", 0, ValueError),
        ("sample_count", True, TypeError),
        ("step_seconds", 0, ValueError),
        ("field_radius_deg", 181.0, ValueError),
        ("start_utc", "2026-09-15", ValueError),
    ],
)
def test_builder_rejects_invalid_sampling_inputs(
    tmp_path, keyword, value, exception
):
    arguments = {keyword: value}

    with pytest.raises(exception):
        build_specimens(tmp_path / keyword, **arguments)


def test_builder_source_has_no_crossing_result_or_network_client():
    source = (
        Path(__file__).parents[1]
        / "tools"
        / "build_50s4_satellite_specimens.py"
    ).read_text(encoding="utf-8")

    assert "SatelliteCrossingResult" not in source
    assert "requests" not in source
    assert "urllib" not in source
