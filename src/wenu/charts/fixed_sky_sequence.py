"""Planning contract for a fixed celestial scene and rotating local horizon."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from wenu.configuration import ConfigurationDefaults
from wenu.temporal import PlaybackSpec, TemporalTimeline

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
        if self.celestial_request.observer.time == self.local_observer.time:
            # Equality is allowed for the anchor frame, but ownership remains
            # deliberately represented by two separate request values.
            return


@dataclass(frozen=True)
class FixedSkyRotatingHorizonSequenceRequest:
    """One fixed celestial/camera anchor paired with local observer instants.

    This is a planning contract.  It does not render frames, cache geometry,
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
