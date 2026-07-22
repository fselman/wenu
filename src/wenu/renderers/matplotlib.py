"""Matplotlib rendering primitives for projected Cartesian geometry."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon as MatplotlibPolygon

from wenu.projected import (
    ProjectedCurve,
    ProjectedPoint,
    ProjectedPolygon,
)


def render_point(
    ax: Axes,
    point: ProjectedPoint,
    **style,
) -> PathCollection:
    """
    Render a projected point on a Matplotlib axis.

    Parameters
    ----------
    ax
        Matplotlib axis on which the point is drawn.

    point
        Point in projected Cartesian coordinates.

    **style
        Keyword arguments forwarded to ``Axes.scatter``.

    Returns
    -------
    matplotlib.collections.PathCollection
        The Matplotlib artist created by ``Axes.scatter``.
    """
    return ax.scatter(
        [point.x],
        [point.y],
        **style,
    )


def render_points(
    ax: Axes,
    x,
    y,
    **style,
) -> PathCollection:
    """
    Render a collection of projected points on a Matplotlib axis.

    Parameters
    ----------
    ax
        Matplotlib axis on which the points are drawn.

    x, y
        One-dimensional projected Cartesian coordinate arrays.

    **style
        Keyword arguments forwarded to ``Axes.scatter``.

    Returns
    -------
    matplotlib.collections.PathCollection
        The Matplotlib scatter artist.
    """
    x = np.asarray(
        x,
        dtype=float,
    )
    y = np.asarray(
        y,
        dtype=float,
    )

    if x.ndim != 1 or y.ndim != 1:
        raise ValueError(
            "x and y must be one-dimensional arrays."
        )

    if x.shape != y.shape:
        raise ValueError(
            "x and y must have the same shape."
        )

    return ax.scatter(
        x,
        y,
        **style,
    )


def render_curve(
    ax: Axes,
    curve: ProjectedCurve,
    **style,
) -> Line2D:
    """
    Render a projected curve on a Matplotlib axis.

    Non-finite samples are passed directly to Matplotlib. Matplotlib uses
    them to separate disconnected visible segments.

    Parameters
    ----------
    ax
        Matplotlib axis on which the curve is drawn.

    curve
        Curve in projected Cartesian coordinates.

    **style
        Keyword arguments forwarded to ``Axes.plot``.

    Returns
    -------
    matplotlib.lines.Line2D
        The Matplotlib line artist.
    """
    x = curve.x
    y = curve.y

    if curve.closed and not (
        x[0] == x[-1]
        and y[0] == y[-1]
    ):
        x = np.concatenate(
            (x, x[:1])
        )
        y = np.concatenate(
            (y, y[:1])
        )

    line, = ax.plot(
        x,
        y,
        **style,
    )

    return line


def render_polygon(
    ax: Axes,
    polygon: ProjectedPolygon,
    **style,
) -> MatplotlibPolygon:
    """
    Render a projected polygon on a Matplotlib axis.

    Parameters
    ----------
    ax
        Matplotlib axis on which the polygon is drawn.

    polygon
        Polygon in projected Cartesian coordinates.

    **style
        Keyword arguments forwarded to
        ``matplotlib.patches.Polygon``.

    Returns
    -------
    matplotlib.patches.Polygon
        The polygon patch added to the axis.
    """
    vertices = np.column_stack(
        (
            polygon.x,
            polygon.y,
        )
    )

    patch = MatplotlibPolygon(
        vertices,
        closed=True,
        **style,
    )

    ax.add_patch(patch)

    return patch


