"""Immutable paired north/south polar-planisphere geometry."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.polar_planisphere import PolarPlanisphereChart


@dataclass(frozen=True)
class PolarRegistrationMark:
    """One corresponding asymmetric mark on both physical faces."""

    identifier: str
    radius_fraction: float
    south_angle_deg: float
    north_angle_deg: float


@dataclass(frozen=True)
class PolarFaceRegistration:
    """Resolved face identity and non-rendered assembly metadata."""

    face: str
    center: tuple[float, float]
    outer_radius_mm: float
    calendar_radius_mm: float | None
    pivot_radius_mm: float | None
    marks: tuple[tuple[str, float, float], ...]
    text_mirrored: bool = False


@dataclass(frozen=True)
class PolarPlanispherePair:
    """Resolved matched disk faces and physical registration metadata."""

    south: PolarPlanisphereChart
    north: PolarPlanisphereChart
    south_registration: PolarFaceRegistration
    north_registration: PolarFaceRegistration

    @property
    def faces(self):
        return self.south, self.north


@dataclass(frozen=True)
class PolarPlanispherePairRequest:
    """One source of truth for a matched back-to-back disk pair."""

    projection_name: str = "polar_azimuthal_equidistant"
    south_limiting_declination_deg: float = 20.0
    north_limiting_declination_deg: float = -20.0
    position_angle_deg: float = 0.0
    projection_radius: float = 2.0
    physical_diameter_mm: float = 195.0
    south_flip_ew: bool | None = None
    boundary_samples: int = 721
    calendar_radius_mm: float | None = None
    pivot_radius_mm: float | None = None
    registration_radius_fraction: float = 0.975
    registration_angles_deg: tuple[float, ...] = (0.0, 97.0, 211.0)

    def __post_init__(self):
        projection_name = str(self.projection_name).strip().lower()
        if projection_name not in {
            "polar_azimuthal_equidistant",
            "stereographic",
        }:
            raise ValueError(
                "projection_name must be 'polar_azimuthal_equidistant' "
                "or 'stereographic'."
            )
        values = np.asarray(
            (
                self.south_limiting_declination_deg,
                self.north_limiting_declination_deg,
                self.position_angle_deg,
                self.projection_radius,
                self.physical_diameter_mm,
                self.registration_radius_fraction,
            ),
            dtype=float,
        )
        if not np.all(np.isfinite(values)):
            raise ValueError("Paired polar-planisphere values must be finite.")
        south_limit = float(self.south_limiting_declination_deg)
        north_limit = float(self.north_limiting_declination_deg)
        if not -90.0 < south_limit < 90.0:
            raise ValueError(
                "south_limiting_declination_deg must be between -90 and 90."
            )
        if not -90.0 < north_limit < 90.0:
            raise ValueError(
                "north_limiting_declination_deg must be between -90 and 90."
            )
        if south_limit < 0.0 or north_limit > 0.0:
            raise ValueError(
                "paired limits must cover the celestial equator."
            )
        south_radius = 90.0 + south_limit
        north_radius = 90.0 - north_limit
        if not np.isclose(south_radius, north_radius, atol=1.0e-12):
            raise ValueError(
                "north and south limits must produce the same polar radius."
            )
        projection_radius = float(self.projection_radius)
        physical_diameter = float(self.physical_diameter_mm)
        if projection_radius <= 0.0:
            raise ValueError("projection_radius must be positive.")
        if physical_diameter <= 0.0:
            raise ValueError("physical_diameter_mm must be positive.")
        if int(self.boundary_samples) < 16:
            raise ValueError("boundary_samples must be at least 16.")
        radius_fraction = float(self.registration_radius_fraction)
        if not 0.0 < radius_fraction < 1.0:
            raise ValueError(
                "registration_radius_fraction must be between 0 and 1."
            )
        angles = tuple(
            float(value) % 360.0 for value in self.registration_angles_deg
        )
        if not np.all(np.isfinite(angles)):
            raise ValueError("registration angles must be finite.")
        if len(angles) < 3 or len(set(angles)) != len(angles):
            raise ValueError(
                "registration_angles_deg must contain at least three "
                "unique angles."
            )
        ordered_angles = np.sort(np.asarray(angles, dtype=float))
        gaps = np.diff(np.append(ordered_angles, ordered_angles[0] + 360.0))
        if np.allclose(gaps, gaps[0]):
            raise ValueError("registration angles must be asymmetric.")
        outer_radius = physical_diameter / 2.0
        for name in ("calendar_radius_mm", "pivot_radius_mm"):
            value = getattr(self, name)
            if value is None:
                continue
            value = float(value)
            if not np.isfinite(value) or not 0.0 < value < outer_radius:
                raise ValueError(
                    f"{name} must be positive and smaller than the "
                    "outer radius."
                )
            object.__setattr__(self, name, value)
        if (
            self.calendar_radius_mm is not None
            and self.pivot_radius_mm is not None
            and self.pivot_radius_mm >= self.calendar_radius_mm
        ):
            raise ValueError(
                "pivot_radius_mm must be smaller than calendar_radius_mm."
            )
        object.__setattr__(self, "projection_name", projection_name)
        object.__setattr__(
            self, "south_limiting_declination_deg", south_limit
        )
        object.__setattr__(
            self, "north_limiting_declination_deg", north_limit
        )
        object.__setattr__(
            self, "position_angle_deg", float(self.position_angle_deg)
        )
        object.__setattr__(
            self, "projection_radius", projection_radius
        )
        object.__setattr__(
            self, "physical_diameter_mm", physical_diameter
        )
        if self.south_flip_ew is not None:
            object.__setattr__(
                self, "south_flip_ew", bool(self.south_flip_ew)
            )
        object.__setattr__(
            self, "boundary_samples", int(self.boundary_samples)
        )
        object.__setattr__(
            self, "registration_radius_fraction", radius_fraction
        )
        object.__setattr__(self, "registration_angles_deg", angles)

    @property
    def overlap_deg(self):
        return (
            self.south_limiting_declination_deg
            - self.north_limiting_declination_deg
        )

    @property
    def outer_radius_mm(self):
        return self.physical_diameter_mm / 2.0

    @property
    def registration_marks(self):
        return tuple(
            PolarRegistrationMark(
                identifier=f"registration_{index + 1}",
                radius_fraction=self.registration_radius_fraction,
                south_angle_deg=angle,
                north_angle_deg=(180.0 - angle) % 360.0,
            )
            for index, angle in enumerate(self.registration_angles_deg)
        )

    @property
    def north_flip_ew(self):
        if self.projection_name == "polar_azimuthal_equidistant":
            return not self.resolved_south_flip_ew
        return self.resolved_south_flip_ew

    @property
    def resolved_south_flip_ew(self):
        if self.south_flip_ew is not None:
            return bool(self.south_flip_ew)
        return self.projection_name == "polar_azimuthal_equidistant"

    def resolve(self):
        """Return matched immutable faces and assembly metadata."""
        shared = {
            "projection_name": self.projection_name,
            "position_angle_deg": self.position_angle_deg,
            "projection_radius": self.projection_radius,
            "physical_diameter_mm": self.physical_diameter_mm,
            "boundary_samples": self.boundary_samples,
        }
        south = PolarPlanisphereChart(
            pole="south",
            limiting_declination_deg=(
                self.south_limiting_declination_deg
            ),
            flip_ew=self.resolved_south_flip_ew,
            **shared,
        )
        north = PolarPlanisphereChart(
            pole="north",
            limiting_declination_deg=(
                self.north_limiting_declination_deg
            ),
            flip_ew=self.north_flip_ew,
            **shared,
        )
        if not np.isclose(
            south.boundary_radius, north.boundary_radius, atol=1.0e-12
        ):
            raise ValueError("Resolved faces must have matching boundaries.")
        if (
            self._paper_ra_direction(south)
            != -self._paper_ra_direction(north)
        ):
            raise ValueError(
                "Resolved faces must have opposite paper RA direction."
            )
        south_registration = self._face_registration("south")
        north_registration = self._face_registration("north")
        return PolarPlanispherePair(
            south=south,
            north=north,
            south_registration=south_registration,
            north_registration=north_registration,
        )

    def _face_registration(self, face):
        marks = self.registration_marks
        return PolarFaceRegistration(
            face=face,
            center=(0.0, 0.0),
            outer_radius_mm=self.outer_radius_mm,
            calendar_radius_mm=self.calendar_radius_mm,
            pivot_radius_mm=self.pivot_radius_mm,
            marks=tuple(
                (
                    mark.identifier,
                    mark.radius_fraction,
                    (
                        mark.south_angle_deg
                        if face == "south"
                        else mark.north_angle_deg
                    ),
                )
                for mark in marks
            ),
        )

    @staticmethod
    def _paper_ra_direction(chart):
        x, y = chart.projection.project_spherical(
            np.asarray((0.0, 1.0)),
            np.asarray((0.0, 0.0)),
        )
        angle = np.degrees(np.arctan2(x, y))
        difference = (angle[1] - angle[0] + 180.0) % 360.0 - 180.0
        return int(np.sign(difference))
