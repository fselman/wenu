"""Renderer-neutral temporal sequence vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from math import isfinite
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class TimeScale(StrEnum):
    """Time scales supported by the first temporal-sequence contract."""

    UTC = "utc"


class SamplingKind(StrEnum):
    """Relationship between consecutive simulation instants."""

    UNIFORM = "uniform"
    EXPLICIT = "explicit"


def _utc_instant(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("simulation instants must be datetime values.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("simulation instants must include a UTC offset.")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class TemporalTimeline:
    """Ordered physical instants and their separate civil-time display."""

    instants: tuple[datetime, ...]
    display_timezone: str = "UTC"
    time_scale: TimeScale = TimeScale.UTC

    def __post_init__(self):
        try:
            scale = TimeScale(self.time_scale)
        except ValueError as error:
            raise ValueError(
                f"Unsupported simulation time scale: {self.time_scale!r}."
            ) from error
        object.__setattr__(self, "time_scale", scale)

        if not isinstance(self.display_timezone, str):
            raise TypeError("display_timezone must be an IANA time-zone name.")
        try:
            ZoneInfo(self.display_timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError(
                "display_timezone must be a valid IANA time-zone name."
            ) from error

        instants = tuple(_utc_instant(value) for value in self.instants)
        if not instants:
            raise ValueError("A temporal timeline requires at least one instant.")
        if any(
            current <= previous
            for previous, current in zip(instants, instants[1:])
        ):
            raise ValueError(
                "Simulation instants must be strictly increasing."
            )
        object.__setattr__(self, "instants", instants)

    @classmethod
    def uniform(
        cls,
        start: datetime,
        stop: datetime,
        count: int,
        *,
        display_timezone: str = "UTC",
        time_scale: TimeScale = TimeScale.UTC,
    ) -> "TemporalTimeline":
        """Return inclusive, uniformly sampled simulation instants."""
        start_utc = _utc_instant(start)
        stop_utc = _utc_instant(stop)
        if not isinstance(count, int) or isinstance(count, bool):
            raise TypeError("count must be an integer.")
        if count < 2:
            raise ValueError("Uniform sampling requires at least two instants.")
        if stop_utc <= start_utc:
            raise ValueError("stop must be later than start.")
        duration = stop_utc - start_utc
        instants = tuple(
            start_utc + duration * (index / (count - 1))
            for index in range(count)
        )
        return cls(
            instants=instants,
            display_timezone=display_timezone,
            time_scale=time_scale,
        )

    @property
    def frame_count(self) -> int:
        return len(self.instants)

    @property
    def simulation_duration(self) -> timedelta:
        if len(self.instants) == 1:
            return timedelta(0)
        return self.instants[-1] - self.instants[0]

    @property
    def sampling_interval(self) -> timedelta | None:
        """Return the uniform physical interval, if one exists."""
        if len(self.instants) < 2:
            return None
        intervals = tuple(
            current - previous
            for previous, current in zip(
                self.instants,
                self.instants[1:],
            )
        )
        first = intervals[0]
        if all(value == first for value in intervals[1:]):
            return first
        return None

    @property
    def sampling_kind(self) -> SamplingKind:
        if len(self.instants) >= 2 and self.sampling_interval is not None:
            return SamplingKind.UNIFORM
        return SamplingKind.EXPLICIT

    @property
    def display_instants(self) -> tuple[datetime, ...]:
        """Represent the same physical instants in civil display time."""
        zone = ZoneInfo(self.display_timezone)
        return tuple(value.astimezone(zone) for value in self.instants)

    def frame_name(
        self,
        index: int,
        *,
        prefix: str = "frame",
        suffix: str = ".png",
        width: int = 4,
    ) -> str:
        """Return one deterministic frame filename."""
        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError("frame index must be an integer.")
        if not 0 <= index < self.frame_count:
            raise IndexError("frame index is outside the timeline.")
        if not isinstance(width, int) or isinstance(width, bool) or width < 1:
            raise ValueError("frame filename width must be a positive integer.")
        if not isinstance(prefix, str) or not prefix:
            raise ValueError("frame filename prefix must be non-empty.")
        if not isinstance(suffix, str):
            raise TypeError("frame filename suffix must be a string.")
        return f"{prefix}-{index:0{width}d}{suffix}"


@dataclass(frozen=True)
class PlaybackSpec:
    """Presentation cadence separate from physical simulation time."""

    duration: timedelta
    frames_per_second: float

    def __post_init__(self):
        if not isinstance(self.duration, timedelta):
            raise TypeError("playback duration must be a timedelta.")
        seconds = self.duration.total_seconds()
        if not isfinite(seconds) or seconds <= 0.0:
            raise ValueError("playback duration must be positive and finite.")
        if isinstance(self.frames_per_second, bool):
            raise TypeError("frames_per_second must be a number.")
        try:
            frames_per_second = float(self.frames_per_second)
        except (TypeError, ValueError) as error:
            raise TypeError(
                "frames_per_second must be a number."
            ) from error
        if not isfinite(frames_per_second) or frames_per_second <= 0.0:
            raise ValueError(
                "frames_per_second must be positive and finite."
            )
        object.__setattr__(
            self,
            "frames_per_second",
            frames_per_second,
        )

    @property
    def frame_count(self) -> int:
        return round(
            self.duration.total_seconds() * self.frames_per_second
        )

    def validate_timeline(self, timeline: TemporalTimeline) -> None:
        """Require timeline and presentation to imply the same frame count."""
        if not isinstance(timeline, TemporalTimeline):
            raise TypeError("timeline must be a TemporalTimeline.")
        if timeline.frame_count != self.frame_count:
            raise ValueError(
                "Timeline frame count does not match playback duration "
                "and frames per second."
            )
