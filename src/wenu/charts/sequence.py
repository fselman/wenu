"""Canonical repeated-static observer-time chart sequences."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from pathlib import Path
from wenu.configuration import ConfigurationDefaults
from wenu.temporal import PlaybackSpec, TemporalTimeline

from .product_options import ChartProductOptions
from .request import ChartRequest
from .request_generation import (
    ChartRequestGeneration,
    generate_chart_request,
)


@dataclass(frozen=True)
class ObserverTimeChartSequenceFrame:
    """One deterministic static chart request in a temporal sequence."""

    index: int
    simulation_time: datetime
    display_time: datetime
    name: str
    request: ChartRequest
    expected_output: Path


@dataclass(frozen=True)
class ObserverTimeChartSequenceRequest:
    """One immutable chart product paired with observer-time instants."""

    chart: ChartRequest
    timeline: TemporalTimeline
    playback: PlaybackSpec | None = None
    configuration: ConfigurationDefaults | None = None

    def __post_init__(self):
        if not isinstance(self.chart, ChartRequest):
            raise TypeError("chart must be a ChartRequest.")
        if not isinstance(self.timeline, TemporalTimeline):
            raise TypeError("timeline must be a TemporalTimeline.")
        if self.playback is not None:
            if not isinstance(self.playback, PlaybackSpec):
                raise TypeError("playback must be a PlaybackSpec or None.")
            self.playback.validate_timeline(self.timeline)
        if self.configuration is not None and not isinstance(
            self.configuration,
            ConfigurationDefaults,
        ):
            raise TypeError(
                "configuration must be ConfigurationDefaults or None."
            )
        product = self.chart.product
        if product.all_products:
            raise ValueError(
                "The first sequence contract accepts one chart product."
            )
        if product.output_format is None:
            raise ValueError(
                "A chart sequence requires an explicit output format."
            )
        if product.output.suffix:
            raise ValueError(
                "A chart sequence output must be a directory."
            )

    @property
    def frame_count(self) -> int:
        return self.timeline.frame_count

    @property
    def frames(self) -> tuple[ObserverTimeChartSequenceFrame, ...]:
        """Resolve immutable per-frame requests without rendering."""
        product = self.chart.product
        suffix = product.output_format.extension
        frames = []
        for index, (instant, display_instant) in enumerate(
            zip(
                self.timeline.instants,
                self.timeline.display_instants,
                strict=True,
            )
        ):
            name = self.timeline.frame_name(index, suffix=suffix)
            output = product.output / name
            frame_product = replace(product, output=output)
            observer = replace(self.chart.observer, time=instant)
            request = replace(
                self.chart,
                observer=observer,
                product=frame_product,
            )
            frames.append(
                ObserverTimeChartSequenceFrame(
                    index=index,
                    simulation_time=instant,
                    display_time=display_instant,
                    name=name,
                    request=request,
                    expected_output=output,
                )
            )
        return tuple(frames)


class SequenceFrameDisposition(str, Enum):
    """Whether one result was rendered now or reused after verification."""

    RENDERED = "rendered"
    REUSED = "reused"


@dataclass(frozen=True)
class ObserverTimeChartSequenceFrameResult:
    """Verified output for one rendered or safely reused sequence frame."""

    frame: ObserverTimeChartSequenceFrame
    generation: ChartRequestGeneration | None
    disposition: SequenceFrameDisposition = SequenceFrameDisposition.RENDERED

    def __post_init__(self):
        if not isinstance(self.frame, ObserverTimeChartSequenceFrame):
            raise TypeError("frame must be a ObserverTimeChartSequenceFrame.")
        disposition = SequenceFrameDisposition(self.disposition)
        object.__setattr__(self, "disposition", disposition)
        if disposition is SequenceFrameDisposition.RENDERED:
            if not isinstance(self.generation, ChartRequestGeneration):
                raise TypeError(
                    "A rendered frame requires ChartRequestGeneration."
                )
            if self.generation.outputs != (self.frame.expected_output,):
                raise ValueError(
                    "Static generation outputs do not match the frame plan."
                )
        elif self.generation is not None:
            raise ValueError("A reused frame must not claim new generation.")

    @property
    def output(self) -> Path:
        return self.frame.expected_output

    @property
    def reused(self) -> bool:
        return self.disposition is SequenceFrameDisposition.REUSED


@dataclass(frozen=True)
class ObserverTimeChartSequenceGeneration:
    """Ordered results from canonical rendering and verified reuse."""

    request: ObserverTimeChartSequenceRequest
    frames: tuple[ObserverTimeChartSequenceFrameResult, ...]
    manifest_path: Path | None = None

    def __post_init__(self):
        if not isinstance(self.request, ObserverTimeChartSequenceRequest):
            raise TypeError("request must be a ObserverTimeChartSequenceRequest.")
        frames = tuple(self.frames)
        if len(frames) != self.request.frame_count:
            raise ValueError(
                "Sequence result count does not match its timeline."
            )
        if tuple(item.frame.index for item in frames) != tuple(
            range(len(frames))
        ):
            raise ValueError("Sequence frame results must remain ordered.")
        object.__setattr__(self, "frames", frames)
        if self.manifest_path is not None:
            object.__setattr__(self, "manifest_path", Path(self.manifest_path))

    @property
    def outputs(self) -> tuple[Path, ...]:
        return tuple(item.output for item in self.frames)

    @property
    def rendered_count(self) -> int:
        return sum(not item.reused for item in self.frames)

    @property
    def reused_count(self) -> int:
        return sum(item.reused for item in self.frames)


def generate_observer_time_chart_sequence(
    request: ObserverTimeChartSequenceRequest,
    *,
    restart_policy="restart",
    manifest_path: Path | None = None,
) -> ObserverTimeChartSequenceGeneration:
    """Generate frames or resume only outputs verified by a compatible manifest."""
    if not isinstance(request, ObserverTimeChartSequenceRequest):
        raise TypeError("request must be an ObserverTimeChartSequenceRequest.")

    from .sequence_manifest import (
        ObserverTimeSequenceManifest,
        SEQUENCE_MANIFEST_NAME,
        SequenceRestartPolicy,
        read_observer_time_sequence_manifest,
        update_observer_time_sequence_manifest,
    )

    try:
        policy = SequenceRestartPolicy(restart_policy)
    except ValueError as error:
        raise ValueError("restart_policy must be 'restart' or 'resume'.") from error
    destination = (
        request.chart.product.output / SEQUENCE_MANIFEST_NAME
        if manifest_path is None
        else Path(manifest_path)
    )
    if policy is SequenceRestartPolicy.RESUME and destination.is_file():
        manifest = read_observer_time_sequence_manifest(destination)
        manifest.assert_compatible(request)
    else:
        manifest = ObserverTimeSequenceManifest.from_sequence(request)
        update_observer_time_sequence_manifest(manifest, destination)

    results = []
    for frame in request.frames:
        if (
            policy is SequenceRestartPolicy.RESUME
            and manifest.output_is_valid(frame.index, frame.expected_output)
        ):
            results.append(
                ObserverTimeChartSequenceFrameResult(
                    frame=frame,
                    generation=None,
                    disposition=SequenceFrameDisposition.REUSED,
                )
            )
            continue
        generation_options = {}
        if request.configuration is not None:
            generation_options["configuration"] = request.configuration
        generation = generate_chart_request(
            frame.request,
            **generation_options,
        )
        result = ObserverTimeChartSequenceFrameResult(
            frame=frame,
            generation=generation,
        )
        manifest = manifest.with_completed_output(
            frame.index,
            frame.expected_output,
        )
        update_observer_time_sequence_manifest(manifest, destination)
        results.append(result)
    return ObserverTimeChartSequenceGeneration(
        request=request,
        frames=tuple(results),
        manifest_path=destination,
    )
