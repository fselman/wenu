"""Tests for drawable projected Solar-System track annotations."""
from types import SimpleNamespace
import numpy as np
from wenu.geometry.projected import ProjectedCurve, ProjectedCurves, ProjectedGrid
from wenu.sky.solar_system_track_layer import prepare_projected_track, start_label_anchor

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
        assert np.allclose(np.diff(tick.y), (2.0,))

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
