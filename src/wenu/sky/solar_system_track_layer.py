"""Drawable Solar-System track layer and projected annotations."""
from __future__ import annotations
import numpy as np
from wenu.geometry.projected import ProjectedCurve, ProjectedCurves, ProjectedGrid
from wenu.rendering.label_placement import CurveLabelPlacement
from wenu.sky.sky_layer import SkyLayer
from wenu.sky.solar_system_tracks import SolarSystemTrackRealizer, SolarSystemTrackRequest

class SolarSystemTrackLayer(SkyLayer):
    """Realize one scientific track as an ordinary spherical curve."""
    layer_name = "solar_system_track"

    def __init__(self, request, *, realizer=None, label_ticks=False):
        if not isinstance(request, SolarSystemTrackRequest):
            raise TypeError("request must be a SolarSystemTrackRequest.")
        self.request = request
        self.realizer = SolarSystemTrackRealizer() if realizer is None else realizer
        self.last_result = None
        self.label_ticks = bool(label_ticks)

    def realize(self, context, observer, **geometry_options):
        if geometry_options:
            raise TypeError("SolarSystemTrackLayer accepts no geometry options.")
        self.last_result = self.realizer.curve(self.request, context=context, observer=observer)
        return self.last_result.geometry

    def spherical_geometry(self, observer):
        del observer
        raise RuntimeError("SolarSystemTrackLayer requires a LayerRealizationContext.")

def prepare_projected_track(
    spherical, projected, *, tick_length, include_start_tick=False, label_ticks=False
):
    """Return path and perpendicular projected tick components."""
    if not isinstance(projected, ProjectedCurves) or len(projected) != 1:
        raise TypeError("projected must contain exactly one track curve.")
    tick_length = float(tick_length)
    if not np.isfinite(tick_length) or tick_length <= 0.0:
        raise ValueError("tick_length must be positive and finite.")
    source = projected[0]
    indices = tuple(spherical.metadata.get("tick_sample_indices", ()))
    if not include_start_tick:
        indices = indices[1:]
    ticks, omitted = [], []
    for tick_number, index in enumerate(indices):
        index = int(index)
        tangent = _projected_tangent(source, index)
        if tangent is None:
            omitted.append(index)
            continue
        tx, ty = tangent
        half = 0.5 * tick_length
        nx, ny = -ty * half, tx * half
        x = (source.x[index] - nx, source.x[index] + nx)
        y = (source.y[index] - ny, source.y[index] + ny)
        if tick_number % 2:
            x = x[::-1]
            y = y[::-1]
        ticks.append(ProjectedCurve(
            x=np.asarray(x),
            y=np.asarray(y),
            name=_tick_label(spherical, index) if label_ticks else None,
        ))
    path = ProjectedCurve(
        x=source.x, y=source.y, closed=False, name=None
    )
    start_label = ProjectedCurve(
        x=np.asarray((source.x[0], source.x[0])),
        y=np.asarray((source.y[0], source.y[0])),
        closed=False,
        name=_start_label(spherical),
    )
    return ProjectedGrid(
        components={
            "path": ProjectedCurves(items=[path]),
            "ticks": ProjectedCurves(items=ticks),
            "labels": ProjectedCurves(items=[start_label]),
        },
        metadata={
            **dict(projected.metadata),
            "tick_sample_indices": indices,
            "omitted_tick_sample_indices": tuple(omitted),
        },
    )

def track_label_anchor(curve, ax):
    """Place track labels away from the path and inward at field edges."""
    finite = np.flatnonzero(curve.finite)
    if finite.size == 0:
        return None
    x = float(np.mean(curve.x[finite]))
    y = float(np.mean(curve.y[finite]))
    x_min, x_max = sorted(ax.get_xlim())
    y_min, y_max = sorted(ax.get_ylim())
    if finite.size == 2:
        first, last = (int(value) for value in finite)
        dx = float(curve.x[last] - curve.x[first])
        dy = float(curve.y[last] - curve.y[first])
        norm = float(np.hypot(dx, dy))
        if norm > 1.0e-12:
            padding = 0.012 * min(x_max - x_min, y_max - y_min)
            x = float(curve.x[last]) + padding * dx / norm
            y = float(curve.y[last]) + padding * dy / norm
            if not (x_min <= x <= x_max and y_min <= y <= y_max):
                dx, dy = -dx, -dy
                x = float(curve.x[first]) + padding * dx / norm
                y = float(curve.y[first]) + padding * dy / norm
            return CurveLabelPlacement(
                x=x,
                y=y,
                horizontal_alignment="left" if dx >= 0.0 else "right",
                vertical_alignment="bottom" if dy >= 0.0 else "top",
            )
    x_margin = 0.12 * abs(x_max - x_min)
    y_margin = 0.10 * abs(y_max - y_min)
    horizontal = "right" if x > x_max - x_margin else "left"
    vertical = "top" if y > y_max - y_margin else "bottom"
    return CurveLabelPlacement(
        x=x, y=y,
        horizontal_alignment=horizontal,
        vertical_alignment=vertical,
    )



class TrackLabelAnchor:
    """Render-local collision-aware placement for track date labels."""

    def __init__(self, *, fontsize):
        self.fontsize = float(fontsize)
        if not np.isfinite(self.fontsize) or self.fontsize <= 0.0:
            raise ValueError("fontsize must be positive and finite.")
        self._axes = None
        self._claimed = []

    def __call__(self, curve, ax):
        if ax is not self._axes:
            self._axes = ax
            self._claimed = []
        finite = np.flatnonzero(curve.finite)
        if finite.size == 0:
            return None
        points = ax.transData.transform(
            np.column_stack((curve.x[finite], curve.y[finite]))
        )
        if len(points) == 2:
            direction = points[1] - points[0]
            norm = float(np.hypot(*direction))
            if norm > 1.0e-9:
                return self._place_tick(curve, ax, points, direction / norm)
        return self._place_point(curve, ax, np.mean(points, axis=0))

    def _place_tick(self, curve, ax, points, preferred):
        candidates = []
        pixels_per_point = ax.figure.dpi / 72.0
        for direction, endpoint in (
            (preferred, points[1]),
            (-preferred, points[0]),
        ):
            tangent = np.asarray((-direction[1], direction[0]))
            for lane in (0, 1, -1, 2, -2, 3, -3):
                for distance_em in (0.55, 1.35, 2.25):
                    display = (
                        endpoint
                        + (
                            direction * distance_em
                            + tangent * lane * 1.35
                        )
                        * self.fontsize
                        * pixels_per_point
                    )
                    candidates.append((display, direction))
        return self._choose(curve, ax, candidates)

    def _place_point(self, curve, ax, center):
        directions = np.asarray((
            (1.0, 1.0), (-1.0, 1.0),
            (1.0, -1.0), (-1.0, -1.0),
            (1.0, 0.0), (-1.0, 0.0),
            (0.0, 1.0), (0.0, -1.0),
        ))
        directions /= np.maximum(
            np.hypot(directions[:, 0], directions[:, 1])[:, None],
            1.0e-12,
        )
        pixels_per_point = ax.figure.dpi / 72.0
        candidates = [
            (
                center
                + direction * distance_em * self.fontsize * pixels_per_point,
                direction,
            )
            for distance_em in (0.65, 1.5, 2.5)
            for direction in directions
        ]
        return self._choose(curve, ax, candidates)

    def _choose(self, curve, ax, candidates):
        evaluated = [
            self._candidate(curve, ax, display, direction)
            for display, direction in candidates
        ]
        available = [
            value for value in evaluated
            if value["inside"] and value["overlap"] == 0.0
        ]
        chosen = (
            available[0]
            if available
            else min(
                evaluated,
                key=lambda value: (
                    not value["inside"],
                    value["overlap"],
                ),
            )
        )
        self._claimed.append(chosen["box"])
        x, y = ax.transData.inverted().transform(chosen["display"])
        dx, dy = chosen["direction"]
        return CurveLabelPlacement(
            x=float(x),
            y=float(y),
            horizontal_alignment="left" if dx >= 0.0 else "right",
            vertical_alignment="bottom" if dy >= 0.0 else "top",
        )

    def _candidate(self, curve, ax, display, direction):
        pixels_per_point = ax.figure.dpi / 72.0
        width = (
            max(len(str(curve.name or "")), 1)
            * 0.58
            * self.fontsize
            * pixels_per_point
        )
        height = 1.15 * self.fontsize * pixels_per_point
        dx, dy = direction
        left = display[0] if dx >= 0.0 else display[0] - width
        bottom = display[1] if dy >= 0.0 else display[1] - height
        box = (left, bottom, left + width, bottom + height)
        axes_points = ax.transData.transform((
            (ax.get_xlim()[0], ax.get_ylim()[0]),
            (ax.get_xlim()[1], ax.get_ylim()[1]),
        ))
        x_min, x_max = sorted(axes_points[:, 0])
        y_min, y_max = sorted(axes_points[:, 1])
        inside = (
            box[0] >= x_min and box[2] <= x_max
            and box[1] >= y_min and box[3] <= y_max
        )
        overlap = sum(_box_overlap(box, claimed) for claimed in self._claimed)
        return {
            "display": display,
            "direction": direction,
            "box": box,
            "inside": inside,
            "overlap": overlap,
        }


def _box_overlap(left, right):
    width = max(0.0, min(left[2], right[2]) - max(left[0], right[0]))
    height = max(0.0, min(left[3], right[3]) - max(left[1], right[1]))
    return width * height

def start_label_anchor(curve, ax):
    """Compatibility name for the shared track label placement."""
    return track_label_anchor(curve, ax)

def _tick_label(spherical, index):
    instants = tuple(spherical.metadata.get("sample_instants", ()))
    return instants[index][:10] if index < len(instants) else None

def _start_label(spherical):
    instants = tuple(spherical.metadata.get("sample_instants", ()))
    date = instants[0][:10] if instants else ""
    display_name = str(spherical.names[0]) if spherical.names is not None else "Venus"
    glyph = {"Venus": "\N{FEMALE SIGN}"}.get(display_name, display_name)
    return f"{glyph} {date}".strip()

def _projected_tangent(curve, index):
    if index < 0 or index >= len(curve) or not curve.finite[index]:
        return None
    left = index - 1
    while left >= 0:
        if curve.finite[left] and np.hypot(
            curve.x[index] - curve.x[left], curve.y[index] - curve.y[left]
        ) > 1.0e-12:
            break
        left -= 1
    if left < 0:
        left = None
    right = index + 1
    while right < len(curve):
        if curve.finite[right] and np.hypot(
            curve.x[right] - curve.x[index], curve.y[right] - curve.y[index]
        ) > 1.0e-12:
            break
        right += 1
    if right >= len(curve):
        right = None
    if left is not None and right is not None:
        dx, dy = curve.x[right] - curve.x[left], curve.y[right] - curve.y[left]
    elif left is not None:
        dx, dy = curve.x[index] - curve.x[left], curve.y[index] - curve.y[left]
    elif right is not None:
        dx, dy = curve.x[right] - curve.x[index], curve.y[right] - curve.y[index]
    else:
        return None
    norm = float(np.hypot(dx, dy))
    if not np.isfinite(norm) or norm <= 1.0e-12:
        return None
    return float(dx) / norm, float(dy) / norm
