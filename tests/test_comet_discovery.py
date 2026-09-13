"""Comet-discovery provider, parsing, provenance, and CLI contracts."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest

from wenu import comet_discovery
from wenu.cli import comets


FIXTURE = Path("tests/fixtures/sbdb_comet_discovery_response.json")


def fixture_bytes():
    return FIXTURE.read_bytes()


def test_query_uses_inclusive_utc_days_converted_to_tdb():
    start, stop = comet_discovery.civil_utc_interval(
        "2026-09-01", "2026-09-30"
    )
    parameters = comet_discovery.discovery_query_parameters(start, stop, 5.0)
    constraints = json.loads(parameters["sb-cdata"])["AND"]

    assert start.isoformat() == "2026-09-01T00:00:00+00:00"
    assert stop.isoformat() == "2026-09-30T23:59:59.999999+00:00"
    assert parameters["sb-kind"] == "c"
    assert parameters["sort"] == "tp,pdes"
    assert constraints[0].startswith("tp|RG|2461284.")
    assert constraints[1] == "q|LE|5"


def test_invalid_date_interval_fails_before_provider_access():
    calls = []
    with pytest.raises(ValueError, match="STOP must not precede START"):
        comet_discovery.discover_comets(
            "2026-10-01", "2026-09-01",
            fetch=lambda *values: calls.append(values),
        )
    assert calls == []


def test_frozen_response_is_typed_sorted_and_preserves_unknowns():
    version, count, records = comet_discovery.parse_discovery_response(
        fixture_bytes()
    )

    assert version == "1.0"
    assert count == "2"
    assert [record.primary_designation for record in records] == [
        "2026 A1", "2P",
    ]
    assert [record.canonical_designation for record in records] == [
        "C/2026 A1", "2P",
    ]
    assert records[0].first_observation == "2026-01-03"
    assert records[0].period_days is None
    assert records[0].earth_moid_au is None
    assert records[1].name == "Encke"
    assert records[1].orbit_solution_id == "K273/14"


def test_provider_signature_schema_and_kind_drift_fail_closed():
    document = json.loads(fixture_bytes())
    for mutation, message in (
        (lambda value: value["signature"].update(source="other"), "signature"),
        (lambda value: value["fields"].pop(), "fields"),
        (lambda value: value["data"][0].__setitem__(2, "an"), "non-comet"),
    ):
        changed = json.loads(json.dumps(document))
        mutation(changed)
        with pytest.raises(ValueError, match=message):
            comet_discovery.parse_discovery_response(
                json.dumps(changed).encode("utf-8")
            )


def test_nonfinite_and_out_of_filter_values_fail_closed():
    document = json.loads(fixture_bytes())
    q_index = document["fields"].index("q")
    document["data"][0][q_index] = "nan"
    with pytest.raises(ValueError, match="invalid values"):
        comet_discovery.parse_discovery_response(
            json.dumps(document).encode("utf-8")
        )

    document = json.loads(fixture_bytes())
    q_index = document["fields"].index("q")
    document["data"][0][q_index] = "6"
    with pytest.raises(ValueError, match="outside the requested filter"):
        comet_discovery.discover_comets(
            "2026-09-01",
            "2026-09-30",
            fetch=lambda *values: json.dumps(document).encode("utf-8"),
        )


def test_discovery_retains_request_and_raw_response_provenance():
    raw = fixture_bytes()
    calls = []
    now = datetime(2026, 9, 13, 20, 0, tzinfo=timezone.utc)

    result = comet_discovery.discover_comets(
        "2026-09-01",
        "2026-09-30",
        fetch=lambda url, parameters: (
            calls.append((url, parameters)) or raw
        ),
        now=lambda: now,
    )

    assert calls[0][0] == comet_discovery.SBDB_QUERY_API
    assert result.retrieved_at_utc == now
    assert result.raw_sha256 == sha256(raw).hexdigest()
    assert dict(result.request_parameters) == calls[0][1]


def test_table_labels_model_parameters_and_visibility_limit():
    result = comet_discovery.discover_comets(
        "2026-09-01", "2026-09-30", fetch=lambda *values: fixture_bytes()
    )
    text = comets.table_text(result)

    assert "not a visibility forecast" in text
    assert "M1 model" in text
    assert "unknown" in text
    for explanation in (
        "Header key:",
        "1st obs.: earliest observation used by the current orbit",
        "not necessarily the discovery date",
        "P: periodic; C: non-periodic; D: disappeared",
        "A: object found to be a minor planet",
        "I: interstellar object",
        "permanent number of a periodic comet",
        "SBDB orbit-class code",
        "minimum orbit intersection distance",
        "total/nuclear absolute-magnitude parameters",
        "total/nuclear magnitude-slope parameters",
        "UTC: Coordinated Universal Time",
    ):
        assert explanation in text
    assert text.index("C/2026 A1") < text.index("2P")


def test_json_retains_units_time_scale_and_provider_identity():
    result = comet_discovery.discover_comets(
        "2026-09-01", "2026-09-30", fetch=lambda *values: fixture_bytes()
    )
    document = json.loads(comets.json_text(result))

    assert document["selection"]["max_perihelion_distance"]["unit"] == "au"
    assert (
        document["provider"]["identity"]
        == comet_discovery.SBDB_QUERY_SOURCE
    )
    assert document["records"][0]["perihelion"]["time_scale"] == "TDB"
    assert document["records"][0]["canonical_designation"] == "C/2026 A1"
    assert document["records"][0]["first_observation"] == "2026-01-03"
    assert document["records"][0]["period_days"] == {
        "unit": "d", "value": None,
    }


def test_cli_writes_selected_serialization(tmp_path, monkeypatch):
    result = comet_discovery.discover_comets(
        "2026-09-01", "2026-09-30", fetch=lambda *values: fixture_bytes()
    )
    output = tmp_path / "comets.json"
    monkeypatch.setattr(
        comets, "discover_comets", lambda *args, **kwargs: result
    )

    assert comets.main([
        "2026-09-01", "2026-09-30", "--format", "json",
        "--output", str(output),
    ]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["records"]


def test_cli_has_no_observer_option_in_bounded_50a5d1a_slice():
    with pytest.raises(SystemExit):
        comets.parser().parse_args([
            "2026-09-01", "2026-09-30", "--observer-location", "La Ligua",
        ])


def test_console_entry_point_is_packaged():
    project = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'wenu_retrieve_comets = "wenu.cli.comets:main"' in project
