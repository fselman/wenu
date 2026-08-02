"""Chart-local preparation of automatic constellation label anchors."""

from __future__ import annotations

import numpy as np

from wenu.geometry.clipping import (
    clip_polygon_to_convex_boundary,
    polygon_centroid,
)
from wenu.geometry.projected import ProjectedCurve, ProjectedPoints
from wenu.rendering.preparation import project_geometry_for_viewport


_BOUNDARY_IDS = {"SERCAP": "SER1", "SERCAU": "SER2"}


def apply_visible_constellation_label_anchors(
    layer_options,
    *,
    sky,
    projection,
    viewport,
    boundary,
    inset=0.94,
    maximum_boundary_vertices=73,
):
    """Use visible IAU regions to prepare labels at a chart boundary."""
    labels = getattr(sky, "constellation_labels", None)
    regions = getattr(sky, "constellation_boundaries", None)
    if labels is None or regions is None:
        return layer_options

    resolved = {
        layer: dict(options)
        for layer, options in layer_options.items()
    }
    options = dict(resolved.get(labels, {}))
    previous = options.get("prepare")
    boundary_radius = _boundary_radius(boundary)
    safe_boundary = _simplified_inset_boundary(
        boundary,
        inset=inset,
        maximum_vertices=maximum_boundary_vertices,
    )

    def prepare(spherical, projected):
        prepared = (
            projected
            if previous is None
            else previous(spherical, projected)
        )
        if not isinstance(prepared, ProjectedPoints):
            raise TypeError(
                "constellation label preparation requires ProjectedPoints."
            )
        region_spherical = regions.spherical_geometry(sky.observer)
        region_projected = project_geometry_for_viewport(
            region_spherical,
            projection=projection,
            viewport=viewport,
        )
        visible = {}
        complete = set()
        for polygon in region_projected:
            clipped = clip_polygon_to_convex_boundary(
                polygon, safe_boundary
            )
            if clipped is None:
                continue
            identifier = str(polygon.name or "").upper()
            visible[identifier] = polygon_centroid(clipped)
            if np.all(
                np.hypot(polygon.x, polygon.y)
                <= boundary_radius * (1.0 + 1.0e-9)
            ):
                complete.add(identifier)

        x = np.asarray(prepared.x, dtype=float).copy()
        y = np.asarray(prepared.y, dtype=float).copy()
        names = prepared.labels
        if names is None:
            names = prepared.names
        if names is None:
            return prepared
        for index, name in enumerate(names):
            identifier = _BOUNDARY_IDS.get(
                str(name).upper(), str(name).upper()
            )
            anchor_inside = (
                np.isfinite(x[index])
                and np.isfinite(y[index])
                and np.hypot(x[index], y[index])
                <= boundary_radius * (1.0 + 1.0e-9)
            )
            if identifier in complete and anchor_inside:
                continue
            replacement = visible.get(identifier)
            if replacement is None:
                x[index] = np.nan
                y[index] = np.nan
            else:
                x[index], y[index] = replacement
        metadata = dict(prepared.metadata)
        metadata["visible_region_anchors"] = True
        metadata["visible_region_anchor_inset"] = float(inset)
        return ProjectedPoints(
            x=x,
            y=y,
            metadata=metadata,
            ids=prepared.ids,
            labels=prepared.labels,
            names=prepared.names,
        )

    options["prepare"] = prepare
    resolved[labels] = options
    return resolved


def _boundary_radius(boundary):
    finite = boundary.finite
    return float(
        np.nanmedian(np.hypot(boundary.x[finite], boundary.y[finite]))
    )


def _simplified_inset_boundary(
    boundary,
    *,
    inset,
    maximum_vertices,
):
    inset = float(inset)
    maximum_vertices = int(maximum_vertices)
    if not 0.0 < inset <= 1.0:
        raise ValueError("inset must be in the interval (0, 1].")
    if maximum_vertices < 9:
        raise ValueError("maximum_boundary_vertices must be at least 9.")
    finite = boundary.finite
    x = np.asarray(boundary.x[finite], dtype=float)
    y = np.asarray(boundary.y[finite], dtype=float)
    if len(x) < 3:
        raise ValueError("boundary needs at least three finite vertices.")
    if np.allclose((x[0], y[0]), (x[-1], y[-1])):
        x = x[:-1]
        y = y[:-1]
    if len(x) > maximum_vertices:
        indices = np.linspace(
            0,
            len(x) - 1,
            maximum_vertices,
            dtype=int,
        )
        x = x[indices]
        y = y[indices]
    return ProjectedCurve(
        x=inset * x,
        y=inset * y,
        closed=True,
        name="constellation_label_safe_boundary",
    )
