"""Renderer-neutral physical appearance of spherical Solar-System bodies."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import (
    asin,
    atan2,
    cos,
    degrees,
    hypot,
    isfinite,
    pi,
    radians,
    sin,
    sqrt,
)

from wenu.ephemeris import EphemerisStateRequest, EphemerisStateSource
from wenu.solar_system_directions import ApparentDirection

AU_KM = 149_597_870.7
MERCURY_MEAN_RADIUS_KM = 2439.4
VENUS_MEAN_RADIUS_KM = 6051.8
BRIGHT_LIMB_POSITION_ANGLE_CONVENTION = (
    "observer-origin apparent ICRS tangent plane; "
    "zero at celestial north; positive toward east"
)


class SolarSystemAppearanceError(ValueError):
    """Base error for deterministic physical-appearance failures."""


class SolarSystemAppearanceIdentityError(SolarSystemAppearanceError):
    """Direction, observer, or provider identity is inconsistent."""


class SolarSystemAppearanceGeometryError(SolarSystemAppearanceError):
    """The requested physical appearance is geometrically undefined."""


def _text(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty.")
    return normalized


def _finite(value, *, name):
    normalized = float(value)
    if not isfinite(normalized):
        raise ValueError(f"{name} must be finite.")
    return normalized


def _unit_vector(longitude_deg, latitude_deg):
    longitude = radians(float(longitude_deg))
    latitude = radians(float(latitude_deg))
    cos_latitude = cos(latitude)
    return (
        cos_latitude * cos(longitude),
        cos_latitude * sin(longitude),
        sin(latitude),
    )


def _angle_between(left, right):
    left_length = sqrt(sum(value * value for value in left))
    right_length = sqrt(sum(value * value for value in right))
    if left_length <= 0.0 or right_length <= 0.0:
        raise SolarSystemAppearanceGeometryError(
            "phase vectors must have positive length."
        )
    cross = (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )
    cross_length = sqrt(sum(value * value for value in cross))
    dot = sum(a * b for a, b in zip(left, right))
    return degrees(atan2(cross_length, dot))


def _bright_limb_position_angle(target, sun):
    target_ra = radians(float(target.geometry.lon_deg[0]))
    target_dec = radians(float(target.geometry.lat_deg[0]))
    sun_ra = radians(float(sun.geometry.lon_deg[0]))
    sun_dec = radians(float(sun.geometry.lat_deg[0]))
    delta_ra = sun_ra - target_ra

    numerator = cos(sun_dec) * sin(delta_ra)
    denominator = (
        sin(sun_dec) * cos(target_dec)
        - cos(sun_dec) * sin(target_dec) * cos(delta_ra)
    )
    if hypot(numerator, denominator) <= 1.0e-15:
        raise SolarSystemAppearanceGeometryError(
            "bright-limb position angle is undefined for coincident "
            "apparent target and Sun directions."
        )
    return degrees(atan2(numerator, denominator)) % 360.0


@dataclass(frozen=True)
class SolarSystemApparentDisk:
    """One physical spherical-body appearance before display magnification."""

    target: str
    display_name: str
    apparent_direction: ApparentDirection
    sun_apparent_direction: ApparentDirection
    physical_radius_km: float
    radius_model: str
    angular_diameter_arcsec: float
    phase_angle_deg: float
    illuminated_fraction: float
    bright_limb_position_angle_deg: float
    position_angle_convention: str = BRIGHT_LIMB_POSITION_ANGLE_CONVENTION
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        for name in (
            "target",
            "display_name",
            "radius_model",
            "position_angle_convention",
        ):
            object.__setattr__(
                self,
                name,
                _text(getattr(self, name), name=name),
            )
        for name in ("apparent_direction", "sun_apparent_direction"):
            if not isinstance(getattr(self, name), ApparentDirection):
                raise TypeError(f"{name} must be an ApparentDirection.")

        radius = _finite(self.physical_radius_km, name="physical_radius_km")
        diameter = _finite(
            self.angular_diameter_arcsec,
            name="angular_diameter_arcsec",
        )
        phase = _finite(self.phase_angle_deg, name="phase_angle_deg")
        fraction = _finite(
            self.illuminated_fraction,
            name="illuminated_fraction",
        )
        position_angle = _finite(
            self.bright_limb_position_angle_deg,
            name="bright_limb_position_angle_deg",
        )
        if radius <= 0.0:
            raise ValueError("physical_radius_km must be positive.")
        if diameter <= 0.0:
            raise ValueError("angular_diameter_arcsec must be positive.")
        if not 0.0 <= phase <= 180.0:
            raise ValueError("phase_angle_deg must be between 0 and 180.")
        if not 0.0 <= fraction <= 1.0:
            raise ValueError("illuminated_fraction must be between 0 and 1.")
        if not 0.0 <= position_angle < 360.0:
            raise ValueError(
                "bright_limb_position_angle_deg must be in [0, 360)."
            )
        object.__setattr__(self, "physical_radius_km", radius)
        object.__setattr__(self, "angular_diameter_arcsec", diameter)
        object.__setattr__(self, "phase_angle_deg", phase)
        object.__setattr__(self, "illuminated_fraction", fraction)
        object.__setattr__(
            self,
            "bright_limb_position_angle_deg",
            position_angle,
        )
        object.__setattr__(
            self,
            "provenance",
            tuple(_text(value, name="provenance entry") for value in self.provenance),
        )


class SolarSystemAppearanceRealizer:
    """Realize physical spherical-body appearance from accepted directions."""

    def appearance(
        self,
        source,
        apparent_direction,
        sun_apparent_direction,
        *,
        display_name,
        physical_radius_km,
        radius_model,
    ):
        if not isinstance(source, EphemerisStateSource):
            raise TypeError("source must satisfy EphemerisStateSource.")
        if not isinstance(apparent_direction, ApparentDirection):
            raise TypeError(
                "apparent_direction must be an ApparentDirection."
            )
        if not isinstance(sun_apparent_direction, ApparentDirection):
            raise TypeError(
                "sun_apparent_direction must be an ApparentDirection."
            )
        self._validate_directions(
            apparent_direction,
            sun_apparent_direction,
        )

        astrometric = apparent_direction.astrometric
        observer_state = astrometric.observer_state
        request = astrometric.request
        sun_request = EphemerisStateRequest(
            target="sun",
            centre=request.centre,
            frame="icrf",
            instant=request.reception_instant,
            time_scale=request.reception_time_scale,
        )
        sun_state = source.state(sun_request)
        self._validate_sun_state(sun_state, sun_request, observer_state)

        unit = _unit_vector(
            astrometric.geometry.lon_deg[0],
            astrometric.geometry.lat_deg[0],
        )
        observer_to_target = tuple(
            astrometric.distance_au * component for component in unit
        )
        sun_to_target_parallel = tuple(
            target - sun + observer
            for target, sun, observer in zip(
                observer_to_target,
                sun_state.position,
                observer_state.position,
            )
        )
        phase_angle_deg = _angle_between(
            observer_to_target,
            sun_to_target_parallel,
        )
        illuminated_fraction = 0.5 * (
            1.0 + cos(radians(phase_angle_deg))
        )

        radius_km = _finite(
            physical_radius_km,
            name="physical_radius_km",
        )
        radius_au = radius_km / AU_KM
        if radius_au <= 0.0:
            raise ValueError("physical_radius_km must be positive.")
        if radius_au >= astrometric.distance_au:
            raise SolarSystemAppearanceGeometryError(
                "physical radius must be smaller than observer-target "
                "distance."
            )
        angular_diameter_arcsec = (
            2.0
            * asin(radius_au / astrometric.distance_au)
            * 180.0
            / pi
            * 3600.0
        )
        bright_limb_position_angle_deg = _bright_limb_position_angle(
            apparent_direction,
            sun_apparent_direction,
        )

        resource = observer_state.resource
        return SolarSystemApparentDisk(
            target=request.target,
            display_name=display_name,
            apparent_direction=apparent_direction,
            sun_apparent_direction=sun_apparent_direction,
            physical_radius_km=radius_km,
            radius_model=radius_model,
            angular_diameter_arcsec=angular_diameter_arcsec,
            phase_angle_deg=phase_angle_deg,
            illuminated_fraction=illuminated_fraction,
            bright_limb_position_angle_deg=(
                bright_limb_position_angle_deg
            ),
            provenance=(
                "target distance from accepted retarded astrometric direction",
                "Sun barycentric state evaluated at reception",
                "phase convention: Sun-target-observer",
                (
                    "bright-limb convention: "
                    + BRIGHT_LIMB_POSITION_ANGLE_CONVENTION
                ),
                f"ephemeris model: {resource.model}",
                f"ephemeris sha256: {resource.sha256}",
            ),
        )

    @staticmethod
    def _validate_directions(target, sun):
        target_astrometric = target.astrometric
        sun_astrometric = sun.astrometric
        target_request = target_astrometric.request
        sun_request = sun_astrometric.request
        if sun_request.target.strip().lower() != "sun":
            raise SolarSystemAppearanceIdentityError(
                "sun_apparent_direction must realize target='sun'."
            )
        if target_request.target.strip().lower() == "sun":
            raise SolarSystemAppearanceIdentityError(
                "apparent target must not be the Sun."
            )
        for name in (
            "centre",
            "reception_instant",
            "reception_time_scale",
        ):
            if getattr(target_request, name) != getattr(sun_request, name):
                raise SolarSystemAppearanceIdentityError(
                    "target and Sun directions must share centre, "
                    "reception instant, and time scale."
                )
        if target_astrometric.observer_state != sun_astrometric.observer_state:
            raise SolarSystemAppearanceIdentityError(
                "target and Sun directions must share one observer state."
            )
        if (
            target.geometry.coordinate_spec
            != sun.geometry.coordinate_spec
        ):
            target_spec = target.geometry.coordinate_spec
            sun_spec = sun.geometry.coordinate_spec
            for name in (
                "frame",
                "origin",
                "position_status",
                "instant",
                "time_scale",
            ):
                if getattr(target_spec, name) != getattr(sun_spec, name):
                    raise SolarSystemAppearanceIdentityError(
                        "target and Sun apparent directions must share one "
                        "apparent ICRS coordinate identity."
                    )

    @staticmethod
    def _validate_sun_state(state, request, observer):
        if state.request != request:
            raise SolarSystemAppearanceIdentityError(
                "source returned a different Sun state request."
            )
        if state.position_unit != "au":
            raise SolarSystemAppearanceIdentityError(
                "Sun position must use AU."
            )
        if state.resource != observer.resource:
            raise SolarSystemAppearanceIdentityError(
                "Sun and observer states must use the same resource."
            )
        if (
            state.provider_target_id is not None
            and state.provider_target_id != "10"
        ):
            raise SolarSystemAppearanceIdentityError(
                "Sun provider target must be NAIF ID 10."
            )
        if (
            state.provider_centre_id is not None
            and observer.provider_centre_id is not None
            and state.provider_centre_id != observer.provider_centre_id
        ):
            raise SolarSystemAppearanceIdentityError(
                "Sun and observer states must use the same provider centre."
            )
