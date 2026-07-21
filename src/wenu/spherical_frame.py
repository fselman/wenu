"""
Coordinate-neutral rotations of the celestial sphere.

This module establishes the SphericalFrame abstraction without connecting it
to the existing Wenu projection or rendering pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SphericalCoordinates:
    """
    Generic spherical longitude and latitude coordinates.

    Parameters
    ----------
    lon_deg
        Longitude in degrees.

    lat_deg
        Latitude in degrees.

    Notes
    -----
    These coordinates deliberately have no astronomical interpretation.
    They may represent a rotated form of ICRS, Galactic, ecliptic, horizontal,
    or any other spherical coordinate system.
    """

    lon_deg: np.ndarray
    lat_deg: np.ndarray


@dataclass(frozen=True)
class SphericalFrame:
    """
    A rotated coordinate frame on the unit sphere.

    The frame is defined by:

    - a spherical position placed at the frame's north pole;
    - a position angle that controls rotation about that pole.

    This class performs spherical rotation only. It does not project
    coordinates onto a plane and does not perform viewport clipping.

    Parameters
    ----------
    pole_lon_deg
        Longitude of the new frame's north pole in the source coordinate
        system, in degrees.

    pole_lat_deg
        Latitude of the new frame's north pole in the source coordinate
        system, in degrees.

    position_angle_deg
        Rotation of the new longitude system about its pole, in degrees.
        The default is zero.
    """

    pole_lon_deg: float
    pole_lat_deg: float
    position_angle_deg: float = 0.0

    def transform(
        self,
        lon_deg,
        lat_deg,
    ) -> SphericalCoordinates:
        """
        Rotate source spherical coordinates into this frame.

        Parameters
        ----------
        lon_deg
            Source longitudes in degrees. Scalars and array-like values are
            accepted.

        lat_deg
            Source latitudes in degrees. Scalars and array-like values are
            accepted.

        Returns
        -------
        SphericalCoordinates
            Longitudes and latitudes in the rotated frame.

        Notes
        -----
        Output longitudes are normalized to the interval ``[-180, 180)``.
        """

        lon, lat = np.broadcast_arrays(
            np.asarray(lon_deg, dtype=float),
            np.asarray(lat_deg, dtype=float),
        )

        vectors = self._spherical_to_cartesian(
            lon,
            lat,
        )

        rotated = np.einsum(
            "ij,...j->...i",
            self.rotation_matrix,
            vectors,
        )

        transformed_lon, transformed_lat = (
            self._cartesian_to_spherical(rotated)
        )

        return SphericalCoordinates(
            lon_deg=transformed_lon,
            lat_deg=transformed_lat,
        )

    def inverse_transform(
        self,
        lon_deg,
        lat_deg,
    ) -> SphericalCoordinates:
        """
        Rotate coordinates from this frame back to the source frame.

        Parameters
        ----------
        lon_deg
            Longitudes in this frame, in degrees.

        lat_deg
            Latitudes in this frame, in degrees.

        Returns
        -------
        SphericalCoordinates
            Coordinates in the original source frame.
        """

        lon, lat = np.broadcast_arrays(
            np.asarray(lon_deg, dtype=float),
            np.asarray(lat_deg, dtype=float),
        )

        vectors = self._spherical_to_cartesian(
            lon,
            lat,
        )

        restored = np.einsum(
            "ji,...j->...i",
            self.rotation_matrix,
            vectors,
        )

        restored_lon, restored_lat = (
            self._cartesian_to_spherical(restored)
        )

        return SphericalCoordinates(
            lon_deg=restored_lon,
            lat_deg=restored_lat,
        )

    @property
    def rotation_matrix(self) -> np.ndarray:
        """
        Return the source-to-frame rotation matrix.

        The matrix is orthogonal. Its transpose therefore performs the
        inverse transformation.
        """

        pole_lon = np.radians(
            self.pole_lon_deg
        )
        pole_lat = np.radians(
            self.pole_lat_deg
        )
        position_angle = np.radians(
            self.position_angle_deg
        )

        pole = np.array(
            [
                np.cos(pole_lat) * np.cos(pole_lon),
                np.cos(pole_lat) * np.sin(pole_lon),
                np.sin(pole_lat),
            ],
            dtype=float,
        )

        reference = np.array(
            [0.0, 0.0, 1.0],
            dtype=float,
        )

        if np.isclose(
            abs(np.dot(reference, pole)),
            1.0,
        ):
            reference = np.array(
                [1.0, 0.0, 0.0],
                dtype=float,
            )

        x_axis = reference - np.dot(
            reference,
            pole,
        ) * pole

        x_axis /= np.linalg.norm(
            x_axis
        )

        y_axis = np.cross(
            pole,
            x_axis,
        )

        cos_pa = np.cos(
            position_angle
        )
        sin_pa = np.sin(
            position_angle
        )

        rotated_x = (
            cos_pa * x_axis
            + sin_pa * y_axis
        )

        rotated_y = (
            -sin_pa * x_axis
            + cos_pa * y_axis
        )

        return np.vstack(
            (
                rotated_x,
                rotated_y,
                pole,
            )
        )

    @staticmethod
    def _spherical_to_cartesian(
        lon_deg: np.ndarray,
        lat_deg: np.ndarray,
    ) -> np.ndarray:
        lon = np.radians(
            lon_deg
        )
        lat = np.radians(
            lat_deg
        )

        cos_lat = np.cos(
            lat
        )

        return np.stack(
            (
                cos_lat * np.cos(lon),
                cos_lat * np.sin(lon),
                np.sin(lat),
            ),
            axis=-1,
        )

    @staticmethod
    def _cartesian_to_spherical(
        vectors: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        x = vectors[..., 0]
        y = vectors[..., 1]
        z = np.clip(
            vectors[..., 2],
            -1.0,
            1.0,
        )

        lon = np.degrees(
            np.arctan2(y, x)
        )
        lat = np.degrees(
            np.arcsin(z)
        )

        lon = (
            lon + 180.0
        ) % 360.0 - 180.0

        return lon, lat


