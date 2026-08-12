"""Presentation helpers for constellation-region masks."""

from __future__ import annotations

import numpy as np

from wenu.geometry.projected import ProjectedPolygons
from wenu.geometry.spherical import SphericalPolygons


def _expanded_names(names):
    expanded = set()
    for name in names:
        key = str(name).strip().upper()
        if key == "SER":
            expanded.update(("SER1", "SER2"))
        elif key == "SERCAP":
            expanded.add("SER1")
        elif key == "SERCAU":
            expanded.add("SER2")
        else:
            expanded.add(key)
    return expanded


def draw_constellation_outside_mask(
    *,
    sky,
    projection,
    renderer,
    viewport,
    observer=None,
    constellations,
    style,
    visible_minimum_latitude_deg=None,
    transform_spherical=None,
):
    """Draw a presentation mask outside selected official boundaries.

    When a visible minimum latitude is supplied, wholly invisible regions
    are discarded before projection. Partly visible polygons remain complete
    so the renderer's final chart-boundary clip produces the exact visible
    opening.
    """
    boundaries = sky.constellation_boundaries
    if boundaries is None:
        raise RuntimeError(
            "Add constellation boundaries before requesting an "
            "outside-constellation mask."
        )
    resolved_observer = getattr(sky, "observer", None) if observer is None else observer
    if resolved_observer is None:
        raise TypeError("outside masking requires an observer.")
    selected = _expanded_names(constellations)
    spherical = boundaries.spherical_geometry(
        resolved_observer,
        selected=selected,
    )
    if visible_minimum_latitude_deg is not None:
        spherical = _visible_polygons(
            spherical,
            minimum=float(visible_minimum_latitude_deg),
        )
    if transform_spherical is not None:
        spherical = transform_spherical(spherical)
    projected = projection.project_geometry(spherical)
    if not isinstance(projected, ProjectedPolygons):
        raise TypeError(
            "Constellation boundaries must project to ProjectedPolygons."
        )
    return renderer.draw_outside_mask(
        projected,
        viewport=viewport,
        style=style,
    )


def _visible_polygons(spherical, *, minimum):
    """Return polygons with at least one sampled visible vertex."""
    if not isinstance(spherical, SphericalPolygons):
        raise TypeError(
            "Constellation boundaries must be SphericalPolygons."
        )
    minimum = float(minimum)
    if not np.isfinite(minimum):
        raise ValueError("minimum must be finite.")
    indices = [
        index
        for index, latitude in enumerate(spherical.lat_deg)
        if np.any(
            np.isfinite(latitude)
            & (np.asarray(latitude, dtype=float) >= minimum)
        )
    ]

    def selected(values):
        if values is None:
            return None
        return np.asarray(values, dtype=object)[indices]

    return SphericalPolygons(
        lon_deg=tuple(spherical.lon_deg[index] for index in indices),
        lat_deg=tuple(spherical.lat_deg[index] for index in indices),
        ids=selected(spherical.ids),
        labels=selected(spherical.labels),
        names=selected(spherical.names),
        metadata=dict(spherical.metadata),
    )
