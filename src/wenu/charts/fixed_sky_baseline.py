"""Complete-render baseline and PNG comparison for fixed-sky work."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import re
import subprocess
from xml.etree import ElementTree

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
            "The first complete-render baseline is limited to "
            "circumpolar charts."
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
    """Generate the baseline through the canonical static pipeline."""
    baseline = fixed_sky_complete_render_baseline_request(request, output)
    return generate_observer_time_chart_sequence(
        baseline,
        restart_policy=restart_policy,
    )


def compare_png_frames(candidate: Path, baseline: Path) -> PngFrameComparison:
    """Compare two PNG frames in canonical RGBA pixel space."""
    candidate = Path(candidate)
    baseline = Path(baseline)
    with Image.open(candidate) as candidate_image:
        candidate_rgba = np.asarray(
            candidate_image.convert("RGBA"), dtype=np.int16
        )
    with Image.open(baseline) as baseline_image:
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
            f"candidate {candidate_size}, baseline {baseline_size}."
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


_VOLATILE_SVG_ID = re.compile(r"[mp][0-9a-f]+")


def normalized_svg_graphical_record(path: Path) -> bytes:
    """Return deterministic SVG structure without exporter volatility.

    Dublin Core metadata is non-graphical. Matplotlib's random marker and clip
    identifiers are replaced in document order, including their references.
    Wenu semantic identifiers and every graphical attribute remain intact.
    """
    root = ElementTree.parse(Path(path)).getroot()
    for parent in root.iter():
        for child in tuple(parent):
            if child.tag.endswith("}metadata") or child.tag == "metadata":
                parent.remove(child)
    replacements = {}
    for element in root.iter():
        identifier = element.attrib.get("id")
        if identifier and _VOLATILE_SVG_ID.fullmatch(identifier):
            replacements[identifier] = f"volatile-{len(replacements):04d}"
    for element in root.iter():
        for name, value in tuple(element.attrib.items()):
            for old, new in replacements.items():
                value = value.replace(f"#{old}", f"#{new}")
            if name == "id" and value in replacements:
                value = replacements[value]
            element.attrib[name] = value
    return ElementTree.tostring(root, encoding="utf-8")


def compare_normalized_svg(candidate: Path, baseline: Path) -> bool:
    """Compare semantic and graphical SVG structure after safe normalization."""
    return normalized_svg_graphical_record(candidate) == (
        normalized_svg_graphical_record(baseline)
    )


def render_pdf_page_rgba(
    path: Path,
    destination: Path,
    *,
    dpi: int = 150,
) -> Path:
    """Rasterize a one-page PDF with Poppler for graphical comparison."""
    if dpi <= 0:
        raise ValueError("dpi must be positive.")
    path = Path(path)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    prefix = destination.with_suffix("")
    try:
        subprocess.run(
            (
                "pdftoppm",
                "-f", "1",
                "-l", "1",
                "-singlefile",
                "-r", str(dpi),
                "-png",
                str(path),
                str(prefix),
            ),
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "Rendered-PDF comparison requires the 'pdftoppm' executable."
        ) from error
    except subprocess.CalledProcessError as error:
        message = error.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"PDF rasterization failed: {message}") from error
    rendered = prefix.with_suffix(".png")
    if not rendered.is_file():
        raise RuntimeError("PDF rasterization did not create its PNG output.")
    if rendered != destination:
        rendered.replace(destination)
    return destination
