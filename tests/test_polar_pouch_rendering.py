"""Matplotlib realization of immutable folded-pouch furniture."""

import matplotlib.pyplot as plt
import pytest

from wenu import (
    PolarHorizonFaceOverlay,
    PolarHorizonPairOverlay,
    PolarPouchFurnitureRequest,
    draw_polar_pouch_face,
)


def pouches():
    common = {
        "page_size_mm": (210.0, 297.0),
        "disk_center_mm": (105.0, 148.5),
        "disk_radius_mm": 97.5,
        "site_latitude_deg": -32.443342,
        "cut_clearance_mm": 1.0,
        "pole_position_mm": (105.0, 148.5),
    }
    return PolarPouchFurnitureRequest().resolve(
        PolarHorizonPairOverlay(
            south=PolarHorizonFaceOverlay(
                face="south",
                horizon_segments_mm=(
                    ((7.5, 148.5), (105.0, 120.0), (202.5, 148.5)),
                ),
                meridian_horizon_position_mm=(105.0, 120.0),
                **common,
            ),
            north=PolarHorizonFaceOverlay(
                face="north",
                horizon_segments_mm=(
                    ((7.5, 148.5), (105.0, 177.0), (202.5, 148.5)),
                ),
                meridian_horizon_position_mm=(105.0, 177.0),
                **common,
            ),
        )
    )


def test_renderer_realizes_every_resolved_artist_once_in_black():
    face = pouches().south
    figure = plt.figure(figsize=(210.0 / 25.4, 297.0 / 25.4))
    try:
        result = draw_polar_pouch_face(face, figure=figure)
    finally:
        plt.close(figure)

    assert result.page_axes.get_xlim() == pytest.approx((0.0, 210.0))
    assert result.page_axes.get_ylim() == pytest.approx((0.0, 297.0))
    assert len(result.horizon_lines) == len(face.horizon_segments_mm)
    assert len(result.date_windows) == 3
    assert len(result.hour_ticks) == 11
    assert len(result.hour_labels) == 11
    assert len(result.labels) == len(face.labels)
    assert len(result.glue_strips) == 2
    assert all(artist.get_color() == "black" for artist in result.hour_ticks)
    assert all(label.get_color() == "black" for label in result.hour_labels)
    assert result.hour_circle.get_linewidth() == pytest.approx(0.8)
    assert all(
        window.get_linewidth() == pytest.approx(1.2)
        for window in result.date_windows
    )
    assert all(
        tick.get_linewidth() == pytest.approx(0.8)
        for tick in result.hour_ticks
    )
    assert all(
        label.get_fontsize() == pytest.approx(12.4)
        for label in result.hour_labels
    )
    assert all(
        label.get_fontweight() == "bold" for label in result.hour_labels
    )
    assert tuple(label.get_text() for label in result.labels) == tuple(
        label.text for label in face.labels
    )


def test_front_and_back_realization_preserve_hour_reading_direction():
    value = pouches()
    figures = [
        plt.figure(figsize=(210.0 / 25.4, 297.0 / 25.4)),
        plt.figure(figsize=(210.0 / 25.4, 297.0 / 25.4)),
    ]
    try:
        south = draw_polar_pouch_face(value.south, figure=figures[0])
        north = draw_polar_pouch_face(value.north, figure=figures[1])
    finally:
        for figure in figures:
            plt.close(figure)

    assert south.hour_labels[0].get_position()[0] > (
        south.hour_labels[-1].get_position()[0]
    )
    assert north.hour_labels[0].get_position()[0] < (
        north.hour_labels[-1].get_position()[0]
    )
    assert south.labels[-1].get_text() == "Muchos cielos, un firmamento"
    assert tuple(label.get_text() for label in south.labels).count(
        "HORIZONTE"
    ) == 2
    assert all(
        label.get_text() != "Muchos cielos, un firmamento"
        for label in north.labels
    )
    assert tuple(label.get_text() for label in north.labels).count(
        "HORIZONTE"
    ) == 2
    assert all(
        label.get_fontweight() == "bold"
        for label in north.labels
        if label.get_text() in {"W", "N", "E", "HORIZONTE"}
    )
    title = south.labels[-1]
    assert title.get_fontsize() == pytest.approx(14.0)
    assert title.get_fontfamily()[0] == "serif"
    assert title.get_fontstyle() == "italic"


def test_renderer_rejects_unresolved_values_and_does_not_save():
    with pytest.raises(TypeError, match="face"):
        draw_polar_pouch_face(object())

    from pathlib import Path

    source = (
        Path(__file__).parents[1]
        / "src/wenu/charts/polar_pouch_rendering.py"
    ).read_text(encoding="utf-8")
    assert "savefig" not in source
    assert ".save(" not in source
