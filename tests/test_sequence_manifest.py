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


@pytest.mark.parametrize("change", ("playback", "display", "physical", "reference", "configuration"))
def test_resume_identity_rejects_changed_time_presentation_and_realization_inputs(tmp_path, change):
    from wenu.charts.reference_policy import CelestialReferencePolicy

    planned = sequence(tmp_path / "frames")
    if change == "playback":
        changed = replace(planned, playback=PlaybackSpec(timedelta(seconds=2), 1))
        assert changed.timeline == planned.timeline
    elif change == "display":
        changed = replace(planned, timeline=replace(planned.timeline, display_timezone="UTC"))
        assert changed.timeline.instants == planned.timeline.instants
    elif change == "physical":
        changed = replace(planned, timeline=TemporalTimeline.uniform(
            planned.timeline.instants[0], planned.timeline.instants[-1] + timedelta(seconds=1), 2,
            display_timezone=planned.timeline.display_timezone))
    elif change == "reference":
        changed = replace(planned, chart=replace(planned.chart,
            reference_policy=CelestialReferencePolicy("of_date")))
    else:
        changed = replace(planned, configuration=load_configuration_defaults())
    manifest = ObserverTimeSequenceManifest.from_sequence(planned)
    assert manifest.identity_sha256 != ObserverTimeSequenceManifest.from_sequence(changed).identity_sha256
    with pytest.raises(ValueError, match="incompatible"):
        manifest.assert_compatible(changed)


def test_repeated_civil_hour_keeps_distinct_physical_frame_identity(tmp_path):
    planned = sequence(tmp_path / "frames")
    instants = (datetime(2026, 11, 1, 5, 30, tzinfo=timezone.utc),
                datetime(2026, 11, 1, 6, 30, tzinfo=timezone.utc))
    planned = replace(planned, timeline=TemporalTimeline(instants,
        display_timezone="America/New_York"))
    manifest = ObserverTimeSequenceManifest.from_sequence(planned)
    assert tuple(frame.simulation_time for frame in manifest.frames) == tuple(t.isoformat() for t in instants)
    assert manifest.frames[0].display_time != manifest.frames[1].display_time
    assert tuple(datetime.fromisoformat(frame.display_time).astimezone(timezone.utc)
        for frame in manifest.frames) == instants
    assert ObserverTimeSequenceManifest.from_json(manifest.to_json()) == manifest



def test_cluster_model_identity_retains_active_inputs_and_lookup_compatibility(tmp_path):
    from wenu.charts.sequence_manifest import _chart_request_identity
    from wenu.charts.request_satellite_tracks import chart_request_provenance_parameters
    from wenu.charts.request import ClusterMotionRequest
    base=sequence(tmp_path).chart
    assert 'cluster_motion' not in _chart_request_identity(base)
    assert 'cluster_motion' not in chart_request_provenance_parameters(base)
    admitted=ClusterMotionRequest(model='nominal-observed',identifiers=('constructed',),
        leap_seconds_path='/synthetic/leaps',leap_seconds_sha256='0'*64,
        eop_path='/synthetic/eop',eop_sha256='1'*64,
        backend_identity=('synthetic','synthetic','synthetic','2'*64),
        start_jd_tt=2456000.,stop_jd_tt=2457000.,start_jd_tcb=2400000.,stop_jd_tcb=2500000.,
        height_wgs84_m=52.)
    active=replace(base,cluster_motion=admitted)
    identity=_chart_request_identity(active)
    assert identity['cluster_motion']['eop_sha256']=='1'*64
    assert chart_request_provenance_parameters(active)['cluster_motion']['identifiers']==('constructed',)
    assert _chart_request_identity(replace(active,cluster_motion=replace(admitted,identifiers=('other',))))!=identity

    configured=replace(sequence(tmp_path/'configured'),configuration=load_configuration_defaults())
    assert 'cluster_motion' not in ObserverTimeSequenceManifest.from_sequence(configured).configuration
    active_configured=replace(configured,chart=replace(configured.chart,cluster_motion=admitted))
    assert 'cluster_motion' in ObserverTimeSequenceManifest.from_sequence(active_configured).chart_request
