"""Wenu appearance preparation and compatible shared-mathematics aliases."""

from __future__ import annotations

import numpy as np

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPolygon,
    ProjectedPolygons,
    ProjectedPoints,
)
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


from wenu_kernel.geometry.domain import (
    clip_to_latitude,
    clip_polygons_to_latitude,
    clip_polygons_to_projection_cap,
    project_geometry_for_viewport,
    projection_cap_for_viewport,
    project_polygons_to_projection_cap,
)


def magnitude_sizes(
    magnitudes,
    *,
    scale=1.5,
    reference_magnitude=5.0,
    exponent=0.35,
    minimum=1.0,
    maximum=None,
):
    """Convert magnitudes to Matplotlib scatter areas."""
    values = scale * 10.0 ** (
        exponent
        * (reference_magnitude - np.asarray(magnitudes, dtype=float))
    )
    values = np.maximum(values, minimum)
    return values if maximum is None else np.minimum(values, maximum)


def configured_magnitude_sizes(
    magnitudes,
    sizing,
    *,
    limiting_magnitude=None,
):
    """Apply an immutable stellar sizing configuration."""
    if sizing.algorithm != "legacy":
        difference = np.maximum(0.0, sizing.size_reference_magnitude
                                - np.asarray(magnitudes, dtype=float))
        growth = (difference**2 if sizing.algorithm == "quadratic" else
                  difference if sizing.algorithm == "linear" else np.arcsinh(difference / sizing.b_mag))
        diameter = sizing.dmin_mm + sizing.a_mm * growth
        if not np.isfinite(diameter).all() or not np.isfinite((diameter * 72 / 25.4)**2).all():
            raise ValueError("Stellar diameter parameters overflow the finite sizing range.")
        return (diameter * 72 / 25.4)**2
    reference = float(sizing.reference_magnitude)
    if sizing.reference == "limiting_magnitude":
        if limiting_magnitude is None:
            raise ValueError(
                "limiting_magnitude is required by the sizing configuration."
            )
        reference = float(limiting_magnitude)
    return magnitude_sizes(
        magnitudes,
        scale=sizing.scale,
        reference_magnitude=reference,
        exponent=sizing.exponent,
        minimum=sizing.minimum_area,
        maximum=sizing.maximum_area,
    )


def cull_points_to_viewport(
    projected,
    viewport,
    *,
    margin_fraction=0.02,
):
    """Mark points well outside a projected viewport as non-renderable.

    The small margin preserves marker fragments at the axes edge.  Point
    arrays and metadata retain their original length so renderer masks and
    per-object style arrays remain aligned.
    """
    from wenu.geometry.viewport import Viewport

    if not isinstance(projected, ProjectedPoints):
        raise TypeError("projected must be ProjectedPoints.")
    if not isinstance(viewport, Viewport):
        raise TypeError("viewport must be a Viewport.")
    margin_fraction = float(margin_fraction)
    if (
        not np.isfinite(margin_fraction)
        or margin_fraction < 0.0
    ):
        raise ValueError(
            "margin_fraction must be finite and non-negative."
        )
    margin_x = margin_fraction * viewport.width
    margin_y = margin_fraction * viewport.height
    x = np.asarray(projected.x, dtype=float).copy()
    y = np.asarray(projected.y, dtype=float).copy()
    retained = (
        np.isfinite(x)
        & np.isfinite(y)
        & (x >= viewport.x_min - margin_x)
        & (x <= viewport.x_max + margin_x)
        & (y >= viewport.y_min - margin_y)
        & (y <= viewport.y_max + margin_y)
    )
    x[~retained] = np.nan
    y[~retained] = np.nan
    return ProjectedPoints(
        x=x,
        y=y,
        ids=projected.ids,
        labels=projected.labels,
        names=projected.names,
        metadata=dict(projected.metadata),
    )


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


def diameter_marker_areas(diameters, minimum_area, points_per_unit):
    """Map supplied diameters to scatter areas, bounded by the current symbol.

    Missing, masked, nonfinite and nonpositive diameters keep the minimum.
    Circle markers have unit normalized width: sqrt(s) is diameter in points.
    """
    if isinstance(points_per_unit, bool) or not np.isfinite(points_per_unit) or points_per_unit <= 0:
        raise ValueError("points_per_unit must be finite and positive.")
    diameters = np.ma.asarray(diameters, dtype=float).filled(np.nan)
    minimum = np.broadcast_to(np.asarray(minimum_area, dtype=float), diameters.shape)
    if np.any(~np.isfinite(minimum)) or np.any(minimum < 0):
        raise ValueError("Minimum marker areas must be finite and nonnegative.")
    valid = np.isfinite(diameters) & (diameters > 0)
    sizes = np.where(valid, diameters, 0) * points_per_unit
    with np.errstate(over="ignore"):
        areas = sizes ** 2
    if np.any(~np.isfinite(areas)):
        raise ValueError("Angular marker areas overflow the finite range.")
    return np.maximum(minimum, areas)
