"""Independent complete-render baseline and PNG comparison tests."""

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image
import pytest

import wenu.charts.fixed_sky_baseline as baseline_module
from wenu.charts.fixed_sky_baseline import (
    PngFrameComparisonTolerance,
    compare_png_frames,
    fixed_sky_complete_render_baseline_request,
    generate_fixed_sky_complete_render_baseline,
)
from wenu.charts.fixed_sky_sequence import (
    FixedSkyRotatingHorizonSequenceRequest,
)
from wenu.charts.product_options import ChartProductOptions
from wenu.charts.request import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartRequest,
    ChartSubjectRequest,
)
from wenu.output_policy import OutputFormat
from wenu.temporal import TemporalTimeline


def fixed_request(output, *, family="circumpolar"):
    return FixedSkyRotatingHorizonSequenceRequest(
        chart=ChartRequest(
            observer=ChartObserverRequest(
                time="2026-08-21T21:00:00-04:00",
                location="La Ligua",
            ),
            family=family,
            subject=(
                ChartSubjectRequest(constellations=("CRU",))
                if family == "regional"
                else ChartSubjectRequest()
            ),
            frame=ChartFrameRequest(
                pole="south",
                limiting_declination_deg=-60,
            ),
            product=ChartProductOptions(
                output=output,
                output_format=OutputFormat.PNG,
            ),
        ),
        timeline=TemporalTimeline.uniform(
            datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
            datetime(2026, 8, 22, 7, tzinfo=timezone.utc),
            3,
            display_timezone="America/Santiago",
        ),
        celestial_anchor_time=datetime(
            2026, 8, 22, 1, tzinfo=timezone.utc
        ),
    )


def write_rgba(path: Path, values):
    Image.fromarray(np.asarray(values, dtype=np.uint8), "RGBA").save(path)


def test_baseline_is_an_independent_complete_observer_time_plan(tmp_path):
    fixed = fixed_request(tmp_path / "candidate")
    baseline = fixed_sky_complete_render_baseline_request(
        fixed,
        tmp_path / "baseline",
    )

    assert baseline.chart.product.output == tmp_path / "baseline"
    assert baseline.timeline is fixed.timeline
    assert tuple(
        frame.request.observer.time for frame in baseline.frames
    ) == fixed.timeline.instants
    assert tuple(
        frame.request.product.output for frame in baseline.frames
    ) == tuple(
        tmp_path / "baseline" / f"frame-{index:04d}.png"
        for index in range(3)
    )
    assert all(
        frame.request.observer.time
        == fixed.frames[frame.index].local_observer.time
        for frame in baseline.frames
    )


def test_baseline_generation_delegates_to_observer_time_pipeline(
    tmp_path,
    monkeypatch,
):
    fixed = fixed_request(tmp_path / "candidate")
    calls = []

    def generate(request, *, restart_policy):
        calls.append((request, restart_policy))
        return SimpleNamespace(request=request)

    monkeypatch.setattr(
        baseline_module,
        "generate_observer_time_chart_sequence",
        generate,
    )

    result = generate_fixed_sky_complete_render_baseline(
        fixed,
        tmp_path / "baseline",
        restart_policy="resume",
    )

    assert len(calls) == 1
    assert calls[0][0].chart.product.output == tmp_path / "baseline"
    assert calls[0][1] == "resume"
    assert result.request is calls[0][0]


def test_first_baseline_rejects_unproved_chart_families(tmp_path):
    fixed = fixed_request(tmp_path / "candidate", family="regional")

    with pytest.raises(ValueError, match="limited to circumpolar"):
        fixed_sky_complete_render_baseline_request(
            fixed,
            tmp_path / "baseline",
        )


def test_png_comparison_reports_exact_rgba_metrics(tmp_path):
    baseline = tmp_path / "baseline.png"
    candidate = tmp_path / "candidate.png"
    pixels = np.zeros((2, 2, 4), dtype=np.uint8)
    pixels[:, :, 3] = 255
    write_rgba(baseline, pixels)
    changed = pixels.copy()
    changed[0, 1, 0] = 20
    changed[1, 0, 2] = 4
    write_rgba(candidate, changed)

    comparison = compare_png_frames(candidate, baseline)

    assert comparison.dimensions == (2, 2)
    assert comparison.pixel_count == 4
    assert comparison.changed_pixels == 2
    assert comparison.changed_pixel_fraction == 0.5
    assert comparison.max_channel_delta == 20
    assert comparison.mean_absolute_channel_delta == 1.5
    assert comparison.accepted(
        PngFrameComparisonTolerance(
            max_changed_pixel_fraction=0.5,
            max_channel_delta=20,
            max_mean_absolute_channel_delta=1.5,
        )
    )
    assert not comparison.accepted(
        PngFrameComparisonTolerance(
            max_changed_pixel_fraction=0.49,
            max_channel_delta=20,
            max_mean_absolute_channel_delta=1.5,
        )
    )


def test_png_comparison_normalizes_color_modes_and_rejects_size(tmp_path):
    rgb = tmp_path / "rgb.png"
    rgba = tmp_path / "rgba.png"
    Image.new("RGB", (3, 2), (10, 20, 30)).save(rgb)
    Image.new("RGBA", (3, 2), (10, 20, 30, 255)).save(rgba)

    comparison = compare_png_frames(rgb, rgba)

    assert comparison.changed_pixels == 0
    assert comparison.accepted(PngFrameComparisonTolerance())

    wrong = tmp_path / "wrong.png"
    Image.new("RGBA", (2, 2), (10, 20, 30, 255)).save(wrong)
    with pytest.raises(ValueError, match="dimensions differ"):
        compare_png_frames(wrong, rgba)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_changed_pixel_fraction": -0.1}, "between 0 and 1"),
        ({"max_channel_delta": 256}, "between 0 and 255"),
        (
            {"max_mean_absolute_channel_delta": 256},
            "between 0 and 255",
        ),
    ],
)
def test_png_comparison_tolerances_are_bounded(kwargs, message):
    with pytest.raises(ValueError, match=message):
        PngFrameComparisonTolerance(**kwargs)
