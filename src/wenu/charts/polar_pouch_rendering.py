"""Matplotlib realization of resolved polar-pouch furniture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.polar_pouch_furniture import PolarPouchFaceFurniture


_LABEL_STYLE = {
    "cardinal": {"fontsize": 11.0, "fontweight": "bold"},
    "horizon": {"fontsize": 6.5, "fontweight": "medium"},
    "horizon_bold": {"fontsize": 6.5, "fontweight": "bold"},
    "title": {
        "fontsize": 14.0,
        "fontfamily": "serif",
        "fontstyle": "italic",
        "fontweight": "semibold",
    },
}


@dataclass(frozen=True)
class PolarPouchFaceRendering:
    """Inspectable artists for one actual-size pouch face."""

    page_axes: object
    disk_guide: object
    sky_window: object
    horizon_lines: tuple[object, ...]
    date_windows: tuple[object, ...]
    hour_circle: object
    hour_ticks: tuple[object, ...]
    hour_labels: tuple[object, ...]
    labels: tuple[object, ...]
    fold_line: object
    glue_strips: tuple[object, ...]


def draw_polar_pouch_face(
    face,
    *,
    figure=None,
    axes=None,
    artist_transform=None,
    clip_bounds_mm=None,
):
    """Realize one resolved pouch face without calculating or saving it."""
    if not isinstance(face, PolarPouchFaceFurniture):
        raise TypeError("face must be a PolarPouchFaceFurniture value.")
    if figure is not None and axes is not None and axes.figure is not figure:
        raise ValueError("figure and axes must refer to the same figure.")
    if figure is None and axes is None:
        import matplotlib.pyplot as plt

        figure = plt.figure(
            figsize=(face.page_size_mm[0] / 25.4, face.page_size_mm[1] / 25.4),
            facecolor="white",
        )
    from matplotlib.patches import Arc, Circle, Polygon, Rectangle, Wedge

    if axes is None:
        ax = figure.add_axes(
            (0.0, 0.0, 1.0, 1.0), label=f"{face.face}_pouch"
        )
    else:
        ax = axes
    ax.set_xlim(0.0, face.page_size_mm[0])
    ax.set_ylim(0.0, face.page_size_mm[1])
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_facecolor("white")
    disk_guide = Circle(
        face.disk_center_mm,
        face.disk_radius_mm,
        fill=False,
        edgecolor="black",
        linewidth=0.25,
        linestyle=(0, (1.5, 2.5)),
        zorder=2,
    )
    ax.add_patch(disk_guide)
    sky_window = Polygon(
        face.sky_window_boundary_mm,
        closed=True,
        fill=False,
        edgecolor="black",
        linewidth=0.65,
        linestyle=(0, (3.0, 1.5)),
        zorder=5,
    )
    ax.add_patch(sky_window)
    horizon_lines = tuple(
        ax.plot(
            tuple(point[0] for point in segment),
            tuple(point[1] for point in segment),
            color="black",
            linewidth=0.8,
            zorder=6,
        )[0]
        for segment in face.horizon_segments_mm
    )
    date_windows = tuple(
        Wedge(
            window.center_mm,
            window.outer_radius_mm,
            window.start_angle_deg,
            window.end_angle_deg,
            width=(window.outer_radius_mm - window.inner_radius_mm),
            fill=False,
            edgecolor="black",
            linewidth=1.2,
            linestyle=(0, (2.0, 1.5)),
            zorder=7,
        )
        for window in face.date_windows
    )
    for artist in date_windows:
        ax.add_patch(artist)
    angles = tuple(mark.angle_deg for mark in face.hour_marks)
    hour_circle = Arc(
        face.disk_center_mm,
        2.0 * face.hour_circle_radius_mm,
        2.0 * face.hour_circle_radius_mm,
        theta1=min(angles),
        theta2=max(angles),
        edgecolor="black",
        linewidth=0.8,
        zorder=7,
    )
    ax.add_patch(hour_circle)
    hour_ticks = tuple(
        ax.plot(
            (mark.tick_start_mm[0], mark.tick_end_mm[0]),
            (mark.tick_start_mm[1], mark.tick_end_mm[1]),
            color="black",
            linewidth=0.8,
            solid_capstyle="butt",
            zorder=8,
        )[0]
        for mark in face.hour_marks
    )
    hour_labels = tuple(
        ax.text(
            *mark.numeral_position_mm,
            f"{mark.hour:02d}",
            color="black",
            fontsize=12.4,
            fontweight="bold",
            ha="center",
            va="center",
            rotation=mark.numeral_rotation_deg,
            rotation_mode="anchor",
            zorder=8,
        )
        for mark in face.hour_marks
    )
    labels = tuple(
        ax.text(
            *label.position_mm,
            label.text,
            color="black",
            ha="center",
            va="center",
            rotation=label.rotation_deg,
            rotation_mode="anchor",
            zorder=8,
            **_LABEL_STYLE[label.role],
        )
        for label in face.labels
    )
    fold = np.asarray(face.fold_line_mm, dtype=float)
    fold_line = ax.plot(
        fold[:, 0],
        fold[:, 1],
        color="black",
        linewidth=0.55,
        linestyle=(0, (5.0, 2.5)),
        zorder=4,
    )[0]
    glue_strips = tuple(
        Rectangle(
            strip.lower_left_mm,
            strip.upper_right_mm[0] - strip.lower_left_mm[0],
            strip.upper_right_mm[1] - strip.lower_left_mm[1],
            fill=False,
            edgecolor="black",
            linewidth=0.4,
            hatch="////",
            zorder=3,
        )
        for strip in face.glue_strips
    )
    for artist in glue_strips:
        ax.add_patch(artist)
    result = PolarPouchFaceRendering(
        page_axes=ax,
        disk_guide=disk_guide,
        sky_window=sky_window,
        horizon_lines=horizon_lines,
        date_windows=date_windows,
        hour_circle=hour_circle,
        hour_ticks=hour_ticks,
        hour_labels=hour_labels,
        labels=labels,
        fold_line=fold_line,
        glue_strips=glue_strips,
    )
    if artist_transform is not None or clip_bounds_mm is not None:
        _place_rendering(
            result,
            artist_transform=artist_transform,
            clip_bounds_mm=clip_bounds_mm,
        )
    return result


def _place_rendering(result, *, artist_transform, clip_bounds_mm):
    from matplotlib.patches import Rectangle
    from matplotlib.transforms import Affine2D

    transform = artist_transform or Affine2D()
    display_transform = transform + result.page_axes.transData
    clip = None
    if clip_bounds_mm is not None:
        left, bottom, right, top = tuple(float(v) for v in clip_bounds_mm)
        clip = Rectangle(
            (left, bottom),
            right - left,
            top - bottom,
            transform=result.page_axes.transData,
        )
    for artist in _rendering_artists(result):
        artist.set_transform(display_transform)
        if clip is not None:
            artist.set_clip_path(clip)


def _rendering_artists(result):
    return (
        result.disk_guide,
        result.sky_window,
        *result.horizon_lines,
        *result.date_windows,
        result.hour_circle,
        *result.hour_ticks,
        *result.hour_labels,
        *result.labels,
        result.fold_line,
        *result.glue_strips,
    )
