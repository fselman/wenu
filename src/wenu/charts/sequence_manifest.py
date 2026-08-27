"""Deterministic manifests for canonical observer-time chart sequences."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
from collections.abc import Mapping
from typing import Any

from .request import ChartRequest
from .sequence import ObserverTimeChartSequenceRequest


SEQUENCE_MANIFEST_SCHEMA_VERSION = 1
SEQUENCE_MANIFEST_NAME = "wenu-sequence-manifest.json"


class SequenceRestartPolicy(str, Enum):
    """How generation treats an existing compatible sequence."""

    RESTART = "restart"
    RESUME = "resume"


def _canonical(value: Any):
    """Return a JSON-safe, deterministically ordered public value."""
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Enum):
        return _canonical(value.value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (set, frozenset)):
        items = (_canonical(item) for item in value)
        return sorted(
            items,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ),
        )
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(
        f"Cannot serialize {type(value).__name__} in a sequence manifest."
    )


def _canonical_json(value: Any, *, pretty: bool) -> str:
    options = {"ensure_ascii": False, "sort_keys": True}
    if pretty:
        options.update(indent=2)
    else:
        options.update(separators=(",", ":"))
    return json.dumps(value, **options)


def _chart_request_identity(request: ChartRequest) -> dict[str, Any]:
    """Return chart identity while leaving time/path ownership to sequence."""
    if not isinstance(request, ChartRequest):
        raise TypeError("request must be a ChartRequest.")
    identity = _canonical(request)
    identity["observer"]["time"] = None
    identity["product"]["output"] = None
    return identity


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class SequenceManifestFrame:
    """One expected output and its last verified completion record."""

    index: int
    name: str
    simulation_time: str
    display_time: str
    output_bytes: int | None = None
    output_sha256: str | None = None

    def __post_init__(self):
        if self.index < 0:
            raise ValueError("manifest frame index cannot be negative.")
        if not self.name or Path(self.name).name != self.name:
            raise ValueError("manifest frame name must be one filename.")
        for name in ("simulation_time", "display_time"):
            value = getattr(self, name)
            try:
                parsed = datetime.fromisoformat(value)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"manifest {name} must be an ISO datetime."
                ) from error
            if parsed.utcoffset() is None:
                raise ValueError(f"manifest {name} must include a UTC offset.")
        completion = (self.output_bytes, self.output_sha256)
        if (completion[0] is None) != (completion[1] is None):
            raise ValueError(
                "Manifest completion bytes and SHA-256 must be recorded together."
            )
        if completion[0] is not None:
            if not isinstance(completion[0], int) or completion[0] < 0:
                raise ValueError(
                    "Manifest output byte count must be a nonnegative integer."
                )
            digest = str(completion[1]).lower()
            if len(digest) != 64 or any(
                character not in "0123456789abcdef" for character in digest
            ):
                raise ValueError("Manifest output SHA-256 is invalid.")
            object.__setattr__(self, "output_sha256", digest)

    @property
    def is_complete(self) -> bool:
        return self.output_sha256 is not None


@dataclass(frozen=True)
class ObserverTimeSequenceManifest:
    """Portable deterministic identity and verified observer-time progress."""

    chart_request: dict[str, Any]
    time_scale: str
    display_timezone: str
    sampling_kind: str
    playback_duration_seconds: float | None
    playback_frames_per_second: float | None
    frames: tuple[SequenceManifestFrame, ...]
    configuration: dict[str, Any] | None = None
    schema_version: int = SEQUENCE_MANIFEST_SCHEMA_VERSION
    sequence_kind: str = "observer_time"

    def __post_init__(self):
        if self.schema_version != SEQUENCE_MANIFEST_SCHEMA_VERSION:
            raise ValueError("Unsupported sequence manifest schema version.")
        if self.sequence_kind != "observer_time":
            raise ValueError("Unsupported sequence manifest kind.")
        frames = tuple(self.frames)
        if not frames:
            raise ValueError("A sequence manifest requires at least one frame.")
        if tuple(frame.index for frame in frames) != tuple(range(len(frames))):
            raise ValueError("Manifest frames must be complete and ordered.")
        if len({frame.name for frame in frames}) != len(frames):
            raise ValueError("Manifest frame names must be unique.")
        object.__setattr__(self, "frames", frames)

    @classmethod
    def from_sequence(
        cls,
        sequence: ObserverTimeChartSequenceRequest,
    ) -> "ObserverTimeSequenceManifest":
        if not isinstance(sequence, ObserverTimeChartSequenceRequest):
            raise TypeError(
                "sequence must be an ObserverTimeChartSequenceRequest."
            )
        playback = sequence.playback
        return cls(
            chart_request=_chart_request_identity(sequence.chart),
            configuration=(
                None
                if sequence.configuration is None
                else _canonical(sequence.configuration)
            ),
            time_scale=sequence.timeline.time_scale.value,
            display_timezone=sequence.timeline.display_timezone,
            sampling_kind=sequence.timeline.sampling_kind.value,
            playback_duration_seconds=(
                None
                if playback is None
                else playback.duration.total_seconds()
            ),
            playback_frames_per_second=(
                None if playback is None else playback.frames_per_second
            ),
            frames=tuple(
                SequenceManifestFrame(
                    index=frame.index,
                    name=frame.name,
                    simulation_time=frame.simulation_time.isoformat(),
                    display_time=frame.display_time.isoformat(),
                )
                for frame in sequence.frames
            ),
        )

    def _identity_payload(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "sequence_kind": self.sequence_kind,
            "chart_request": self.chart_request,
            "timeline": {
                "time_scale": self.time_scale,
                "display_timezone": self.display_timezone,
                "sampling_kind": self.sampling_kind,
            },
            "playback": (
                None
                if self.playback_duration_seconds is None
                else {
                    "duration_seconds": self.playback_duration_seconds,
                    "frames_per_second": self.playback_frames_per_second,
                }
            ),
            "frames": [
                {
                    "index": frame.index,
                    "name": frame.name,
                    "simulation_time": frame.simulation_time,
                    "display_time": frame.display_time,
                }
                for frame in self.frames
            ],
        }
        if self.configuration is not None:
            payload["configuration"] = self.configuration
        return payload

    def _document_payload(self) -> dict[str, Any]:
        document = self._identity_payload()
        document["identity_sha256"] = self.identity_sha256
        for item, frame in zip(document["frames"], self.frames, strict=True):
            item["output"] = (
                None
                if not frame.is_complete
                else {
                    "bytes": frame.output_bytes,
                    "sha256": frame.output_sha256,
                }
            )
        return document

    @property
    def identity_sha256(self) -> str:
        encoded = _canonical_json(
            self._identity_payload(),
            pretty=False,
        ).encode("utf-8")
        return sha256(encoded).hexdigest()

    def to_json(self) -> str:
        return _canonical_json(self._document_payload(), pretty=True) + "\n"

    @classmethod
    def from_json(cls, text: str) -> "ObserverTimeSequenceManifest":
        try:
            document = json.loads(text)
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("Sequence manifest is not valid JSON.") from error
        if not isinstance(document, dict):
            raise ValueError("Sequence manifest root must be an object.")
        expected_hash = document.get("identity_sha256")
        try:
            timeline = document["timeline"]
            playback = document["playback"]
            manifest = cls(
                schema_version=document["schema_version"],
                sequence_kind=document["sequence_kind"],
                chart_request=document["chart_request"],
                configuration=document.get("configuration"),
                time_scale=timeline["time_scale"],
                display_timezone=timeline["display_timezone"],
                sampling_kind=timeline["sampling_kind"],
                playback_duration_seconds=(
                    None if playback is None else playback["duration_seconds"]
                ),
                playback_frames_per_second=(
                    None
                    if playback is None
                    else playback["frames_per_second"]
                ),
                frames=tuple(
                    SequenceManifestFrame(
                        index=frame["index"],
                        name=frame["name"],
                        simulation_time=frame["simulation_time"],
                        display_time=frame["display_time"],
                        output_bytes=(
                            None
                            if frame["output"] is None
                            else frame["output"]["bytes"]
                        ),
                        output_sha256=(
                            None
                            if frame["output"] is None
                            else frame["output"]["sha256"]
                        ),
                    )
                    for frame in document["frames"]
                ),
            )
        except (KeyError, TypeError) as error:
            raise ValueError(
                "Sequence manifest does not match schema version 1."
            ) from error
        if expected_hash != manifest.identity_sha256:
            raise ValueError("Sequence manifest identity hash does not match.")
        if document != manifest._document_payload():
            raise ValueError("Sequence manifest contains unsupported fields.")
        return manifest

    def assert_compatible(
        self,
        sequence: ObserverTimeChartSequenceRequest,
    ) -> None:
        planned = type(self).from_sequence(sequence)
        if self.identity_sha256 != planned.identity_sha256:
            raise ValueError(
                "Existing sequence manifest is incompatible with this plan."
            )

    def with_completed_output(
        self,
        index: int,
        path: Path,
    ) -> "ObserverTimeSequenceManifest":
        output = Path(path)
        if not output.is_file():
            raise ValueError("A completed sequence output must be a file.")
        frame = self.frames[index]
        completed = replace(
            frame,
            output_bytes=output.stat().st_size,
            output_sha256=_file_sha256(output),
        )
        frames = list(self.frames)
        frames[index] = completed
        return replace(self, frames=tuple(frames))

    def output_is_valid(self, index: int, path: Path) -> bool:
        frame = self.frames[index]
        output = Path(path)
        return (
            frame.is_complete
            and output.is_file()
            and output.stat().st_size == frame.output_bytes
            and _file_sha256(output) == frame.output_sha256
        )


def _write_manifest(
    manifest: ObserverTimeSequenceManifest,
    destination: Path,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(manifest.to_json(), encoding="utf-8")
    temporary.replace(destination)
    return destination


def write_observer_time_sequence_manifest(
    sequence: ObserverTimeChartSequenceRequest,
    path: Path | None = None,
) -> Path:
    """Atomically write a fresh deterministic planned-sequence manifest."""
    manifest = ObserverTimeSequenceManifest.from_sequence(sequence)
    destination = (
        sequence.chart.product.output / SEQUENCE_MANIFEST_NAME
        if path is None
        else Path(path)
    )
    return _write_manifest(manifest, destination)


def update_observer_time_sequence_manifest(
    manifest: ObserverTimeSequenceManifest,
    path: Path,
) -> Path:
    """Atomically persist verified progress without changing plan identity."""
    if not isinstance(manifest, ObserverTimeSequenceManifest):
        raise TypeError("manifest must be an ObserverTimeSequenceManifest.")
    return _write_manifest(manifest, Path(path))


def read_observer_time_sequence_manifest(
    path: Path,
) -> ObserverTimeSequenceManifest:
    """Read and validate one observer-time sequence manifest."""
    return ObserverTimeSequenceManifest.from_json(
        Path(path).read_text(encoding="utf-8")
    )
