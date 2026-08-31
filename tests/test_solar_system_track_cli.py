"""CLI contract tests for Solar-System tracks."""
import argparse
import pytest
from wenu.charts.chart_arguments import (
    add_chart_content_arguments,
    chart_track_options,
)

def parse(*values):
    parser = argparse.ArgumentParser()
    add_chart_content_arguments(parser)
    return parser.parse_args(values)

def test_complete_venus_track_group_uses_governed_duration_units():
    options = chart_track_options(parse(
        "--planet-track", "venus",
        "--track-start", "2026-08-30T00:00:00Z",
        "--track-sample-step", "1h",
        "--track-tick-step", "7day",
        "--track-tick-count", "4",
    ))
    assert options.body == "venus"
    assert options.start_instant == "2026-08-30T00:00:00Z"
    assert options.sample_step_days == pytest.approx(1.0 / 24.0)
    assert options.tick_step_days == 7.0
    assert options.tick_count == 4
    assert options.label_ticks is False

def test_absent_track_group_resolves_to_none():
    assert chart_track_options(parse()) is None

def test_partial_track_group_is_rejected():
    with pytest.raises(ValueError, match="requires all track options"):
        chart_track_options(parse("--planet-track", "venus"))

@pytest.mark.parametrize("value", ("0h", "-1d", "minute", "1w"))
def test_duration_vocabulary_rejects_unsupported_or_nonpositive_values(value):
    with pytest.raises(SystemExit):
        parse(
            "--planet-track", "venus",
            "--track-start", "2026-08-30T00:00:00Z",
            "--track-sample-step", value,
            "--track-tick-step", "7d",
            "--track-tick-count", "4",
        )

def test_tick_count_must_be_positive():
    with pytest.raises(ValueError, match="positive integer"):
        chart_track_options(parse(
            "--planet-track", "venus",
            "--track-start", "2026-08-30T00:00:00Z",
            "--track-sample-step", "1h",
            "--track-tick-step", "7d",
            "--track-tick-count", "0",
        ))


def test_major_tick_date_labels_are_explicitly_opt_in():
    options = chart_track_options(parse(
        "--planet-track", "venus",
        "--track-start", "2026-08-30T00:00:00Z",
        "--track-sample-step", "1h",
        "--track-tick-step", "7d",
        "--track-tick-count", "4",
        "--track-tick-labels",
    ))
    assert options.label_ticks is True
