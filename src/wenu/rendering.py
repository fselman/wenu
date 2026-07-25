"""Generic preparation between projection and rendering."""

from __future__ import annotations

import numpy as np

from wenu.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPolygons,
    ProjectedPoints,
)
from wenu.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


def magnitude_sizes(
    magnitudes,
    *,
    scale=1.5,
    reference_magnitude=5.0,
    exponent=0.35,
    minimum=1.0,
):
    """Convert magnitudes to Matplotlib scatter areas."""
    values = scale * 10.0 ** (
        exponent
        * (reference_magnitude - np.asarray(magnitudes, dtype=float))
    )
    return np.maximum(values, minimum)


def point_styles(metadata, *, default_zorder=None):
    """Return renderer styles encoded by a spherical point collection."""
    count = len(metadata.get("style", ()))
    styles = []
    for index in range(count):
        style = dict(metadata["style"][index])
        style.pop("label_offset", None)
        style.pop("fontsize", None)
        style.setdefault("marker", metadata["marker"][index])
        style.setdefault("s", metadata["size"][index])
        style.setdefault("color", metadata["color"][index])
        zorder = metadata["zorder"][index]
        if zorder is None:
            zorder = default_zorder
        if zorder is not None:
            style.setdefault("zorder", zorder)
        styles.append(style)
    return styles


def radial_label_offset(distance):
    """Return a projection-generic radial label-offset callback."""
    distance = float(distance)

    def offset(x, y):
        radius = np.hypot(x, y)
        if radius <= 1.0e-12:
            return 0.0, 0.0
        return distance * x / radius, distance * y / radius

    return offset


def clip_to_latitude(spherical, projected, *, minimum=0.0):
    """Clip corresponding projected geometry by spherical latitude."""
    minimum = float(minimum)
    if isinstance(spherical, SphericalPoints):
        return _clip_points(spherical, projected, minimum)
    if isinstance(spherical, SphericalCurves):
        return _clip_curves(spherical, projected, minimum)
    if isinstance(spherical, SphericalGrid):
        return ProjectedGrid(
            components={
                name: _clip_curves(
                    curves,
                    projected.components[name],
                    minimum,
                )
                for name, curves in spherical.components.items()
            },
            metadata=dict(projected.metadata),
        )
    if isinstance(spherical, SphericalPolygons):
        return _clip_polygon_boundaries(
            spherical,
            projected,
            minimum,
        )
    raise TypeError(
        "Latitude clipping does not support "
        f"{type(spherical).__name__}."
    )


def _clip_points(spherical, projected, minimum):
    visible = (
        np.isfinite(spherical.lat_deg)
        & (spherical.lat_deg >= minimum)
    )
    x = np.asarray(projected.x, dtype=float).copy()
    y = np.asarray(projected.y, dtype=float).copy()
    x[~visible] = np.nan
    y[~visible] = np.nan
    return ProjectedPoints(
        x=x,
        y=y,
        ids=projected.ids,
        labels=projected.labels,
        names=projected.names,
        metadata=dict(projected.metadata),
    )


def _clip_curves(spherical, projected, minimum):
    items = []
    source_indices = []
    for source_index, (latitude, curve, closed) in enumerate(
        zip(spherical.lat_deg, projected, spherical.closed)
    ):
        for x, y in _visible_segments(
            curve.x,
            curve.y,
            latitude,
            closed=bool(closed),
            minimum=minimum,
        ):
            items.append(
                ProjectedCurve(
                    x=x,
                    y=y,
                    closed=False,
                    name=curve.name,
                )
            )
            source_indices.append(source_index)

    metadata = dict(projected.metadata)
    styles = metadata.get("styles")
    if styles is not None:
        metadata["styles"] = tuple(
            styles[index] for index in source_indices
        )
    return ProjectedCurves(items=items, metadata=metadata)


def _clip_polygon_boundaries(spherical, projected, minimum):
    if not isinstance(projected, ProjectedPolygons):
        raise TypeError(
            "SphericalPolygons require ProjectedPolygons."
        )
    items = []
    for latitude, polygon in zip(spherical.lat_deg, projected):
        for x, y in _visible_segments(
            polygon.x,
            polygon.y,
            latitude,
            closed=True,
            minimum=minimum,
        ):
            items.append(
                ProjectedCurve(
                    x=x,
                    y=y,
                    closed=False,
                    name=polygon.name,
                )
            )
    return ProjectedCurves(
        items=items,
        metadata=dict(projected.metadata),
    )


def _visible_segments(x, y, latitude, *, closed, minimum):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    latitude = np.asarray(latitude, dtype=float)
    visible = (
        np.isfinite(x)
        & np.isfinite(y)
        & np.isfinite(latitude)
        & (latitude >= minimum)
    )
    if not np.any(visible):
        return []
    if closed:
        if np.all(visible):
            return [(np.append(x, x[0]), np.append(y, y[0]))]
        first_hidden = int(np.flatnonzero(~visible)[0])
        order = (
            np.arange(len(x), dtype=int) + first_hidden + 1
        ) % len(x)
        x = x[order]
        y = y[order]
        visible = visible[order]

    segments = []
    start = None
    for index, is_visible in enumerate(visible):
        if is_visible and start is None:
            start = index
        if not is_visible and start is not None:
            if index - start >= 2:
                segments.append((x[start:index], y[start:index]))
            start = None
    if start is not None and len(x) - start >= 2:
        segments.append((x[start:], y[start:]))
    return segments
