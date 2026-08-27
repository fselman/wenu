"""Canonical repeated-static observer-time chart sequences."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
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

    def __post_init__(self):
        if not isinstance(self.chart, ChartRequest):
            raise TypeError("chart must be a ChartRequest.")
        if not isinstance(self.timeline, TemporalTimeline):
            raise TypeError("timeline must be a TemporalTimeline.")
        if self.playback is not None:
            if not isinstance(self.playback, PlaybackSpec):
                raise TypeError("playback must be a PlaybackSpec or None.")
            self.playback.validate_timeline(self.timeline)
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


@dataclass(frozen=True)
class ObserverTimeChartSequenceFrameResult:
    """Completed canonical generation for one sequence frame."""

    frame: ObserverTimeChartSequenceFrame
    generation: ChartRequestGeneration

    def __post_init__(self):
        if not isinstance(self.frame, ObserverTimeChartSequenceFrame):
            raise TypeError("frame must be a ObserverTimeChartSequenceFrame.")
        if not isinstance(self.generation, ChartRequestGeneration):
            raise TypeError(
                "generation must be a ChartRequestGeneration."
            )
        if self.generation.outputs != (self.frame.expected_output,):
            raise ValueError(
                "Static generation outputs do not match the frame plan."
            )

    @property
    def output(self) -> Path:
        return self.frame.expected_output


@dataclass(frozen=True)
class ObserverTimeChartSequenceGeneration:
    """Ordered immutable results from complete canonical static renders."""

    request: ObserverTimeChartSequenceRequest
    frames: tuple[ObserverTimeChartSequenceFrameResult, ...]

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

    @property
    def outputs(self) -> tuple[Path, ...]:
        return tuple(item.output for item in self.frames)


def generate_observer_time_chart_sequence(
    request: ObserverTimeChartSequenceRequest,
) -> ObserverTimeChartSequenceGeneration:
    """Generate observer-time frames through the canonical static executor."""
    if not isinstance(request, ObserverTimeChartSequenceRequest):
        raise TypeError("request must be an ObserverTimeChartSequenceRequest.")

    results = []
    for frame in request.frames:
        generation = generate_chart_request(frame.request)
        results.append(
            ObserverTimeChartSequenceFrameResult(
                frame=frame,
                generation=generation,
            )
        )
    return ObserverTimeChartSequenceGeneration(
        request=request,
        frames=tuple(results),
    )
