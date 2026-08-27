"""Temporal-sequence contract tests."""

from datetime import datetime, timedelta, timezone

import pytest

from wenu.temporal import (
    PlaybackSpec,
    SamplingKind,
    TemporalTimeline,
    TimeScale,
)


def test_uniform_timeline_separates_physical_and_civil_time():
    start = datetime.fromisoformat("2026-08-21T21:00:00-04:00")
    stop = datetime.fromisoformat("2026-08-22T09:00:00-04:00")

    timeline = TemporalTimeline.uniform(
        start,
        stop,
        181,
        display_timezone="America/Santiago",
    )

    assert timeline.time_scale is TimeScale.UTC
    assert timeline.frame_count == 181
    assert timeline.instants[0] == datetime(
        2026, 8, 22, 1, tzinfo=timezone.utc
    )
    assert timeline.instants[-1] == datetime(
        2026, 8, 22, 13, tzinfo=timezone.utc
    )
    assert timeline.simulation_duration == timedelta(hours=12)
    assert timeline.sampling_interval == timedelta(minutes=4)
    assert timeline.sampling_kind is SamplingKind.UNIFORM
    assert timeline.display_instants[0].isoformat() == (
        "2026-08-21T21:00:00-04:00"
    )


def test_explicit_irregular_timeline_has_no_uniform_interval():
    timeline = TemporalTimeline(
        (
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 1, 0, 3, tzinfo=timezone.utc),
        )
    )

    assert timeline.sampling_kind is SamplingKind.EXPLICIT
    assert timeline.sampling_interval is None


def test_timeline_rejects_ambiguous_or_unordered_instants():
    with pytest.raises(ValueError, match="UTC offset"):
        TemporalTimeline((datetime(2026, 1, 1),))

    instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="strictly increasing"):
        TemporalTimeline((instant, instant))


def test_timeline_requires_a_real_display_timezone():
    with pytest.raises(ValueError, match="IANA"):
        TemporalTimeline(
            (datetime(2026, 1, 1, tzinfo=timezone.utc),),
            display_timezone="UTC-4",
        )


def test_playback_cadence_is_independent_of_simulation_duration():
    timeline = TemporalTimeline.uniform(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
        180,
    )
    playback = PlaybackSpec(
        duration=timedelta(seconds=15),
        frames_per_second=12,
    )

    assert timeline.simulation_duration == timedelta(hours=12)
    assert playback.duration == timedelta(seconds=15)
    assert playback.frames_per_second == 12.0
    assert playback.frame_count == 180
    playback.validate_timeline(timeline)


def test_playback_rejects_a_mismatched_timeline():
    timeline = TemporalTimeline.uniform(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        24,
    )
    playback = PlaybackSpec(timedelta(seconds=2), 25)

    with pytest.raises(ValueError, match="frame count"):
        playback.validate_timeline(timeline)


def test_frame_names_are_deterministic():
    timeline = TemporalTimeline.uniform(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        2,
    )

    assert timeline.frame_name(0) == "frame-0000.png"
    assert timeline.frame_name(
        1,
        prefix="chart",
        suffix=".svg",
        width=3,
    ) == "chart-001.svg"

    with pytest.raises(IndexError):
        timeline.frame_name(2)
