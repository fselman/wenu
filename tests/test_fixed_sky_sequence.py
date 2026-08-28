"""Fixed-sky and rotating-horizon planning-contract tests."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from wenu.charts.fixed_sky_sequence import (
    FixedSkyRotatingHorizonSequenceRequest,
    resolve_fixed_sky_rotating_horizon_frame,
)
from wenu.charts.product_options import ChartProductOptions
from wenu.charts.request import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartRequest,
)
from wenu.output_policy import OutputFormat
from wenu.temporal import PlaybackSpec, TemporalTimeline


def chart_request(output):
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
        ),
    )


def timeline():
    return TemporalTimeline.uniform(
        datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
        datetime(2026, 8, 22, 7, tzinfo=timezone.utc),
        3,
        display_timezone="America/Santiago",
    )


def test_fixed_sky_plan_separates_anchor_and_local_observer_time(tmp_path):
    anchor = datetime(
        2026, 8, 21, 21, tzinfo=timezone(timedelta(hours=-4))
    )
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        celestial_anchor_time=anchor,
        playback=PlaybackSpec(timedelta(seconds=1.5), 2),
    )

    assert sequence.celestial_anchor_time == datetime(
        2026, 8, 22, 1, tzinfo=timezone.utc
    )
    assert sequence.frame_count == 3
    assert tuple(frame.name for frame in sequence.frames) == (
        "frame-0000.png",
        "frame-0001.png",
        "frame-0002.png",
    )
    assert {
        frame.celestial_request.observer.time
        for frame in sequence.frames
    } == {sequence.celestial_anchor_time}
    assert tuple(
        frame.local_observer.time for frame in sequence.frames
    ) == sequence.timeline.instants
    assert tuple(
        frame.expected_output for frame in sequence.frames
    ) == tuple(
        tmp_path / "frames" / f"frame-{index:04d}.png"
        for index in range(3)
    )


def test_fixed_sky_plan_preserves_location_for_both_time_owners(tmp_path):
    request = chart_request(tmp_path / "frames")
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=request,
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[1],
    )

    assert sequence.celestial_observer.location == "La Ligua"
    assert all(
        frame.local_observer.location == "La Ligua"
        for frame in sequence.frames
    )
    assert all(
        frame.celestial_request.observer.location == "La Ligua"
        for frame in sequence.frames
    )


def test_anchor_is_not_inferred_from_timeline_or_catalogue_epoch(tmp_path):
    explicit = datetime(2035, 1, 1, tzinfo=timezone.utc)
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        celestial_anchor_time=explicit,
    )

    assert sequence.celestial_anchor_time == explicit
    assert sequence.celestial_anchor_time not in sequence.timeline.instants
    assert not hasattr(sequence, "catalogue_reference_epoch")


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ("2026-08-22T01:00:00Z", TypeError),
        (datetime(2026, 8, 22, 1), ValueError),
    ],
)
def test_fixed_sky_anchor_requires_an_aware_datetime(
    tmp_path,
    value,
    error,
):
    with pytest.raises(error, match="celestial_anchor_time"):
        FixedSkyRotatingHorizonSequenceRequest(
            chart=chart_request(tmp_path / "frames"),
            timeline=timeline(),
            celestial_anchor_time=value,
        )


def test_fixed_sky_sequence_retains_single_product_constraints(tmp_path):
    request = chart_request(tmp_path / "frames")

    with pytest.raises(ValueError, match="explicit output format"):
        FixedSkyRotatingHorizonSequenceRequest(
            chart=replace(
                request,
                product=ChartProductOptions(output=tmp_path / "frames"),
            ),
            timeline=timeline(),
            celestial_anchor_time=timeline().instants[0],
        )

    with pytest.raises(ValueError, match="must be a directory"):
        FixedSkyRotatingHorizonSequenceRequest(
            chart=replace(
                request,
                product=replace(
                    request.product,
                    output=tmp_path / "frame.png",
                ),
            ),
            timeline=timeline(),
            celestial_anchor_time=timeline().instants[0],
        )



def test_resolved_frames_use_local_time_and_anchor_relative_rotation(tmp_path):
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[0],
    )

    first = resolve_fixed_sky_rotating_horizon_frame(sequence.frames[0])
    last = resolve_fixed_sky_rotating_horizon_frame(sequence.frames[-1])

    assert first.chart_request.observer == sequence.frames[0].local_observer
    assert last.chart_request.observer == sequence.frames[-1].local_observer
    assert first.orientation.position_angle_deg == 0.0
    assert first.chart_request.frame.position_angle_deg == 0.0
    assert last.orientation.position_angle_deg != 0.0
    assert (
        last.chart_request.frame.position_angle_deg
        == last.orientation.position_angle_deg
    )
    assert all(
        frame.celestial_request.observer.time
        == sequence.celestial_anchor_time
        for frame in sequence.frames
    )


def test_resolved_frame_preserves_explicit_anchor_position_angle(tmp_path):
    request = chart_request(tmp_path / "frames")
    request = replace(
        request,
        frame=replace(request.frame, position_angle_deg=17.5),
    )
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=request,
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[1],
    )

    resolved = resolve_fixed_sky_rotating_horizon_frame(sequence.frames[1])

    assert resolved.orientation.position_angle_deg == 17.5
    assert resolved.chart_request.frame.position_angle_deg == 17.5


def test_resolved_frame_rejects_unproved_chart_families(tmp_path):
    request = chart_request(tmp_path / "frames")
    frame = sequence_frame = FixedSkyRotatingHorizonSequenceRequest(
        chart=request,
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[0],
    ).frames[0]
    unsupported_request = replace(
        sequence_frame.celestial_request,
        family="planisphere",
        frame=ChartFrameRequest(),
    )
    unsupported = replace(frame, celestial_request=unsupported_request)

    with pytest.raises(ValueError, match="currently supports circumpolar"):
        resolve_fixed_sky_rotating_horizon_frame(unsupported)
