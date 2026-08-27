"""Command-line temporal sequence vocabulary tests."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from wenu.charts.sequence_arguments import chart_sequence_cli_options
from wenu.configuration import SequenceDefaults
from wenu.charts.sequence_manifest import SequenceRestartPolicy


def arguments(**values):
    defaults = {
        "sequence_stop": None,
        "sequence_frames": None,
        "display_timezone": None,
        "playback_duration": None,
        "frames_per_second": None,
        "restart_policy": "restart",
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def test_omitted_sequence_controls_preserve_static_generation():
    assert chart_sequence_cli_options(
        arguments(),
        start=datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
    ) is None


def test_cli_sequence_resolves_physical_and_display_time_separately():
    options = chart_sequence_cli_options(
        arguments(
            sequence_stop="2026-08-22T07:00:00+00:00",
            sequence_frames=3,
            display_timezone="America/Santiago",
            playback_duration=1.5,
            frames_per_second=2,
            restart_policy="resume",
        ),
        start=datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
    )

    assert options.timeline.frame_count == 3
    assert options.timeline.instants[0].isoformat() == (
        "2026-08-22T01:00:00+00:00"
    )
    assert options.timeline.display_instants[0].isoformat() == (
        "2026-08-21T21:00:00-04:00"
    )
    assert options.playback.duration.total_seconds() == pytest.approx(1.5)
    assert options.playback.frames_per_second == pytest.approx(2.0)
    assert options.restart_policy is SequenceRestartPolicy.RESUME


def test_cli_sequence_uses_observer_timezone_as_display_default():
    options = chart_sequence_cli_options(
        arguments(
            sequence_stop="2026-08-22T07:00:00Z",
            sequence_frames=2,
        ),
        start=datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
        default_display_timezone="America/Santiago",
    )

    assert options.timeline.display_timezone == "America/Santiago"


@pytest.mark.parametrize(
    ("values", "message"),
    (
        ({"sequence_stop": "2026-08-22T07:00:00Z"}, "must be used together"),
        ({"sequence_frames": 3}, "must be used together"),
        ({"display_timezone": "UTC"}, "require --sequence-stop"),
        ({"restart_policy": "resume"}, "require --sequence-stop"),
        (
            {
                "sequence_stop": "2026-08-22T07:00:00Z",
                "sequence_frames": 3,
                "playback_duration": 1.5,
            },
            "must be used together",
        ),
    ),
)
def test_cli_sequence_rejects_incomplete_control_sets(values, message):
    with pytest.raises(ValueError, match=message):
        chart_sequence_cli_options(
            arguments(**values),
            start=datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
        )


def test_cli_sequence_requires_an_offset_aware_stop():
    with pytest.raises(ValueError, match="UTC offset"):
        chart_sequence_cli_options(
            arguments(
                sequence_stop="2026-08-22T07:00:00",
                sequence_frames=2,
            ),
            start=datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
        )


def test_cli_values_override_sequence_configuration_defaults():
    defaults = SequenceDefaults(
        stop="2026-08-22T05:00:00Z",
        frames=3,
        display_timezone="UTC",
        playback_duration_seconds=None,
        frames_per_second=None,
        restart_policy="restart",
    )

    options = chart_sequence_cli_options(
        arguments(
            sequence_stop="2026-08-22T07:00:00Z",
            sequence_frames=2,
            display_timezone="America/Santiago",
            restart_policy="resume",
        ),
        start=datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
        defaults=defaults,
    )

    assert options.timeline.frame_count == 2
    assert options.timeline.instants[-1].hour == 7
    assert options.timeline.display_timezone == "America/Santiago"
    assert options.restart_policy is SequenceRestartPolicy.RESUME


def test_complete_sequence_configuration_activates_without_cli_values():
    defaults = SequenceDefaults(
        stop="2026-08-22T07:00:00Z",
        frames=2,
        display_timezone="America/Santiago",
        playback_duration_seconds=None,
        frames_per_second=None,
        restart_policy="resume",
    )

    options = chart_sequence_cli_options(
        SimpleNamespace(
            sequence_stop=None,
            sequence_frames=None,
            display_timezone=None,
            playback_duration=None,
            frames_per_second=None,
            restart_policy=None,
        ),
        start=datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
        defaults=defaults,
    )

    assert options.timeline.frame_count == 2
    assert options.restart_policy is SequenceRestartPolicy.RESUME
