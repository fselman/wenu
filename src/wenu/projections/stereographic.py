import numpy as np

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPoint,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.geometry.frame import (
    SphericalCoordinates,
    SphericalFrame,
)
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)
from wenu.geometry.viewport import Viewport


class StereographicProjection:
    """Stereographic projection tangent at spherical latitude +90 degrees."""

    def __init__(
        self,
        radius: float = 2.0,
        flip_ew: bool = True,
        frame: SphericalFrame | None = None,
    ):
        radius = float(radius)
        if radius <= 0.0:
            raise ValueError("radius must be positive.")
        self.radius = radius
        self.flip_ew = bool(flip_ew)
        if frame is not None and not isinstance(frame, SphericalFrame):
            raise TypeError("frame must be a SphericalFrame or None.")
        self.frame = frame

    def transform_spherical(
        self,
        lon_deg,
        lat_deg,
    ) -> SphericalCoordinates:
        """Return coordinates aligned with the projection pole.

        With no configured frame, the input coordinates are already
        projection-aligned. With a frame, spherical rotation is delegated
        to ``SphericalFrame`` before the planar projection is evaluated.

        At zero position angle, the direction toward the source frame's
        north pole is placed along projected positive y. Positive position
        angle rotates that direction toward projected negative x before
        any east-west flip is applied.
        """
        if self.frame is not None:
            return self.frame.transform(lon_deg, lat_deg)

        lon, lat = np.broadcast_arrays(
            np.asarray(lon_deg, dtype=float),
            np.asarray(lat_deg, dtype=float),
        )
        return SphericalCoordinates(
            lon_deg=lon,
            lat_deg=lat,
        )

    def project_spherical(self, lon_deg, lat_deg):
        """Rotate, when configured, and project spherical coordinates."""
        coordinates = self.transform_spherical(lon_deg, lat_deg)
        return self._project_aligned(
            coordinates.lon_deg,
            coordinates.lat_deg,
        )

    def _project_aligned(self, lon_deg, lat_deg):
        """Project coordinates whose north pole is the tangent point."""
        lon = np.radians(lon_deg)
        lat = np.radians(lat_deg)
        r = self.radius * np.tan((np.pi / 2.0 - lat) / 2.0)
        x = r * np.sin(lon)
        y = r * np.cos(lon)
        if self.flip_ew:
            x = -x
        return x, y

    def projected_radius(self, angular_radius_deg: float) -> float:
        """Convert angular separation from chart center to plane radius."""
        angular_radius_deg = float(angular_radius_deg)
        if (
            not np.isfinite(angular_radius_deg)
            or angular_radius_deg <= 0.0
            or angular_radius_deg >= 180.0
        ):
            raise ValueError(
                "angular_radius_deg must be finite and between "
                "0 and 180 degrees."
            )
        return float(
            self.radius
            * np.tan(np.radians(angular_radius_deg) / 2.0)
        )

    def viewport_for_angular_radius(
        self,
        angular_radius_deg: float,
    ) -> Viewport:
        """Return the centered square viewport bounding an angular field."""
        projected_radius = self.projected_radius(angular_radius_deg)
        diameter = 2.0 * projected_radius
        return Viewport.centered(
            width=diameter,
            height=diameter,
        )

    def project(self, alt_deg, az_deg):
        """Backward-compatible horizontal Alt/Az projection."""
        return self.project_spherical(
            lon_deg=az_deg,
            lat_deg=alt_deg,
        )

    def project_geometry(self, geometry):
        """Project a supported spherical geometry object."""
        if isinstance(geometry, SphericalPoints):
            return self.project_points(geometry)
        if isinstance(geometry, SphericalCurves):
            return self.project_curves(geometry)
        if isinstance(geometry, SphericalGrid):
            return self.project_grid(geometry)
        if isinstance(geometry, SphericalPolygons):
            return self.project_polygons(geometry)
        raise TypeError(
            "Unsupported spherical geometry type: "
            f"{type(geometry).__name__}."
        )

    def project_points(
        self,
        points: SphericalPoints,
    ) -> ProjectedPoints:
        x, y = self.project_spherical(
            points.lon_deg,
            points.lat_deg,
        )
        return ProjectedPoints(
            x=x,
            y=y,
            metadata=points.metadata,
            ids=points.ids,
            labels=points.labels,
            names=points.names,
        )

    def project_curves(
        self,
        curves: SphericalCurves,
    ) -> ProjectedCurves:
        items = []
        for index, (lon_deg, lat_deg) in enumerate(
            zip(curves.lon_deg, curves.lat_deg)
        ):
            name = (
                None
                if curves.names is None
                else curves.names[index]
            )
            items.append(
                self.project_curve(
                    lon_deg,
                    lat_deg,
                    closed=curves.closed[index],
                    name=name,
                )
            )
        metadata = self._collection_metadata(curves)
        return ProjectedCurves(items=items, metadata=metadata)

    def project_grid(
        self,
        grid: SphericalGrid,
    ) -> ProjectedGrid:
        return ProjectedGrid(
            components={
                name: self.project_curves(curves)
                for name, curves in grid.components.items()
            },
            metadata=grid.metadata,
        )

    def project_polygons(
        self,
        polygons: SphericalPolygons,
    ) -> ProjectedPolygons:
        items = []
        for index, (lon_deg, lat_deg) in enumerate(
            zip(polygons.lon_deg, polygons.lat_deg)
        ):
            name = (
                None
                if polygons.names is None
                else polygons.names[index]
            )
            items.append(
                self.project_polygon(
                    lon_deg,
                    lat_deg,
                    name=name,
                )
            )
        metadata = self._collection_metadata(polygons)
        return ProjectedPolygons(items=items, metadata=metadata)

    @staticmethod
    def _collection_metadata(geometry) -> dict[str, object]:
        metadata = dict(geometry.metadata)
        for name in ("ids", "labels", "names"):
            values = getattr(geometry, name, None)
            if values is not None:
                metadata[name] = values.copy()
        return metadata

    def project_point(
        self,
        lon_deg,
        lat_deg,
        *,
        name: str | None = None,
    ) -> ProjectedPoint:
        x, y = self.project_spherical(lon_deg, lat_deg)
        x_array = np.asarray(x)
        y_array = np.asarray(y)
        if x_array.ndim != 0 or y_array.ndim != 0:
            raise ValueError(
                "project_point requires scalar longitude and latitude."
            )
        return ProjectedPoint(
            x=float(x_array),
            y=float(y_array),
            name=name,
        )

    def project_curve(
        self,
        lon_deg,
        lat_deg,
        *,
        closed: bool = False,
        name: str | None = None,
    ) -> ProjectedCurve:
        lon_deg = np.asarray(lon_deg, dtype=float)
        lat_deg = np.asarray(lat_deg, dtype=float)
        if lon_deg.ndim != 1 or lat_deg.ndim != 1:
            raise ValueError(
                "lon_deg and lat_deg must be one-dimensional arrays."
            )
        if lon_deg.shape != lat_deg.shape:
            raise ValueError(
                "lon_deg and lat_deg must have the same shape."
            )
        if lon_deg.size < 2:
            raise ValueError(
                "A projected curve requires at least two samples."
            )
        x, y = self.project_spherical(lon_deg, lat_deg)
        return ProjectedCurve(
            x=x,
            y=y,
            closed=closed,
            name=name,
        )

    def project_polygon(
        self,
        lon_deg,
        lat_deg,
        *,
        name: str | None = None,
    ) -> ProjectedPolygon:
        lon_deg = np.asarray(lon_deg, dtype=float)
        lat_deg = np.asarray(lat_deg, dtype=float)
        if lon_deg.ndim != 1 or lat_deg.ndim != 1:
            raise ValueError(
                "lon_deg and lat_deg must be one-dimensional arrays."
            )
        if lon_deg.shape != lat_deg.shape:
            raise ValueError(
                "lon_deg and lat_deg must have the same shape."
            )
        if lon_deg.size < 3:
            raise ValueError(
                "A projected polygon requires at least three vertices."
            )
        x, y = self.project_spherical(lon_deg, lat_deg)
        return ProjectedPolygon(x=x, y=y, name=name)
