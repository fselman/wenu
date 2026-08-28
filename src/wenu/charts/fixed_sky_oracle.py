"""Independent complete-render baseline and PNG comparison for fixed-sky work."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from PIL import Image

from .fixed_sky_sequence import FixedSkyRotatingHorizonSequenceRequest
from .sequence import (
    ObserverTimeChartSequenceGeneration,
    ObserverTimeChartSequenceRequest,
    generate_observer_time_chart_sequence,
)


@dataclass(frozen=True)
class PngFrameComparisonTolerance:
    """Declared graphical acceptance limits for one pair of RGBA frames."""

    max_changed_pixel_fraction: float = 0.0
    max_channel_delta: int = 0
    max_mean_absolute_channel_delta: float = 0.0

    def __post_init__(self):
        fraction = float(self.max_changed_pixel_fraction)
        channel_delta = int(self.max_channel_delta)
        mean_delta = float(self.max_mean_absolute_channel_delta)
        if not 0.0 <= fraction <= 1.0:
            raise ValueError(
                "max_changed_pixel_fraction must be between 0 and 1."
            )
        if not 0 <= channel_delta <= 255:
            raise ValueError("max_channel_delta must be between 0 and 255.")
        if not 0.0 <= mean_delta <= 255.0:
            raise ValueError(
                "max_mean_absolute_channel_delta must be between 0 and 255."
            )
        object.__setattr__(
            self, "max_changed_pixel_fraction", fraction
        )
        object.__setattr__(self, "max_channel_delta", channel_delta)
        object.__setattr__(
            self, "max_mean_absolute_channel_delta", mean_delta
        )


@dataclass(frozen=True)
class PngFrameComparison:
    """Measured graphical difference between candidate and baseline frames."""

    candidate: Path
    baseline: Path
    dimensions: tuple[int, int]
    changed_pixels: int
    pixel_count: int
    max_channel_delta: int
    mean_absolute_channel_delta: float

    def __post_init__(self):
        object.__setattr__(self, "candidate", Path(self.candidate))
        object.__setattr__(self, "baseline", Path(self.baseline))

    @property
    def changed_pixel_fraction(self) -> float:
        return (
            0.0
            if self.pixel_count == 0
            else self.changed_pixels / self.pixel_count
        )

    def accepted(self, tolerance: PngFrameComparisonTolerance) -> bool:
        if not isinstance(tolerance, PngFrameComparisonTolerance):
            raise TypeError(
                "tolerance must be a PngFrameComparisonTolerance."
            )
        return (
            self.changed_pixel_fraction
            <= tolerance.max_changed_pixel_fraction
            and self.max_channel_delta <= tolerance.max_channel_delta
            and self.mean_absolute_channel_delta
            <= tolerance.max_mean_absolute_channel_delta
        )


def fixed_sky_complete_render_baseline_request(
    request: FixedSkyRotatingHorizonSequenceRequest,
    output: Path,
) -> ObserverTimeChartSequenceRequest:
    """Plan complete canonical circumpolar renders in a separate directory."""
    if not isinstance(request, FixedSkyRotatingHorizonSequenceRequest):
        raise TypeError(
            "request must be a FixedSkyRotatingHorizonSequenceRequest."
        )
    if request.chart.family != "circumpolar":
        raise ValueError(
            "The first fixed-sky oracle is proved only for circumpolar charts."
        )
    output = Path(output)
    if output.suffix:
        raise ValueError("The baseline output must be a directory.")
    chart = replace(
        request.chart,
        product=replace(request.chart.product, output=output),
    )
    return ObserverTimeChartSequenceRequest(
        chart=chart,
        timeline=request.timeline,
        playback=request.playback,
        configuration=request.configuration,
    )


def generate_fixed_sky_complete_render_baseline(
    request: FixedSkyRotatingHorizonSequenceRequest,
    output: Path,
    *,
    restart_policy="restart",
) -> ObserverTimeChartSequenceGeneration:
    """Generate the independent oracle through the canonical static pipeline."""
    oracle = fixed_sky_complete_render_baseline_request(request, output)
    return generate_observer_time_chart_sequence(
        oracle,
        restart_policy=restart_policy,
    )


def compare_png_frames(candidate: Path, baseline: Path) -> PngFrameComparison:
    """Compare two PNG frames in canonical RGBA pixel space."""
    candidate = Path(candidate)
    oracle = Path(baseline)
    with Image.open(candidate) as candidate_image:
        candidate_rgba = np.asarray(
            candidate_image.convert("RGBA"), dtype=np.int16
        )
    with Image.open(oracle) as baseline_image:
        baseline_rgba = np.asarray(
            baseline_image.convert("RGBA"), dtype=np.int16
        )
    if candidate_rgba.shape != baseline_rgba.shape:
        candidate_size = (
            int(candidate_rgba.shape[1]),
            int(candidate_rgba.shape[0]),
        )
        baseline_size = (
            int(baseline_rgba.shape[1]),
            int(baseline_rgba.shape[0]),
        )
        raise ValueError(
            "PNG frame dimensions differ: "
            f"candidate {candidate_size}, oracle {baseline_size}."
        )
    absolute = np.abs(candidate_rgba - baseline_rgba)
    changed = np.any(absolute != 0, axis=2)
    height, width, _ = absolute.shape
    return PngFrameComparison(
        candidate=candidate,
        baseline=baseline,
        dimensions=(width, height),
        changed_pixels=int(np.count_nonzero(changed)),
        pixel_count=int(width * height),
        max_channel_delta=int(np.max(absolute, initial=0)),
        mean_absolute_channel_delta=float(np.mean(absolute)),
    )
