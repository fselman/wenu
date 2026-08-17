"""Matplotlib realization of resolved polar physical-page furniture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.polar_calendar_furniture import PolarCalendarFaceFurniture
from wenu.charts.polar_page_furniture import PolarFacePageFurniture


SPANISH_MONTH_NAMES = (
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)
_REGISTRATION_MARKERS = {
    "triangle": "^",
    "circle": "o",
    "square": "s",
}
_TEXT_STYLE = {
    "face_identity": {"fontsize": 11.0, "fontweight": "bold"},
    "rights_notice": {"fontsize": 5.2, "fontweight": "medium"},
    "edition_site": {"fontsize": 6.5},
    "geometry": {"fontsize": 6.2},
    "print_instruction": {"fontsize": 7.0, "fontweight": "bold"},
    "time_instruction": {"fontsize": 5.8},
    "assembly_instruction": {"fontsize": 5.8},
    "face_use": {"fontsize": 5.5, "fontweight": "bold"},
    "provenance": {"fontsize": 4.8},
    "ruler_caption": {"fontsize": 4.8},
}


@dataclass(frozen=True)
class PolarFacePageRendering:
    """Inspectable artists created for one resolved physical page."""

    calendar_lines: tuple[object, ...]
    calendar_labels: tuple[object, ...]
    page_axes: object
    cut_line: object
    center_artists: tuple[object, ...]
    registration_artists: tuple[object, ...]
    ruler_artists: tuple[object, ...]
    text_artists: tuple[object, ...]


def polar_disk_axes_bounds(face):
    """Return the outer-disk rectangle in normalized figure coordinates."""
    if not isinstance(face, PolarFacePageFurniture):
        raise TypeError("face must be a PolarFacePageFurniture value.")
    left = (face.disk_center_mm[0] - face.disk_radius_mm) / face.page_width_mm
    bottom = (
        face.disk_center_mm[1] - face.disk_radius_mm
    ) / face.page_height_mm
    return (
        left,
        bottom,
        face.disk_diameter_mm / face.page_width_mm,
        face.disk_diameter_mm / face.page_height_mm,
    )


def draw_polar_page_furniture(
    *,
    chart,
    sky,
    renderer,
    composition,
    rendering,
    calendar_face,
    page_face,
    month_names=SPANISH_MONTH_NAMES,
):
    """Draw resolved calendar and page records before canonical final save."""
    del sky, rendering
    if not isinstance(calendar_face, PolarCalendarFaceFurniture):
        raise TypeError(
            "calendar_face must be a PolarCalendarFaceFurniture value."
        )
    if not isinstance(page_face, PolarFacePageFurniture):
        raise TypeError("page_face must be a PolarFacePageFurniture value.")
    if calendar_face.face != page_face.face or chart.pole != page_face.face:
        raise ValueError("Chart, calendar, and page furniture faces must match.")
    names = tuple(str(value) for value in month_names)
    if len(names) != 12 or any(not value.strip() for value in names):
        raise ValueError("month_names must contain twelve non-empty values.")
    unit_per_mm = chart.boundary_radius / calendar_face.star_disk_radius_mm
    outer = calendar_face.outer_radius_mm * unit_per_mm
    renderer.ax.set_xlim(-outer, outer)
    renderer.ax.set_ylim(-outer, outer)
    renderer.ax.set_aspect("equal")
    renderer.ax.set_axis_off()
    label_color = composition.style.canvas.foreground_color
    calendar_lines, calendar_labels = _draw_calendar(
        renderer.ax,
        calendar_face,
        unit_per_mm,
        month_names=names,
        color=label_color,
        label_color=label_color,
        typography=composition.style.calendar,
    )
    page = _draw_page_axes(
        renderer.ax.figure,
        page_face,
        color=label_color,
    )
    return PolarFacePageRendering(
        calendar_lines=calendar_lines,
        calendar_labels=calendar_labels,
        **page,
    )


def _draw_calendar(
    ax,
    face,
    scale,
    *,
    month_names,
    color,
    label_color,
    typography,
):
    lines = []
    labels = []
    for tick in face.ticks:
        line = ax.plot(
            (tick.inner[0] * scale, tick.outer[0] * scale),
            (tick.inner[1] * scale, tick.outer[1] * scale),
            color=color,
            linewidth=(
                0.55
                if tick.month_boundary
                else 0.36 if tick.labeled_day else 0.18
            ),
            alpha=1.0,
            solid_capstyle="butt",
            zorder=30,
        )[0]
        lines.append(line)
    for label in face.day_labels:
        labels.append(
            ax.text(
                label.position[0] * scale,
                label.position[1] * scale,
                label.text,
                color=label_color,
                fontsize=typography.day_label_fontsize,
                fontweight=typography.day_label_fontweight,
                ha="center",
                va="baseline",
                rotation=label.rotation_deg,
                rotation_mode="anchor",
                zorder=31,
            )
        )
    for label in face.month_labels:
        labels.append(
            ax.text(
                label.position[0] * scale,
                label.position[1] * scale,
                month_names[label.month - 1],
                color=label_color,
                fontsize=typography.month_label_fontsize,
                fontweight=typography.month_label_fontweight,
                ha="center",
                va="baseline",
                rotation=label.rotation_deg,
                rotation_mode="anchor",
                zorder=31,
            )
        )
    return tuple(lines), tuple(labels)


def _draw_page_axes(figure, face, *, color):
    from matplotlib.patches import Circle

    ax = figure.add_axes((0.0, 0.0, 1.0, 1.0), label=f"{face.face}_page")
    ax.set_xlim(0.0, face.page_width_mm)
    ax.set_ylim(0.0, face.page_height_mm)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.patch.set_alpha(0.0)
    ax.set_zorder(100)
    cut_line = Circle(
        face.disk_center_mm,
        face.disk_radius_mm,
        fill=False,
        edgecolor="black",
        linewidth=0.35,
        linestyle=(0, (2.0, 2.0)),
        zorder=101,
    )
    ax.add_patch(cut_line)
    center_circle = Circle(
        face.disk_center_mm,
        face.center_punch_radius_mm,
        fill=False,
        edgecolor="black",
        linewidth=0.45,
        zorder=103,
    )
    ax.add_patch(center_circle)
    center_cross = ax.plot(
        *face.disk_center_mm,
        marker="+",
        markersize=5.0,
        markeredgewidth=0.55,
        color="black",
        linestyle="none",
        zorder=103,
    )[0]
    registration = tuple(
        ax.plot(
            *mark.position_mm,
            marker=_REGISTRATION_MARKERS[mark.glyph],
            markersize=(
                5.0
                if mark.identifier == face.orientation_mark_identifier
                else 3.8
            ),
            markerfacecolor="black",
            markeredgecolor="black",
            markeredgewidth=0.55,
            linestyle="none",
            zorder=103,
        )[0]
        for mark in face.registration_marks
    )
    ruler = _draw_ruler(ax, face, color=color)
    text = tuple(_draw_text_block(ax, block, color=color) for block in face.text_blocks)
    return {
        "page_axes": ax,
        "cut_line": cut_line,
        "center_artists": (center_circle, center_cross),
        "registration_artists": registration,
        "ruler_artists": ruler,
        "text_artists": text,
    }


def _draw_ruler(ax, face, *, color):
    ruler = face.scale_ruler
    start = np.asarray(ruler.start_mm, dtype=float)
    end = np.asarray(ruler.end_mm, dtype=float)
    direction = end - start
    length = np.linalg.norm(direction)
    unit = direction / length
    normal = np.asarray((-unit[1], unit[0]))
    artists = [
        ax.plot(
            (start[0], end[0]),
            (start[1], end[1]),
            color=color,
            linewidth=0.6,
            zorder=103,
        )[0]
    ]
    positions = np.arange(
        0.0,
        ruler.length_mm + ruler.major_interval_mm / 2.0,
        ruler.major_interval_mm,
    )
    for position in positions:
        point = start + unit * position
        edge = point + normal * 2.0
        artists.append(
            ax.plot(
                (point[0], edge[0]),
                (point[1], edge[1]),
                color=color,
                linewidth=0.55,
                zorder=103,
            )[0]
        )
    artists.append(
        ax.text(
            *(start + normal * 3.0),
            ruler.label,
            color=color,
            fontsize=4.8,
            ha="left",
            va="bottom",
            zorder=103,
        )
    )
    return tuple(artists)


def _draw_text_block(ax, block, *, color):
    options = dict(_TEXT_STYLE.get(block.role, {"fontsize": 5.5}))
    return ax.text(
        *block.position_mm,
        "\n".join(block.lines),
        color=color,
        ha=block.horizontal_alignment,
        va="center",
        linespacing=1.15,
        zorder=103,
        **options,
    )
