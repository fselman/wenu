"""Command-line adaptation for canonical temporal chart sequences."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from wenu.configuration import SequenceDefaults
from wenu.temporal import PlaybackSpec, TemporalTimeline

from .sequence_manifest import SequenceRestartPolicy


@dataclass(frozen=True)
class ChartSequenceCliOptions:
    """Resolved temporal and restart controls for one CLI sequence."""

    timeline: TemporalTimeline
    playback: PlaybackSpec | None
    restart_policy: SequenceRestartPolicy


def add_chart_sequence_arguments(parser):
    """Add optional observer-time sequence controls to a chart parser."""
    parser.add_argument(
        "--sequence-stop",
        metavar="TIME",
        help=(
            "inclusive final simulation time as ISO 8601 with UTC offset; "
            "--observer-time supplies the start"
        ),
    )
    parser.add_argument(
        "--sequence-frames",
        type=int,
        metavar="COUNT",
        help="number of uniformly sampled frames, including both endpoints",
    )
    parser.add_argument(
        "--display-timezone",
        metavar="IANA_ZONE",
        help="civil-time zone recorded for frame display metadata",
    )
    parser.add_argument(
        "--playback-duration",
        type=float,
        metavar="SECONDS",
        help="optional presentation duration, separate from simulation time",
    )
    parser.add_argument(
        "--frames-per-second",
        type=float,
        metavar="FPS",
        help="optional presentation frame rate, separate from simulation time",
    )
    parser.add_argument(
        "--restart-policy",
        choices=tuple(item.value for item in SequenceRestartPolicy),
        default=None,
        help="restart every frame or resume only manifest-verified frames",
    )
    return parser


def _offset_datetime(value, *, option):
    try:
        instant = datetime.fromisoformat(str(value).strip())
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{option} must be an ISO 8601 datetime with UTC offset."
        ) from error
    if instant.utcoffset() is None:
        raise ValueError(
            f"{option} must be an ISO 8601 datetime with UTC offset."
        )
    return instant


def chart_sequence_cli_options(
    arguments,
    *,
    start: datetime,
    default_display_timezone: str = "UTC",
    defaults: SequenceDefaults | None = None,
) -> ChartSequenceCliOptions | None:
    """Resolve optional CLI controls without rendering or reading catalogues."""
    configured = (
        SequenceDefaults(None, None, None, None, None, "restart")
        if defaults is None else defaults
    )
    if not isinstance(configured, SequenceDefaults):
        raise TypeError("defaults must be SequenceDefaults or None.")

    def selected(name, fallback):
        value = getattr(arguments, name, None)
        return fallback if value is None else value

    stop = selected("sequence_stop", configured.stop)
    count = selected("sequence_frames", configured.frames)
    duration = selected(
        "playback_duration",
        configured.playback_duration_seconds,
    )
    frames_per_second = selected(
        "frames_per_second",
        configured.frames_per_second,
    )
    display_timezone = selected(
        "display_timezone",
        configured.display_timezone,
    )
    restart_policy = selected(
        "restart_policy",
        configured.restart_policy,
    )
    sequence_selected = stop is not None or count is not None
    ancillary_selected = any(
        value is not None
        for value in (
            duration,
            frames_per_second,
            display_timezone,
        )
    ) or restart_policy != SequenceRestartPolicy.RESTART.value
    if not sequence_selected:
        if ancillary_selected:
            raise ValueError(
                "Sequence playback, timezone, and restart controls require "
                "--sequence-stop and --sequence-frames."
            )
        return None
    if stop is None or count is None:
        raise ValueError(
            "--sequence-stop and --sequence-frames must be used together."
        )
    if (duration is None) != (frames_per_second is None):
        raise ValueError(
            "--playback-duration and --frames-per-second must be used "
            "together."
        )
    timeline = TemporalTimeline.uniform(
        start,
        _offset_datetime(stop, option="--sequence-stop"),
        count,
        display_timezone=(
            default_display_timezone
            if display_timezone is None
            else display_timezone
        ),
    )
    playback = (
        None
        if duration is None
        else PlaybackSpec(
            duration=timedelta(seconds=duration),
            frames_per_second=frames_per_second,
        )
    )
    if playback is not None:
        playback.validate_timeline(timeline)
    return ChartSequenceCliOptions(
        timeline=timeline,
        playback=playback,
        restart_policy=SequenceRestartPolicy(restart_policy),
    )
