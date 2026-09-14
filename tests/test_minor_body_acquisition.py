"""Moving-object preflight acquisition and immutable-cache contracts."""

from dataclasses import replace
from datetime import datetime, timezone
import base64
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu.cli import chart
from wenu.minor_body_acquisition import (
    MovingObjectDataPolicy,
    _identity_keys,
    _publish_acquisition,
    acquire_minor_body_resources,
    coverage_interval,
    ensure_minor_body_resources,
    ensure_numbered_asteroid_resources,
)
from wenu.minor_body_identity import ResolvedMinorBodyIdentity
from wenu.minor_body_resources import MinorBodyResourceCollection


def resolved_tempel_2():
    return ResolvedMinorBodyIdentity(
        original_selection="10P",
        normalized_selection="10p",
        object_class="comet",
        kind="cn",
        canonical_designation="10P",
        primary_designation="10P",
        prefix="P",
        permanent_number=10,
        fragment=None,
        name="Tempel 2",
        aliases=("10P", "10P/Tempel 2", "Tempel 2"),
        provider_spk_id="1000094",
        orbit_class_code="JFc",
        orbit_class_name="Jupiter-family Comet",
        orbit_solution_id="K265/50",
        provider="NASA/JPL Small-Body Database (SBDB) API",
        provider_version="1.3",
        source="provider",
        request_parameters=(("des", "10P"),),
        retrieved_at_utc=datetime(2026, 9, 13, tzinfo=timezone.utc),
        raw_sha256="a" * 64,
    )


def horizons_tempel_2(*, spk=False, target="1000094"):
    result = """JPL/HORIZONS                    10P/Tempel 2               2026-Sep-13 18:15:46
Rec #:90000214 (+COV) Soln.date: 2026-Sep-08_14:24:57   # obs: 6790 (2003-2026)
EPOCH=  2457869.5 ! 2017-Apr-26.0000000 (TDB)
Comet non-gravitational force model
 AMRAT=  0. DT=  0.
 A1= 2.556003071368E-10 A2= 8.289547404274E-12 A3= 0.
 ALN= .1112620426 NK= 4.6142 NM= 2.15 NN= 5.093 R0= 2.808
COMET comments
1: soln ref.= JPL#K265/50, data arc: 2003-03-07 to 2026-09-07
"""
    document = {
        "signature": {
            "source": "NASA/JPL Horizons API",
            "version": "1.2",
        },
        "result": result,
    }
    if spk:
        document.update({
            "spk_file_id": target,
            "spk": base64.b64encode(b"DAF/fake comet").decode("ascii"),
        })
    return document


def test_policy_reuses_warm_cache_without_acquisition(tmp_path):
    cached = tmp_path / "verified"
    calls = []

    result = ensure_numbered_asteroid_resources(
        (79989,), tmp_path, "2026-08-01", "2026-10-01",
        finder=lambda *values: cached,
        acquire=lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    assert result.resource_directory == cached
    assert result.policy is MovingObjectDataPolicy.ACQUIRE_IF_MISSING
    assert result.acquired is False
    assert calls == []


def test_offline_policy_fails_before_any_acquisition(tmp_path):
    calls = []

    with pytest.raises(FileNotFoundError, match="offline data policy"):
        ensure_numbered_asteroid_resources(
            (79989,), tmp_path, "2026-08-01", "2026-10-01",
            policy="offline",
            finder=lambda *values: None,
            acquire=lambda *args, **kwargs: calls.append((args, kwargs)),
        )

    assert calls == []


def test_refresh_acquires_even_when_a_warm_resource_exists(
    tmp_path, monkeypatch
):
    cached = tmp_path / "old"
    fresh = tmp_path / "new"
    calls = []
    monkeypatch.setattr(
        "wenu.minor_body_acquisition._publish_acquisition",
        lambda root, numbers, start, stop, acquire: (
            calls.append((root, numbers, start, stop, acquire)) or fresh
        ),
    )

    result = ensure_numbered_asteroid_resources(
        (79989,), tmp_path, "2026-08-01", "2026-10-01",
        policy="refresh",
        finder=lambda *values: cached,
        acquire=object(),
    )

    assert result.resource_directory == fresh
    assert result.policy is MovingObjectDataPolicy.REFRESH
    assert result.acquired is True
    assert len(calls) == 1


def test_publication_is_content_addressed_and_leaves_no_staging_directory(
    tmp_path, monkeypatch
):
    def acquire(numbers, directory, *, start, stop):
        assert numbers == (79989,)
        (directory / "79989.bsp").write_bytes(b"DAF/test")
        manifest = directory / "acquisition-report.json"
        manifest.write_text(json.dumps({
            "resources": [{
                "identity": {"permanent_number": 79989},
                "filename": "79989.bsp",
                "sha256": "unused by injected validation",
                "coverage_request": {"start": start, "stop": stop},
            }]
        }, sort_keys=True) + "\n", encoding="utf-8")
        return manifest

    monkeypatch.setattr(
        "wenu.minor_body_acquisition.resource_covers",
        lambda *values: True,
    )
    destination = _publish_acquisition(
        tmp_path, (79989,), "2026-08-01", "2026-10-01", acquire
    )

    assert len(destination.name) == 64
    assert (destination / "acquisition-report.json").is_file()
    assert not tuple(tmp_path.glob(".acquire-*"))


def test_coverage_interval_contains_static_sequence_and_track_instants():
    start, stop = coverage_interval((
        datetime(2026, 9, 16, tzinfo=timezone.utc),
        datetime(2026, 12, 1, tzinfo=timezone.utc),
    ))

    assert start == "2026-08-17"
    assert stop == "2026-12-31"


def test_cli_collects_numbered_center_point_and_track_selections():
    arguments = chart.parser().parse_args([
        "regional", "--center-on", "asteroid:79989",
        "--asteroid", "79989", "--asteroid-track", "1",
        "--track-start", "2026-09-01", "--track-sample-step", "1d",
        "--track-tick-step", "7d", "--track-tick-count", "2",
    ])

    assert chart._numbered_asteroid_selections(arguments) == (1, 79989)


def test_cli_collects_unqualified_numbered_asteroid_center():
    arguments = chart.parser().parse_args([
        "regional", "--center-on", "79989",
    ])

    assert chart._numbered_asteroid_selections(arguments) == (79989,)


def test_cli_collects_typed_comet_point_track_and_explicit_center_once():
    arguments = chart.parser().parse_args([
        "regional", "--center-on", "comet:10P",
        "--comet", "10P", "--comet-track", "10P",
        "--track-start", "2026-09-01", "--track-sample-step", "1d",
        "--track-tick-step", "7d", "--track-tick-count", "2",
    ])

    assert chart._typed_minor_body_selections(arguments) == (
        ("comet", "10p"),
    )


def test_cli_preflight_installs_resolved_directory_before_chart_build(
    tmp_path, monkeypatch
):
    arguments = chart.parser().parse_args([
        "regional", "--center-on", "asteroid:79989",
        "--data-policy", "acquire-if-missing",
    ])
    observer = SimpleNamespace(
        utc_datetime=datetime(2026, 9, 16, tzinfo=timezone.utc),
        data_directory=tmp_path,
    )
    configuration = SimpleNamespace(
        minor_body_resource_directory=None,
        moving_object_data_policy="acquire-if-missing",
    )
    resolved = tmp_path / "resolved"
    calls = []
    identity = replace(
        resolved_tempel_2(),
        object_class="asteroid",
        canonical_designation="79989",
        primary_designation="79989",
        permanent_number=79989,
        name=None,
        aliases=("79989",),
        provider_spk_id="2079989",
    )
    monkeypatch.setattr(
        chart, "_candidate_minor_body_directories", lambda observer: (),
    )
    monkeypatch.setattr(
        chart, "resolve_minor_body_identity", lambda *args, **kwargs: identity,
    )
    monkeypatch.setattr(
        chart,
        "ensure_minor_body_resources",
        lambda identities, root, start, stop, policy: (
            calls.append((identities, root, start, stop, policy))
            or SimpleNamespace(
                resource_directory=resolved, acquired=False
            )
        ),
    )

    chart._preflight_minor_body_resources(
        arguments, configuration, observer, None
    )

    assert arguments.minor_body_resource_directory == resolved
    assert calls[0][0] == (identity,)
    assert calls[0][4] == "acquire-if-missing"


def test_explicit_resource_directory_cannot_be_refreshed(tmp_path):
    arguments = chart.parser().parse_args([
        "regional", "--asteroid", "79989",
        "--minor-body-resource-directory", str(tmp_path),
        "--data-policy", "refresh",
    ])
    configuration = SimpleNamespace(
        minor_body_resource_directory=None,
        moving_object_data_policy="acquire-if-missing",
    )
    observer = SimpleNamespace(
        utc_datetime=datetime(2026, 9, 16, tzinfo=timezone.utc),
        data_directory=tmp_path,
    )

    with pytest.raises(ValueError, match="cannot replace an explicit"):
        chart._preflight_minor_body_resources(
            arguments, configuration, observer, None
        )


def test_explicit_resource_directory_preserves_installed_name_selection(
    tmp_path, monkeypatch,
):
    arguments = chart.parser().parse_args([
        "regional", "--asteroid", "ceres",
        "--minor-body-resource-directory", str(tmp_path),
    ])
    configuration = SimpleNamespace(
        minor_body_resource_directory=None,
        moving_object_data_policy="acquire-if-missing",
    )
    observer = SimpleNamespace(
        utc_datetime=datetime(2026, 9, 16, tzinfo=timezone.utc),
        data_directory=tmp_path,
    )
    monkeypatch.setattr(
        chart, "_installed_candidate", lambda *values: (object(),),
    )

    chart._preflight_minor_body_resources(
        arguments, configuration, observer, None
    )

    assert arguments.minor_body_resource_directory == tmp_path


def test_comet_track_extends_preflight_coverage():
    arguments = chart.parser().parse_args([
        "regional", "--comet-track", "10P",
        "--track-start", "2026-09-01", "--track-sample-step", "1d",
        "--track-tick-step", "7d", "--track-tick-count", "4",
    ])
    observer = SimpleNamespace(
        utc_datetime=datetime(2026, 9, 16, tzinfo=timezone.utc),
    )

    instants = chart._minor_body_coverage_instants(arguments, observer, None)

    assert instants[1] == datetime(2026, 9, 1, tzinfo=timezone.utc)
    assert instants[2] == datetime(2026, 9, 29, tzinfo=timezone.utc)


def test_cli_preflight_composes_one_mixed_identity_collection(
    tmp_path, monkeypatch
):
    arguments = chart.parser().parse_args([
        "regional", "--asteroid-track", "79989",
        "--comet-track", "10P",
        "--track-start", "2026-09-01", "--track-sample-step", "1d",
        "--track-tick-step", "7d", "--track-tick-count", "2",
    ])
    observer = SimpleNamespace(
        utc_datetime=datetime(2026, 9, 16, tzinfo=timezone.utc),
        data_directory=tmp_path,
    )
    configuration = SimpleNamespace(
        minor_body_resource_directory=None,
        moving_object_data_policy="acquire-if-missing",
    )
    asteroid = replace(
        resolved_tempel_2(),
        object_class="asteroid",
        canonical_designation="79989",
        primary_designation="79989",
        permanent_number=79989,
        name=None,
        aliases=("79989",),
        provider_spk_id="2079989",
    )
    comet = resolved_tempel_2()
    identities = {"79989": asteroid, "10p": comet}
    calls = []
    destination = tmp_path / "mixed"
    monkeypatch.setattr(
        chart, "_candidate_minor_body_directories", lambda observer: (),
    )
    monkeypatch.setattr(
        chart,
        "resolve_minor_body_identity",
        lambda selection, **kwargs: identities[selection],
    )
    monkeypatch.setattr(
        chart,
        "ensure_minor_body_resources",
        lambda resolved, root, start, stop, policy: (
            calls.append((resolved, root, start, stop, policy))
            or SimpleNamespace(resource_directory=destination, acquired=True)
        ),
    )

    chart._preflight_minor_body_resources(
        arguments, configuration, observer, None
    )

    assert calls[0][0] == (asteroid, comet)
    assert arguments.minor_body_resource_directory == destination


def test_automatic_name_lookup_remains_outside_numbered_asteroid_slice():
    arguments = chart.parser().parse_args([
        "regional", "--asteroid", "ceres",
    ])

    with pytest.raises(ValueError, match="positive permanent number"):
        chart._numbered_asteroid_selections(arguments)


def test_resolved_comet_binds_unique_horizons_record_and_publishes_manifest(
    tmp_path, monkeypatch
):
    calls = []

    def fetch(url, parameters):
        calls.append((url, parameters))
        return horizons_tempel_2(spk=len(calls) == 2)

    monkeypatch.setattr(
        "wenu.minor_body_acquisition._actual_coverage",
        lambda path, target, **options: {
            "start_jd_tdb": 2461254.5,
            "stop_jd_tdb": 2461374.5,
        },
    )
    manifest = acquire_minor_body_resources(
        (resolved_tempel_2(),),
        tmp_path,
        start="2026-08-02",
        stop="2026-11-30",
        fetch_json=fetch,
    )

    assert len(calls) == 2
    assert calls[0][1]["COMMAND"] == "'DES=10P;CAP;NOFRAG'"
    assert calls[1][1]["COMMAND"] == "'90000214;'"
    document = json.loads(manifest.read_text(encoding="utf-8"))
    record = document["resources"][0]
    assert record["spk_file_id"] == "1000094"
    assert record["identity"]["primary_designation"] == "10P"
    assert record["solution"]["orbit_solution_id"] == "K265/50"
    assert "soln ref.= JPL#K265/50" in record["horizons_result"]
    assert record["solution"]["horizons_command"] == "90000214;"
    assert record["solution"]["non_gravitational_parameters"]["A1"] == (
        "2.556003071368E-10"
    )
    assert record["receipt"]["identity_raw_sha256"] == "a" * 64
    collection = MinorBodyResourceCollection(tmp_path)
    assert collection.resolve("Tempel 2").canonical_designation == (
        "10P/Tempel 2"
    )


def test_resolved_comet_rejects_changed_horizons_target(tmp_path, monkeypatch):
    calls = []

    def fetch(url, parameters):
        calls.append(parameters)
        return horizons_tempel_2(
            spk=len(calls) == 2, target="different"
        )

    with pytest.raises(ValueError, match="provider targets differ"):
        acquire_minor_body_resources(
            (resolved_tempel_2(),), tmp_path,
            start="2026-08-02", stop="2026-11-30", fetch_json=fetch,
        )

    assert not tuple(tmp_path.iterdir())


def test_resolved_comet_rejects_nonunique_horizons_lookup(tmp_path):
    ambiguous = horizons_tempel_2()
    ambiguous["result"] = "Matching small-bodies: 10P"

    with pytest.raises(ValueError, match="unique record"):
        acquire_minor_body_resources(
            (resolved_tempel_2(),), tmp_path,
            start="2026-08-02", stop="2026-11-30",
            fetch_json=lambda *values: ambiguous,
        )


def test_typed_preflight_reuses_warm_comet_cache_without_network(tmp_path):
    cached = tmp_path / "verified"
    calls = []

    result = ensure_minor_body_resources(
        (resolved_tempel_2(),), tmp_path,
        "2026-08-02", "2026-11-30",
        finder=lambda *values: cached,
        acquire=lambda *values, **kwargs: calls.append((values, kwargs)),
    )

    assert result.resource_directory == cached
    assert result.acquired is False
    assert calls == []


def test_typed_offline_preflight_reports_identity_and_coverage(tmp_path):
    calls = []

    with pytest.raises(
        FileNotFoundError, match="10P covering 2026-08-02 through 2026-11-30"
    ):
        ensure_minor_body_resources(
            (resolved_tempel_2(),), tmp_path,
            "2026-08-02", "2026-11-30",
            policy="offline",
            finder=lambda *values: None,
            acquire=lambda *values, **kwargs: calls.append((values, kwargs)),
        )

    assert calls == []


def test_typed_publication_is_atomic_and_content_addressed(
    tmp_path, monkeypatch
):
    identity = resolved_tempel_2()

    def acquire(identities, directory, *, start, stop):
        assert identities == (identity,)
        (directory / "10p.bsp").write_bytes(b"DAF/test")
        manifest = directory / "acquisition-report.json"
        manifest.write_text(json.dumps({
            "resources": [{
                "identity": {
                    "object_class": "comet",
                    "provider_spk_id": "1000094",
                    "primary_designation": "10P",
                },
                "filename": "10p.bsp",
                "sha256": "injected",
                "spk_file_id": "1000094",
            }],
        }, sort_keys=True) + "\n", encoding="utf-8")
        return manifest

    checks = []
    monkeypatch.setattr(
        "wenu.minor_body_acquisition.resource_covers_identities",
        lambda *values: checks.append(values) or True,
    )
    result = ensure_minor_body_resources(
        (identity,), tmp_path, "2026-08-02", "2026-11-30",
        policy="refresh", finder=lambda *values: None, acquire=acquire,
    )

    assert result.acquired is True
    assert len(result.resource_directory.name) == 64
    assert len(checks) == 2
    assert not tuple(tmp_path.glob(".acquire-*"))


def test_identity_lock_key_is_filename_safe_for_provisional_comets():
    identity = resolved_tempel_2()
    identity = replace(
        identity,
        canonical_designation="C/2025 E1",
        primary_designation="2025 E1",
        prefix="C",
        permanent_number=None,
    )

    assert len(_identity_keys((identity,))[0]) == 64
    assert "/" not in _identity_keys((identity,))[0]
