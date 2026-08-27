"""Reference circumpolar movie adapter tests."""

from datetime import timedelta

import pytest

from tools import render_circumpolar_movie as movie


def test_movie_adapter_resolves_one_explicit_temporal_contract():
    arguments = movie.parser().parse_args([])

    timeline, playback = movie.sequence_contract(arguments)

    assert timeline.frame_count == 180
    assert timeline.simulation_duration == timedelta(hours=12)
    assert timeline.display_timezone == "America/Santiago"
    assert timeline.frame_name(0) == "frame-0000.png"
    assert timeline.frame_name(179) == "frame-0179.png"
    assert playback.duration == timedelta(seconds=15)
    assert playback.frames_per_second == 12.0
    assert playback.frame_count == timeline.frame_count


def test_movie_adapter_keeps_playback_out_of_physical_sampling():
    arguments = movie.parser().parse_args(
        [
            "--duration-hours", "24",
            "--movie-seconds", "10",
            "--fps", "24",
        ]
    )

    timeline, playback = movie.sequence_contract(arguments)

    assert timeline.simulation_duration == timedelta(hours=24)
    assert timeline.frame_count == 240
    assert playback.duration == timedelta(seconds=10)
    assert playback.frames_per_second == 24.0


@pytest.mark.parametrize(
    "values",
    (
        ("--duration-hours", "0"),
        ("--movie-seconds", "0"),
        ("--fps", "0"),
    ),
)
def test_movie_adapter_rejects_nonpositive_time_controls(values):
    arguments = movie.parser().parse_args(list(values))

    with pytest.raises(SystemExit):
        movie.sequence_contract(arguments)
