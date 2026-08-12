"""Projection preparation for observer-horizon mask openings."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.geometry.spherical import SphericalPolygons
from wenu.geometry.viewport import Viewport
from wenu.rendering.preparation import project_geometry_for_viewport
from wenu.sky.horizon import HorizonReference


HORIZON_VISIBILITIES = frozenset({"above", "crossing", "below"})


@dataclass(frozen=True)
class PreparedHorizonMask:
    """Native openings and their projection for one chart field."""

    visibility: str
    spherical: SphericalPolygons
    projected: ProjectedPolygons

    def __post_init__(self):
        if self.visibility not in HORIZON_VISIBILITIES:
            raise ValueError("Unsupported horizon-mask visibility.")
        if not isinstance(self.spherical, SphericalPolygons):
            raise TypeError("spherical must be SphericalPolygons.")
        if not isinstance(self.projected, ProjectedPolygons):
            raise TypeError("projected must be ProjectedPolygons.")


def prepare_horizon_mask_opening(
    *,
    projection,
    viewport,
    observer,
    boundary=None,
    transform_spherical=None,
    complete_sphere=False,
    samples=721,
    radial_step_deg=5.0,
):
    """Prepare altitude-nonnegative openings through one projection path."""
    if not isinstance(viewport, Viewport):
        raise TypeError("viewport must be a Viewport.")
    if boundary is not None and not isinstance(boundary, ProjectedCurve):
        raise TypeError("boundary must be a ProjectedCurve or None.")
    if transform_spherical is not None and not callable(transform_spherical):
        raise TypeError("transform_spherical must be callable or None.")
    source = HorizonReference(samples=samples).visible_hemisphere_geometry(
        observer,
        radial_step_deg=radial_step_deg,
    )

    if complete_sphere:
        prepared = (
            source
            if transform_spherical is None
            else transform_spherical(source)
        )
        projected = projection.project_geometry(prepared)
        projected.metadata["horizon_visibility"] = "crossing"
        projected.metadata["mask_opening"] = "above_horizon"
        return PreparedHorizonMask("crossing", source, projected)

    visibility = _stereographic_field_visibility(
        projection,
        viewport,
        boundary=boundary,
        samples=samples,
    )
    if visibility == "above":
        projected = ProjectedPolygons(
            items=[_viewport_polygon(viewport)],
            metadata={
                "horizon_visibility": visibility,
                "mask_opening": "above_horizon",
            },
        )
    elif visibility == "below":
        projected = ProjectedPolygons(
            items=[],
            metadata={
                "horizon_visibility": visibility,
                "mask_opening": "above_horizon",
            },
        )
    else:
        projected = project_geometry_for_viewport(
            source,
            projection=projection,
            viewport=viewport,
        )
        projected.metadata["horizon_visibility"] = visibility
        projected.metadata["mask_opening"] = "above_horizon"
    return PreparedHorizonMask(visibility, source, projected)


def _stereographic_field_visibility(
    projection,
    viewport,
    *,
    boundary,
    samples,
):
    inverse = getattr(projection, "unproject_spherical", None)
    if not callable(inverse):
        raise TypeError(
            "regional horizon masking requires inverse projection."
        )
    x, y = _field_samples(viewport, boundary=boundary, samples=samples)
    x, y = _include_altitude_extrema(
        projection,
        viewport,
        boundary,
        x,
        y,
    )
    latitude = np.asarray(inverse(x, y).lat_deg, dtype=float)
    finite = np.isfinite(latitude)
    if not np.any(finite):
        raise ValueError("The chart field has no finite spherical samples.")
    minimum = float(np.min(latitude[finite]))
    maximum = float(np.max(latitude[finite]))
    tolerance = 1.0e-10
    if minimum >= -tolerance:
        return "above"
    if maximum <= tolerance:
        return "below"
    return "crossing"


def _field_samples(viewport, *, boundary, samples):
    if boundary is not None:
        finite = boundary.finite
        x = np.asarray(boundary.x[finite], dtype=float)
        y = np.asarray(boundary.y[finite], dtype=float)
    else:
        count = max(4, int(np.ceil(int(samples) / 4.0)))
        horizontal = np.linspace(viewport.x_min, viewport.x_max, count)
        vertical = np.linspace(viewport.y_min, viewport.y_max, count)
        x = np.concatenate((
            horizontal,
            np.full(count, viewport.x_max),
            horizontal[::-1],
            np.full(count, viewport.x_min),
        ))
        y = np.concatenate((
            np.full(count, viewport.y_min),
            vertical,
            np.full(count, viewport.y_max),
            vertical[::-1],
        ))
    return (
        np.concatenate((x, [0.5 * (viewport.x_min + viewport.x_max)])),
        np.concatenate((y, [0.5 * (viewport.y_min + viewport.y_max)])),
    )


def _include_altitude_extrema(projection, viewport, boundary, x, y):
    candidates_x, candidates_y = projection.project_spherical(
        np.asarray((0.0, 0.0)),
        np.asarray((90.0, -90.0)),
    )
    included_x = list(np.asarray(x, dtype=float))
    included_y = list(np.asarray(y, dtype=float))
    for candidate_x, candidate_y in zip(candidates_x, candidates_y):
        if not viewport.contains(candidate_x, candidate_y):
            continue
        if boundary is not None and not _inside_convex_boundary(
            candidate_x, candidate_y, boundary
        ):
            continue
        included_x.append(float(candidate_x))
        included_y.append(float(candidate_y))
    return np.asarray(included_x), np.asarray(included_y)


def _inside_convex_boundary(x, y, boundary):
    finite = boundary.finite
    vertices = np.column_stack((boundary.x[finite], boundary.y[finite]))
    if len(vertices) < 3:
        return False
    edges = np.roll(vertices, -1, axis=0) - vertices
    relative = np.asarray((x, y), dtype=float) - vertices
    cross = edges[:, 0] * relative[:, 1] - edges[:, 1] * relative[:, 0]
    tolerance = 1.0e-10
    return bool(
        np.all(cross >= -tolerance) or np.all(cross <= tolerance)
    )


def _viewport_polygon(viewport):
    return ProjectedPolygon(
        x=np.asarray((
            viewport.x_min,
            viewport.x_max,
            viewport.x_max,
            viewport.x_min,
        )),
        y=np.asarray((
            viewport.y_min,
            viewport.y_min,
            viewport.y_max,
            viewport.y_max,
        )),
        name="above_horizon",
    )
