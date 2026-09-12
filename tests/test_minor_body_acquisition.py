"""Moving-object preflight acquisition and immutable-cache contracts."""

from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu.cli import chart
from wenu.minor_body_acquisition import (
    MovingObjectDataPolicy,
    _publish_acquisition,
    coverage_interval,
    ensure_numbered_asteroid_resources,
)


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


def test_cli_preflight_installs_resolved_directory_before_chart_build(
    tmp_path, monkeypatch
):
    arguments = chart.parser().parse_args([
        "regional", "--center-on", "asteroid:79989",
        "--data-policy", "offline",
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
    monkeypatch.setattr(chart, "resource_covers", lambda *values: False)
    monkeypatch.setattr(
        chart,
        "ensure_numbered_asteroid_resources",
        lambda numbers, root, start, stop, policy: (
            calls.append((numbers, root, start, stop, policy))
            or SimpleNamespace(
                resource_directory=resolved, acquired=False
            )
        ),
    )

    chart._preflight_minor_body_resources(
        arguments, configuration, observer, None
    )

    assert arguments.minor_body_resource_directory == resolved
    assert calls[0][0] == (79989,)
    assert calls[0][4] == "offline"


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
    tmp_path,
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

    chart._preflight_minor_body_resources(
        arguments, configuration, observer, None
    )

    assert arguments.minor_body_resource_directory == tmp_path


def test_automatic_name_lookup_remains_outside_numbered_asteroid_slice():
    arguments = chart.parser().parse_args([
        "regional", "--asteroid", "ceres",
    ])

    with pytest.raises(ValueError, match="positive permanent number"):
        chart._numbered_asteroid_selections(arguments)
