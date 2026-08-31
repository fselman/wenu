"""Tests for drawable projected Solar-System track annotations."""

from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from wenu.charts.styles import PublicationStyle
from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
)
from wenu.sky.solar_system_track_layer import (
    TrackLabelAnchor,
    _start_label_anchor,
    prepare_projected_track,
)


def spherical(indices=(0, 2, 4)):
    return SimpleNamespace(
        metadata={
            "tick_sample_indices": indices,
            "sample_instants": ("2026-08-30T00:00:00.000",),
        },
        names=np.asarray(("Venus",), dtype=object),
    )


def projected(x=(0, 1, 2, 3, 4), y=(0, 0, 0, 0, 0)):
    return ProjectedCurves(items=[
        ProjectedCurve(
            x=np.asarray(x, dtype=float),
            y=np.asarray(y, dtype=float),
        )
    ])


def test_preparation_builds_path_and_perpendicular_major_ticks():
    result = prepare_projected_track(
        spherical(), projected(), tick_length=2.0
    )

    assert isinstance(result, ProjectedGrid)
    assert result["path"][0].name is None
    assert result["labels"][0].name == "♀ 2026-08-30"
    assert np.allclose(result["labels"][0].x, (0.0, 0.0))
    assert np.allclose(result["labels"][0].y, (0.0, 0.0))
    assert len(result["ticks"]) == 2
    for tick in result["ticks"]:
        assert (
            np.allclose(tick.x, (2.0, 2.0))
            or np.allclose(tick.x, (4.0, 4.0))
        )
        assert np.allclose(np.abs(np.diff(tick.y)), (2.0,))


def test_preparation_uses_nearest_samples_at_stationary_tick():
    result = prepare_projected_track(
        spherical((0, 2)),
        projected(x=(0, 1, 1, 1, 2)),
        tick_length=1.0,
    )

    assert len(result["ticks"]) == 1
    assert result.metadata["omitted_tick_sample_indices"] == ()


def test_preparation_omits_unresolved_tick_deterministically():
    result = prepare_projected_track(
        spherical((0, 2)),
        projected(x=(1, 1, 1, 1, 1)),
        tick_length=1.0,
    )

    assert len(result["ticks"]) == 0
    assert result.metadata["omitted_tick_sample_indices"] == (2,)


def test_preparation_omits_start_tick_by_default():
    result = prepare_projected_track(
        spherical(), projected(), tick_length=1.0
    )

    assert result.metadata["tick_sample_indices"] == (2, 4)


def test_major_tick_labels_use_exact_sample_dates_when_enabled():
    source = spherical()
    source.metadata["sample_instants"] = (
        "2026-08-30T00:00:00.000",
        "2026-09-01T00:00:00.000",
        "2026-09-06T00:00:00.000",
        "2026-09-13T00:00:00.000",
        "2026-09-27T00:00:00.000",
    )

    result = prepare_projected_track(
        source, projected(), tick_length=1.0, label_ticks=True
    )

    assert tuple(curve.name for curve in result["ticks"]) == (
        "2026-09-06",
        "2026-09-27",
    )


def test_start_label_anchor_turns_inward_near_field_edge():
    curve = ProjectedCurve(
        x=np.asarray((0.95, 0.95)),
        y=np.asarray((0.95, 0.95)),
    )
    axes = SimpleNamespace(
        get_xlim=lambda: (-1.0, 1.0),
        get_ylim=lambda: (-1.0, 1.0),
    )

    anchor = _start_label_anchor(curve, axes)

    assert anchor.horizontal_alignment == "right"
    assert anchor.vertical_alignment == "top"


def test_two_pass_layout_keeps_one_side_when_labels_are_clear():
    figure, axes = plt.subplots(figsize=(4.0, 4.0), dpi=100)
    axes.set_xlim(-1.0, 1.0)
    axes.set_ylim(-1.0, 1.0)
    track = ProjectedCurve(
        x=np.linspace(-0.8, 0.8, 41),
        y=np.zeros(41),
    )
    ticks = tuple(
        ProjectedCurve(
            x=np.asarray((x, x)),
            y=np.asarray((-0.04, 0.04)),
            name=f"2026-09-{day:02d}",
        )
        for x, day in ((-0.75, 6), (0.75, 13))
    )
    anchor = TrackLabelAnchor(fontsize=9.0)
    anchor.set_geometry(track, ticks)

    try:
        placements = tuple(anchor(tick, axes) for tick in ticks)
        assert len({
            placement.vertical_alignment for placement in placements
        }) == 1
    finally:
        plt.close(figure)


def test_two_pass_layout_switches_only_between_tick_sides():
    figure, axes = plt.subplots(figsize=(4.0, 4.0), dpi=100)
    axes.set_xlim(-1.0, 1.0)
    axes.set_ylim(-1.0, 1.0)
    track = ProjectedCurve(
        x=np.linspace(-0.8, 0.8, 41),
        y=np.full(41, -0.5),
    )
    ticks = tuple(
        ProjectedCurve(
            x=np.asarray((-0.03, 0.03)),
            y=np.asarray((-0.01, 0.01)),
            name=name,
        )
        for name in ("2026-10-04", "2026-10-11")
    )
    anchor = TrackLabelAnchor(fontsize=9.0)
    anchor.set_geometry(track, ticks)

    try:
        placements = tuple(anchor(tick, axes) for tick in ticks)
        midpoint = axes.transData.transform((0.0, 0.0))
        direction = (
            axes.transData.transform((0.03, 0.01)) - midpoint
        )
        for placement in placements:
            offset = axes.transData.transform(
                (placement.x, placement.y)
            ) - midpoint
            assert abs(np.cross(direction, offset)) < 1.0e-8
        assert (
            placements[0].horizontal_alignment
            != placements[1].horizontal_alignment
        )
        assert _boxes_do_not_overlap(*anchor._claimed)
    finally:
        plt.close(figure)


def test_two_pass_layout_uses_inside_tick_side_near_viewport_edge():
    figure, axes = plt.subplots(figsize=(4.0, 4.0), dpi=100)
    axes.set_xlim(-1.0, 1.0)
    axes.set_ylim(-1.0, 1.0)
    track = ProjectedCurve(
        x=np.linspace(-0.8, 0.8, 41),
        y=np.full(41, -0.5),
    )
    tick = ProjectedCurve(
        x=np.asarray((0.95, 0.95)),
        y=np.asarray((0.90, 1.00)),
        name="2026-09-06",
    )
    anchor = TrackLabelAnchor(fontsize=9.0)
    anchor.set_geometry(track, (tick,))

    try:
        placement = anchor(tick, axes)
        assert placement.y < 0.90
        assert placement.vertical_alignment == "top"
    finally:
        plt.close(figure)


def test_publication_style_owns_track_appearance():
    style = PublicationStyle()

    assert style.solar_system_track_color == "#FFB000"
    assert style.solar_system_track_linewidth == 1.2
    assert style.solar_system_track_tick_linewidth == 1.0
    assert style.solar_system_track_label_fontsize == 9.0


def _boxes_do_not_overlap(left, right):
    return not (
        min(left[2], right[2]) > max(left[0], right[0])
        and min(left[3], right[3]) > max(left[1], right[1])
    )
