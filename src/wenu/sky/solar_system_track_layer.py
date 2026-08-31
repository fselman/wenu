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
