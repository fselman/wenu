"""Independent complete-render baseline and PNG comparison tests."""

from dataclasses import replace
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image
import pytest

import wenu.charts.fixed_sky_baseline as baseline_module
from wenu.charts.fixed_sky_baseline import (
    PngFrameComparisonTolerance,
    compare_png_frames,
    compare_normalized_svg,
    fixed_sky_complete_render_baseline_request,
    generate_fixed_sky_complete_render_baseline,
    render_pdf_page_rgba,
)
from wenu.charts.fixed_sky_sequence import (
    FixedSkyRotatingHorizonSequenceRequest,
)
from wenu.charts.fixed_sky_orientation import (
    FixedSkyCircumpolarOrientation,
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


def cold_benchmark_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "tools/benchmark_cold_frames.py"
    )
    spec = importlib.util.spec_from_file_location(
        "benchmark_cold_frames", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_svg_comparison_removes_only_metadata_and_volatile_exporter_ids(
    tmp_path,
):
    first = tmp_path / "first.svg"
    second = tmp_path / "second.svg"
    template = """<svg xmlns="http://www.w3.org/2000/svg">
      <metadata>{date}</metadata>
      <g id="wenu-layer-sky" data-wenu-layer="sky">
        <defs><clipPath id="{clip}"><path d="M 0 0"/></clipPath></defs>
        <path id="{marker}" clip-path="url(#{clip})" d="M 1 1"/>
      </g>
    </svg>"""
    first.write_text(
        template.format(date="one", clip="p123abc", marker="m456def")
    )
    second.write_text(
        template.format(date="two", clip="p987abc", marker="m654def")
    )

    assert compare_normalized_svg(first, second)

    second.write_text(
        template.format(date="two", clip="p987abc", marker="m654def")
        .replace('data-wenu-layer="sky"', 'data-wenu-layer="horizon"')
    )
    assert not compare_normalized_svg(first, second)


def test_pdf_page_rendering_uses_declared_poppler_arguments(
    tmp_path,
    monkeypatch,
):
    calls = []

    def run(command, **options):
        calls.append((command, options))
        Path(command[-1]).with_suffix(".png").write_bytes(b"png")

    monkeypatch.setattr(baseline_module.subprocess, "run", run)
    destination = tmp_path / "rendered.png"

    assert render_pdf_page_rgba(
        tmp_path / "frame.pdf", destination, dpi=144
    ) == destination
    assert calls == [(
        (
            "pdftoppm", "-f", "1", "-l", "1", "-singlefile",
            "-r", "144", "-png", str(tmp_path / "frame.pdf"),
            str(tmp_path / "rendered"),
        ),
        {"check": True, "capture_output": True},
    )]


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


def test_cold_benchmark_uses_three_independent_canonical_frames(
    tmp_path,
    monkeypatch,
    capsys,
):
    module = cold_benchmark_module()
    calls = []

    class Timer:
        def measure(self, operation):
            value = operation()
            return value, {
                **{stage: 1 for stage in module.STAGES},
                "unclassified_residual": 1,
                "complete_frame": len(module.STAGES) + 1,
            }

    def generate(request, *, configuration=None):
        del configuration
        calls.append(request)
        output = request.product.output
        output.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (3, 2), (10, 20, 30, 255)).save(output)
        rendering = SimpleNamespace(layers=())
        export = SimpleNamespace(rendering=rendering)
        return SimpleNamespace(outputs=(output,), exports=(export,))

    monkeypatch.setattr(module, "ExclusiveStageTimer", Timer)
    monkeypatch.setattr(module, "generate_chart_request", generate)
    monkeypatch.setattr(module, "_commit", lambda: "abc123")
    monkeypatch.setattr(
        module,
        "resolve_fixed_sky_rotating_horizon_frame",
        lambda frame: SimpleNamespace(
            chart_request=replace(
                frame.celestial_request,
                observer=frame.local_observer,
            ),
            orientation=FixedSkyCircumpolarOrientation(
                pole="south",
                anchor_reference_position_angle_deg=0.0,
                frame_reference_position_angle_deg=0.0,
                position_angle_deg=0.0,
            ),
        ),
    )

    report = module.benchmark(tmp_path / "outside-repository")

    assert report["schema"].endswith(".v1")
    assert report["environment"]["commit"] == "abc123"
    assert report["measurement"]["exclusive"] is True
    assert report["measurement"]["threshold"] is None
    assert len(report["frames"]) == 3
    assert report["measurement"]["summary"]["complete_frame"] == {
        "median_ns": 9,
        "minimum_ns": 9,
        "maximum_ns": 9,
        "range_ns": 0,
    }
    assert len(calls) == 3
    assert len({id(request) for request in calls}) == 3
    assert tuple(request.observer.time.isoformat() for request in calls) == (
        tuple(frame["simulation_time"] for frame in report["frames"])
    )
    json.dumps(report, default=module._json_value)
    progress = capsys.readouterr().out
    assert "[0/3 0%] starting frame 1" in progress
    assert "[3/3 100%] frame complete" in progress
    assert "accounting closed=True" in progress


def test_exclusive_timer_closes_accounting_without_overlapping_stages():
    module = cold_benchmark_module()
    namespace = {}
    clock_calls = []

    def clock():
        clock_calls.append(len(clock_calls) + 1)
        return clock_calls[-1]

    exec(
        compile(
            "def transform():\n"
            "    total = 0\n"
            "    for value in range(2000):\n"
            "        total += value\n"
            "    return total\n",
            "/tmp/wenu/coordinate_service.py",
            "exec",
        ),
        namespace,
    )

    result, timings = module.ExclusiveStageTimer(clock=clock).measure(
        namespace["transform"]
    )

    assert result == sum(range(2000))
    assert timings["astronomical_transformation"] > 0
    assert timings["complete_frame"] == sum(
        timings[name]
        for name in module.STAGES + ("unclassified_residual",)
    )
    assert len(clock_calls) <= 6


def test_cold_benchmark_products_must_remain_outside_repository():
    module = cold_benchmark_module()

    with pytest.raises(ValueError, match="output must be outside"):
        module.benchmark(
            Path(__file__).resolve().parents[1] / "output" / "cold-frames"
        )
