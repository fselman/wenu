"""Matplotlib realization of polar calendar and A4 page furniture."""

import matplotlib.pyplot as plt
import numpy as np
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
    pair = PolarPlanispherePairRequest(calendar_radius_mm=86.0).resolve()
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

    assert result.page_axes.patch.get_visible() is False
    assert result.calendar_lines[0].get_gid().startswith(
        "daily-tick-marks--"
    )
    assert result.day_labels[0].get_gid().startswith("day-labels--")
    assert result.month_labels[0].get_gid().startswith(
        "month-labels--"
    )
    assert result.cut_line.get_gid() == "cut-line"
    assert result.text_artists[0].get_gid().startswith(
        "page-information--"
    )
    assert len(result.calendar_lines) == 365
    assert len(result.calendar_labels) == 83
    assert len(result.day_labels) == len(calendar.south.day_labels)
    assert len(result.month_labels) == len(calendar.south.month_labels)
    assert len(result.center_artists) == 2
    assert len(result.registration_artists) == 3
    assert len(result.ruler_artists) == 8
    assert len(result.text_artists) == len(pages.south.text_blocks)
    assert len(result.magnitude_scale.markers) == 9
    assert len(result.magnitude_scale.labels) == 9
    assert tuple(
        marker.get_markersize() for marker in result.magnitude_scale.markers
    ) == pytest.approx(
        tuple(
            np.sqrt(entry.marker_area_points2)
            for entry in pages.south.magnitude_scale.entries
        )
    )
    assert result.page_axes.get_xlim() == pytest.approx((0.0, 210.0))
    assert result.page_axes.get_ylim() == pytest.approx((0.0, 297.0))
    outer = chart.boundary_radius * 97.5 / 86.0
    assert ax.get_xlim() == pytest.approx((-outer, outer))
    assert all(
        artist.get_markerfacecolor() == "black"
        and artist.get_markeredgecolor() == "black"
        for artist in result.registration_artists
    )
    assert result.center_artists[0].get_edgecolor() == (0.0, 0.0, 0.0, 1.0)
    assert result.center_artists[1].get_color() == "black"
    day = result.calendar_labels[0]
    month = result.calendar_labels[-1]
    assert day.get_fontsize() == pytest.approx(6.45)
    assert day.get_fontweight() == "semibold"
    assert month.get_fontsize() == pytest.approx(11.5)
    assert month.get_fontweight() == "semibold"
    assert all(line.get_color() == "#16394D" for line in result.calendar_lines)
    assert all(line.get_alpha() == pytest.approx(1.0) for line in result.calendar_lines)


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


def test_rendered_page_text_extents_remain_inside_the_safe_page():
    pair, calendar, pages = resolved_values()
    chart = pair.south
    page = pages.south
    composition = compose_chart(chart, style="atlas", mode="print")
    figure = plt.figure(figsize=(210.0 / 25.4, 297.0 / 25.4))
    ax = figure.add_axes(polar_disk_axes_bounds(page))
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
            page_face=page,
        )
        figure.canvas.draw()
        canvas_renderer = figure.canvas.get_renderer()
        inverse = result.page_axes.transData.inverted()
        for artist in result.text_artists:
            bounds = inverse.transform(
                artist.get_window_extent(renderer=canvas_renderer).get_points()
            )
            assert bounds[:, 0].min() >= page.safe_margin_mm
            assert bounds[:, 0].max() <= (
                page.page_width_mm - page.safe_margin_mm
            )
            assert bounds[:, 1].min() >= page.safe_margin_mm
            assert bounds[:, 1].max() <= (
                page.page_height_mm - page.safe_margin_mm
            )
    finally:
        plt.close(figure)


def test_larger_calendar_labels_remain_inside_the_physical_disk():
    pair, calendar, pages = resolved_values()
    chart = pair.south
    page = pages.south
    composition = compose_chart(chart, style="atlas", mode="print")
    figure = plt.figure(
        figsize=(210.0 / 25.4, 297.0 / 25.4), dpi=300
    )
    ax = figure.add_axes(polar_disk_axes_bounds(page))
    composition.style.configure_axes(ax)
    try:
        result = draw_polar_page_furniture(
            chart=chart,
            sky=object(),
            renderer=MatplotlibRenderer(ax),
            composition=composition,
            rendering=object(),
            calendar_face=calendar.south,
            page_face=page,
        )
        figure.canvas.draw()
        canvas_renderer = figure.canvas.get_renderer()
        millimetres_per_pixel = 25.4 / figure.dpi
        for artist in result.calendar_labels:
            rotation = artist.get_rotation()
            artist.set_rotation(0.0)
            figure.canvas.draw()
            bounds = artist.get_window_extent(renderer=canvas_renderer)
            anchor = ax.transData.transform(artist.get_position())
            artist.set_rotation(rotation)
            half_tangential_mm = max(
                abs(bounds.x0 - anchor[0]),
                abs(bounds.x1 - anchor[0]),
            ) * millimetres_per_pixel
            outward_mm = max(
                abs(bounds.y0 - anchor[1]),
                abs(bounds.y1 - anchor[1]),
            ) * millimetres_per_pixel
            anchor_radius_mm = (
                np.hypot(*artist.get_position())
                / chart.boundary_radius
                * calendar.south.star_disk_radius_mm
            )
            outer_corner_mm = np.hypot(
                anchor_radius_mm + outward_mm,
                half_tangential_mm,
            )
            assert outer_corner_mm <= page.disk_radius_mm
    finally:
        plt.close(figure)
