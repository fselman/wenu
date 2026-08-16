"""Matplotlib realization of polar calendar and A4 page furniture."""

import matplotlib.pyplot as plt
import pytest

from wenu import (
    MatplotlibRenderer,
    PolarCalendarFurnitureRequest,
    PolarPageFurnitureRequest,
    PolarPlanispherePairRequest,
    compose_chart,
    draw_polar_page_furniture,
    polar_disk_axes_bounds,
)


def resolved_values():
    pair = PolarPlanispherePairRequest(calendar_radius_mm=78.0).resolve()
    calendar = PolarCalendarFurnitureRequest().resolve(pair)
    pages = PolarPageFurnitureRequest(
        source_revision="7fd4649"
    ).resolve(pair)
    return pair, calendar, pages


def test_disk_axes_bounds_preserve_actual_physical_disk_size():
    _, _, pages = resolved_values()

    bounds = polar_disk_axes_bounds(pages.south)

    assert bounds == pytest.approx(
        (
            7.5 / 210.0,
            51.0 / 297.0,
            195.0 / 210.0,
            195.0 / 297.0,
        )
    )


def test_resolved_calendar_and_page_records_are_realized_once():
    pair, calendar, pages = resolved_values()
    chart = pair.south
    composition = compose_chart(chart, style="atlas", mode="print")
    figure = plt.figure(figsize=(210.0 / 25.4, 297.0 / 25.4))
    ax = figure.add_axes(polar_disk_axes_bounds(pages.south))
    composition.style.configure_axes(ax)
    renderer = MatplotlibRenderer(ax)
    try:
        result = draw_polar_page_furniture(
            chart=chart,
            sky=object(),
            renderer=renderer,
            composition=composition,
            rendering=object(),
            calendar_face=calendar.south,
            page_face=pages.south,
        )
    finally:
        plt.close(figure)

    assert len(result.calendar_lines) == 365
    assert len(result.calendar_labels) == 83
    assert len(result.center_artists) == 2
    assert len(result.registration_artists) == 3
    assert len(result.ruler_artists) == 8
    assert len(result.text_artists) == len(pages.south.text_blocks)
    assert result.page_axes.get_xlim() == pytest.approx((0.0, 210.0))
    assert result.page_axes.get_ylim() == pytest.approx((0.0, 297.0))
    outer = chart.boundary_radius * 97.5 / 78.0
    assert ax.get_xlim() == pytest.approx((-outer, outer))


def test_realization_rejects_mixed_faces_and_invalid_month_names():
    pair, calendar, pages = resolved_values()
    chart = pair.south
    composition = compose_chart(chart, style="atlas", mode="print")
    figure = plt.figure(figsize=(210.0 / 25.4, 297.0 / 25.4))
    ax = figure.add_axes(polar_disk_axes_bounds(pages.south))
    renderer = MatplotlibRenderer(ax)
    try:
        with pytest.raises(ValueError, match="faces must match"):
            draw_polar_page_furniture(
                chart=chart,
                sky=object(),
                renderer=renderer,
                composition=composition,
                rendering=object(),
                calendar_face=calendar.north,
                page_face=pages.south,
            )
        with pytest.raises(ValueError, match="twelve"):
            draw_polar_page_furniture(
                chart=chart,
                sky=object(),
                renderer=renderer,
                composition=composition,
                rendering=object(),
                calendar_face=calendar.south,
                page_face=pages.south,
                month_names=("Enero",),
            )
    finally:
        plt.close(figure)
