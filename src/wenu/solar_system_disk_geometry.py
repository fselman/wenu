"""Renderer-neutral physical spherical geometry for apparent body disks."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, radians, sin
from operator import index

import numpy as np

from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalPoints,
    SphericalPolygons,
)
from wenu.solar_system_appearance import SolarSystemApparentDisk


DEFAULT_SOLAR_SYSTEM_DISK_SAMPLES = 720
SOLAR_SYSTEM_DISK_GEOMETRY_MODEL = (
    "orthographic spherical phase with radial angular-offset mapping"
)


def _sample_count(value):
    if isinstance(value, bool):
        raise TypeError("samples must be an integer.")
    try:
        samples = index(value)
    except TypeError as error:
        raise TypeError("samples must be an integer.") from error
    if samples < 16:
        raise ValueError("samples must be at least 16.")
    if samples % 2:
        raise ValueError("samples must be even.")
    return samples


def _unit_vector(longitude_deg, latitude_deg):
    longitude = radians(float(longitude_deg))
    latitude = radians(float(latitude_deg))
    cos_latitude = cos(latitude)
    return np.asarray(
        (
            cos_latitude * cos(longitude),
            cos_latitude * sin(longitude),
            sin(latitude),
        ),
        dtype=float,
    )


def _tangent_basis(longitude_deg, latitude_deg, position_angle_deg):
    longitude = radians(float(longitude_deg))
    latitude = radians(float(latitude_deg))
    angle = radians(float(position_angle_deg))
    north = np.asarray(
        (
            -sin(latitude) * cos(longitude),
            -sin(latitude) * sin(longitude),
            cos(latitude),
        ),
        dtype=float,
    )
    east = np.asarray(
        (-sin(longitude), cos(longitude), 0.0),
        dtype=float,
    )
    bright = cos(angle) * north + sin(angle) * east
    perpendicular = -sin(angle) * north + cos(angle) * east
    return bright, perpendicular


def _offset_coordinates(
    centre,
    bright,
    perpendicular,
    x,
    y,
    angular_radius_rad,
):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    radial_fraction = np.hypot(x, y)
    angular_offset = angular_radius_rad * radial_fraction
    tangent = (
        x[:, np.newaxis] * bright
        + y[:, np.newaxis] * perpendicular
    )
    scale = np.full(radial_fraction.shape, angular_radius_rad)
    nonzero = radial_fraction > 0.0
    scale[nonzero] = (
        np.sin(angular_offset[nonzero]) / radial_fraction[nonzero]
    )
    directions = (
        np.cos(angular_offset)[:, np.newaxis] * centre
        + scale[:, np.newaxis] * tangent
    )
    directions /= np.linalg.norm(directions, axis=1)[:, np.newaxis]
    longitude = np.degrees(
        np.arctan2(directions[:, 1], directions[:, 0])
    ) % 360.0
    latitude = np.degrees(
        np.arcsin(np.clip(directions[:, 2], -1.0, 1.0))
    )
    return longitude, latitude


@dataclass(frozen=True)
class SolarSystemDiskGeometry:
    """One physical apparent disk expressed as ordinary spherical records."""

    appearance: SolarSystemApparentDisk
    centre: SphericalPoints
    limb: SphericalCurves
    terminator: SphericalCurves
    illuminated_face: SphericalPolygons
    samples: int

    def __post_init__(self):
        if not isinstance(self.appearance, SolarSystemApparentDisk):
            raise TypeError(
                "appearance must be a SolarSystemApparentDisk."
            )
        expected = (
            ("centre", self.centre, SphericalPoints),
            ("limb", self.limb, SphericalCurves),
            ("terminator", self.terminator, SphericalCurves),
            (
                "illuminated_face",
                self.illuminated_face,
                SphericalPolygons,
            ),
        )
        for name, value, kind in expected:
            if not isinstance(value, kind):
                raise TypeError(f"{name} must be a {kind.__name__}.")
        if len(self.centre) != 1:
            raise ValueError("centre must contain exactly one point.")
        if len(self.limb) != 1:
            raise ValueError("limb must contain exactly one curve.")
        if len(self.terminator) != 1:
            raise ValueError("terminator must contain exactly one curve.")
        if len(self.illuminated_face) != 1:
            raise ValueError(
                "illuminated_face must contain exactly one polygon."
            )
        coordinate_spec = self.centre.coordinate_spec
        for name in ("limb", "terminator", "illuminated_face"):
            if getattr(self, name).coordinate_spec != coordinate_spec:
                raise ValueError(
                    "all disk geometries must share one coordinate spec."
                )
        object.__setattr__(self, "samples", _sample_count(self.samples))


class SolarSystemDiskGeometryRealizer:
    """Construct physical limb, terminator, and illuminated-face geometry."""

    def geometry(
        self,
        appearance,
        *,
        samples=DEFAULT_SOLAR_SYSTEM_DISK_SAMPLES,
    ):
        if not isinstance(appearance, SolarSystemApparentDisk):
            raise TypeError(
                "appearance must be a SolarSystemApparentDisk."
            )
        samples = _sample_count(samples)
        direction = appearance.apparent_direction.geometry
        if len(direction) != 1:
            raise ValueError(
                "appearance direction must contain exactly one point."
            )

        centre_lon = float(direction.lon_deg[0])
        centre_lat = float(direction.lat_deg[0])
        centre_vector = _unit_vector(centre_lon, centre_lat)
        bright, perpendicular = _tangent_basis(
            centre_lon,
            centre_lat,
            appearance.bright_limb_position_angle_deg,
        )
        angular_radius_rad = radians(
            appearance.angular_diameter_arcsec / 7200.0
        )

        limb_angle = np.linspace(
            0.0,
            2.0 * pi,
            samples,
            endpoint=False,
        )
        limb_x = np.cos(limb_angle)
        limb_y = np.sin(limb_angle)

        half_samples = samples // 2
        bright_angle = np.linspace(
            -0.5 * pi,
            0.5 * pi,
            half_samples + 1,
        )
        bright_x = np.cos(bright_angle)
        bright_y = np.sin(bright_angle)

        terminator_angle = np.linspace(
            0.5 * pi,
            1.5 * pi,
            half_samples + 1,
        )
        terminator_x = (
            cos(radians(appearance.phase_angle_deg))
            * np.cos(terminator_angle)
        )
        terminator_y = np.sin(terminator_angle)

        face_x = np.concatenate(
            (bright_x, terminator_x[1:-1])
        )
        face_y = np.concatenate(
            (bright_y, terminator_y[1:-1])
        )

        limb_lon, limb_lat = _offset_coordinates(
            centre_vector,
            bright,
            perpendicular,
            limb_x,
            limb_y,
            angular_radius_rad,
        )
        terminator_lon, terminator_lat = _offset_coordinates(
            centre_vector,
            bright,
            perpendicular,
            terminator_x,
            terminator_y,
            angular_radius_rad,
        )
        face_lon, face_lat = _offset_coordinates(
            centre_vector,
            bright,
            perpendicular,
            face_x,
            face_y,
            angular_radius_rad,
        )

        coordinate_spec = direction.coordinate_spec
        identity = np.asarray((appearance.target,), dtype=object)
        common_metadata = {
            "target": appearance.target,
            "display_name": appearance.display_name,
            "angular_radius_arcsec": (
                0.5 * appearance.angular_diameter_arcsec
            ),
            "phase_angle_deg": appearance.phase_angle_deg,
            "illuminated_fraction": appearance.illuminated_fraction,
            "bright_limb_position_angle_deg": (
                appearance.bright_limb_position_angle_deg
            ),
            "position_angle_convention": (
                appearance.position_angle_convention
            ),
            "samples": samples,
            "geometry_model": SOLAR_SYSTEM_DISK_GEOMETRY_MODEL,
            "radius_model": appearance.radius_model,
            "provenance": appearance.provenance,
        }

        def metadata(component):
            return {**common_metadata, "component": component}

        centre = SphericalPoints(
            np.asarray((centre_lon,)),
            np.asarray((centre_lat,)),
            coordinate_spec=coordinate_spec,
            ids=identity.copy(),
            labels=np.asarray(
                (appearance.display_name,),
                dtype=object,
            ),
            names=np.asarray(("centre",), dtype=object),
            metadata=metadata("centre"),
        )
        limb = SphericalCurves(
            (limb_lon,),
            (limb_lat,),
            coordinate_spec=coordinate_spec,
            closed=np.asarray((True,)),
            ids=identity.copy(),
            names=np.asarray(("limb",), dtype=object),
            metadata=metadata("limb"),
        )
        terminator = SphericalCurves(
            (terminator_lon,),
            (terminator_lat,),
            coordinate_spec=coordinate_spec,
            closed=np.asarray((False,)),
            ids=identity.copy(),
            names=np.asarray(("terminator",), dtype=object),
            metadata=metadata("terminator"),
        )
        illuminated_face = SphericalPolygons(
            (face_lon,),
            (face_lat,),
            coordinate_spec=coordinate_spec,
            ids=identity.copy(),
            names=np.asarray(
                ("illuminated_face",),
                dtype=object,
            ),
            metadata=metadata("illuminated_face"),
        )
        return SolarSystemDiskGeometry(
            appearance=appearance,
            centre=centre,
            limb=limb,
            terminator=terminator,
            illuminated_face=illuminated_face,
            samples=samples,
        )
