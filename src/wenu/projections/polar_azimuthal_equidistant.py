"""Polar azimuthal-equidistant projection for physical sky disks."""

from __future__ import annotations

import numpy as np

from wenu.geometry.frame import SphericalCoordinates, SphericalFrame
from wenu.projections.stereographic import StereographicProjection


class PolarAzimuthalEquidistantProjection(StereographicProjection):
    """Project angular distance from a selected celestial pole linearly.

    ``radius`` is the projected radius of the spherical equator. The class
    reuses the established coordinate transformation and geometry-dispatch
    protocol from ``StereographicProjection`` while replacing every planar
    and radial projection calculation.
    """

    def __init__(
        self,
        radius: float = 2.0,
        pole: str = "north",
        position_angle_deg: float = 0.0,
        flip_ew: bool = True,
        frame: SphericalFrame | None = None,
    ):
        radius = float(radius)
        if not np.isfinite(radius) or radius <= 0.0:
            raise ValueError("radius must be positive and finite.")
        super().__init__(radius=radius, flip_ew=flip_ew, frame=frame)
        pole = str(pole).strip().lower()
        if pole not in {"north", "south"}:
            raise ValueError("pole must be 'north' or 'south'.")
        position_angle_deg = float(position_angle_deg)
        if not np.isfinite(position_angle_deg):
            raise ValueError("position_angle_deg must be finite.")
        self.pole = pole
        self.position_angle_deg = position_angle_deg

    def _project_aligned(self, lon_deg, lat_deg):
        """Project source-frame longitudes and declinations."""
        longitude, latitude = np.broadcast_arrays(
            np.asarray(lon_deg, dtype=float),
            np.asarray(lat_deg, dtype=float),
        )
        if not np.all(np.isfinite(longitude)):
            raise ValueError("longitude must be finite.")
        if not np.all(np.isfinite(latitude)):
            raise ValueError("latitude must be finite.")
        if np.any((latitude < -90.0) | (latitude > 90.0)):
            raise ValueError("latitude must be between -90 and 90 degrees.")

        if self.pole == "north":
            polar_distance_deg = 90.0 - latitude
        else:
            polar_distance_deg = 90.0 + latitude
        if np.any(polar_distance_deg >= 180.0):
            raise ValueError(
                "The opposite pole is outside the invertible "
                "projection domain."
            )
        projected_radius = self.radius * polar_distance_deg / 90.0
        angle = np.radians(longitude - self.position_angle_deg)
        x = projected_radius * np.sin(angle)
        y = projected_radius * np.cos(angle)
        if self.flip_ew:
            x = -x
        return x, y

    def unproject_spherical(self, x, y):
        """Return source-frame coordinates for projected positions."""
        projected_x, projected_y = np.broadcast_arrays(
            np.asarray(x, dtype=float),
            np.asarray(y, dtype=float),
        )
        if not np.all(np.isfinite(projected_x)):
            raise ValueError("x must be finite.")
        if not np.all(np.isfinite(projected_y)):
            raise ValueError("y must be finite.")
        aligned_x = -projected_x if self.flip_ew else projected_x
        projected_radius = np.hypot(aligned_x, projected_y)
        if np.any(projected_radius >= 2.0 * self.radius):
            raise ValueError(
                "projected radius exceeds the spherical projection domain."
            )
        polar_distance_deg = 90.0 * projected_radius / self.radius
        if self.pole == "north":
            latitude = 90.0 - polar_distance_deg
        else:
            latitude = -90.0 + polar_distance_deg
        longitude = (
            np.degrees(np.arctan2(aligned_x, projected_y))
            + self.position_angle_deg
        )
        longitude = (longitude + 180.0) % 360.0 - 180.0
        coordinates = SphericalCoordinates(longitude, latitude)
        if self.frame is None:
            return coordinates
        return self.frame.inverse_transform(
            coordinates.lon_deg,
            coordinates.lat_deg,
        )

    def projected_radius(self, angular_radius_deg: float) -> float:
        """Convert polar angular radius to projected radius."""
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
        return self.radius * angular_radius_deg / 90.0

    def angular_radius_for_projected_radius(
        self,
        projected_radius,
    ) -> float:
        """Convert projected radius to polar angular radius."""
        projected_radius = float(projected_radius)
        if (
            not np.isfinite(projected_radius)
            or projected_radius < 0.0
            or projected_radius >= 2.0 * self.radius
        ):
            raise ValueError(
                "projected_radius must be finite, non-negative, and "
                "less than twice the equatorial radius."
            )
        return 90.0 * projected_radius / self.radius
