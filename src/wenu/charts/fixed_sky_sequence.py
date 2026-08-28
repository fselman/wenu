"""Planning contract for a fixed celestial scene and rotating local horizon."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from wenu.configuration import ConfigurationDefaults
from wenu.observer import Observer
from wenu.temporal import PlaybackSpec, TemporalTimeline

from .fixed_sky_orientation import (
    FixedSkyCircumpolarOrientation,
    fixed_sky_circumpolar_orientation,
)
from .request import ChartObserverRequest, ChartRequest


def _utc_anchor(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("celestial_anchor_time must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("celestial_anchor_time must include a UTC offset.")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class FixedSkyRotatingHorizonFrame:
    """One frame with fixed celestial ownership and local-time ownership."""

    index: int
    simulation_time: datetime
    display_time: datetime
    name: str
    celestial_request: ChartRequest
    local_observer: ChartObserverRequest
    expected_output: Path

    def __post_init__(self):
        if not isinstance(self.celestial_request, ChartRequest):
            raise TypeError("celestial_request must be a ChartRequest.")
        if not isinstance(self.local_observer, ChartObserverRequest):
            raise TypeError("local_observer must be a ChartObserverRequest.")
        object.__setattr__(self, "expected_output", Path(self.expected_output))


@dataclass(frozen=True)
class ResolvedFixedSkyRotatingHorizonFrame:
    """One canonical render request plus its anchor-rotation provenance."""

    frame: FixedSkyRotatingHorizonFrame
    chart_request: ChartRequest
    orientation: FixedSkyCircumpolarOrientation


def resolve_fixed_sky_rotating_horizon_frame(
    frame: FixedSkyRotatingHorizonFrame,
) -> ResolvedFixedSkyRotatingHorizonFrame:
    """Resolve one circumpolar frame through the established request seam.

    Celestial and local observer ownership remain explicit in the input frame.
    The returned canonical request uses the frame observer so horizon, AltAz
    geometry, visibility, and furniture retain their normal local-time
    behavior. Only the chart position angle is corrected relative to the
    celestial anchor.
    """
    if not isinstance(frame, FixedSkyRotatingHorizonFrame):
        raise TypeError("frame must be a FixedSkyRotatingHorizonFrame.")
    request = frame.celestial_request
    if request.family != "circumpolar":
        raise ValueError(
            "Fixed-sky frame resolution currently supports circumpolar charts."
        )
    anchor_observer = Observer(
        **request.observer.observer_kwargs()
    )
    local_observer = Observer(
        **frame.local_observer.observer_kwargs()
    )
    try:
        anchor_position_angle = request.frame.position_angle_deg or 0.0
        orientation = fixed_sky_circumpolar_orientation(
            anchor_observer,
            local_observer,
            pole=request.frame.pole,
            anchor_position_angle_deg=anchor_position_angle,
        )
    finally:
        anchor_observer.close()
        local_observer.close()
    chart_request = replace(
        request,
        observer=frame.local_observer,
        frame=replace(
            request.frame,
            orientation=None,
            position_angle_deg=orientation.position_angle_deg,
        ),
    )
    return ResolvedFixedSkyRotatingHorizonFrame(
        frame=frame,
        chart_request=chart_request,
        orientation=orientation,
    )


@dataclass(frozen=True)
class FixedSkyRotatingHorizonSequenceRequest:
    """One fixed celestial/camera anchor paired with local observer instants.

    This is a planning contract. It does not render frames, cache geometry,
    or introduce an alternate chart pipeline.
    """

    chart: ChartRequest
    timeline: TemporalTimeline
    celestial_anchor_time: datetime
    playback: PlaybackSpec | None = None
    configuration: ConfigurationDefaults | None = None

    def __post_init__(self):
        if not isinstance(self.chart, ChartRequest):
            raise TypeError("chart must be a ChartRequest.")
        if not isinstance(self.timeline, TemporalTimeline):
            raise TypeError("timeline must be a TemporalTimeline.")
        object.__setattr__(
            self,
            "celestial_anchor_time",
            _utc_anchor(self.celestial_anchor_time),
        )
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
                "A fixed-sky sequence accepts one chart product."
            )
        if product.output_format is None:
            raise ValueError(
                "A fixed-sky sequence requires an explicit output format."
            )
        if product.output.suffix:
            raise ValueError(
                "A fixed-sky sequence output must be a directory."
            )

    @property
    def frame_count(self) -> int:
        return self.timeline.frame_count

    @property
    def celestial_observer(self) -> ChartObserverRequest:
        """Observer location with the explicit fixed celestial anchor time."""
        return replace(
            self.chart.observer,
            time=self.celestial_anchor_time,
        )

    @property
    def frames(self) -> tuple[FixedSkyRotatingHorizonFrame, ...]:
        """Resolve frame ownership without rendering or claiming reuse."""
        product = self.chart.product
        suffix = product.output_format.extension
        celestial_observer = self.celestial_observer
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
            celestial_request = replace(
                self.chart,
                observer=celestial_observer,
                product=replace(product, output=output),
            )
            local_observer = replace(self.chart.observer, time=instant)
            frames.append(
                FixedSkyRotatingHorizonFrame(
                    index=index,
                    simulation_time=instant,
                    display_time=display_instant,
                    name=name,
                    celestial_request=celestial_request,
                    local_observer=local_observer,
                    expected_output=output,
                )
            )
        return tuple(frames)



@dataclass(frozen=True)
class FixedSkyRotatingHorizonFrameResult:
    """One completed uncached reference-render frame."""

    resolved: ResolvedFixedSkyRotatingHorizonFrame
    generation: object
    output: Path


@dataclass(frozen=True)
class FixedSkyRotatingHorizonGeneration:
    """Completed uncached reference rendering of a fixed-sky sequence."""

    frames: tuple[FixedSkyRotatingHorizonFrameResult, ...]

    @property
    def outputs(self) -> tuple[Path, ...]:
        return tuple(frame.output for frame in self.frames)


def generate_fixed_sky_rotating_horizon_sequence(
    request: FixedSkyRotatingHorizonSequenceRequest,
) -> FixedSkyRotatingHorizonGeneration:
    """Render the fixed-sky reference sequence through canonical requests.

    This intentionally performs a complete independent chart generation for
    every frame. It is the behavior-validation renderer, not a caching or
    resume implementation.
    """
    if not isinstance(request, FixedSkyRotatingHorizonSequenceRequest):
        raise TypeError(
            "request must be a FixedSkyRotatingHorizonSequenceRequest."
        )
    from .request_generation import generate_chart_request

    results = []
    for frame in request.frames:
        resolved = resolve_fixed_sky_rotating_horizon_frame(frame)
        generation = generate_chart_request(
            resolved.chart_request,
            configuration=request.configuration,
        )
        outputs = tuple(generation.outputs)
        if outputs != (frame.expected_output,):
            raise RuntimeError(
                "Fixed-sky frame generation returned an unexpected output."
            )
        results.append(
            FixedSkyRotatingHorizonFrameResult(
                resolved=resolved,
                generation=generation,
                output=outputs[0],
            )
        )
    return FixedSkyRotatingHorizonGeneration(frames=tuple(results))
