# src/wenu/projection.py

import numpy as np

from typing import Any

from wenu.projected import (
    ProjectedCurve,
    ProjectedPoint,
    ProjectedPolygon,
)

from wenu.visibility import visible_segments

# -----------------------
# Proyección estereográfica (cenit)
# -----------------------
class StereographicProjection:

    def __init__(self, radius=2.0, flip_ew=True):
        self.radius = radius
        self.flip_ew = flip_ew

    def project_spherical(
        self,
        lon_deg,
        lat_deg,
    ):
        """
        Project generic spherical longitude and latitude coordinates.

        Parameters
        ----------
        lon_deg
            Spherical longitude in degrees.

        lat_deg
            Spherical latitude in degrees.

        Returns
        -------
        tuple
            Projected ``(x, y)`` coordinates.

        Notes
        -----
        Latitude +90 degrees is the tangent point and maps to the
        projection origin.
        """

        lon = np.radians(lon_deg)
        lat = np.radians(lat_deg)

        r = self.radius * np.tan(
            (np.pi / 2.0 - lat) / 2.0
        )

        x = r * np.sin(lon)
        y = r * np.cos(lon)

        if self.flip_ew:
            x = -x

        return x, y

    def project(
        self,
        alt_deg,
        az_deg,
    ):
        """
        Project horizontal Alt/Az coordinates.

        This is the backward-compatible interface used by the existing
        Wenu code. Altitude is interpreted as spherical latitude and
        azimuth as spherical longitude.
        """

        return self.project_spherical(
            lon_deg=az_deg,
            lat_deg=alt_deg,
        )

    def project_point(
        self,
        lon_deg,
        lat_deg,
        *,
        name: str | None = None,
    ) -> ProjectedPoint:
        """
        Project one spherical point.

        Parameters
        ----------
        lon_deg, lat_deg
            Generic spherical longitude and latitude in degrees.
        name
            Optional point identifier.

        Returns
        -------
        ProjectedPoint
            Cartesian representation of the point.
        """
        x, y = self.project_spherical(
            lon_deg=lon_deg,
            lat_deg=lat_deg,
        )

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
        """
        Project a sampled spherical curve.

        This method performs projection only. It does not apply horizon
        visibility, viewport clipping, segmentation, or rendering.
        """
        lon_deg = np.asarray(
            lon_deg,
            dtype=float,
        )
        lat_deg = np.asarray(
            lat_deg,
            dtype=float,
        )

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

        x, y = self.project_spherical(
            lon_deg=lon_deg,
            lat_deg=lat_deg,
        )

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
        """
        Project a spherical polygon boundary.

        This method performs projection only. It does not clip or draw
        the resulting polygon.
        """
        lon_deg = np.asarray(
            lon_deg,
            dtype=float,
        )
        lat_deg = np.asarray(
            lat_deg,
            dtype=float,
        )

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

        x, y = self.project_spherical(
            lon_deg=lon_deg,
            lat_deg=lat_deg,
        )

        return ProjectedPolygon(
            x=x,
            y=y,
            name=name,
        )

    def visible(self, alt_deg, az_deg=None):
        """
        Return a Boolean mask indicating which altitude samples are visible.

        This method is retained for backward compatibility and delegates to
        ``wenu.visibility.visibility_mask()``.
        """

        return np.asarray(alt_deg) > 0.0

