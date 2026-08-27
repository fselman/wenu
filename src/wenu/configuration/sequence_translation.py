"""Translation of temporal sequence configuration defaults."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .validation import validate_configuration


def _optional(value):
    return None if value == "none" else value


@dataclass(frozen=True)
class SequenceDefaults:
    """Disabled or fully specified observer-time sequence defaults."""

    stop: str | None
    frames: int | None
    display_timezone: str | None
    playback_duration_seconds: float | None
    frames_per_second: float | None
    restart_policy: str


def translate_sequence_defaults(
    configuration: Mapping[str, Any],
) -> SequenceDefaults:
    """Translate validated public values into immutable runtime defaults."""
    values = validate_configuration(configuration)["sequence"]
    return SequenceDefaults(
        stop=_optional(values["stop"]),
        frames=_optional(values["frames"]),
        display_timezone=_optional(values["display_timezone"]),
        playback_duration_seconds=_optional(
            values["playback_duration"]
        ),
        frames_per_second=_optional(values["frames_per_second"]),
        restart_policy=values["restart_policy"],
    )
