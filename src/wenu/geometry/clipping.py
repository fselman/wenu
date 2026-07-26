from __future__ import annotations

from collections.abc import Callable

import numpy as np

from wenu.geometry.projected import (
        ProjectedPoint,
        ProjectedCurve,
        ProjectedPolygon,
        )
from wenu.geometry.viewport import Viewport

def clip_point_to_viewport(
    point: ProjectedPoint,
    viewport: Viewport,
) -> ProjectedPoint | None:
    """
    Clip one projected point to a rectangular viewport.

    Parameters
    ----------
    point
        Point in projected Cartesian coordinates.

    viewport
        Rectangular clipping region.

    Returns
    -------
    ProjectedPoint or None
        The original point when it is finite and lies inside the
        viewport, otherwise ``None``.
    """
    if (
        not point.finite
        or not viewport.contains(point.x, point.y)
    ):
        return None

    return point

def clip_curve_to_viewport(
    curve: ProjectedCurve,
    viewport: Viewport,
) -> list[ProjectedCurve]:
    """
    Clip a projected curve to a rectangular viewport.

    Parameters
    ----------
    curve
        Sampled curve in projected Cartesian coordinates.

    viewport
        Rectangular clipping region.

    Returns
    -------
    list of ProjectedCurve
        Visible contiguous curve fragments. The list is empty when the
        curve does not intersect the viewport.

    Notes
    -----
    A clipped curve may produce several disconnected fragments.

    Closed input curves include the segment connecting the final sample
    back to the first sample. Returned fragments are open because
    viewport clipping generally breaks geometric closure.

    Non-finite samples act as breaks in the input curve.
    """
    if curve.closed:
        x = np.concatenate(
            [
                curve.x,
                curve.x[:1],
            ]
        )
        y = np.concatenate(
            [
                curve.y,
                curve.y[:1],
            ]
        )
    else:
        x = curve.x
        y = curve.y

    clipped_arrays = _clip_polyline_to_viewport(
        x=x,
        y=y,
        viewport=viewport,
    )

    return [
        ProjectedCurve(
            x=clipped_x,
            y=clipped_y,
            closed=False,
            name=curve.name,
        )
        for clipped_x, clipped_y in clipped_arrays
    ]


_Point = tuple[float, float]


def _clip_polygon_against_edge(
    vertices: list[_Point],
    *,
    inside: Callable[[float, float], bool],
    intersect: Callable[[_Point, _Point], _Point],
) -> list[_Point]:
    """
    Clip polygon vertices against one half-plane boundary.
    """
    if not vertices:
        return []

    output: list[_Point] = []
    previous = vertices[-1]
    previous_inside = inside(*previous)

    for current in vertices:
        current_inside = inside(*current)

        if current_inside:
            if not previous_inside:
                output.append(
                    intersect(
                        previous,
                        current,
                    )
                )

            output.append(current)

        elif previous_inside:
            output.append(
                intersect(
                    previous,
                    current,
                )
            )

        previous = current
        previous_inside = current_inside

    return output


def _intersect_vertical_edge(
    start: _Point,
    end: _Point,
    x_edge: float,
) -> _Point:
    """
    Intersect a segment with a vertical clipping boundary.
    """
    x0, y0 = start
    x1, y1 = end

    dx = x1 - x0

    if dx == 0.0:
        return (
            float(x_edge),
            float(y0),
        )

    t = (x_edge - x0) / dx

    return (
        float(x_edge),
        float(y0 + t * (y1 - y0)),
    )


def _intersect_horizontal_edge(
    start: _Point,
    end: _Point,
    y_edge: float,
) -> _Point:
    """
    Intersect a segment with a horizontal clipping boundary.
    """
    x0, y0 = start
    x1, y1 = end

    dy = y1 - y0

    if dy == 0.0:
        return (
            float(x0),
            float(y_edge),
        )

    t = (y_edge - y0) / dy

    return (
        float(x0 + t * (x1 - x0)),
        float(y_edge),
    )


def _remove_consecutive_duplicate_vertices(
    vertices: list[_Point],
) -> list[_Point]:
    """
    Remove consecutive duplicate polygon vertices.
    """
    if not vertices:
        return []

    cleaned = [vertices[0]]

    for vertex in vertices[1:]:
        if not np.allclose(
            vertex,
            cleaned[-1],
        ):
            cleaned.append(vertex)

    if (
        len(cleaned) > 1
        and np.allclose(
            cleaned[0],
            cleaned[-1],
        )
    ):
        cleaned.pop()

    return cleaned


def clip_polygon_to_viewport(
    polygon: ProjectedPolygon,
    viewport: Viewport,
) -> ProjectedPolygon | None:
    """
    Clip a projected polygon to a rectangular viewport.

    Parameters
    ----------
    polygon
        Polygon in projected Cartesian coordinates.

    viewport
        Rectangular clipping region.

    Returns
    -------
    ProjectedPolygon or None
        The clipped polygon, or ``None`` if there is no polygonal
        intersection with the viewport.

    Notes
    -----
    The polygon boundary is implicitly closed.

    This implementation clips one exterior ring. Polygon holes and
    multiple disconnected rings are not represented by ProjectedPolygon.
    """
    finite = polygon.finite

    if not np.all(finite):
        return None

    vertices = list(
        zip(
            polygon.x,
            polygon.y,
            strict=True,
        )
    )

    vertices = _clip_polygon_against_edge(
        vertices,
        inside=lambda x, y: x >= viewport.x_min,
        intersect=lambda start, end: _intersect_vertical_edge(
            start,
            end,
            viewport.x_min,
        ),
    )

    vertices = _clip_polygon_against_edge(
        vertices,
        inside=lambda x, y: x <= viewport.x_max,
        intersect=lambda start, end: _intersect_vertical_edge(
            start,
            end,
            viewport.x_max,
        ),
    )

    vertices = _clip_polygon_against_edge(
        vertices,
        inside=lambda x, y: y >= viewport.y_min,
        intersect=lambda start, end: _intersect_horizontal_edge(
            start,
            end,
            viewport.y_min,
        ),
    )

    vertices = _clip_polygon_against_edge(
        vertices,
        inside=lambda x, y: y <= viewport.y_max,
        intersect=lambda start, end: _intersect_horizontal_edge(
            start,
            end,
            viewport.y_max,
        ),
    )

    vertices = _remove_consecutive_duplicate_vertices(
        vertices,
    )

    if len(vertices) < 3:
        return None

    x, y = zip(
        *vertices,
        strict=True,
    )

    return ProjectedPolygon(
        x=np.asarray(x, dtype=float),
        y=np.asarray(y, dtype=float),
        name=polygon.name,
    )


def clip_line_segment_to_viewport(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    viewport: Viewport,
) -> tuple[float, float, float, float] | None:
    """
    Clip one Cartesian line segment to a rectangular viewport.

    The implementation uses the Liang-Barsky parametric clipping
    algorithm.

    Returns
    -------
    tuple or None
        ``(clipped_x0, clipped_y0, clipped_x1, clipped_y1)``,
        or ``None`` when the segment does not intersect the viewport.
    """
    x0 = float(x0)
    y0 = float(y0)
    x1 = float(x1)
    y1 = float(y1)

    if not np.all(
        np.isfinite([x0, y0, x1, y1])
    ):
        return None

    dx = x1 - x0
    dy = y1 - y0

    p = np.array(
        [-dx, dx, -dy, dy],
        dtype=float,
    )

    q = np.array(
        [
            x0 - viewport.x_min,
            viewport.x_max - x0,
            y0 - viewport.y_min,
            viewport.y_max - y0,
        ],
        dtype=float,
    )

    t_enter = 0.0
    t_leave = 1.0

    for pi, qi in zip(p, q):
        if pi == 0.0:
            if qi < 0.0:
                return None
            continue

        ratio = qi / pi

        if pi < 0.0:
            t_enter = max(t_enter, ratio)
        else:
            t_leave = min(t_leave, ratio)

        if t_enter > t_leave:
            return None

    return (
        x0 + t_enter * dx,
        y0 + t_enter * dy,
        x0 + t_leave * dx,
        y0 + t_leave * dy,
    )


def _clip_polyline_to_viewport(
    x,
    y,
    viewport: Viewport,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """
    Low-level helper that clips sampled Cartesian polyline arrays to a
    rectangular viewport.

    This function operates directly on NumPy coordinate arrays and is
    intended for internal use by the public projected-geometry clipping
    functions.

    Parameters
    ----------
    x, y
        One-dimensional Cartesian coordinate arrays with equal shape.

    viewport
        Rectangular clipping region.

    Returns
    -------
    list of tuple
        Each tuple contains the x and y arrays for one visible,
        contiguous clipped polyline.

    Notes
    -----
    This clips line segments rather than merely selecting points inside
    the viewport. Consequently, a segment crossing the viewport remains
    visible even when both of its original endpoints lie outside it.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if x.ndim != 1 or y.ndim != 1:
        raise ValueError(
            "x and y must be one-dimensional arrays."
        )

    if x.shape != y.shape:
        raise ValueError(
            "x and y must have the same shape."
        )

    if x.size < 2:
        return []

    polylines: list[
        tuple[np.ndarray, np.ndarray]
    ] = []

    current_x: list[float] = []
    current_y: list[float] = []

    for index in range(x.size - 1):
        clipped = clip_line_segment_to_viewport(
            x[index],
            y[index],
            x[index + 1],
            y[index + 1],
            viewport,
        )

        if clipped is None:
            if len(current_x) >= 2:
                polylines.append(
                    (
                        np.asarray(current_x),
                        np.asarray(current_y),
                    )
                )

            current_x = []
            current_y = []
            continue

        clipped_x0, clipped_y0, clipped_x1, clipped_y1 = clipped

        if not current_x:
            current_x = [
                clipped_x0,
                clipped_x1,
            ]
            current_y = [
                clipped_y0,
                clipped_y1,
            ]
            continue

        previous_x = current_x[-1]
        previous_y = current_y[-1]

        connected = np.isclose(
            previous_x,
            clipped_x0,
        ) and np.isclose(
            previous_y,
            clipped_y0,
        )

        if connected:
            if not (
                np.isclose(previous_x, clipped_x1)
                and np.isclose(previous_y, clipped_y1)
            ):
                current_x.append(clipped_x1)
                current_y.append(clipped_y1)
        else:
            if len(current_x) >= 2:
                polylines.append(
                    (
                        np.asarray(current_x),
                        np.asarray(current_y),
                    )
                )

            current_x = [
                clipped_x0,
                clipped_x1,
            ]
            current_y = [
                clipped_y0,
                clipped_y1,
            ]

    if len(current_x) >= 2:
        polylines.append(
            (
                np.asarray(current_x),
                np.asarray(current_y),
            )
        )

    return polylines


