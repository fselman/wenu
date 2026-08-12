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
    observer=None,
    inset=0.94,
    maximum_boundary_vertices=73,
    transform_spherical=None,
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
        resolved_observer = getattr(sky, "observer", None) if observer is None else observer
        if resolved_observer is None:
            raise TypeError("constellation label placement requires an observer.")
        region_spherical = regions.spherical_geometry(resolved_observer)
        if transform_spherical is not None:
            region_spherical = transform_spherical(region_spherical)
        region_projected = project_geometry_for_viewport(
            region_spherical,
            projection=projection,
            viewport=viewport,
        )
        visible = {}
        visible_area = {}
        complete = set()
        for polygon in region_projected:
            clipped = clip_polygon_to_convex_boundary(
                polygon, safe_boundary
            )
            if clipped is None:
                continue
            identifier = str(polygon.name or "").upper()
            area = _polygon_area(clipped)
            if area > visible_area.get(identifier, -1.0):
                visible[identifier] = polygon_centroid(clipped)
                visible_area[identifier] = area
            if _points_inside_convex_boundary(
                polygon.x, polygon.y, boundary
            ).all():
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
            anchor_inside = bool(_points_inside_convex_boundary(
                [x[index]], [y[index]], boundary
            )[0])
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


def _polygon_area(polygon):
    return float(0.5 * abs(np.sum(
        polygon.x * np.roll(polygon.y, -1)
        - np.roll(polygon.x, -1) * polygon.y
    )))


def _points_inside_convex_boundary(x, y, boundary):
    """Return finite points inside a closed convex boundary."""
    finite = boundary.finite
    vertices = np.column_stack((boundary.x[finite], boundary.y[finite]))
    if len(vertices) < 3:
        raise ValueError("boundary needs at least three finite vertices.")
    if np.allclose(vertices[0], vertices[-1]):
        vertices = vertices[:-1]
    edges = np.roll(vertices, -1, axis=0) - vertices
    area = np.sum(
        vertices[:, 0] * np.roll(vertices[:, 1], -1)
        - np.roll(vertices[:, 0], -1) * vertices[:, 1]
    )
    orientation = 1.0 if area > 0.0 else -1.0
    points = np.column_stack((
        np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    ))
    valid = np.all(np.isfinite(points), axis=1)
    inside = valid.copy()
    for start, edge in zip(vertices, edges, strict=True):
        relative = points - start
        cross = edge[0] * relative[:, 1] - edge[1] * relative[:, 0]
        inside &= orientation * cross >= -1.0e-9
    return inside


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
