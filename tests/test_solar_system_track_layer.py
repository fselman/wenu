"""Tests for drawable projected Solar-System track annotations."""
from types import SimpleNamespace
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from wenu.geometry.projected import ProjectedCurve, ProjectedCurves, ProjectedGrid
from wenu.charts.styles import PublicationStyle
from wenu.sky.solar_system_track_layer import (
    TrackLabelAnchor,
    prepare_projected_track,
    start_label_anchor,
    track_label_anchor,
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
        ProjectedCurve(x=np.asarray(x, dtype=float), y=np.asarray(y, dtype=float))
    ])

def test_preparation_builds_one_path_and_perpendicular_major_ticks():
    result = prepare_projected_track(spherical(), projected(), tick_length=2.0)
    assert isinstance(result, ProjectedGrid)
    assert result["path"][0].name is None
    assert result["labels"][0].name == "♀ 2026-08-30"
    assert np.allclose(result["labels"][0].x, (0.0, 0.0))
    assert np.allclose(result["labels"][0].y, (0.0, 0.0))
    assert len(result["ticks"]) == 2
    for tick in result["ticks"]:
        assert np.allclose(tick.x, (2.0, 2.0)) or np.allclose(tick.x, (4.0, 4.0))
        assert np.allclose(np.abs(np.diff(tick.y)), (2.0,))

def test_preparation_uses_nearest_noncoincident_samples_at_stationary_tick():
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
    result = prepare_projected_track(spherical(), projected(), tick_length=1.0)
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
        "2026-09-06", "2026-09-27"
    )


def test_label_anchor_turns_inward_near_upper_right_field_edge():
    curve = ProjectedCurve(
        x=np.asarray((0.95, 0.95)), y=np.asarray((0.95, 0.95))
    )
    axes = SimpleNamespace(
        get_xlim=lambda: (-1.0, 1.0),
        get_ylim=lambda: (-1.0, 1.0),
    )
    anchor = start_label_anchor(curve, axes)
    assert anchor.horizontal_alignment == "right"
    assert anchor.vertical_alignment == "top"


def test_successive_tick_labels_alternate_across_the_track():
    source = spherical()
    source.metadata["sample_instants"] = tuple(
        f"2026-09-{day:02d}T00:00:00.000" for day in range(1, 6)
    )
    result = prepare_projected_track(
        source, projected(), tick_length=2.0, label_ticks=True
    )
    axes = SimpleNamespace(
        get_xlim=lambda: (-5.0, 5.0),
        get_ylim=lambda: (-5.0, 5.0),
    )
    first = track_label_anchor(result["ticks"][0], axes)
    second = track_label_anchor(result["ticks"][1], axes)
    assert first.y > 1.0
    assert first.vertical_alignment == "bottom"
    assert second.y < -1.0
    assert second.vertical_alignment == "top"


def test_publication_style_owns_projection_friendly_track_appearance():
    style = PublicationStyle()
    assert style.solar_system_track_color == "#FFB000"
    assert style.solar_system_track_linewidth == 1.2
    assert style.solar_system_track_tick_linewidth == 1.0
    assert style.solar_system_track_label_fontsize == 9.0



def test_tick_label_switches_sides_to_remain_inside_viewport():
    tick = ProjectedCurve(
        x=np.asarray((0.95, 0.95)),
        y=np.asarray((0.90, 1.00)),
        name="2026-09-06",
    )
    axes = SimpleNamespace(
        get_xlim=lambda: (-1.0, 1.0),
        get_ylim=lambda: (-1.0, 1.0),
    )
    anchor = track_label_anchor(tick, axes)
    assert anchor.y < 0.90
    assert anchor.vertical_alignment == "top"



def test_collision_aware_anchor_claims_nonoverlapping_display_boxes():
    figure, axes = plt.subplots(figsize=(4.0, 4.0), dpi=100)
    axes.set_xlim(-1.0, 1.0)
    axes.set_ylim(-1.0, 1.0)
    anchor = TrackLabelAnchor(fontsize=9.0)
    try:
        for index, x in enumerate((0.00, 0.02, 0.04, 0.06)):
            tick = ProjectedCurve(
                x=np.asarray((x - 0.03, x + 0.03)),
                y=np.asarray((-0.01, 0.01)),
                name=f"2026-10-{4 + 7 * index:02d}",
            )
            assert anchor(tick, axes) is not None
        assert len(anchor._claimed) == 4
        for index, left in enumerate(anchor._claimed):
            for right in anchor._claimed[index + 1:]:
                assert not (
                    min(left[2], right[2]) > max(left[0], right[0])
                    and min(left[3], right[3]) > max(left[1], right[1])
                )
    finally:
        plt.close(figure)
