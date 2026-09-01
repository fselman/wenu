"""Projected display magnification for resolved Solar-System disks."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)


def _scaled_coordinates(x, y, centre_x, centre_y, factor):
    return (
        centre_x + factor * (np.asarray(x) - centre_x),
        centre_y + factor * (np.asarray(y) - centre_y),
    )


def _magnify(projected, centre_x, centre_y, factor):
    metadata = dict(projected.metadata)
    metadata["display_magnification"] = factor
    if isinstance(projected, ProjectedCurves):
        items = []
        for curve in projected:
            x, y = _scaled_coordinates(
                curve.x, curve.y, centre_x, centre_y, factor
            )
            items.append(
                ProjectedCurve(
                    x=x,
                    y=y,
                    closed=curve.closed,
                    name=curve.name,
                )
            )
        return ProjectedCurves(items, metadata=metadata)
    if isinstance(projected, ProjectedPolygons):
        items = []
        for polygon in projected:
            x, y = _scaled_coordinates(
                polygon.x, polygon.y, centre_x, centre_y, factor
            )
            items.append(ProjectedPolygon(x=x, y=y, name=polygon.name))
        return ProjectedPolygons(items, metadata=metadata)
    raise TypeError(
        "resolved disk preparation requires projected curves or polygons."
    )


def _magnify_sequence(projected, centres, factor):
    metadata = dict(projected.metadata)
    metadata["display_magnification"] = factor
    if len(projected) != len(centres):
        raise ValueError(
            "resolved sequence components must align with projected centres."
        )
    if isinstance(projected, ProjectedCurves):
        items = []
        for curve, (centre_x, centre_y) in zip(projected, centres):
            x, y = _scaled_coordinates(curve.x, curve.y, centre_x, centre_y, factor)
            items.append(ProjectedCurve(x=x, y=y, closed=curve.closed, name=curve.name))
        return ProjectedCurves(items, metadata=metadata)
    if isinstance(projected, ProjectedPolygons):
        items = []
        for polygon, (centre_x, centre_y) in zip(projected, centres):
            x, y = _scaled_coordinates(polygon.x, polygon.y, centre_x, centre_y, factor)
            items.append(ProjectedPolygon(x=x, y=y, name=polygon.name))
        return ProjectedPolygons(items, metadata=metadata)
    raise TypeError(
        "resolved sequence preparation requires projected curves or polygons."
    )


@dataclass(frozen=True)
class MagnifyProjectedDisk:
    """Scale a projected disk component about its exact projected centre."""

    realization: object
    factor: float

    def bind_project_geometry(self, project_geometry):
        """Bind the chart's canonical projector for centre realization."""
        if not callable(project_geometry):
            raise TypeError("project_geometry must be callable.")

        centre = project_geometry(self.realization.transformed.centre)
        if not isinstance(centre, ProjectedPoints) or len(centre) != 1:
            raise TypeError(
                "resolved disk centre must project to one ProjectedPoints item."
            )
        centre_x = float(centre.x[0])
        centre_y = float(centre.y[0])
        factor = float(self.factor)

        def prepare(spherical, projected):
            del spherical
            return _magnify(
                projected,
                centre_x,
                centre_y,
                factor,
            )

        return prepare

    def __call__(self, spherical, projected):
        del spherical, projected
        raise RuntimeError(
            "MagnifyProjectedDisk must be bound to project_geometry first."
        )


@dataclass(frozen=True)
class MagnifyProjectedDiskSequence:
    """Scale each projected disk about its own projected physical centre."""

    realization: object
    factor: float

    def bind_project_geometry(self, project_geometry):
        if not callable(project_geometry):
            raise TypeError("project_geometry must be callable.")
        centre = project_geometry(self.realization.transformed.centres)
        if not isinstance(centre, ProjectedPoints) or len(centre) < 1:
            raise TypeError(
                "resolved sequence centres must project to ProjectedPoints."
            )
        centres = tuple(zip(centre.x.astype(float), centre.y.astype(float)))
        factor = float(self.factor)

        def prepare(spherical, projected):
            del spherical
            return _magnify_sequence(projected, centres, factor)

        return prepare

    def __call__(self, spherical, projected):
        del spherical, projected
        raise RuntimeError(
            "MagnifyProjectedDiskSequence must be bound to project_geometry first."
        )
