"""Comet-discovery provider, parsing, provenance, and CLI contracts."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

import pytest

from wenu import comet_discovery, comet_photometry
from wenu.cli import comets


FIXTURE = Path("tests/fixtures/sbdb_comet_discovery_response.json")
PHOTOMETRY_FIXTURE = Path(
    "tests/fixtures/horizons_comet_photometry_response.json"
)


def fixture_bytes():
    return FIXTURE.read_bytes()


def photometry_fixture_bytes():
    return PHOTOMETRY_FIXTURE.read_bytes()


def synthetic_photometry_response(parameters):
    """Adapt the exact provider envelope to requested synthetic epochs."""
    document = json.loads(photometry_fixture_bytes())
    result = document["result"]
    start = result.index("$$SOE") + len("$$SOE")
    stop = result.index("$$EOE", start)
    jd_values = re.findall(r"\d+\.\d+", parameters["TLIST"])
    rows = []
    for jd_value in jd_values:
        epoch = comet_photometry.Time(
            float(jd_value), format="jd", scale="utc"
        ).utc.datetime
        rows.append(
            f" {epoch:%Y-%b-%d %H:%M:%S.%f},"
            f" {float(jd_value):.9f},C, ,    -11.,    12.,"
        )
    document["result"] = (
        result[:start] + "\n" + "\n".join(rows) + "\n" + result[stop:]
    )
    return json.dumps(document).encode("utf-8")


def short_mcnaught_discovery():
    result = comet_discovery.discover_comets(
        "2026-09-01", "2026-09-30", fetch=lambda *values: fixture_bytes()
    )
    record = replace(
        result.records[1],
        spk_id="1002410",
        full_name="C/2006 P1 (McNaught)",
        kind="cu",
        primary_designation="2006 P1",
        name="McNaught",
        first_observation="2006-08-07",
        prefix="C",
        orbit_class="COM",
        orbit_solution_id="JPL 27",
    )
    return replace(
        result,
        start_utc=datetime(2007, 1, 12, tzinfo=timezone.utc),
        stop_utc=datetime(
            2007, 1, 12, 23, 59, 59, 999999, tzinfo=timezone.utc
        ),
        records=(record,),
    )


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
        assert changed != document
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


def test_magnitude_step_and_endpoint_sampling_are_bounded():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    stop = start + timedelta(hours=25)

    canonical, epochs = comet_photometry.magnitude_sample_epochs(
        start, stop, "12H"
    )

    assert canonical == "12h"
    assert epochs == (
        start,
        start + timedelta(hours=12),
        start + timedelta(hours=24),
        stop,
    )
    for invalid in ("", "0h", "1.5d", "minutes", "-1d"):
        with pytest.raises(ValueError, match="positive whole number"):
            comet_photometry.parse_magnitude_step(invalid)
    with pytest.raises(ValueError, match="limit is 367"):
        comet_photometry.magnitude_sample_epochs(
            start, start + timedelta(days=367), "1d"
        )
    automatic, automatic_epochs = comet_photometry.magnitude_sample_epochs(
        start, start + timedelta(days=730), None
    )
    assert automatic == "2d"
    assert len(automatic_epochs) == 366


def test_photometry_window_is_centered_on_each_comet_perihelion():
    record = short_mcnaught_discovery().records[0]
    start, stop = comet_photometry.perihelion_sampling_window(record)
    center = comet_photometry.Time(
        record.perihelion_jd_tdb, format="jd", scale="tdb"
    ).utc.to_datetime(timezone=timezone.utc)

    assert center - start == timedelta(days=30)
    assert stop - center == timedelta(days=30)


def test_photometry_request_is_topocentric_airless_and_exactly_sampled():
    discovery = short_mcnaught_discovery()
    _, epochs = comet_photometry.magnitude_sample_epochs(
        discovery.start_utc, discovery.stop_utc, "12h"
    )
    parameters = comet_photometry.photometry_query_parameters(
        discovery.records[0],
        latitude_deg=-32.452,
        longitude_deg=-71.232,
        elevation_m=50.0,
        epochs_utc=epochs,
    )

    assert parameters["COMMAND"] == "'DES=2006 P1;CAP;NOFRAG'"
    assert parameters["CENTER"] == "'coord@399'"
    assert parameters["TABLE_TYPE"] == "'OBSERVER'"
    assert parameters["COORD_TYPE"] == "'GEODETIC'"
    assert parameters["SITE_COORD"] == "'-71.232,-32.452,0.05'"
    assert parameters["TIME_TYPE"] == "'UT'"
    assert parameters["QUANTITIES"] == "'9'"
    assert parameters["APPARENT"] == "'AIRLESS'"
    assert parameters["SKIP_DAYLT"] == "'NO'"
    assert parameters["ELEV_CUT"] == "'-90'"
    assert parameters["TLIST"].count(",") == len(epochs) - 1
    assert len(parameters["TLIST"].splitlines()) == len(epochs)


def test_photometry_transport_posts_a_horizons_batch_file(monkeypatch):
    discovery = short_mcnaught_discovery()
    _, epochs = comet_photometry.magnitude_sample_epochs(
        discovery.start_utc, discovery.stop_utc, "12h"
    )
    parameters = comet_photometry.photometry_query_parameters(
        discovery.records[0],
        latitude_deg=-32.452,
        longitude_deg=-71.232,
        elevation_m=50.0,
        epochs_utc=epochs,
    )
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *values):
            return False

        def read(self):
            return b"response"

    def open_request(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(comet_photometry, "urlopen", open_request)
    assert comet_photometry._fetch(
        comet_photometry.HORIZONS_API, parameters
    ) == b"response"

    request = captured["request"]
    body = request.data.decode("utf-8")
    assert request.method == "POST"
    assert request.full_url.endswith("/api/horizons_file.api")
    assert 'name="format"' in body
    assert 'name="input"' in body
    assert "!$$SOF\n" in body
    assert "TLIST=" in body
    assert "?" not in request.full_url


def test_frozen_horizons_photometry_preserves_unknowns_and_provenance():
    discovery = short_mcnaught_discovery()
    _, epochs = comet_photometry.magnitude_sample_epochs(
        discovery.start_utc, discovery.stop_utc, "12h"
    )
    version, samples, notices = comet_photometry.parse_photometry_response(
        photometry_fixture_bytes(),
        record=discovery.records[0],
        requested_epochs_utc=epochs,
    )

    assert version == "1.2"
    assert sha256(photometry_fixture_bytes()).hexdigest() == (
        "054f05bd5905997f4b1dd22de92417d51b8cfead345089f1d5dfb2b6f2dda7f0"
    )
    assert b"McNaught (C/2006 P1)" in photometry_fixture_bytes()
    assert b"{source: JPL#27}" in photometry_fixture_bytes()
    assert len(samples) == 3
    assert samples[0].total_magnitude == -11.0
    assert samples[0].nuclear_magnitude == 12.0
    assert samples[1].nuclear_magnitude == 13.0
    assert abs(
        (samples[-1].epoch_utc - discovery.stop_utc).total_seconds()
    ) < 1.0
    assert any("apparent visual total magnitude" in notice for notice in notices)

    synthetic = json.loads(photometry_fixture_bytes())
    synthetic["result"] = synthetic["result"].replace(
        "    -11.,    12.,",
        "    -11.,  n.a.,",
        1,
    )
    _, unknown_samples, _ = comet_photometry.parse_photometry_response(
        json.dumps(synthetic).encode("utf-8"),
        record=discovery.records[0],
        requested_epochs_utc=epochs,
    )
    assert unknown_samples[0].nuclear_magnitude is None


def test_photometry_provider_drift_fails_closed():
    discovery = short_mcnaught_discovery()
    record = discovery.records[0]
    _, epochs = comet_photometry.magnitude_sample_epochs(
        discovery.start_utc, discovery.stop_utc, "12h"
    )
    document = json.loads(photometry_fixture_bytes())

    mutations = (
        (lambda value: value["signature"].update(source="other"), "signature"),
        (
            lambda value: value.update(
                result=value["result"].replace("C/2006 P1", "C/2006 P2")
            ),
            "target differs",
        ),
        (
            lambda value: value.update(
                result=value["result"].replace("JPL#27", "JPL#other")
            ),
            "orbit solutions differ",
        ),
        (
            lambda value: value.update(
                result=value["result"].replace("    -11.,    12.,", "    nan,    12.,", 1)
            ),
            "invalid values",
        ),
        (
            lambda value: value.update(
                result=value["result"].replace(
                    " 2007-Jan-13 00:00:00.000,"
                    " 2454113.500000000,C, ,    -11.,    13.,\n",
                    "",
                )
            ),
            "sample count differs",
        ),
    )
    for mutation, message in mutations:
        changed = json.loads(json.dumps(document))
        mutation(changed)
        with pytest.raises(ValueError, match=message):
            comet_photometry.parse_photometry_response(
                json.dumps(changed).encode("utf-8"),
                record=record,
                requested_epochs_utc=epochs,
            )


def test_characterization_resolves_observer_and_retains_exact_response():
    discovery = short_mcnaught_discovery()
    raw = photometry_fixture_bytes()
    calls = []
    now = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)

    result = comet_photometry.characterize_discovery_photometry(
        discovery,
        observer_location="La Ligua",
        magnitude_step="12h",
        fetch=lambda url, parameters: (
            calls.append((url, parameters))
            or synthetic_photometry_response(parameters)
        ),
        now=lambda: now,
    )

    assert len(calls) == 1
    assert calls[0][0] == comet_photometry.HORIZONS_API
    assert result.observer_location == "La Ligua"
    assert result.magnitude_step == "12h"
    model = result.results[0]
    assert model.brightest_total_sample.total_magnitude == -11.0
    assert model.brightest_nuclear_sample.nuclear_magnitude == 12.0
    assert model.provider_endpoint.endswith("/api/horizons_file.api")
    assert model.provider_transport == "multipart/form-data POST"
    assert model.raw_sha256 == sha256(
        synthetic_photometry_response(calls[0][1])
    ).hexdigest()
    assert model.retrieved_at_utc == now
    assert dict(model.request_parameters) == calls[0][1]
    assert model.stop_utc - model.start_utc == timedelta(days=60)
    assert result.perihelion_window_days == 30


def test_long_discovery_interval_does_not_expand_photometry_window():
    discovery = replace(
        short_mcnaught_discovery(),
        start_utc=datetime(2007, 1, 12, tzinfo=timezone.utc),
        stop_utc=datetime(2027, 1, 12, tzinfo=timezone.utc),
    )

    result = comet_photometry.characterize_discovery_photometry(
        discovery,
        observer_location="La Ligua",
        fetch=lambda url, parameters: synthetic_photometry_response(parameters),
    )

    assert result.magnitude_step == "1d"
    assert len(result.results[0].samples) == 61
    assert (
        result.results[0].stop_utc - result.results[0].start_utc
        == timedelta(days=60)
    )


def test_characterization_limits_and_any_provider_failure_fail_whole():
    discovery = short_mcnaught_discovery()
    calls = []
    too_many = replace(
        discovery,
        records=(discovery.records[0],)
        * (comet_photometry.MAX_COMETS + 1),
    )
    with pytest.raises(ValueError, match="current limit is 50"):
        comet_photometry.characterize_discovery_photometry(
            too_many,
            observer_location="La Ligua",
            fetch=lambda *values: calls.append(values),
        )
    assert calls == []

    authorized = comet_photometry.characterize_discovery_photometry(
        too_many,
        observer_location="La Ligua",
        max_comets=comet_photometry.MAX_COMETS + 1,
        fetch=lambda url, parameters: synthetic_photometry_response(parameters),
    )
    assert len(authorized.results) == comet_photometry.MAX_COMETS + 1

    repeated = replace(
        discovery,
        records=(discovery.records[0], discovery.records[0]),
    )
    provider_calls = []

    def fail_second(url, parameters):
        provider_calls.append((url, parameters))
        if len(provider_calls) == 1:
            return synthetic_photometry_response(parameters)
        raise RuntimeError("provider unavailable")

    with pytest.raises(RuntimeError, match="provider unavailable"):
        comet_photometry.characterize_discovery_photometry(
            repeated,
            observer_location="La Ligua",
            magnitude_step="12h",
            fetch=fail_second,
        )
    assert len(provider_calls) == 2


def test_cli_observer_photometry_table_and_json_contract(
    tmp_path, monkeypatch
):
    discovery = short_mcnaught_discovery()
    photometry = comet_photometry.characterize_discovery_photometry(
        discovery,
        observer_location="La Ligua",
        magnitude_step="12h",
        fetch=lambda url, parameters: synthetic_photometry_response(parameters),
        now=lambda: datetime(2026, 9, 14, tzinfo=timezone.utc),
    )
    table = comets.table_text(discovery, photometry)
    document = json.loads(comets.json_text(discovery, photometry))

    assert "brightest sampled T-mag model" in table
    assert "not continuous minima, visibility, or detectability" in table
    assert "roughly 1 mag" in table
    full_discovery = comet_discovery.discover_comets(
        "2026-09-01", "2026-09-30", fetch=lambda *values: fixture_bytes()
    )
    unknown_samples = tuple(
        replace(sample, total_magnitude=None, nuclear_magnitude=None)
        for sample in photometry.results[0].samples
    )
    unknown = replace(
        photometry.results[0],
        canonical_designation=full_discovery.records[0].canonical_designation,
        provider_spk_id=full_discovery.records[0].spk_id,
        orbit_solution_id=full_discovery.records[0].orbit_solution_id,
        samples=unknown_samples,
    )
    known = replace(
        photometry.results[0],
        canonical_designation=full_discovery.records[1].canonical_designation,
        provider_spk_id=full_discovery.records[1].spk_id,
        orbit_solution_id=full_discovery.records[1].orbit_solution_id,
    )
    ordered_photometry = replace(
        photometry,
        results=(unknown, known),
    )
    ordered_table = comets.table_text(full_discovery, ordered_photometry)
    ordered_json = json.loads(
        comets.json_text(full_discovery, ordered_photometry)
    )
    assert ordered_table.index("2P") < ordered_table.index("C/2026 A1")
    assert [
        value["canonical_designation"]
        for value in ordered_json["records"]
    ] == ["2P", "C/2026 A1"]

    model = document["records"][0]["observer_model_photometry"]
    assert model["brightest_sampled_total"]["value"] == -11.0
    assert model["brightest_sampled_nuclear"]["value"] == 12.0
    assert model["provider"]["raw_sha256"] == photometry.results[0].raw_sha256
    assert model["provider"]["endpoint"].endswith("/api/horizons_file.api")
    assert model["provider"]["transport"] == "multipart/form-data POST"
    assert len(model["samples"]) == 121
    assert model["sampling"]["sample_count"] == 121

    output = tmp_path / "comets.json"
    monkeypatch.setattr(
        comets, "discover_comets", lambda *args, **kwargs: discovery
    )
    monkeypatch.setattr(
        comets,
        "characterize_discovery_photometry",
        lambda *args, **kwargs: photometry,
    )
    assert comets.main([
        "2026-09-01",
        "2026-09-02",
        "--observer-location",
        "La Ligua",
        "--magnitude-step",
        "12h",
        "--format",
        "json",
        "--output",
        str(output),
    ]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))[
        "observer_model_photometry"
    ]["observer"]["location"] == "La Ligua"

    with pytest.raises(SystemExit):
        comets.main([
            "2026-09-01",
            "2026-09-02",
            "--magnitude-step",
            "1d",
        ])


def test_cli_formats_expected_failures_and_restores_debug_traceback(
    monkeypatch, capsys
):
    discovery = short_mcnaught_discovery()
    monkeypatch.setattr(
        comets, "discover_comets", lambda *args, **kwargs: discovery
    )
    monkeypatch.setattr(
        comets,
        "characterize_discovery_photometry",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError("provider workload rejected")
        ),
    )

    assert comets.main([
        "2000-01-01", "2020-01-01",
        "--observer-location", "La Ligua",
    ]) == 2
    assert capsys.readouterr().err == (
        "wenu_retrieve_comets: error: provider workload rejected\n"
    )
    with pytest.raises(ValueError, match="provider workload rejected"):
        comets.main([
            "2000-01-01", "2020-01-01",
            "--observer-location", "La Ligua", "--debug",
        ])


def test_zero_match_table_is_explicit():
    discovery = replace(short_mcnaught_discovery(), records=())

    assert "Matched comets: 0" in comets.table_text(discovery)


def test_console_entry_point_is_packaged():
    project = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'wenu_retrieve_comets = "wenu.cli.comets:main"' in project
