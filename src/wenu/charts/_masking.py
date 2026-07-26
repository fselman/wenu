"""Presentation helpers for constellation-region masks."""

from __future__ import annotations

from wenu.geometry.projected import ProjectedPolygons


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
    constellations,
    style,
):
    """Draw a presentation mask outside selected official boundaries."""
    boundaries = sky.constellation_boundaries
    if boundaries is None:
        raise RuntimeError(
            "Add constellation boundaries before requesting an "
            "outside-constellation mask."
        )
    spherical = boundaries.spherical_geometry(sky.observer)
    projected = projection.project_geometry(spherical)
    if not isinstance(projected, ProjectedPolygons):
        raise TypeError(
            "Constellation boundaries must project to ProjectedPolygons."
        )
    selected = _expanded_names(constellations)
    polygons = ProjectedPolygons(
        items=[
            polygon
            for polygon in projected
            if str(polygon.name).upper() in selected
        ],
        metadata=dict(projected.metadata),
    )
    if not polygons.items:
        raise ValueError(
            "No projected boundaries were found for: "
            + ", ".join(sorted(selected))
        )
    return renderer.draw_outside_mask(
        polygons,
        viewport=viewport,
        style=style,
    )
