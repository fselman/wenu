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
    spherical, projected, *, tick_length, include_start_tick=False,
    label_ticks=False, label_anchor=None,
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
    for index in indices:
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
        ticks.append(ProjectedCurve(
            x=np.asarray(x),
            y=np.asarray(y),
            name=_tick_label(spherical, index) if label_ticks else None,
        ))
    if label_anchor is not None:
        label_anchor.set_geometry(source, ticks)
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

def _start_label_anchor(curve, ax):
    """Anchor the start label inward from the nearest field edge."""
    finite = np.flatnonzero(curve.finite)
    if finite.size == 0:
        return None
    x = float(np.mean(curve.x[finite]))
    y = float(np.mean(curve.y[finite]))
    x_min, x_max = sorted(ax.get_xlim())
    y_min, y_max = sorted(ax.get_ylim())
    x_margin = 0.12 * (x_max - x_min)
    y_margin = 0.10 * (y_max - y_min)
    return CurveLabelPlacement(
        x=x,
        y=y,
        horizontal_alignment=(
            "right" if x > x_max - x_margin else "left"
        ),
        vertical_alignment=(
            "top" if y > y_max - y_margin else "bottom"
        ),
    )

class TrackLabelAnchor:
    """Choose a coherent two-sided layout for ordered track labels."""

    def __init__(self, *, fontsize):
        self.fontsize = float(fontsize)
        if not np.isfinite(self.fontsize) or self.fontsize <= 0.0:
            raise ValueError("fontsize must be positive and finite.")
        self._track = None
        self._ticks = ()
        self._axes = None
        self._placements = {}
        self._claimed = []

    def set_geometry(self, track, ticks):
        if not isinstance(track, ProjectedCurve):
            raise TypeError("track must be a ProjectedCurve.")
        if not all(isinstance(tick, ProjectedCurve) for tick in ticks):
            raise TypeError("ticks must contain ProjectedCurve values.")
        self._track = track
        self._ticks = tuple(ticks)
        self._axes = None
        self._placements = {}
        self._claimed = []

    def __call__(self, curve, ax):
        if ax is not self._axes:
            self._build_layout(ax)
        placement = self._placements.get(curve.name)
        if placement is not None:
            return placement
        return _start_label_anchor(curve, ax)

    def _build_layout(self, ax):
        self._axes = ax
        layouts = tuple(self._layout(ax, side) for side in (0, 1))
        chosen = min(layouts, key=lambda value: value["score"])
        self._placements = chosen["placements"]
        self._claimed = chosen["boxes"]

    def _layout(self, ax, starting_side):
        current_side = starting_side
        claimed = []
        placements = {}
        curve_conflicts = 0
        label_conflicts = 0
        boundary_conflicts = 0
        switches = 0
        total_overlap = 0.0
        for tick in self._ticks:
            candidates = tuple(
                self._candidate(tick, ax, side, claimed)
                for side in (0, 1)
            )
            preferred = candidates[current_side]
            other_side = 1 - current_side
            other = candidates[other_side]
            if self._obstruction(other) < self._obstruction(preferred):
                selected = other
                current_side = other_side
                switches += 1
            else:
                selected = preferred
            claimed.append(selected["box"])
            placements[tick.name] = selected["placement"]
            curve_conflicts += int(selected["track_hits"] > 0)
            label_conflicts += int(selected["overlap"] > 0.0)
            boundary_conflicts += int(not selected["inside"])
            total_overlap += selected["overlap"]
        return {
            "placements": placements,
            "boxes": claimed,
            "score": (
                curve_conflicts,
                label_conflicts,
                boundary_conflicts,
                switches,
                total_overlap,
                starting_side,
            ),
        }

    @staticmethod
    def _obstruction(candidate):
        return (
            candidate["track_hits"] > 0,
            candidate["overlap"] > 0.0,
            not candidate["inside"],
            candidate["track_hits"],
            candidate["overlap"],
        )

    def _candidate(self, tick, ax, side, claimed):
        finite = np.flatnonzero(tick.finite)
        points = ax.transData.transform(
            np.column_stack((tick.x[finite], tick.y[finite]))
        )
        if len(points) != 2:
            raise ValueError("track ticks must contain two finite endpoints.")
        direction = points[1] - points[0]
        norm = float(np.hypot(*direction))
        if norm <= 1.0e-9:
            raise ValueError("track tick endpoints must be distinct.")
        direction /= norm
        if side == 0:
            endpoint = points[1]
        else:
            endpoint = points[0]
            direction = -direction
        pixels_per_point = ax.figure.dpi / 72.0
        display = (
            endpoint
            + direction * 0.55 * self.fontsize * pixels_per_point
        )
        width = (
            max(len(str(tick.name or "")), 1)
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
        overlap = sum(_box_overlap(box, previous) for previous in claimed)
        track_hits = self._track_hits(ax, box, np.mean(points, axis=0), norm)
        x, y = ax.transData.inverted().transform(display)
        return {
            "placement": CurveLabelPlacement(
                x=float(x),
                y=float(y),
                horizontal_alignment="left" if dx >= 0.0 else "right",
                vertical_alignment="bottom" if dy >= 0.0 else "top",
            ),
            "box": box,
            "inside": inside,
            "overlap": overlap,
            "track_hits": track_hits,
        }

    def _track_hits(self, ax, box, tick_center, tick_length):
        if self._track is None:
            return 0
        finite = self._track.finite
        track = ax.transData.transform(np.column_stack((
            self._track.x[finite],
            self._track.y[finite],
        )))
        local = np.hypot(
            track[:, 0] - tick_center[0],
            track[:, 1] - tick_center[1],
        ) <= 1.5 * tick_length
        pixels_per_point = ax.figure.dpi / 72.0
        margin = 0.20 * self.fontsize * pixels_per_point
        below_label = (
            (track[:, 0] >= box[0] - margin)
            & (track[:, 0] <= box[2] + margin)
            & (track[:, 1] >= box[1] - margin)
            & (track[:, 1] <= box[3] + margin)
            & ~local
        )
        return int(np.count_nonzero(below_label))



def _box_overlap(left, right):
    width = max(0.0, min(left[2], right[2]) - max(left[0], right[0]))
    height = max(0.0, min(left[3], right[3]) - max(left[1], right[1]))
    return width * height


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
