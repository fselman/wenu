"""Canonical observer-time sequence planning and orchestration tests."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import struct

import pytest

import wenu
import wenu.charts.sequence as sequence_module
from wenu.charts.product_options import ChartProductOptions
from wenu.charts.request import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartRequest,
)
from wenu.charts.request_generation import ChartRequestGeneration
from wenu.charts.sequence import (
    ObserverTimeChartSequenceFrameResult,
    ObserverTimeChartSequenceRequest,
    generate_observer_time_chart_sequence,
)
from wenu.output_policy import OutputFormat
from wenu.temporal import PlaybackSpec, TemporalTimeline


def chart_request(output: Path, **product_options):
    return ChartRequest(
        observer=ChartObserverRequest(
            time="2026-08-21T21:00:00-04:00",
            location="La Ligua",
        ),
        family="circumpolar",
        frame=ChartFrameRequest(
            pole="south",
            limiting_declination_deg=-60,
        ),
        product=ChartProductOptions(
            output=output,
            output_format=OutputFormat.PNG,
            **product_options,
        ),
    )


def timeline(count=3):
    return TemporalTimeline.uniform(
        datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
        datetime(2026, 8, 22, 3, tzinfo=timezone.utc),
        count,
        display_timezone="America/Santiago",
    )



def test_frame_result_has_one_stable_public_name():
    assert (
        ObserverTimeChartSequenceFrameResult.__name__
        == "ObserverTimeChartSequenceFrameResult"
    )
    assert (
        wenu.ObserverTimeChartSequenceFrameResult
        is ObserverTimeChartSequenceFrameResult
    )
    assert not hasattr(
        sequence_module,
        "ObserverTimeObserverTimeChartSequenceFrameResult",
    )

def test_sequence_pairs_one_chart_definition_with_explicit_frames(tmp_path):
    sequence = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        playback=PlaybackSpec(timedelta(seconds=1.5), 2),
    )

    assert sequence.frame_count == 3
    assert tuple(frame.name for frame in sequence.frames) == (
        "frame-0000.png",
        "frame-0001.png",
        "frame-0002.png",
    )
    assert tuple(frame.expected_output for frame in sequence.frames) == (
        tmp_path / "frames" / "frame-0000.png",
        tmp_path / "frames" / "frame-0001.png",
        tmp_path / "frames" / "frame-0002.png",
    )
    assert tuple(
        frame.request.observer.time for frame in sequence.frames
    ) == sequence.timeline.instants
    assert tuple(
        frame.display_time.isoformat() for frame in sequence.frames
    ) == (
        "2026-08-21T21:00:00-04:00",
        "2026-08-21T22:00:00-04:00",
        "2026-08-21T23:00:00-04:00",
    )


def test_sequence_calls_only_the_canonical_static_generator(
    tmp_path,
    monkeypatch,
):
    sequence = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
    )
    calls = []

    def generator(request):
        calls.append(request)
        request.product.output.parent.mkdir(parents=True, exist_ok=True)
        request.product.output.write_bytes(b"frame")
        return ChartRequestGeneration(
            exports=(SimpleNamespace(output=request.product.output),)
        )

    monkeypatch.setattr(sequence_module, "generate_chart_request", generator)
    result = generate_observer_time_chart_sequence(sequence)

    assert tuple(calls) == tuple(
        frame.request for frame in sequence.frames
    )
    assert result.outputs == tuple(
        tmp_path / "frames" / f"frame-{index:04d}.png"
        for index in range(3)
    )
    assert tuple(
        item.frame.simulation_time for item in result.frames
    ) == sequence.timeline.instants


def test_sequence_requires_one_explicitly_formatted_directory(tmp_path):
    base = chart_request(tmp_path / "frames")

    with pytest.raises(ValueError, match="explicit output format"):
        ObserverTimeChartSequenceRequest(
            chart=ChartRequest(
                observer=base.observer,
                family=base.family,
                frame=base.frame,
                product=ChartProductOptions(output=tmp_path / "frames"),
            ),
            timeline=timeline(),
        )

    with pytest.raises(ValueError, match="must be a directory"):
        ObserverTimeChartSequenceRequest(
            chart=chart_request(tmp_path / "frame.png"),
            timeline=timeline(),
        )

    with pytest.raises(ValueError, match="one chart product"):
        ObserverTimeChartSequenceRequest(
            chart=chart_request(
                tmp_path / "frames",
                all_products=True,
            ),
            timeline=timeline(),
        )


def test_sequence_rejects_static_output_different_from_plan(
    tmp_path,
    monkeypatch,
):
    sequence = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(count=2),
    )

    def generator(request):
        return ChartRequestGeneration(
            exports=(SimpleNamespace(output=Path("wrong.png")),)
        )

    monkeypatch.setattr(sequence_module, "generate_chart_request", generator)
    with pytest.raises(ValueError, match="do not match"):
        generate_observer_time_chart_sequence(sequence)


def test_observer_time_sequence_generates_real_canonical_frames(tmp_path):
    sequence = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=TemporalTimeline.uniform(
            datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
            datetime(2026, 8, 22, 7, tzinfo=timezone.utc),
            2,
            display_timezone="America/Santiago",
        ),
    )

    result = generate_observer_time_chart_sequence(sequence)

    assert result.outputs == (
        tmp_path / "frames" / "frame-0000.png",
        tmp_path / "frames" / "frame-0001.png",
    )
    assert all(path.is_file() for path in result.outputs)

    def png_size(path):
        header = path.read_bytes()[:24]
        assert header[:8] == b"\x89PNG\r\n\x1a\n"
        return struct.unpack(">II", header[16:24])

    assert png_size(result.outputs[0]) == png_size(result.outputs[1])
    assert sha256(result.outputs[0].read_bytes()).digest() != sha256(
        result.outputs[1].read_bytes()
    ).digest()



def _file_generator(calls):
    def generate(request):
        calls.append(request.product.output)
        request.product.output.parent.mkdir(parents=True, exist_ok=True)
        request.product.output.write_bytes(
            request.observer.time.isoformat().encode("ascii")
        )
        return ChartRequestGeneration(
            exports=(SimpleNamespace(output=request.product.output),)
        )

    return generate


def test_resume_reuses_only_manifest_verified_outputs(
    tmp_path,
    monkeypatch,
):
    planned = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(count=2),
    )
    first_calls = []
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator(first_calls),
    )
    first = generate_observer_time_chart_sequence(planned)

    assert first.rendered_count == 2
    assert first.reused_count == 0
    assert first.manifest_path.is_file()

    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        lambda request: pytest.fail("verified frame was rendered again"),
    )
    resumed = generate_observer_time_chart_sequence(
        planned,
        restart_policy="resume",
    )

    assert resumed.outputs == first.outputs
    assert resumed.rendered_count == 0
    assert resumed.reused_count == 2
    assert all(frame.generation is None for frame in resumed.frames)


def test_resume_rerenders_an_altered_output_only(tmp_path, monkeypatch):
    planned = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(count=2),
    )
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator([]),
    )
    first = generate_observer_time_chart_sequence(planned)
    first.outputs[0].write_bytes(b"altered")

    resumed_calls = []
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator(resumed_calls),
    )
    resumed = generate_observer_time_chart_sequence(
        planned,
        restart_policy="resume",
    )

    assert resumed_calls == [first.outputs[0]]
    assert resumed.rendered_count == 1
    assert resumed.reused_count == 1
    assert not resumed.frames[0].reused
    assert resumed.frames[1].reused


def test_resume_rejects_an_incompatible_manifest_before_rendering(
    tmp_path,
    monkeypatch,
):
    planned = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(count=2),
    )
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator([]),
    )
    generate_observer_time_chart_sequence(planned)
    incompatible = replace(
        planned,
        chart=replace(planned.chart, title="Different sequence"),
    )
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        lambda request: pytest.fail("incompatible sequence rendered"),
    )

    with pytest.raises(ValueError, match="incompatible"):
        generate_observer_time_chart_sequence(
            incompatible,
            restart_policy="resume",
        )


def test_restart_renders_every_frame_even_when_manifest_is_complete(
    tmp_path,
    monkeypatch,
):
    planned = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(count=2),
    )
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator([]),
    )
    generate_observer_time_chart_sequence(planned)
    restart_calls = []
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator(restart_calls),
    )

    restarted = generate_observer_time_chart_sequence(
        planned,
        restart_policy="restart",
    )

    assert restart_calls == list(restarted.outputs)
    assert restarted.rendered_count == 2
    assert restarted.reused_count == 0
