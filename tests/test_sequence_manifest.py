"""Deterministic observer-time sequence manifest contracts."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from wenu.charts.product_options import ChartProductOptions
from wenu.charts.request import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartRequest,
)
from wenu.charts.sequence import ObserverTimeChartSequenceRequest
from wenu.charts.sequence_manifest import (
    ObserverTimeSequenceManifest,
    SEQUENCE_MANIFEST_NAME,
    read_observer_time_sequence_manifest,
    write_observer_time_sequence_manifest,
)
from wenu.configuration import load_configuration_defaults
from wenu.output_policy import OutputFormat
from wenu.temporal import PlaybackSpec, TemporalTimeline


def sequence(output, *, title="Sequence", stop_hour=7):
    chart = ChartRequest(
        observer=ChartObserverRequest(
            time="2000-01-01T00:00:00Z",
            location="La Ligua",
        ),
        family="circumpolar",
        frame=ChartFrameRequest(
            pole="south",
            limiting_declination_deg=-60,
        ),
        product=ChartProductOptions(
            output=output,
            output_format=OutputFormat.PNG,
        ),
        title=title,
    )
    timeline = TemporalTimeline.uniform(
        datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
        datetime(2026, 8, 22, stop_hour, tzinfo=timezone.utc),
        2,
        display_timezone="America/Santiago",
    )
    return ObserverTimeChartSequenceRequest(
        chart=chart,
        timeline=timeline,
        playback=PlaybackSpec(timedelta(seconds=1), 2),
    )


def test_manifest_is_deterministic_and_portable_between_directories(tmp_path):
    first = ObserverTimeSequenceManifest.from_sequence(
        sequence(tmp_path / "first")
    )
    second_sequence = sequence(tmp_path / "second")
    second_sequence = replace(
        second_sequence,
        chart=replace(
            second_sequence.chart,
            observer=replace(
                second_sequence.chart.observer,
                time="1999-12-31T23:59:59Z",
            ),
        ),
    )
    second = ObserverTimeSequenceManifest.from_sequence(second_sequence)

    assert first.to_json() == second.to_json()
    assert first.identity_sha256 == second.identity_sha256
    assert [frame.name for frame in first.frames] == [
        "frame-0000.png",
        "frame-0001.png",
    ]
    assert json.loads(first.to_json())["identity_sha256"] == (
        first.identity_sha256
    )


def test_manifest_round_trip_and_atomic_default_write(tmp_path):
    request = sequence(tmp_path / "frames")

    path = write_observer_time_sequence_manifest(request)

    assert path == tmp_path / "frames" / SEQUENCE_MANIFEST_NAME
    assert not (path.parent / f".{path.name}.tmp").exists()
    restored = read_observer_time_sequence_manifest(path)
    assert restored == ObserverTimeSequenceManifest.from_sequence(request)
    restored.assert_compatible(request)


def test_manifest_rejects_changed_chart_or_timeline(tmp_path):
    original = sequence(tmp_path / "frames")
    manifest = ObserverTimeSequenceManifest.from_sequence(original)

    with pytest.raises(ValueError, match="incompatible"):
        manifest.assert_compatible(
            replace(
                original,
                chart=replace(original.chart, title="Different"),
            )
        )
    with pytest.raises(ValueError, match="incompatible"):
        manifest.assert_compatible(
            sequence(tmp_path / "frames", stop_hour=8)
        )


def test_manifest_rejects_tampering_and_unknown_fields(tmp_path):
    manifest = ObserverTimeSequenceManifest.from_sequence(
        sequence(tmp_path / "frames")
    )
    document = json.loads(manifest.to_json())
    document["timeline"]["display_timezone"] = "UTC"

    with pytest.raises(ValueError, match="hash does not match"):
        ObserverTimeSequenceManifest.from_json(json.dumps(document))

    document = json.loads(manifest.to_json())
    document["unexpected"] = True
    identity = document.pop("identity_sha256")
    document["identity_sha256"] = identity
    with pytest.raises(ValueError):
        ObserverTimeSequenceManifest.from_json(json.dumps(document))


def test_manifest_requires_offset_aware_frame_times(tmp_path):
    manifest = ObserverTimeSequenceManifest.from_sequence(
        sequence(tmp_path / "frames")
    )
    document = json.loads(manifest.to_json())
    document["frames"][0]["simulation_time"] = "2026-08-22T01:00:00"
    document.pop("identity_sha256")

    with pytest.raises(ValueError, match="UTC offset"):
        ObserverTimeSequenceManifest.from_json(json.dumps(document))


def test_completion_records_do_not_change_plan_identity(tmp_path):
    request = sequence(tmp_path / "frames")
    manifest = ObserverTimeSequenceManifest.from_sequence(request)
    output = request.frames[0].expected_output
    output.parent.mkdir(parents=True)
    output.write_bytes(b"verified frame")

    completed = manifest.with_completed_output(0, output)

    assert completed.identity_sha256 == manifest.identity_sha256
    assert completed.frames[0].is_complete
    assert completed.frames[0].output_bytes == len(b"verified frame")
    assert completed.output_is_valid(0, output)
    output.write_bytes(b"changed")
    assert not completed.output_is_valid(0, output)


def test_completion_progress_survives_manifest_round_trip(tmp_path):
    request = sequence(tmp_path / "frames")
    manifest = ObserverTimeSequenceManifest.from_sequence(request)
    output = request.frames[1].expected_output
    output.parent.mkdir(parents=True)
    output.write_bytes(b"second frame")
    completed = manifest.with_completed_output(1, output)

    restored = ObserverTimeSequenceManifest.from_json(completed.to_json())

    assert restored == completed
    assert restored.output_is_valid(1, output)


def test_manifest_identity_includes_effective_configuration(tmp_path):
    plain = sequence(tmp_path / "frames")
    configured = replace(
        plain,
        configuration=load_configuration_defaults(),
    )

    plain_manifest = ObserverTimeSequenceManifest.from_sequence(plain)
    configured_manifest = ObserverTimeSequenceManifest.from_sequence(configured)
    restored = ObserverTimeSequenceManifest.from_json(
        configured_manifest.to_json()
    )

    assert plain_manifest.configuration is None
    assert configured_manifest.configuration is not None
    assert configured_manifest.identity_sha256 != plain_manifest.identity_sha256
    assert restored == configured_manifest
    with pytest.raises(ValueError, match="incompatible"):
        plain_manifest.assert_compatible(configured)
