"""Presentation helpers for constellation-region masks."""

from __future__ import annotations

import numpy as np

from wenu.chart_document import EditPolicy, SemanticArtistIdentity
from wenu.charts.horizon_mask import prepare_horizon_mask_opening
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
    projected = prepare_constellation_mask_opening(
        sky=sky,
        projection=projection,
        observer=observer,
        constellations=constellations,
        visible_minimum_latitude_deg=visible_minimum_latitude_deg,
        transform_spherical=transform_spherical,
    )
    patch = renderer.draw_outside_mask(
        projected,
        viewport=viewport,
        style=style,
    )
    return _assign_outside_mask_identity(
        renderer,
        patch,
        constellations=True,
        horizon_mask=False,
    )


def prepare_constellation_mask_opening(
    *,
    sky,
    projection,
    observer=None,
    constellations,
    visible_minimum_latitude_deg=None,
    transform_spherical=None,
):
    """Project selected official regions as one mask-opening group."""
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
    return projected


def compose_projected_mask_openings(*groups):
    """Combine independent openings for one nonzero-winding mask path."""
    resolved = tuple(group for group in groups if group is not None)
    if not all(isinstance(group, ProjectedPolygons) for group in resolved):
        raise TypeError("mask openings must be ProjectedPolygons.")
    items = [polygon for group in resolved for polygon in group]
    return ProjectedPolygons(
        items=items,
        metadata={
            "mask_opening_group_sizes": tuple(len(group) for group in resolved),
            "mask_opening_group_count": len(resolved),
        },
    )


def draw_composed_outside_mask(
    *,
    sky,
    projection,
    renderer,
    viewport,
    observer,
    style,
    constellations=None,
    horizon_mask=False,
    planisphere=False,
    boundary=None,
    transform_spherical=None,
    complete_sphere=False,
    visible_minimum_latitude_deg=None,
):
    """Paint all selected outside restrictions exactly once."""
    resolved_observer = (
        getattr(sky, "observer", None) if observer is None else observer
    )
    if resolved_observer is None:
        raise TypeError("outside masking requires an observer.")
    groups = []
    if constellations is not None:
        groups.append(prepare_constellation_mask_opening(
            sky=sky,
            projection=projection,
            observer=resolved_observer,
            constellations=constellations,
            visible_minimum_latitude_deg=visible_minimum_latitude_deg,
            transform_spherical=transform_spherical,
        ))
    if horizon_mask and not planisphere:
        groups.append(prepare_horizon_mask_opening(
            projection=projection,
            viewport=viewport,
            observer=resolved_observer,
            boundary=boundary,
            transform_spherical=transform_spherical,
            complete_sphere=complete_sphere,
        ).projected)
    if not groups:
        return None
    patch = renderer.draw_outside_mask(
        compose_projected_mask_openings(*groups),
        viewport=viewport,
        style=style,
    )
    return _assign_outside_mask_identity(
        renderer,
        patch,
        constellations=constellations is not None,
        horizon_mask=horizon_mask and not planisphere,
    )


def _assign_outside_mask_identity(
    renderer,
    patch,
    *,
    constellations,
    horizon_mask,
):
    """Attach chart-owned meaning without exposing SVG serialization."""
    if constellations and horizon_mask:
        token = "combined_outside_mask"
        display_name = "Combined outside-region mask"
    elif constellations:
        token = "outside_constellation_group_mask"
        display_name = "Outside constellation-group mask"
    else:
        token = "below_horizon_mask"
        display_name = "Below-horizon mask"
    assign = getattr(renderer, "assign_semantic_identity", None)
    if callable(assign):
        assign(
            (patch,),
            SemanticArtistIdentity(
                name=token,
                svg_id=(
                    "outside-mask"
                    if token != "below_horizon_mask"
                    else "below-horizon-mask"
                ),
                edit_policy=EditPolicy.STYLE,
                semantic_path=("chart", "masks_and_boundary", token),
                display_name=display_name,
                presentation_order=80,
                style_role="outside_mask",
            ),
        )
    return patch


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
        coordinate_spec=spherical.coordinate_spec,
        ids=selected(spherical.ids),
        labels=selected(spherical.labels),
        names=selected(spherical.names),
        metadata=dict(spherical.metadata),
    )